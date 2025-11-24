#!/usr/bin/env python3
"""
Build and push Tagger agent Docker image to GCP Artifact Registry
"""

import subprocess
import sys
import os
import json

# Configuration
GCP_PROJECT = os.getenv("GCP_PROJECT", "gen-lang-client-0259050339")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
REPOSITORY = "alex-gcl-docker-repo"
IMAGE_NAME = "tagger-agent"
IMAGE_TAG = "latest"

# Full image path
IMAGE_URI = f"{GCP_REGION}-docker.pkg.dev/{GCP_PROJECT}/{REPOSITORY}/{IMAGE_NAME}:{IMAGE_TAG}"

print("=" * 60)
print("Building and Pushing Tagger Agent to GCP")
print("=" * 60)
print(f"Project: {GCP_PROJECT}")
print(f"Region: {GCP_REGION}")
print(f"Image URI: {IMAGE_URI}")
print()

# Change to backend directory (parent of tagger_gcp)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(backend_dir)
print(f"Build context: {backend_dir}")
print()

try:
    # Step 1: Configure Docker for GCP
    print("Step 1: Configuring Docker authentication...")
    result = subprocess.run(
        ["gcloud", "auth", "configure-docker", f"{GCP_REGION}-docker.pkg.dev"],
        check=True,
        capture_output=True,
        text=True
    )
    print("✅ Docker authentication configured")
    print()

    # Step 2: Build the Docker image
    print("Step 2: Building Docker image...")
    result = subprocess.run(
        [
            "docker", "build",
            "-t", IMAGE_URI,
            "-f", "tagger_gcp/Dockerfile",
            "."
        ],
        check=True,
        capture_output=False  # Show build output
    )
    print("✅ Docker image built successfully")
    print()

    # Step 3: Push to Artifact Registry
    print("Step 3: Pushing image to Artifact Registry...")
    result = subprocess.run(
        ["docker", "push", IMAGE_URI],
        check=True,
        capture_output=False
    )
    print("✅ Image pushed successfully")
    print()

    print("=" * 60)
    print("✅ Build and push complete!")
    print("=" * 60)
    print(f"Image URI: {IMAGE_URI}")
    print()
    print("Next steps:")
    print("1. Deploy to Cloud Run using terraform")
    print("2. Set environment variables (BEDROCK_MODEL_ID, CLOUD_SQL_*, etc.)")
    print("3. Test the /health endpoint")

except subprocess.CalledProcessError as e:
    print(f"❌ Error: {e}")
    if e.stdout:
        print(f"stdout: {e.stdout}")
    if e.stderr:
        print(f"stderr: {e.stderr}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
