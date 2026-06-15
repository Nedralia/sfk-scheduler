variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "eu-north-1"
}

variable "environment" {
  description = "Deployment environment tag."
  type        = string
  default     = "prod"
}

variable "schedule_bucket_name_prefix" {
  description = "Prefix used to build the S3 bucket name that stores the schedule CSV."
  type        = string
  default     = "sfk-scheduler-data"
}

variable "schedule_object_key" {
  description = "S3 object key for the schedule CSV file."
  type        = string
  default     = "schedule.csv"
}

variable "website_bucket_name_prefix" {
  description = "Prefix used to build the S3 bucket name that stores static web assets."
  type        = string
  default     = "sfk-scheduler-web"
}

variable "website_index_document" {
  description = "Index document served by S3 website hosting."
  type        = string
  default     = "index.html"
}

variable "website_error_document" {
  description = "Error document served by S3 website hosting."
  type        = string
  default     = "index.html"
}

variable "website_cloudfront_price_class" {
  description = "CloudFront price class used for the website distribution."
  type        = string
  default     = "PriceClass_100"
}

variable "mailgun_api_key" {
  description = "Mailgun API key for sending reminder emails."
  type        = string
  sensitive   = true
}

variable "mailgun_domain" {
  description = "Mailgun sending domain (e.g. mg.example.com)."
  type        = string
}

variable "members_object_key" {
  description = "S3 object key for the members CSV file (written by sync_members)."
  type        = string
  default     = "members.csv"
}

variable "excluded_object_key" {
  description = "S3 object key for the excluded members CSV file."
  type        = string
  default     = "excluded.csv"
}

variable "reminder_log_key" {
  description = "S3 object key for the reminder log CSV file."
  type        = string
  default     = "reminder_log.csv"
}

variable "mwl_token" {
  description = "MyWebLog API bearer token used by the cron job to sync members."
  type        = string
  sensitive   = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days."
  type        = number
  default     = 14
}

variable "tags" {
  description = "Additional tags applied to AWS resources."
  type        = map(string)
  default     = {}
}