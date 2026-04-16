import csv
import io
import os
from pathlib import Path
import boto3
from datetime import datetime, timedelta


ses = boto3.client("ses")
s3 = boto3.client("s3")
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_SCHEDULE_FILE = PROJECT_ROOT / "data" / "schedule.csv"


def load_schedule_rows():
    bucket_name = os.environ.get("SCHEDULE_BUCKET")
    object_key = os.environ.get("SCHEDULE_KEY")

    if bucket_name and object_key:
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        content = response["Body"].read().decode("utf-8")
        return list(csv.DictReader(io.StringIO(content)))

    schedule_file = Path(os.environ.get("SCHEDULE_FILE", str(DEFAULT_SCHEDULE_FILE)))

    with open(schedule_file, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def lambda_handler(event, context):
    target_date = (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d")

    for row in load_schedule_rows():
        if row["week_start"] == target_date:
            name = row["name"]
            email = row["email"]

            ses.send_email(
                Source=os.environ["FROM_EMAIL"],
                Destination={"ToAddresses": [email]},
                Message={
                    "Subject": {"Data": "🏠 Club House Cleaning Reminder"},
                    "Body": {
                        "Text": {
                            "Data": f"""
Hello {name},

Reminder that you are scheduled to clean the club house on:

📅 {row['week_start']} (Week {row['week_number']})

Thank you!
"""
                    },
                },
            )

