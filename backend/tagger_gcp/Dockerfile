# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install uv for faster dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PYTHONPATH=/app:/app/database_gcp

# Copy database_gcp library first (dependency)
COPY database_gcp/ /app/database_gcp/

# Copy tagger application files
COPY tagger_gcp/pyproject.toml ./
COPY tagger_gcp/agent.py tagger_gcp/main.py tagger_gcp/schemas.py tagger_gcp/templates.py ./

# Install dependencies using uv
RUN uv pip install --no-cache -e /app/database_gcp && \
    uv pip install --no-cache fastapi uvicorn openai-agents[litellm] pydantic python-dotenv tenacity boto3

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Run the FastAPI server
CMD ["python", "main.py"]
