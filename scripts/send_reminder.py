import csv
import os
from pathlib import Path
import boto3
from datetime import datetime, timedelta


ses = boto3.client("ses")
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_SCHEDULE_FILE = PROJECT_ROOT / "data" / "schedule.csv"


def lambda_handler(event, context):
    target_date = (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d")
    schedule_file = Path(os.environ.get("SCHEDULE_FILE", str(DEFAULT_SCHEDULE_FILE)))

    with open(schedule_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
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
                            }
                        },
                    },
                )

