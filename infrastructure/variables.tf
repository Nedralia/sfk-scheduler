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

variable "tags" {
  description = "Additional tags applied to AWS resources."
  type        = map(string)
  default     = {}
}