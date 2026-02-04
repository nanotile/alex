variable "aws_region" {
  description = "AWS region for resources"
  type        = string
}

variable "sagemaker_image_uri" {
  description = "URI of the SageMaker container image"
  type        = string
  default     = "763104351884.dkr.ecr.us-east-1.amazonaws.com/huggingface-pytorch-inference:1.13.1-transformers4.26.0-cpu-py39-ubuntu20.04"
}

variable "sentiment_model_name" {
  description = "Name of the HuggingFace model to use for financial sentiment analysis"
  type        = string
  default     = "ProsusAI/finbert"
}

variable "sagemaker_hf_task" {
  description = "HuggingFace task type for the model"
  type        = string
  default     = "text-classification"
}