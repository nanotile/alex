GITHUB_BEST_PRACTICES.md

Here is a template specifically designed for your **"Digital Mind" / Alex** project. It accounts for the specific stack you are using (Python/uv, Terraform, Docker, AI Agents) and the security lessons we just covered.

Create a file named `GITHUB_BEST_PRACTICES.md` in your repository root and paste this in.

-----

# 🛡️ GitHub Best Practices & Workflow

**Project:** Alex (Digital Mind)
**Maintainer:** nanotile
**Last Updated:** 2025-11-22

This document outlines the standards for maintaining this repository to ensure security, stability, and sanity for "Future Me."

-----

## 1\. 🚨 Security (CRITICAL)

### Zero Tolerance for Secrets

  * **NEVER** commit API keys, passwords, or private keys to GitHub.
  * **ALWAYS** use `.env` files for local development and inject secrets via environment variables in production/Docker.
  * **Scanning:** If a secret is accidentally committed, **rotate it immediately**. Do not try to "hide" it with a new commit; the history is compromised.

### Key Management Strategy

  * **One Key Per Project:** Do not reuse the "Master" OpenAI key. Generate a specific `alex-project-key` for this repo.
  * **Billing Limits:** Ensure hard billing limits are set on all cloud provider accounts (OpenAI, AWS/GCP) to prevent runaway costs from leaked keys.

### Ignored Files

Ensure `.gitignore` always includes:

  * `.env`, `.env.backup`, `.env.*`
  * `*.pem`, `*.key` (SSH/SSL keys)
  * `terraform.tfvars` (Infrastructure secrets)
  * `venv/`, `.ve/`, `.venv/` (Virtual Environments)

-----

## 2\. 🌿 Branching Strategy

**The Golden Rule:** Direct pushes to `main` are forbidden for complex features.

### Workflow: Feature Branches

1.  **Create a Branch:** Name it clearly based on the task.
      * `feature/add-image-agent`
      * `fix/database-connection`
      * `infra/terraform-sagemaker`
2.  **Work & Test:** Make changes and verify they work locally.
3.  **Sync:** If `main` has moved ahead, merge `main` into your feature branch *before* finishing.
4.  **Merge:** Merge the branch into `main` (Squash & Merge is preferred to keep history clean).

-----

## 3\. 📦 Dependency Management

### Python (`uv`)

  * **Lockfiles:** The `uv.lock` file **MUST** be committed. It ensures the production server runs the exact same library versions as the development VM.
  * **Adding Libraries:**
    ```bash
    uv add pandas
    # Automatically updates pyproject.toml and uv.lock
    ```
  * **Syncing Environment:**
    ```bash
    uv sync
    ```

### Infrastructure (Terraform)

  * **Lockfiles:** Always commit `.terraform.lock.hcl`.
  * **State:** NEVER commit `.tfstate` files. Remote state should be stored in GCS/S3 buckets, not in the Git repo.

-----

## 4\. 💾 Data & Models (AI Specific)

### Large Files

  * **Datasets:** Do not commit large datasets (CSV, images, audio) to Git. Store them in cloud storage (GCS/S3) or a local `data/` folder that is git-ignored.
  * **Model Weights:** Do not commit heavy model files (`.pt`, `.h5`, `.bin`). Download them programmatically or mount them at runtime.

### Standard Gitignores for AI

```gitignore
data/
models/
outputs/
wandb/
*.pt
*.pth
*.ckpt
```

-----

## 5\. 📝 Commits & Documentation

### Commit Hygiene

  * **Atomic Commits:** One logical change per commit.
      * *Bad:* "Fixed stuff" (Contains changes to frontend, backend, and readme)
      * *Good:* "Refactor Agent class to support streaming"
  * **Message Format:** Use imperative mood ("Add feature" not "Added feature").

### Documentation

  * **README:** The root `README.md` must contain:
    1.  How to start the dev server.
    2.  How to sync dependencies (`uv sync`).
    3.  Required environment variables.
  * **Code Comments:** Focus on *why* complex logic exists, especially for the AI Agent logic where flow can be non-deterministic.

-----

## 6\. 🛠️ Emergency Recovery

If `main` breaks or history gets messy:

1.  **Don't Panic.**
2.  **Check Local History:** Use `git log` or VS Code Timeline to find the last working state.
3.  **Revert:** Use `git revert <commit-hash>` (safest) rather than `git reset` if the code has already been pushed.



----------------- kb github_new branch   --------------------
'''
# 1. Make sure you are starting from the latest main
git checkout main
git pull origin main

# 2. Create and switch to the new branch
git checkout -b feature/upgrade-agents

# 3. Push the new branch to GitHub (so it exists online)
git push -u origin feature/upgrade-agents

'''


--------------------------------------- BURN IT DOWN AND START AGAIN ------------
# ==========================================
# BURN IT DOWN & START NEW
# Use this to discard a broken feature branch
# and start a fresh one from clean main.

https://gemini.google.com/app/76918706123e0583

burn_it_down_start_new.sh <old branch name> <replace with new branch name>
------------------------------- PUSH TO MAIN WHEN BRANCH IS WORKING -----------------

# 1. Switch to main
git checkout main

# 2. Update main (just in case)
git pull origin main

# 3. Merge your good code into main
git merge feature/fix-frontend_VM2

# 4. Push the updated main to GitHub
git push origin main