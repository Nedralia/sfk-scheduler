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

variable "mailgun_api_key" {
  description = "Mailgun API key for sending reminder emails."
  type        = string
  sensitive   = true
}

variable "mailgun_domain" {
  description = "Mailgun sending domain (e.g. mg.example.com)."
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days for the reminder Lambda."
  type        = number
  default     = 14
}

variable "tags" {
  description = "Additional tags applied to AWS resources."
  type        = map(string)
  default     = {}
}