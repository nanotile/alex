# Variables for CloudWatch monitoring

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "alex"
}

variable "lambda_error_rate_threshold" {
  description = "Error rate percentage threshold for Lambda alarms"
  type        = number
  default     = 5
}

variable "sqs_queue_age_threshold" {
  description = "Maximum message age in seconds before alarm triggers"
  type        = number
  default     = 600  # 10 minutes
}

variable "lambda_function_names" {
  description = "List of Lambda function names to monitor"
  type        = list(string)
  default = [
    "alex-planner",
    "alex-tagger",
    "alex-reporter",
    "alex-charter",
    "alex-retirement"
  ]
}

variable "sqs_queue_name" {
  description = "Name of the SQS queue to monitor"
  type        = string
  default     = "alex-analysis-jobs"
}

variable "alarm_actions" {
  description = "List of ARNs for alarm actions (SNS topics)"
  type        = list(string)
  default     = []
}
