# AWS Terraform Setup

This folder provisions the AWS infrastructure for the scheduler and static site hosting:

- An S3 bucket that stores scheduler data (for example `schedule.csv` and `members.csv`)
- An S3 bucket for the static website assets
- A CloudFront distribution in front of the website bucket
- A daily cron job Lambda (`src/cron_job.py`) for member synchronization
- IAM permissions for CloudWatch Logs and S3 read/write access
- A daily EventBridge trigger for the cron job Lambda

## Prerequisites

- Terraform 1.6+
- AWS credentials configured for the target account
- Required Terraform variables provided (for example `mwl_token`)

## Deploy

1. Copy `terraform.tfvars.example` to `terraform.tfvars`
2. Run:

```bash
terraform -chdir=infrastructure init
terraform -chdir=infrastructure plan
terraform -chdir=infrastructure apply
```

## Notes

- Deploy the web app assets to the website bucket, then invalidate the CloudFront distribution if you need the new content immediately.
