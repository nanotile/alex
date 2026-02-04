terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }
  
  # Using local backend - state will be stored in terraform.tfstate in this directory
  # This is automatically gitignored for security
}

provider "aws" {
  region = var.aws_region
}

# Data source for current caller identity
data "aws_caller_identity" "current" {}

# IAM role for SageMaker
resource "aws_iam_role" "sagemaker_role" {
  name = "alex-sagemaker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

# SageMaker Model — FinBERT financial sentiment analysis
resource "aws_sagemaker_model" "sentiment_model" {
  name               = "alex-sentiment-model"
  execution_role_arn = aws_iam_role.sagemaker_role.arn

  primary_container {
    image = var.sagemaker_image_uri
    environment = {
      HF_MODEL_ID = var.sentiment_model_name
      HF_TASK     = var.sagemaker_hf_task
    }
  }

  depends_on = [aws_iam_role_policy_attachment.sagemaker_full_access]
}

# Serverless Inference Config
resource "aws_sagemaker_endpoint_configuration" "sentiment_config" {
  name = "alex-sentiment-serverless-config"

  production_variants {
    model_name = aws_sagemaker_model.sentiment_model.name

    serverless_config {
      memory_size_in_mb = 3072
      max_concurrency   = 2
    }
  }
}

# Add a delay for IAM role propagation before creating endpoint
resource "time_sleep" "wait_for_iam_propagation" {
  depends_on = [
    aws_iam_role_policy_attachment.sagemaker_full_access
  ]

  create_duration = "15s"
}

# SageMaker Endpoint — FinBERT sentiment analysis
resource "aws_sagemaker_endpoint" "sentiment_endpoint" {
  name                 = "alex-sentiment-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.sentiment_config.name

  depends_on = [
    time_sleep.wait_for_iam_propagation
  ]

}