# R2 Multi-Provider Fallback Implementation

## Overview

R2 (Blog Title Generator) has been completely refactored to remove all hardcoded model dependencies and implement an intelligent provider fallback chain:

**Provider Chain: Groq → Gemini → Cohere → OpenAI**

This eliminates the "model option barriers" and allows the system to work with whatever LLM provider is actually available and configured. Four providers give you maximum flexibility and balanced load distribution.

## What Changed

### 1. **r2_blog_title_generator.py** - Complete Refactor

#### Key Changes:
- **Removed hardcoded model lists** - No more GROQ_MODELS array with specific model names
- **Added multi-provider support** with four separate generation methods:
  - `generate_titles_with_groq()` - Attempts Groq API (no specific model assumed)
  - `generate_titles_with_gemini()` - Attempts Google Gemini API
  - `generate_titles_with_cohere()` - Attempts Cohere API
  - `generate_titles_with_openai()` - Attempts OpenAI API
- **Implemented fallback chain** via `generate_titles_with_fallback()` that tries each provider in order
- **Dynamic API availability** - Each provider is optional; the system only requires at least ONE API key
- **Provider tracking** - Records which provider was used to generate titles in the database

#### How It Works:

```
1. Check available API keys at startup
2. Attempt title generation with Groq
   - If successful → use Groq results
   - If fails for ANY reason → proceed to step 3
3. Attempt title generation with Gemini
   - If successful → use Gemini results
   - If fails for ANY reason → proceed to step 4
4. Attempt title generation with Cohere
   - If successful → use Cohere results
   - If fails for ANY reason → proceed to step 5
5. Attempt title generation with OpenAI
   - If successful → use OpenAI results
   - If fails → return error
```

#### Graceful Degradation:
- If GROQ_API_KEY is not set → automatically skips Groq
- If GEMINI_API_KEY is not set → automatically skips Gemini
- If OPENAI_API_KEY is not set → automatically skips OpenAI
- System only fails if NO API keys are configured

### 2. **.github/workflows/ghgf-automation.yml** - Updated Workflow

#### Changes:
- **Added environment variables** for all three providers:
  ```yaml
  GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
  GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  ```

- **Updated dependency installation**:
  ```bash
  pip install groq google-generativeai openai mysql-connector-python requests
  ```

- **Updated verification logic** - Now checks that at least ONE API key is configured:
  ```bash
  # Old: Required GROQ_API_KEY
  # New: Requires ONE OF (GROQ_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY)
  ```

## Setup Instructions

### Step 1: Add API Keys to GitHub Secrets

You need to add the following secrets to your GitHub repository:
1. Go to: **Settings → Secrets and variables → Actions → Secrets**
2. Create the following secrets (you only need to fill in the ones you have access to):

#### Required Secrets (Database):
- `DB_HOST` - MySQL database host *(already configured)*
- `DB_USER` - MySQL database user *(already configured)*
- `DB_PASSWORD` - MySQL database password *(already configured)*
- `DB_NAME` - MySQL database name *(already configured)*

