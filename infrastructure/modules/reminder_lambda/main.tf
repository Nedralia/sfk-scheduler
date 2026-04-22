data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/send_weekly_reminder.zip"

  source {
    content  = file("${path.module}/../../../src/send_weekly_reminder.py")
    filename = "send_weekly_reminder.py"
  }
}

resource "aws_iam_role" "lambda" {
  name = "${var.function_name}-role"

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

  tags = var.tags
}

resource "aws_iam_role_policy" "lambda_logging" {
  name = "${var.function_name}-logging"
  role = aws_iam_role.lambda.id

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
        Resource = "arn:aws:logs:${var.aws_region}:${var.account_id}:*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_s3_schedule_read" {
  name = "${var.function_name}-s3-schedule-read"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${var.schedule_bucket_arn}/${var.schedule_object_key}"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_s3_log_readwrite" {
  name = "${var.function_name}-s3-log-readwrite"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = "${var.schedule_bucket_arn}/${var.reminder_log_key}"
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

resource "aws_lambda_function" "weekly_reminder" {
  function_name = var.function_name
  role          = aws_iam_role.lambda.arn
  runtime       = "python3.12"
  handler       = "send_weekly_reminder.lambda_handler"

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  memory_size = 128
  timeout     = 30

  environment {
    variables = {
      SCHEDULE_BUCKET    = var.schedule_bucket_name
      SCHEDULE_KEY       = var.schedule_object_key
      REMINDER_LOG_KEY   = var.reminder_log_key
      MAILGUN_API_KEY    = var.mailgun_api_key
      MAILGUN_DOMAIN     = var.mailgun_domain
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy.lambda_logging,
    aws_iam_role_policy.lambda_s3_schedule_read,
    aws_iam_role_policy.lambda_s3_log_readwrite,
  ]

  tags = var.tags
}

resource "aws_cloudwatch_event_rule" "every_monday" {
  name                = "${var.function_name}-every-monday"
  description         = "Triggers the weekly reminder Lambda every Monday at 07:00 UTC"
  schedule_expression = "cron(0 7 ? * MON *)"
  tags                = var.tags
}

resource "aws_cloudwatch_event_target" "weekly_reminder" {
  rule      = aws_cloudwatch_event_rule.every_monday.name
  target_id = "weekly-reminder-lambda"
  arn       = aws_lambda_function.weekly_reminder.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.weekly_reminder.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_monday.arn
}
