import csv
import io
import os
from pathlib import Path
import boto3
from datetime import datetime, timedelta


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


def build_reminder(row):
    return {
        "name": row["name"],
        "email": row.get("email", ""),
        "week_start": row["week_start"],
        "week_number": row["week_number"],
        "subject": "Club House Cleaning Reminder",
        "body": (
            f"Hello {row['name']},\n\n"
            "Reminder that you are scheduled to clean the club house on:\n\n"
            f"{row['week_start']} (Week {row['week_number']})\n\n"
            "Thank you!"
        ),
    }


def lambda_handler(event, context):
    target_date = (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d")
    due_reminders = []

    for row in load_schedule_rows():
        if row["week_start"] == target_date:
            due_reminders.append(build_reminder(row))

    for reminder in due_reminders:
        print(
            "Reminder queued:",
            reminder["week_start"],
            reminder["name"],
            reminder["email"],
        )

    return {
        "target_date": target_date,
        "reminder_count": len(due_reminders),
        "reminders": due_reminders,
    }

