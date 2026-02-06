# Outputs for CloudWatch monitoring

output "lambda_error_alarms" {
  description = "Lambda error rate alarm ARNs"
  value = {
    for name, alarm in aws_cloudwatch_metric_alarm.lambda_errors : name => alarm.arn
  }
}

output "lambda_duration_alarms" {
  description = "Lambda duration warning alarm ARNs"
  value = {
    for name, alarm in aws_cloudwatch_metric_alarm.lambda_duration : name => alarm.arn
  }
}

output "sqs_alarms" {
  description = "SQS alarm ARNs"
  value = {
    message_age  = aws_cloudwatch_metric_alarm.sqs_message_age.arn
    dlq_messages = aws_cloudwatch_metric_alarm.sqs_dlq_messages.arn
  }
}

output "setup_complete" {
  description = "Setup completion message"
  value       = <<-EOT

    CloudWatch Alarms Created:

    Lambda Error Rate Alarms (> ${var.lambda_error_rate_threshold}%):
    %{for name in var.lambda_function_names~}
      - ${name}-error-rate
    %{endfor~}

    Lambda Duration Warnings (> 4 min avg):
    %{for name in var.lambda_function_names~}
      - ${name}-duration-warning
    %{endfor~}

    SQS Alarms:
      - ${var.sqs_queue_name}-message-age (> ${var.sqs_queue_age_threshold}s)
      - ${var.sqs_queue_name}-dlq-messages (any messages)

    To add notifications, set alarm_actions to an SNS topic ARN:
      alarm_actions = ["arn:aws:sns:us-east-1:123456789:my-topic"]

    View alarms in console:
    https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#alarmsV2:
  EOT
}
