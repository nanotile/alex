#!/bin/bash

# Get branch name from parameter, or use default if not provided
BRANCH_NAME="${1:-failed-to-create-new-branch}"

# 1. Make sure you are starting from the latest main
git checkout main
git pull origin main

# 2. Create and switch to the new branch
git checkout -b "$BRANCH_NAME"

# 3. Push the new branch to GitHub (so it exists online)
git push -u origin "$BRANCH_NAME"