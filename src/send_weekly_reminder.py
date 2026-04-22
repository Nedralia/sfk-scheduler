import csv
import io
import os
from datetime import datetime

import boto3

from sfk_scheduler.mailgun import send_email


def load_schedule_from_s3():
    bucket = os.environ["SCHEDULE_BUCKET"]
    key = os.environ["SCHEDULE_KEY"]
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=bucket, Key=key)
    content = response["Body"].read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(content)))


def find_assignment_for_date(rows, target_date):
    """Return the schedule row whose week_start matches target_date, or None."""
    for row in rows:
        if row["week_start"] == target_date:
            return row
    return None


def build_reminder_email(row):
    name = row["name"]
    week_start = row["week_start"]
    week_number = row["week_number"]
    email = row.get("email", "")
    subject = f"Cleaning reminder — week {week_number}"
    body = (
        f"Hello {name},\n\n"
        f"This is a reminder that you are scheduled to clean the club house this week.\n\n"
        f"Week starting: {week_start} (week {week_number})\n\n"
        "Thank you!"
    )
    return email, subject, body


def lambda_handler(event, context):
    today = datetime.utcnow().strftime("%Y-%m-%d")

    rows = load_schedule_from_s3()
    row = find_assignment_for_date(rows, today)

    if not row:
        print(f"No assignment found for {today}")
        return {"date": today, "sent": False}

    email, subject, body = build_reminder_email(row)

    if not email:
        print(f"No email address for {row['name']} — skipping")
        return {"date": today, "sent": False, "reason": "no_email"}

    api_key = os.environ["MAILGUN_API_KEY"]
    domain = os.environ["MAILGUN_DOMAIN"]

    send_email(api_key=api_key, domain=domain, to=email, subject=subject, body=body)

    print(f"Reminder sent to {row['name']} <{email}> for week starting {today}")
    return {"date": today, "sent": True, "recipient": email}