#### LLM Provider API Keys (Add at least ONE):
- `GROQ_API_KEY` - Your Groq API key (get from https://console.groq.com)
- `GEMINI_API_KEY` - Your Google Gemini API key (get from https://aistudio.google.com/app/apikeys)
- `COHERE_API_KEY` - Your Cohere API key (get from https://dashboard.cohere.com/api-keys)
- `OPENAI_API_KEY` - Your OpenAI API key (get from https://platform.openai.com/api-keys)

#### Optional: Specify Model Names (If Not Set, Provider Default Will Be Used)
These are **completely optional** - if you don't set them, each provider will try its available/default model:

- `GROQ_MODEL` - Which Groq model to use (e.g., `llama-3.3-70b-versatile`)
- `GEMINI_MODEL` - Which Gemini model to use (e.g., `gemini-1.5-pro`)
- `COHERE_MODEL` - Which Cohere model to use (e.g., `command-r-plus`)
- `OPENAI_MODEL` - Which OpenAI model to use (e.g., `gpt-4-turbo`)

**This removes ALL hardcoded model assumptions.** The system will dynamically use whatever model you specify, or automatically detect available models.

### Step 2: Update Database Schema (Optional but Recommended)

The new code tracks which provider generated each title. To support this, add the `provider` column to the `blog_titles` table:

```sql
ALTER TABLE blog_titles ADD COLUMN provider VARCHAR(50) DEFAULT 'Unknown' AFTER ctr_score;
```

If this column doesn't exist, the system will still work but won't record which provider was used.

### Step 2.5: (Advanced) Configure Specific Models

If you know which models you want to use with each provider, you can optionally set:

```
GROQ_MODEL = llama-3.3-70b-versatile
GEMINI_MODEL = gemini-1.5-pro  
COHERE_MODEL = command-r-plus
OPENAI_MODEL = gpt-4-turbo
```

**But this is OPTIONAL.** If you leave these blank:
- Groq will auto-detect or use first available model
- Gemini will use `gemini-pro` as fallback
- Cohere will use `command-r` as fallback  
- OpenAI will use `gpt-3.5-turbo` as fallback

**Key Advantage:** You can now change models WITHOUT touching code - just update the GitHub secret and re-run the workflow.

### Step 3: Deploy Changes

Push the updated files to your GitHub repository:

1. **Updated R2 file**: `robots/r2_blog_title_generator.py`
2. **Updated workflow**: `.github/workflows/ghgf-automation.yml`
3. **This guide**: `MULTI_PROVIDER_FALLBACK_SETUP.md`

## How to Use

### With Just Groq:
```
Set: GROQ_API_KEY = [your key]
Skip: GEMINI_API_KEY, COHERE_API_KEY, OPENAI_API_KEY
Result: System will only use Groq
```

### With Two Providers:
```
Set: GROQ_API_KEY = [your key]
Set: GEMINI_API_KEY = [your key]
Skip: COHERE_API_KEY, OPENAI_API_KEY
Result: Uses Groq first, falls back to Gemini if Groq fails
```

### With Three Providers (Balanced Setup):
```
Set: GROQ_API_KEY = [your key]
Set: GEMINI_API_KEY = [your key]
Set: COHERE_API_KEY = [your key]
Skip: OPENAI_API_KEY
Result: Maximum flexibility with free/cheap providers
```

### With All Four (Recommended - Maximum Reliability):
```
Set: GROQ_API_KEY = [your key]
Set: GEMINI_API_KEY = [your key]
Set: COHERE_API_KEY = [your key]
Set: OPENAI_API_KEY = [your key]
Result: Maximum reliability - tries all four providers in order
```

### With No Groq (Start with Gemini):
```
Skip: GROQ_API_KEY
Set: GEMINI_API_KEY = [your key]
Set: COHERE_API_KEY = [your key]
Set: OPENAI_API_KEY = [your key]
Result: Tries Gemini → Cohere → OpenAI
```

## Error Handling

### Provider Failures:
Each provider failure is logged completely with:
- Error type and message
- Full traceback
- Next provider to attempt

Example log output:
```
[1/4] Trying Groq provider...
ERROR - Error Type: AuthenticationError
ERROR - Error Message: Invalid API key
[2/4] Groq failed, trying Gemini provider...
ERROR - Error Type: ConnectionError
[3/4] Gemini failed, trying Cohere provider...
SUCCESS - Generated 5 titles using Cohere
```

### Complete Failure:
If all providers fail, you'll see:
```
❌ ALL PROVIDERS FAILED
Could not generate titles from any provider:
  1. Groq - Failed or no API key
  2. Gemini - Failed or no API key
  3. Cohere - Failed or no API key
  4. OpenAI - Failed or no API key
```

## Testing the Setup

### To Test Locally (if you have terminal access):

```bash
# Set environment variables
export DB_HOST=your_host
export DB_USER=your_user
export DB_PASSWORD=your_password
export DB_NAME=your_db
export GROQ_API_KEY=your_groq_key
export GEMINI_API_KEY=your_gemini_key
export OPENAI_API_KEY=your_openai_key

# Run R2
python robots/r2_blog_title_generator.py
```

### To Test via GitHub:
1. Push all changes to your repository
2. Go to **Actions → GHGF 42-Robot Autonomous Blogging Pipeline**
3. Click **Run workflow**
4. Watch the logs - you should see:
   - Provider chain attempts
   - Successful title generation from one provider
   - Titles saved to database with provider information

## Model Configuration Philosophy

### ✅ What Was Removed
- **Hard-coded model names in code** - No more `llama-3.1-70b-versatile`, `mixtral-8x7b-32768`, etc. buried in Python
- **Model assumptions** - The code doesn't assume which models exist
- **Model barriers** - You're not locked into specific deprecated or restricted models

### ✅ How It Works Now
- **Fully configurable** - Specify any model via environment variables
- **Provider defaults** - If no model specified, each provider uses a sensible default
- **Dynamic detection** - Models can be changed without code changes
- **Graceful fallback** - If a model fails, moves to next provider (not just next model)

### Example: Changing Models Without Code
```bash
# Old way: Had to edit Python code
# Old: model="mixtral-8x7b-32768"

# New way: Just update GitHub Secret
Settings → Secrets → GROQ_MODEL = llama-3.3-70b-versatile
Re-run workflow
Done!
```

### The Real Solution to Model Availability
Instead of hoping a specific model exists on your account, R2 now:
1. **Doesn't assume any specific model exists**
2. **Tries to use your chosen model, or provider default**
3. **If a provider fails (any reason), moves to NEXT PROVIDER**
4. **Not just next model, but next entire provider**

This is what removes the "model option barriers."

## Frequently Asked Questions

### Q: What if I only have a Groq API key?
**A:** The system will only use Groq. If Groq fails (e.g., account restrictions, model not available), the pipeline will fail. Consider adding a backup provider for reliability.

### Q: What if my Groq account is restricted and no models work?
**A:** Simply don't set GROQ_API_KEY and set GEMINI_API_KEY and/or OPENAI_API_KEY instead. The fallback chain will skip Groq automatically.

### Q: Do I need to change anything else in the pipeline?
**A:** No! All downstream robots (R3-R36) use the titles from R2 regardless of which provider generated them. The provider field is metadata only.

### Q: What happens if all API keys fail at runtime?
**A:** The pipeline logs complete error details and R2 returns an error code. This cascades to R3-R12 as before. The solution is to ensure at least one working API key is configured.

### Q: Which provider should I use?
**A:** Rank them by cost + speed:
1. **Groq** - Fastest, free tier available, excellent for production
2. **Gemini** - Great quality, free tier available, very reliable
3. **Cohere** - Good quality, free trial + affordable pricing, balanced option
4. **OpenAI** - Highest quality, paid only (gpt-4-turbo), most expensive

**Recommended setup for balanced reliability:** Groq + Gemini + Cohere (all free tiers available)
**Premium setup for maximum quality:** Add OpenAI as the fallback
**Budget setup:** Groq + Gemini + Cohere (no OpenAI needed)

## Migration Notes

### Backward Compatibility:
- The new R2 is compatible with existing database schemas
- Existing blog_titles records remain unchanged
- The optional `provider` column tracks which LLM generated each title
- No changes required to R3-R36; they work as before

### Breaking Changes:
- None! The refactoring is 100% backward compatible
- All the same title generation logic remains
- Same database schema (except optional new `provider` column)
- Same output format

## Monitoring

The logs now include provider information:

```
Step 3: Generating 5 Title Variations (Multi-Provider Fallback)
[1/4] Trying Groq provider...
[2/4] Groq failed, trying Gemini provider...
[3/4] Gemini failed, trying Cohere provider...
✓ Successfully generated titles using Cohere

SUMMARY
  Provider Used: Cohere
  Titles Generated: 5
  Status: SUCCESS
```

## Next Steps

1. ✅ Review this setup guide
2. ✅ Add API keys to GitHub Secrets (at least one)
3. ✅ Optionally update database schema to add `provider` column
4. ✅ Push all changes to repository
5. ✅ Manually trigger the workflow to test
6. ✅ Monitor logs to see which provider is being used

## Support

If the workflow still fails:
1. Check that at least one API key is set in GitHub Secrets
2. Verify the API key is valid and has active quota
3. Check the complete error logs in the workflow run
4. Try with a different provider to isolate which API is failing
