output "schedule_bucket_name" {
  description = "S3 bucket storing the schedule CSV."
  value       = aws_s3_bucket.schedule_data.bucket
}

output "schedule_object_key" {
  description = "S3 object key for the schedule CSV."
  value       = aws_s3_object.schedule_csv.key
}

output "reminder_lambda_function_name" {
  description = "Name of the weekly reminder Lambda function."
  value       = module.reminder_lambda.function_name
}

output "reminder_eventbridge_rule" {
  description = "EventBridge rule that triggers the Lambda every Monday."
  value       = module.reminder_lambda.eventbridge_rule_name
}
