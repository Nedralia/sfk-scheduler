data "aws_caller_identity" "current" {}

locals {
  schedule_bucket_name = "${var.schedule_bucket_name_prefix}-${data.aws_caller_identity.current.account_id}-${var.aws_region}"
  website_bucket_name  = "${var.website_bucket_name_prefix}-${data.aws_caller_identity.current.account_id}-${var.aws_region}"
  common_tags = merge(
    {
      Project     = "sfk-scheduler"
      ManagedBy   = "Terraform"
      Environment = var.environment
    },
    var.tags,
  )
}

resource "aws_s3_bucket" "sfk_schedule_data" {
  bucket = local.schedule_bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_versioning" "sfk_schedule_data" {
  bucket = aws_s3_bucket.sfk_schedule_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sfk_schedule_data" {
  bucket = aws_s3_bucket.sfk_schedule_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "sfk_schedule_data" {
  bucket = aws_s3_bucket.sfk_schedule_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_object" "sfk_schedule_csv" {
  bucket       = aws_s3_bucket.sfk_schedule_data.id
  key          = var.schedule_object_key
  source       = "${path.module}/../data/schedule.csv"
  etag         = filemd5("${path.module}/../data/schedule.csv")
  content_type = "text/csv"
}

resource "aws_s3_bucket" "sfk_website" {
  bucket = local.website_bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sfk_website" {
  bucket = aws_s3_bucket.sfk_website.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_website_configuration" "sfk_website" {
  bucket = aws_s3_bucket.sfk_website.id

  index_document {
    suffix = var.website_index_document
  }

  error_document {
    key = var.website_error_document
  }
}

resource "aws_s3_bucket_public_access_block" "sfk_website" {
  bucket = aws_s3_bucket.sfk_website.id

  block_public_acls       = true
  block_public_policy     = false
  ignore_public_acls      = true
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "sfk_website_public_read" {
  bucket = aws_s3_bucket.sfk_website.id

  depends_on = [aws_s3_bucket_public_access_block.sfk_website]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.sfk_website.arn}/*"
      }
    ]
  })
}

# module "reminder_lambda" {
#   source = "./modules/reminder_lambda"

#   function_name        = "sfk-scheduler-weekly-reminder"
#   aws_region           = var.aws_region
#   account_id           = data.aws_caller_identity.current.account_id
#   schedule_bucket_name = aws_s3_bucket.sfk_schedule_data.bucket
#   schedule_bucket_arn  = aws_s3_bucket.sfk_schedule_data.arn
#   schedule_object_key  = var.schedule_object_key
#   reminder_log_key     = "reminder_log.csv"
#   mailgun_api_key      = var.mailgun_api_key
#   mailgun_domain       = var.mailgun_domain
#   log_retention_days   = var.log_retention_days
#   tags                 = local.common_tags
# }
