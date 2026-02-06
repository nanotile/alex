# CloudWatch Alarms for Alex Agent Monitoring

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ---------------------
# Lambda Error Rate Alarms
# ---------------------

# Create an alarm for each Lambda function when error rate exceeds threshold
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = toset(var.lambda_function_names)

  alarm_name          = "${each.value}-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = var.lambda_error_rate_threshold

  # Math expression: (Errors / Invocations) * 100
  metric_query {
    id          = "error_rate"
    expression  = "(errors / invocations) * 100"
    label       = "Error Rate %"
    return_data = true
  }

  metric_query {
    id = "errors"
    metric {
      metric_name = "Errors"
      namespace   = "AWS/Lambda"
      period      = 300  # 5 minutes
      stat        = "Sum"
      dimensions = {
        FunctionName = each.value
      }
    }
    return_data = false
  }

  metric_query {
    id = "invocations"
    metric {
      metric_name = "Invocations"
      namespace   = "AWS/Lambda"
      period      = 300
      stat        = "Sum"
      dimensions = {
        FunctionName = each.value
      }
    }
    return_data = false
  }

  alarm_description = "Alarm when ${each.value} error rate exceeds ${var.lambda_error_rate_threshold}%"
  alarm_actions     = var.alarm_actions

  # Handle divide by zero when no invocations
  treat_missing_data = "notBreaching"

  tags = {
    Project   = var.project_name
    Component = "monitoring"
  }
}

# ---------------------
# Lambda Duration Alarms (for timeout warnings)
# ---------------------

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  for_each = toset(var.lambda_function_names)

  alarm_name          = "${each.value}-duration-warning"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Average"
  threshold           = 240000  # 4 minutes (80% of typical 5-minute timeout)

  dimensions = {
    FunctionName = each.value
  }

  alarm_description  = "Warning when ${each.value} average duration exceeds 4 minutes"
  alarm_actions      = var.alarm_actions
  treat_missing_data = "notBreaching"

  tags = {
    Project   = var.project_name
    Component = "monitoring"
  }
}

# ---------------------
# SQS Queue Age Alarm
# ---------------------

resource "aws_cloudwatch_metric_alarm" "sqs_message_age" {
  alarm_name          = "${var.sqs_queue_name}-message-age"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApproximateAgeOfOldestMessage"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Maximum"
  threshold           = var.sqs_queue_age_threshold

  dimensions = {
    QueueName = var.sqs_queue_name
  }

  alarm_description  = "Alarm when oldest message in ${var.sqs_queue_name} exceeds ${var.sqs_queue_age_threshold} seconds"
  alarm_actions      = var.alarm_actions
  treat_missing_data = "notBreaching"

  tags = {
    Project   = var.project_name
    Component = "monitoring"
  }
}

# ---------------------
# SQS Dead Letter Queue Alarm
# ---------------------

resource "aws_cloudwatch_metric_alarm" "sqs_dlq_messages" {
  alarm_name          = "${var.sqs_queue_name}-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 0  # Any message in DLQ is concerning

  dimensions = {
    QueueName = "${var.sqs_queue_name}-dlq"
  }

  alarm_description  = "Alarm when messages appear in dead letter queue"
  alarm_actions      = var.alarm_actions
  treat_missing_data = "notBreaching"

  tags = {
    Project   = var.project_name
    Component = "monitoring"
  }
}
