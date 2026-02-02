variable "aws_region" {
  description = "AWS region for resources"
  type        = string
}

variable "min_capacity" {
  description = "Minimum capacity for Aurora Serverless v2 (in ACUs)"
  type        = number
  default     = 0.5
}

variable "max_capacity" {
  description = "Maximum capacity for Aurora Serverless v2 (in ACUs)"
  type        = number
  default     = 1
}

# Variable to control snapshot behavior during destruction
variable "skip_final_snapshot" {
  description = "If true, no snapshot will be created before the DB is destroyed."
  type        = bool
  default     = true # Default to true for development cost-savings
}