# Git Utilities

Cross-platform Python utilities for common Git operations. All utilities work on Windows, Mac, and Linux.

## Quick Reference

| Utility | Purpose | Usage |
|---------|---------|-------|
| `github_new_branch.py` | Create new branch from main | `uv run github_new_branch.py` |
| `burn_it_down_start_new.py` | Delete broken branch & start fresh | `uv run burn_it_down_start_new.py` |
| `what_has_changed_in_branch.py` | Compare branches (multiple methods) | `uv run what_has_changed_in_branch.py` |
| `delete_branches.py` | Delete branches safely (with list view) | `uv run delete_branches.py` |

All utilities are **interactive** - just run them and follow the prompts!

---

## Available Utilities

### 1. `github_new_branch.py`
Create a new Git branch from main.

**Usage:**
```bash
# Recommended: Interactive mode - will prompt for branch name
uv run github_new_branch.py

# Alternative: Direct python execution with argument
python github_new_branch.py feature/my-new-feature
```

**Note:** Due to how `uv run` handles arguments, we recommend using interactive mode for simplicity. If you need to pass arguments directly, use `python` instead of `uv run`.

**What it does:**
1. Prompts for branch name (if not provided)
2. Checks out main
3. Pulls latest changes from origin/main
4. Creates and switches to new branch
5. Pushes new branch to GitHub

---

### 2. `burn_it_down_start_new.py`
Discard a broken feature branch and start a fresh one from clean main.

**Usage:**
```bash
# Recommended: Interactive mode (will prompt for branch names)
uv run burn_it_down_start_new.py

# Alternative: Direct python execution with arguments
python burn_it_down_start_new.py old-broken-branch new-fresh-branch
```

**What it does:**
1. Prompts for confirmation (this is destructive!)
2. Switches to main and resets to origin/main
3. Force-deletes the old branch locally and remotely
4. Creates a new fresh branch from clean main
5. Pushes new branch to GitHub

**� WARNING:** This permanently deletes the old branch. Use with caution!

---

### 3. `what_has_changed_in_branch.py`
Compare changes between branches using various methods with continuous workflow.

**Usage:**
```bash
uv run what_has_changed_in_branch.py
```

**Interactive Features:**
1. Lists all local and remote branches
2. Select a branch to compare against
3. Choose comparison method:
   - **Full code diff** - See all code changes
   - **File list with status** - See which files changed (M/A/D)
   - **Commit history** - See commit log with graph
   - **Summary statistics** - See files changed with line counts
   - **Compare specific file** - Diff a single file
   - **Show all methods** - Run all comparisons at once
4. **After each comparison**, choose to:
   - Run another comparison method (on same branch)
   - Compare against a different branch
   - Exit

**Example workflow:**
```
$ uv run what_has_changed_in_branch.py

Available branches:
  1) main
  2) feature/upgrade-agents
  3) feature/new-feature

Enter branch number: 1
Selected branch: main

Select comparison method:
1) Full code diff
2) File list with status
3) Commit history
4) Summary statistics
5) Compare specific file
6) Show all methods

Select option (1-6): 2

Files changed:
M       start_dev_server.py
A       new_file.py

What would you like to do next?
1) Run another comparison method
2) Compare against a different branch
3) Exit

Select option (1-3): 1

[Returns to comparison method menu...]
```

---

### 4. `delete_branches.py`
Delete Git branches with safety checks and comprehensive branch listing.

**Usage:**
```bash
uv run delete_branches.py
```

**Interactive Features:**
1. **Lists all branches** with status indicators:
   - Shows both local and remote branches
   - Indicates current branch
   - Marks protected branches (main/master)
   - Shows branch location (Local only, Remote only, or Both)

2. **Delete options**:
   - Delete by branch number (from the displayed list)
   - Delete by branch name (type the name)

3. **Safety Features**:
   - Cannot delete current branch
   - Cannot delete protected branches (main/master)
   - Confirmation prompt before deletion
   - Deletes both local and remote copies (if they exist)
   - Continuous loop for deleting multiple branches

**Example workflow:**
```
$ uv run delete_branches.py

=== Branch Status ===

Current branch: main

Branch List:
#    Branch Name                              Location
----------------------------------------------------------------------
1    feature/old-feature                      Local + Remote
2    feature/test-branch                      Local only
3    feature/upgrade-agents                   Local + Remote      (current)
4    main                                     Local + Remote      (protected)
5    old-experiment                           Remote only

Options:
1) Enter branch number to delete
2) Enter branch name to delete
3) Exit

Select option (1-3): 1
Enter branch number: 1

Branch to delete: feature/old-feature
  ✓ Local branch exists
  ✓ Remote branch exists

Are you sure you want to delete 'feature/old-feature'? (y/n): y

Deleting local branch 'feature/old-feature'...
✓ Local branch 'feature/old-feature' deleted

Deleting remote branch 'feature/old-feature'...
✓ Remote branch 'feature/old-feature' deleted from GitHub
```

**⚠️ WARNING:** Branch deletion is permanent. Deleted branches cannot be easily recovered.

---

## Running from Any Directory

You can run these utilities from any directory in your project:

```bash
# Recommended: Interactive mode (from alex root)
uv run KB_github_UTILITIES/git_utilities/github_new_branch.py

# Recommended: Interactive mode (from git_utilities directory)
cd KB_github_UTILITIES/git_utilities
uv run github_new_branch.py

# With arguments: Use python directly
cd KB_github_UTILITIES/git_utilities
python github_new_branch.py feature/my-branch
```

**Note:** We recommend using interactive mode with `uv run` for simplicity. If you need to pass arguments directly, use `python` instead of `uv run`.

---

## Bash Versions

The original bash versions (`.sh` files) are still available in the parent directory for reference, but the Python versions are recommended for cross-platform compatibility.

---

## Why Python Instead of Bash?

 **Cross-platform**: Works identically on Windows, Mac, and Linux
 **Better error handling**: Clear error messages and proper exception handling
 **Type hints**: Makes code more maintainable
 **No shell quirks**: Avoids platform-specific bash issues
 **Uses uv**: Follows modern Python tooling standards
 **More readable**: Easier to understand and modify