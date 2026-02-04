
output "sagemaker_endpoint_name" {
  description = "Name of the SageMaker sentiment endpoint"
  value       = aws_sagemaker_endpoint.sentiment_endpoint.name
}

output "sagemaker_endpoint_arn" {
  description = "ARN of the SageMaker sentiment endpoint"
  value       = aws_sagemaker_endpoint.sentiment_endpoint.arn
}

output "setup_instructions" {
  description = "Instructions for setting up environment variables"
  value = <<-EOT

    ✅ SageMaker FinBERT sentiment endpoint deployed successfully!

    Endpoint name: alex-sentiment-endpoint
    Set SAGEMAKER_SENTIMENT_ENDPOINT=alex-sentiment-endpoint in your .env

    Follow the instructions in the guide to test the endpoint.
  EOT
}
