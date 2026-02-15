import csv
import os
import boto3
from datetime import datetime, timedelta


ses = boto3.client("ses")


def lambda_handler(event, context):
    target_date = (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d")

    with open("/tmp/schedule.csv", "r") as f:
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

