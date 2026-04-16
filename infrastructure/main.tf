data "aws_caller_identity" "current" {}

data "archive_file" "send_reminder" {
  type        = "zip"
  output_path = "${path.module}/send_reminder.zip"

  source {
    content  = file("${path.module}/../scripts/send_reminder.py")
    filename = "send_reminder.py"
  }
}

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

resource "aws_iam_role" "send_reminder_lambda" {
  name = "${var.lambda_function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "lambda_logging" {
  name = "${var.lambda_function_name}-logging"
  role = aws_iam_role.send_reminder_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Effect   = "Allow"
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_schedule_access" {
  name = "${var.lambda_function_name}-schedule-access"
  role = aws_iam_role.send_reminder_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
        ]
        Effect = "Allow"
        Resource = [
          "${aws_s3_bucket.schedule_data.arn}/${var.schedule_object_key}",
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_ses" {
  name = "${var.lambda_function_name}-ses"
  role = aws_iam_role.send_reminder_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail",
        ]
        Effect = "Allow"
        Resource = [
          var.ses_resource_arn,
        ]
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "send_reminder" {
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

resource "aws_lambda_function" "send_reminder" {
  function_name = var.lambda_function_name
  role          = aws_iam_role.send_reminder_lambda.arn
  runtime       = "python3.12"
  handler       = "send_reminder.lambda_handler"

  filename         = data.archive_file.send_reminder.output_path
  source_code_hash = data.archive_file.send_reminder.output_base64sha256

  memory_size = 128
  timeout     = 30

  environment {
    variables = {
      FROM_EMAIL      = var.from_email
      SCHEDULE_BUCKET = aws_s3_bucket.schedule_data.bucket
      SCHEDULE_KEY    = var.schedule_object_key
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.send_reminder,
    aws_iam_role_policy.lambda_logging,
    aws_iam_role_policy.lambda_schedule_access,
    aws_iam_role_policy.lambda_ses,
  ]

  tags = local.common_tags
}

resource "aws_cloudwatch_event_rule" "send_reminder_daily" {
  name                = "${var.lambda_function_name}-daily"
  description         = "Runs the reminder Lambda every day"
  schedule_expression = var.reminder_schedule_expression
  tags                = local.common_tags
}

resource "aws_cloudwatch_event_target" "send_reminder_daily" {
  rule      = aws_cloudwatch_event_rule.send_reminder_daily.name
  target_id = "send-reminder-lambda"
  arn       = aws_lambda_function.send_reminder.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.send_reminder.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.send_reminder_daily.arn
}