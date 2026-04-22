data "aws_caller_identity" "current" {}

locals {
  schedule_bucket_name = "${var.schedule_bucket_name_prefix}-${data.aws_caller_identity.current.account_id}-${var.aws_region}"
  common_tags = merge(
    {
      Project     = "sfk-scheduler"
      ManagedBy   = "Terraform"
      Environment = var.environment
    },
    var.tags,
  )
}

resource "aws_s3_bucket" "schedule_data" {
  bucket = local.schedule_bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_versioning" "schedule_data" {
  bucket = aws_s3_bucket.schedule_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "schedule_data" {
  bucket = aws_s3_bucket.schedule_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "schedule_data" {
  bucket = aws_s3_bucket.schedule_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_object" "schedule_csv" {
  bucket       = aws_s3_bucket.schedule_data.id
  key          = var.schedule_object_key
  source       = "${path.module}/../data/schedule.csv"
  etag         = filemd5("${path.module}/../data/schedule.csv")
  content_type = "text/csv"
}

module "reminder_lambda" {
  source = "./modules/reminder_lambda"

  function_name        = "sfk-scheduler-weekly-reminder"
  aws_region           = var.aws_region
  account_id           = data.aws_caller_identity.current.account_id
  schedule_bucket_name = aws_s3_bucket.schedule_data.bucket
  schedule_bucket_arn  = aws_s3_bucket.schedule_data.arn
  schedule_object_key  = var.schedule_object_key
  mailgun_api_key      = var.mailgun_api_key
  mailgun_domain       = var.mailgun_domain
  log_retention_days   = var.log_retention_days
  tags                 = local.common_tags
}
