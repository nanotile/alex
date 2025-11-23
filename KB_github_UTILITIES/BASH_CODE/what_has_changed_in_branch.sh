#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Git Branch Comparison Tool ===${NC}\n"

# Get all branches (local and remote)
echo -e "${BLUE}Fetching latest branches from remote...${NC}"
git fetch --all --quiet

# List all branches
echo -e "\n${YELLOW}Available branches:${NC}"
branches=($(git branch -a | grep -v HEAD | sed 's/remotes\/origin\///' | sed 's/^\* //' | sed 's/^  //' | sort -u))

# Display branches with numbers
for i in "${!branches[@]}"; do
    printf "%3d) %s\n" $((i+1)) "${branches[$i]}"
done

# Get branch selection
echo -e "\n${YELLOW}Enter branch number to compare against:${NC}"
read -p "Branch number: " branch_num

# Validate input
if ! [[ "$branch_num" =~ ^[0-9]+$ ]] || [ "$branch_num" -lt 1 ] || [ "$branch_num" -gt "${#branches[@]}" ]; then
    echo "Invalid branch number!"
    exit 1
fi

SELECTED_BRANCH="${branches[$((branch_num-1))]}"
echo -e "${GREEN}Selected branch: ${SELECTED_BRANCH}${NC}\n"

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}Current branch: ${CURRENT_BRANCH}${NC}\n"

# Menu for comparison method
echo -e "${YELLOW}Select comparison method:${NC}"
echo "1) Full code diff (git diff)"
echo "2) File list with status (git diff --name-status)"
echo "3) Commit history (git log)"
echo "4) Summary statistics (git diff --stat)"
echo "5) Compare specific file"
echo "6) Show all methods"
echo ""
read -p "Select option (1-6): " method

echo -e "\n${GREEN}======================================${NC}"

case $method in
    1)
        echo -e "${GREEN}Full code differences:${NC}\n"
        git diff "${SELECTED_BRANCH}"
        ;;
    2)
        echo -e "${GREEN}Files changed:${NC}\n"
        git diff --name-status "${SELECTED_BRANCH}"
        ;;
    3)
        echo -e "${GREEN}Commits in ${CURRENT_BRANCH} not in ${SELECTED_BRANCH}:${NC}\n"
        git log "${SELECTED_BRANCH}..HEAD" --oneline --graph --decorate
        ;;
    4)
        echo -e "${GREEN}Summary statistics:${NC}\n"
        git diff --stat "${SELECTED_BRANCH}"
        ;;
    5)
        echo -e "${YELLOW}Enter file path:${NC}"
        read -p "File: " filepath
        echo -e "\n${GREEN}Differences in ${filepath}:${NC}\n"
        git diff "${SELECTED_BRANCH}" -- "${filepath}"
        ;;
    6)
        echo -e "${GREEN}1. File list with status:${NC}\n"
        git diff --name-status "${SELECTED_BRANCH}"

        echo -e "\n${GREEN}2. Summary statistics:${NC}\n"
        git diff --stat "${SELECTED_BRANCH}"

        echo -e "\n${GREEN}3. Commit history:${NC}\n"
        git log "${SELECTED_BRANCH}..HEAD" --oneline --graph --decorate

        echo -e "\n${GREEN}4. Full code diff (showing first 50 lines):${NC}\n"
        git diff "${SELECTED_BRANCH}" | head -50
        echo -e "\n${YELLOW}(Full diff truncated - use option 1 to see all)${NC}"
        ;;
    *)
        echo "Invalid option!"
        exit 1
        ;;
esac

echo -e "\n${GREEN}======================================${NC}"
echo -e "${BLUE}Comparison complete!${NC}"
