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

resource "aws_s3_bucket" "sfk_website" {
  bucket = local.website_bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_versioning" "sfk_website" {
  bucket = aws_s3_bucket.sfk_website.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sfk_website" {
  bucket = aws_s3_bucket.sfk_website.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "sfk_website" {
  bucket = aws_s3_bucket.sfk_website.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "sfk_website" {
  name                              = "${local.website_bucket_name}-oac"
  description                       = "Origin access control for the sfk website bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "sfk_website" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = var.website_index_document
  comment             = "CloudFront distribution for the SFK website"
  price_class         = var.website_cloudfront_price_class

  origin {
    domain_name              = aws_s3_bucket.sfk_website.bucket_regional_domain_name
    origin_id                = aws_s3_bucket.sfk_website.id
    origin_access_control_id = aws_cloudfront_origin_access_control.sfk_website.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = aws_s3_bucket.sfk_website.id
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }
  }

  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/${var.website_error_document}"
    error_caching_min_ttl = 0
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/${var.website_error_document}"
    error_caching_min_ttl = 0
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = local.common_tags
}

resource "aws_s3_bucket_policy" "sfk_website_cloudfront_read" {
  bucket = aws_s3_bucket.sfk_website.id

  depends_on = [aws_s3_bucket_public_access_block.sfk_website]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServiceRead"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.sfk_website.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.sfk_website.arn
          }
        }
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# Daily cron job Lambda — sync members / auto-generate schedule / send reminder
# ---------------------------------------------------------------------------

data "archive_file" "cron_job_zip" {
  type        = "zip"
  output_path = "${path.module}/cron_job.zip"
  source_dir  = "${path.module}/../src"
  excludes = [
    "page",
    "page/**",
  ]
}

resource "aws_iam_role" "cron_job_lambda" {
  name = "sfk-scheduler-cron-job-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "cron_job_logging" {
  name = "sfk-scheduler-cron-job-logging"
  role = aws_iam_role.cron_job_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "cron_job_s3" {
  name = "sfk-scheduler-cron-job-s3"
  role = aws_iam_role.cron_job_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
        ]
        Resource = "${aws_s3_bucket.sfk_schedule_data.arn}/*"
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "cron_job_lambda" {
  name              = "/aws/lambda/sfk-scheduler-cron-job"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

resource "aws_lambda_function" "cron_job" {
  function_name = "sfk-scheduler-cron-job"
  role          = aws_iam_role.cron_job_lambda.arn
  runtime       = "python3.12"
  handler       = "cron_job.lambda_handler"

  filename         = data.archive_file.cron_job_zip.output_path
  source_code_hash = data.archive_file.cron_job_zip.output_base64sha256

  memory_size = 256
  timeout     = 120

  environment {
    variables = {
      SCHEDULE_BUCKET  = aws_s3_bucket.sfk_schedule_data.bucket
      SCHEDULE_KEY     = var.schedule_object_key
      MEMBERS_KEY      = var.members_object_key
      EXCLUDED_KEY     = var.excluded_object_key
      REMINDER_LOG_KEY = var.reminder_log_key
      MAILGUN_API_KEY  = var.mailgun_api_key
      MAILGUN_DOMAIN   = var.mailgun_domain
      MWL_TOKEN        = var.mwl_token
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.cron_job_lambda,
    aws_iam_role_policy.cron_job_logging,
    aws_iam_role_policy.cron_job_s3,
  ]

  tags = local.common_tags
}

resource "aws_cloudwatch_event_rule" "cron_job_daily" {
  name                = "sfk-scheduler-cron-job-daily"
  description         = "Triggers the SFK cron job Lambda every day at 09:00 UTC"
  schedule_expression = "cron(0 9 * * ? *)"
  tags                = local.common_tags
}

resource "aws_cloudwatch_event_target" "cron_job" {
  rule      = aws_cloudwatch_event_rule.cron_job_daily.name
  target_id = "cron-job-lambda"
  arn       = aws_lambda_function.cron_job.arn
}

resource "aws_lambda_permission" "cron_job_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cron_job.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cron_job_daily.arn
}
