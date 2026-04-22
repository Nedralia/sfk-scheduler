import csv
import io
import os
from datetime import datetime, timedelta
from pathlib import Path

from sfk_scheduler.reminder import find_due_reminders

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEDULE_FILE = PROJECT_ROOT / "data" / "schedule.csv"


def load_schedule_rows():
    bucket_name = os.environ.get("SCHEDULE_BUCKET")
    object_key = os.environ.get("SCHEDULE_KEY")

    if bucket_name and object_key:
        import boto3
        s3 = boto3.client("s3")
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        content = response["Body"].read().decode("utf-8")
        return list(csv.DictReader(io.StringIO(content)))

    schedule_file = Path(os.environ.get("SCHEDULE_FILE", str(DEFAULT_SCHEDULE_FILE)))

    with open(schedule_file, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def lambda_handler(event, context):
    target_date = (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d")
    rows = load_schedule_rows()
    due_reminders = find_due_reminders(rows, target_date)

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

