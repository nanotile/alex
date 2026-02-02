variable "aws_region" {
  description = "AWS region for resources"
  type        = string
}

variable "bedrock_embedding_model" {
  description = "Bedrock embedding model ID (e.g., amazon.titan-embed-text-v2:0)"
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}

variable "bedrock_region" {
  description = "AWS region for Bedrock (may differ from main region)"
  type        = string
  default     = ""  # If empty, uses aws_region
}