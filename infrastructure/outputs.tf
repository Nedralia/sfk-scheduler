output "schedule_bucket_name" {
  description = "S3 bucket storing the schedule CSV."
  value       = aws_s3_bucket.sfk_schedule_data.bucket
}

output "schedule_object_key" {
  description = "S3 object key for the schedule CSV."
  value       = aws_s3_object.sfk_schedule_csv.key
}

output "website_bucket_name" {
  description = "S3 bucket that hosts the web page."
  value       = aws_s3_bucket.sfk_website.bucket
}

output "website_cloudfront_distribution_id" {
  description = "CloudFront distribution ID serving the website bucket."
  value       = aws_cloudfront_distribution.sfk_website.id
}

output "website_cloudfront_domain_name" {
  description = "CloudFront domain name for the hosted web page."
  value       = aws_cloudfront_distribution.sfk_website.domain_name
}

output "cognito_user_pool_id" {
  description = "ID of the Cognito User Pool."
  value       = module.cognito.user_pool_id
}

output "cognito_web_client_id" {
  description = "ID of the Cognito web app client."
  value       = module.cognito.web_client_id
}

output "cognito_hosted_ui_domain" {
  description = "Cognito hosted-UI base URL."
  value       = module.cognito.hosted_ui_domain
}

# output "reminder_lambda_function_name" {
#   description = "Name of the weekly reminder Lambda function."
#   value       = module.reminder_lambda.function_name
# }

# output "reminder_eventbridge_rule" {
#   description = "EventBridge rule that triggers the Lambda every Monday."
#   value       = module.reminder_lambda.eventbridge_rule_name
# }
