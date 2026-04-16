# AWS Terraform Setup

This folder provisions the AWS infrastructure for reminder processing:

- An S3 bucket that stores `schedule.csv`
- A Lambda function based on `scripts/send_reminder.py`
- IAM permissions for CloudWatch Logs and S3 reads
- A daily EventBridge trigger for the Lambda

## Prerequisites

- Terraform 1.6+
- AWS credentials configured for the target account
- `data/schedule.csv` populated with the latest schedule

## Deploy

1. Copy `terraform.tfvars.example` to `terraform.tfvars`
2. Run:

```bash
terraform -chdir=infrastructure init
terraform -chdir=infrastructure plan
terraform -chdir=infrastructure apply
```

## Notes

- Terraform uploads the current `data/schedule.csv` into S3 during apply.
- If the schedule changes locally, run `terraform -chdir=infrastructure apply` again to push the updated CSV.
- The Lambda reads due reminders and logs the generated reminder payloads.
- If you wire in another email provider later, `scripts/send_reminder.py` is the place to add that integration.