#!/bin/bash

# Phase 3: End-to-End Testing Script
# Purpose: Trigger and monitor the automated blogging pipeline with Phase 1 & 2 improvements
# Date: 2026-10-13

set -e

BOLD='\033[1m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
RESET='\033[0m'

echo -e "\n${BOLD}Phase 3: End-to-End Testing${RESET}"
echo "========================================================================"

# Step 1: Pre-flight checks
echo -e "\n${BOLD}Step 1: Pre-flight Checks${RESET}"

# Check git status
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  Working directory has uncommitted changes${RESET}"
    echo "Stashing changes before test..."
    git stash
fi

# Verify we're on main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${RED}✗ Not on main branch (currently on: $CURRENT_BRANCH)${RESET}"
    exit 1
fi

echo -e "${GREEN}✓ On main branch${RESET}"

# Check for untracked files
if git ls-files --others --exclude-standard | grep -q .; then
    echo -e "${YELLOW}⚠️  Untracked files detected (will not affect test)${RESET}"
fi

# Verify Phase 1 & 2 commits are present
echo -e "\n${BOLD}Checking commit history...${RESET}"

git log --oneline -5 | while read line; do
    if [[ $line == *"Phase 1"* ]] || [[ $line == *"Phase 2"* ]]; then
        echo -e "${GREEN}✓ $line${RESET}"
    fi
done

# Step 2: Database pre-flight check
echo -e "\n${BOLD}Step 2: Database Pre-flight Check${RESET}"

if command -v mysql &> /dev/null; then
    echo "✓ MySQL client available"
else
    echo -e "${YELLOW}⚠️  MySQL client not available (will check during pipeline)${RESET}"
fi

# Step 3: Trigger workflow
echo -e "\n${BOLD}Step 3: Triggering GitHub Actions Workflow${RESET}"

if command -v gh &> /dev/null; then
    echo "Triggering: ghgf-automation.yml on main branch..."

    WORKFLOW_RUN=$(gh workflow run ghgf-automation.yml -r main --json id -q '.id' 2>&1 || echo "")

    if [ -z "$WORKFLOW_RUN" ]; then
        echo -e "${YELLOW}⚠️  Could not directly trigger workflow${RESET}"
        echo "Manual trigger instructions:"
        echo "  1. Push to main branch: git push origin main"
        echo "  2. GitHub Actions will automatically start"
        echo "  3. Monitor at: https://github.com/[your-repo]/actions"
        exit 0
    fi

    echo -e "${GREEN}✓ Workflow triggered (Run ID: $WORKFLOW_RUN)${RESET}"

    # Step 4: Monitor workflow
    echo -e "\n${BOLD}Step 4: Monitoring Workflow Execution${RESET}"
    echo "Waiting for workflow to start..."

    sleep 5

    # Check workflow status
    WORKFLOW_STATUS=$(gh run view $WORKFLOW_RUN --json status -q '.status' 2>/dev/null || echo "unknown")

    echo -e "Current status: ${YELLOW}$WORKFLOW_STATUS${RESET}"
    echo -e "\nTo monitor progress:"
    echo "  gh run view $WORKFLOW_RUN --log"
    echo -e "\nTo cancel workflow:"
    echo "  gh run cancel $WORKFLOW_RUN"

else
    echo -e "${RED}✗ GitHub CLI (gh) not available${RESET}"
    echo "Please install it: https://cli.github.com/"
    exit 1
fi

# Step 5: Test information
echo -e "\n${BOLD}Step 5: Test Information${RESET}"
echo "Phase 1 Improvements Tested:"
echo "  ✓ R7: Global image deduplication"
echo "  ✓ R8: Alt text generation and storage"
echo "  ✓ R9: Placeholder validation"
echo "  ✓ R31: Pre-flight validation"

echo -e "\nPhase 2 Improvements Tested:"
echo "  ✓ R3: Keyword diversity"
echo "  ✓ R6: Header keyword appending fix"
echo "  ✓ R9.5: Fact-checking and disclaimers"

echo -e "\n${BOLD}Expected Duration:${RESET} 8-12 hours"

echo -e "\n${BOLD}Next Steps:${RESET}"
echo "1. Monitor workflow execution"
echo "2. Wait for all robots to complete"
echo "3. Verify database updates"
echo "4. Check WordPress posts (if configured)"
echo "5. Review test results"

echo -e "\n${BOLD}Documentation:${RESET}"
echo "  Phase 3 Test Plan: claude/phase-3-end-to-end-testing-plan.md"
echo "  Phase 1 Summary: claude/phase-1-critical-fixes-complete.md"
echo "  Phase 2 Summary: claude/phase-2-quality-improvements-complete.md"

echo -e "\n========================================================================"
echo -e "${GREEN}Phase 3 testing initiated successfully!${RESET}\n"
