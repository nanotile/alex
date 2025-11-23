#!/bin/bash

# ==========================================
# BURN IT DOWN & START NEW
# Use this to discard a broken feature branch
# and start a fresh one from clean main.

https://gemini.google.com/app/76918706123e0583
# ==========================================

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Get Arguments (or prompt if missing)
OLD_BRANCH=$1
NEW_BRANCH=$2

if [ -z "$OLD_BRANCH" ]; then
    read -p "Enter the name of the BROKEN branch to delete: " OLD_BRANCH
fi

if [ -z "$NEW_BRANCH" ]; then
    read -p "Enter the name of the NEW branch to create: " NEW_BRANCH
fi

# 2. Confirmation Safety Check
echo -e "${RED}WARNING: This will force-delete '$OLD_BRANCH' locally and on GitHub.${NC}"
read -p "Are you sure you want to proceed? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo -e "\n${YELLOW}Step 1: Switching to Main and cleaning up...${NC}"
git checkout main
git fetch origin
# Hard reset main to match GitHub exactly
git reset --hard origin/main

echo -e "\n${YELLOW}Step 2: Deleting the old branch ('$OLD_BRANCH')...${NC}"
# Delete local copy (force)
git branch -D "$OLD_BRANCH" 2>/dev/null || echo "Local branch '$OLD_BRANCH' not found (skipping)."

# Delete remote copy
git push origin --delete "$OLD_BRANCH" 2>/dev/null || echo "Remote branch '$OLD_BRANCH' not found on GitHub (skipping)."

echo -e "\n${YELLOW}Step 3: Creating fresh branch ('$NEW_BRANCH')...${NC}"
git checkout -b "$NEW_BRANCH"

echo -e "\n${YELLOW}Step 4: Pushing to GitHub...${NC}"
git push -u origin "$NEW_BRANCH"

echo -e "\n${GREEN}DONE! You are now on '$NEW_BRANCH' which is a clean copy of main.${NC}"