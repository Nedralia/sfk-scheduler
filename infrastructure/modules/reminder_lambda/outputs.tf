output "function_name" {
  description = "Name of the deployed Lambda function."
  value       = aws_lambda_function.weekly_reminder.function_name
}

output "function_arn" {
  description = "ARN of the deployed Lambda function."
  value       = aws_lambda_function.weekly_reminder.arn
}

output "eventbridge_rule_name" {
  description = "Name of the EventBridge rule that triggers the Lambda every Monday."
  value       = aws_cloudwatch_event_rule.every_monday.name
}
