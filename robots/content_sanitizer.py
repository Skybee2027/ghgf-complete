#!/usr/bin/env python3
"""
Content sanitizer for generated blog posts.

Runs on every post body before it is saved, so new posts cannot carry:
  - Markdown code fences (```html ... ```) as visible text
  - YAML/front-matter blocks (--- key: value ---)
  - A duplicate title repeated at the top of the body
  - Empty image placeholders (![]() or <img src="">)
  - Placeholder text (example.com, XYZ, lorem ipsum, TODO, [insert ...])
  - Truncated endings (body stops mid-sentence)
  - Health posts without a medical disclaimer

clean_content() returns (cleaned_html, problems). Problems are blocking:
a post with any problem must not be marked ready for WordPress.
"""

import re

HEALTH_KEYWORDS = re.compile(
    r"\b(health|fitness|sleep|diet|nutrition|supplement|probiotic|medical|symptom|exercise|weight)\b",
    re.IGNORECASE,
)

DISCLAIMER_TEXT = "health disclaimer"

PLACEHOLDER_PATTERNS = [
    (re.compile(r"example\.(com|org|net)", re.IGNORECASE), "placeholder domain (example.com)"),
    (re.compile(r"lorem ipsum", re.IGNORECASE), "lorem ipsum filler"),
    (re.compile(r"\bXYZ\b"), "placeholder product name (XYZ)"),
    (re.compile(r"\bTODO\b|\bTBD\b|\bFIXME\b"), "unfinished marker (TODO/TBD/FIXME)"),
    (re.compile(r"\[(insert|add|your)[^\]]*\]", re.IGNORECASE), "bracketed placeholder"),
    (re.compile(r"\{\{.*?\}\}"), "unrendered template variable"),
]

CODE_FENCE_LINE = re.compile(r"^\s*```[a-zA-Z0-9_-]*\s*$", re.MULTILINE)
EMPTY_MARKDOWN_IMAGE = re.compile(r"!\[[^\]]*\]\(\s*\)")
EMPTY_HTML_IMAGE = re.compile(r"<img[^>]*src=[\"']\s*[\"'][^>]*>", re.IGNORECASE)
FRONT_MATTER = re.compile(r"\A\s*---\s*\n(?:[A-Za-z0-9_-]+\s*:.*\n?)+?\s*---\s*\n?", re.MULTILINE)
HEADING_RE = re.compile(r"<h([1-2])[^>]*>(.*?)</h\1>", re.IGNORECASE | re.DOTALL)


def strip_code_fences(text):
    """Remove ``` fence lines. Keeps the code between them, since it is the post body."""
    return CODE_FENCE_LINE.sub("", text)


def strip_front_matter(text):
    """Remove a leading --- key: value --- block."""
    return FRONT_MATTER.sub("", text, count=1)


def strip_empty_images(text):
    """Remove image tags and markdown images that have no source."""
    text = EMPTY_MARKDOWN_IMAGE.sub("", text)
    text = EMPTY_HTML_IMAGE.sub("", text)
    return text


def _plain(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip().lower()


def remove_duplicate_title(text, title):
    """Remove a leading h1/h2 that only repeats the post title."""
    if not title:
        return text
    target = _plain(title)
    stripped = text.lstrip()
    m = HEADING_RE.match(stripped)
    if m and _plain(m.group(2)) == target:
        return stripped[m.end():].lstrip()
    # Also catch a title repeated as the first line inside an HTML wrapper
    return text


def plain_text(text):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def is_truncated(text):
    """True when the body ends mid-sentence."""
    tail = plain_text(text)
    if not tail:
        return True
    return tail[-1] not in '.!?)"\'”’:'


def find_placeholders(text):
    found = []
    for pattern, label in PLACEHOLDER_PATTERNS:
        if pattern.search(text):
            found.append(label)
    return found


def has_disclaimer(text):
    return DISCLAIMER_TEXT in text.lower()


def clean_content(text, title=None):
    """
    Clean and validate a generated post body.
    Returns (cleaned_html, problems). An empty problems list means the body is ready
    for the next robot; any problem blocks publishing.
    """
    original = text or ""
    cleaned = strip_code_fences(original)
    cleaned = strip_front_matter(cleaned)
    cleaned = remove_duplicate_title(cleaned, title)
    cleaned = strip_empty_images(cleaned)
    cleaned = cleaned.strip()

    problems = []
    if not cleaned:
        problems.append("body is empty after cleaning")
    if "```" in cleaned:
        problems.append("code fence still present")
    for label in find_placeholders(cleaned):
        problems.append(label)
    if is_truncated(cleaned):
        problems.append("body ends mid-sentence")
    if HEALTH_KEYWORDS.search(plain_text(cleaned)) and not has_disclaimer(cleaned):
        problems.append("health content missing medical disclaimer")
    return cleaned, problems


if __name__ == "__main__":
    import sys
    body = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 else ""
    out, probs = clean_content(body, sys.argv[2] if len(sys.argv) > 2 else None)
    print(out)
    print("PROBLEMS:", probs or "none")
