#!/usr/bin/env python3
"""
Package the Retirement Lambda function using Docker for AWS compatibility.
"""

import os
import sys
import shutil
import tempfile
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and capture output."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout

def package_lambda():
    """Package the Lambda function with all dependencies."""
    
    # Get the directory containing this script
    retirement_dir = Path(__file__).parent.absolute()
    backend_dir = retirement_dir.parent
    
    # Create a temporary directory for packaging
    temp_dir = tempfile.mkdtemp()
    try:
        temp_path = Path(temp_dir)
        package_dir = temp_path / "package"
        package_dir.mkdir()

        print("Creating Lambda package using Docker...")

        # Export exact requirements from uv.lock (excluding the editable database package)
        print("Exporting requirements from uv.lock...")
        requirements_result = run_command(
            ["uv", "export", "--no-hashes", "--no-emit-project"],
            cwd=str(retirement_dir)
        )

        # Filter out packages that don't work in Lambda or are installed separately
        EXCLUDE_PREFIXES = [
            "-e ",           # editable local packages
            "pyperclip",     # clipboard library
            "anthropic",     # not needed — using Bedrock via LiteLLM
            "cohere",        # not needed
            "google-genai",  # not needed
            "google-auth",   # not needed
            "googleapis-",   # not needed
            "groq",          # not needed
            "mistralai",     # not needed
            "tokenizers",    # not needed (large Rust binary)
            "huggingface",   # not needed
            "hf-xet",       # not needed
            "cloud-sql",    # Google Cloud SQL, not AWS
            "pg8000",       # PostgreSQL driver (we use Data API)
            "sqlalchemy",   # ORM (we use Data API)
            "greenlet",     # SQLAlchemy async dep
            "temporalio",   # workflow orchestration, not needed
            "nexus-rpc",    # not needed
            "pydantic-evals",  # not needed
            "pydantic-graph",  # not needed
            "griffe",       # documentation generator
            "invoke",       # task runner
            "protobuf",     # gRPC serialization, not needed
            "types-protobuf",  # not needed
            "fastavro",     # Avro serialization, not needed
            "numpy",        # large, removed from package (breaks pandas-ta but saves ~30MB)
            "numba",        # LLVM JIT compiler for pandas-ta, ~100MB
            "llvmlite",     # LLVM bindings for numba, ~20MB
            "pandas",       # large, also matches pandas-ta (~50MB)
            "boto3",        # pre-installed in Lambda runtime
            "botocore",     # pre-installed in Lambda runtime
            "s3transfer",   # pre-installed in Lambda runtime
            "jmespath",     # pre-installed in Lambda runtime
        ]
        filtered_requirements = []
        for line in requirements_result.splitlines():
            if any(line.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
                print(f"Excluding: {line.split('==')[0] if '==' in line else line}")
                continue
            filtered_requirements.append(line)

        req_file = temp_path / "requirements.txt"
        req_file.write_text("\n".join(filtered_requirements))

        # Use Docker to install dependencies for Lambda's architecture
        docker_cmd = [
            "docker", "run", "--rm",
            "--platform", "linux/amd64",
            "-v", f"{temp_path}:/build",
            "-v", f"{backend_dir}/database:/database",
            "--entrypoint", "/bin/bash",
            "public.ecr.aws/lambda/python:3.12",
            "-c",
            """cd /build && pip install --target ./package -r requirements.txt && pip install --target ./package --no-deps /database && rm -rf ./package/boto3* ./package/botocore* ./package/s3transfer* ./package/jmespath* 2>/dev/null; find ./package -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null; find ./package -type d -name 'tests' -exec rm -rf {} + 2>/dev/null; find ./package -type d -name '*.dist-info' -exec rm -rf {} + 2>/dev/null; find ./package -name '*.pyc' -delete 2>/dev/null; rm -rf ./package/numpy* ./package/pandas* 2>/dev/null; true"""
        ]

        run_command(docker_cmd)

        # Copy Lambda handler, agent, templates, and observability
        shutil.copy(retirement_dir / "lambda_handler.py", package_dir)
        shutil.copy(retirement_dir / "agent.py", package_dir)
        shutil.copy(retirement_dir / "templates.py", package_dir)
        shutil.copy(retirement_dir / "observability.py", package_dir)

        # Create the zip file
        zip_path = retirement_dir / "retirement_lambda.zip"

        # Remove old zip if it exists
        if zip_path.exists():
            zip_path.unlink()

        # Create new zip
        print(f"Creating zip file: {zip_path}")
        run_command(
            ["zip", "-r", str(zip_path), "."],
            cwd=str(package_dir)
        )

        # Get file size
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"Package created: {zip_path} ({size_mb:.1f} MB)")

        return zip_path
    finally:
        # Clean up temp directory with sudo if needed (Docker creates files as root)
        try:
            shutil.rmtree(temp_dir)
        except PermissionError:
            # Docker created files as root, use sudo to clean up
            subprocess.run(["sudo", "rm", "-rf", temp_dir], check=False)

def deploy_lambda(zip_path):
    """Deploy the Lambda function to AWS. Uses S3 for packages > 50MB."""
    import boto3

    lambda_client = boto3.client('lambda')
    function_name = 'alex-retirement'
    size_mb = zip_path.stat().st_size / (1024 * 1024)

    print(f"Deploying to Lambda function: {function_name}")

    try:
        if size_mb > 50:
            sts = boto3.client('sts')
            account_id = sts.get_caller_identity()['Account']
            bucket = f"alex-lambda-packages-{account_id}"
            s3_key = "retirement/retirement_lambda.zip"
            print(f"Package is {size_mb:.1f} MB — uploading to s3://{bucket}/{s3_key}")
            s3 = boto3.client('s3')
            s3.upload_file(str(zip_path), bucket, s3_key)
            response = lambda_client.update_function_code(
                FunctionName=function_name, S3Bucket=bucket, S3Key=s3_key
            )
        else:
            with open(zip_path, 'rb') as f:
                response = lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=f.read()
                )
        print(f"Successfully updated Lambda function: {function_name}")
        print(f"Function ARN: {response['FunctionArn']}")
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"Lambda function {function_name} not found. Please deploy via Terraform first.")
        sys.exit(1)
    except Exception as e:
        print(f"Error deploying Lambda: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Package Retirement Lambda for deployment')
    parser.add_argument('--deploy', action='store_true', help='Deploy to AWS after packaging')
    args = parser.parse_args()
    
    # Check if Docker is available
    try:
        run_command(["docker", "--version"])
    except FileNotFoundError:
        print("Error: Docker is not installed or not in PATH")
        sys.exit(1)
    
    # Package the Lambda
    zip_path = package_lambda()
    
    # Deploy if requested
    if args.deploy:
        deploy_lambda(zip_path)

if __name__ == "__main__":
    main()