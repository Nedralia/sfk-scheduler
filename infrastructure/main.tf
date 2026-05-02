data "aws_caller_identity" "current" {}

locals {
  schedule_bucket_name           = "${var.schedule_bucket_name_prefix}-${data.aws_caller_identity.current.account_id}-${var.aws_region}"
  website_bucket_name            = "${var.website_bucket_name_prefix}-${data.aws_caller_identity.current.account_id}-${var.aws_region}"
  website_hosted_zone_id         = var.website_hosted_zone_id == null ? "" : trimspace(var.website_hosted_zone_id)
  website_dns_automation_enabled = local.website_hosted_zone_id != ""
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

resource "aws_acm_certificate" "sfk_website" {
  provider          = aws.us_east_1
  domain_name       = var.website_domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = local.common_tags
}

resource "aws_route53_record" "sfk_website_certificate_validation" {
  for_each = local.website_dns_automation_enabled ? {
    for option in aws_acm_certificate.sfk_website.domain_validation_options : option.domain_name => {
      name   = option.resource_record_name
      record = option.resource_record_value
      type   = option.resource_record_type
    }
  } : {}

  allow_overwrite = true
  zone_id         = local.website_hosted_zone_id
  name            = each.value.name
  type            = each.value.type
  ttl             = 60
  records         = [each.value.record]
}

resource "aws_acm_certificate_validation" "sfk_website" {
  provider = aws.us_east_1
  count    = local.website_dns_automation_enabled ? 1 : 0

  certificate_arn         = aws_acm_certificate.sfk_website.arn
  validation_record_fqdns = [for record in aws_route53_record.sfk_website_certificate_validation : record.fqdn]
}

resource "aws_cloudfront_distribution" "sfk_website" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = var.website_index_document
  comment             = "CloudFront distribution for the SFK website"
  price_class         = var.website_cloudfront_price_class
  aliases             = var.website_activate_custom_domain ? [var.website_domain_name] : []

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
    cloudfront_default_certificate = !var.website_activate_custom_domain
    acm_certificate_arn            = var.website_activate_custom_domain ? aws_acm_certificate.sfk_website.arn : null
    ssl_support_method             = var.website_activate_custom_domain ? "sni-only" : null
    minimum_protocol_version       = var.website_activate_custom_domain ? "TLSv1.2_2021" : null
  }

  tags = local.common_tags
}

resource "aws_route53_record" "sfk_website_cloudfront_alias_ipv4" {
  count = local.website_dns_automation_enabled && var.website_activate_custom_domain ? 1 : 0

  zone_id = local.website_hosted_zone_id
  name    = var.website_domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.sfk_website.domain_name
    zone_id                = aws_cloudfront_distribution.sfk_website.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "sfk_website_cloudfront_alias_ipv6" {
  count = local.website_dns_automation_enabled && var.website_activate_custom_domain ? 1 : 0

  zone_id = local.website_hosted_zone_id
  name    = var.website_domain_name
  type    = "AAAA"

  alias {
    name                   = aws_cloudfront_distribution.sfk_website.domain_name
    zone_id                = aws_cloudfront_distribution.sfk_website.hosted_zone_id
    evaluate_target_health = false
  }
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
