# AWS Terraform Setup

This folder provisions the AWS infrastructure for reminder emails:

- An S3 bucket that stores `schedule.csv`
- A Lambda function based on `scripts/send_reminder.py`
- IAM permissions for CloudWatch Logs, S3 reads, and SES sends
- A daily EventBridge trigger for the Lambda

## Prerequisites

- Terraform 1.6+
- AWS credentials configured for the target account
- An SES verified sender address or identity
- `data/schedule.csv` populated with the latest schedule

## Deploy

1. Copy `terraform.tfvars.example` to `terraform.tfvars`
2. Set `from_email` and `ses_resource_arn`
3. Run:

```bash
terraform -chdir=infrastructure init
terraform -chdir=infrastructure plan
terraform -chdir=infrastructure apply
```

## Notes

- Terraform uploads the current `data/schedule.csv` into S3 during apply.
- If the schedule changes locally, run `terraform -chdir=infrastructure apply` again to push the updated CSV.
- The Lambda expects `schedule.csv` rows to include an `email` column.