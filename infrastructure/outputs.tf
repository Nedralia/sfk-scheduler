output "lambda_function_name" {
  description = "Name of the deployed reminder Lambda."
  value       = aws_lambda_function.send_reminder.function_name
}

output "schedule_bucket_name" {
  description = "S3 bucket storing the schedule CSV."
  value       = aws_s3_bucket.schedule_data.bucket
}

output "schedule_object_key" {
  description = "S3 object key used by the reminder Lambda."
  value       = aws_s3_object.schedule_csv.key
}

output "eventbridge_rule_name" {
  description = "Name of the EventBridge rule that triggers the Lambda."
  value       = aws_cloudwatch_event_rule.send_reminder_daily.name
}