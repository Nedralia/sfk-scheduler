variable "function_name" {
  description = "Name of the Lambda function."
  type        = string
}

variable "aws_region" {
  description = "AWS region used when building IAM resource ARNs."
  type        = string
}

variable "account_id" {
  description = "AWS account ID used when building IAM resource ARNs."
  type        = string
}

variable "schedule_bucket_name" {
  description = "Name of the S3 bucket that holds the schedule CSV."
  type        = string
}

variable "schedule_bucket_arn" {
  description = "ARN of the S3 bucket that holds the schedule CSV."
  type        = string
}

variable "schedule_object_key" {
  description = "S3 object key for the schedule CSV file."
  type        = string
}

variable "reminder_log_key" {
  description = "S3 object key for the reminder log CSV file."
  type        = string
  default     = "reminder_log.csv"
}

variable "mailgun_api_key" {
  description = "Mailgun API key."
  type        = string
  sensitive   = true
}

variable "mailgun_domain" {
  description = "Mailgun sending domain (e.g. mg.example.com)."
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days."
  type        = number
  default     = 14
}

variable "tags" {
  description = "Tags to apply to all resources."
  type        = map(string)
  default     = {}
}
