"""
Daily cron job Lambda handler — runs every day at 09:00 UTC.

The cron job runs the member sync step and checks the schedule for reminders.
"""

import csv
import io
import os
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from sfk_scheduler.myweblog import fetch_current_members


MEMBERS_FIELDS = ["member_number", "name"]
SCHEDULE_KEYS = ("data/schedule.csv", "schedule.csv")


def _s3():
    return boto3.client("s3")


def _write_csv(s3, bucket, key, fieldnames, rows):
    """Write a list of dicts as CSV to S3."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=buf.getvalue().encode("utf-8"),
        ContentType="text/csv",
    )


def _read_csv(s3, bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    payload = response["Body"].read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(payload)))


def _load_schedule_rows(s3, bucket, schedule_keys=SCHEDULE_KEYS):
    for key in schedule_keys:
        try:
            rows = _read_csv(s3, bucket, key)
            print(f"[send_reminders] Loaded {len(rows)} rows from s3://{bucket}/{key}")
            return rows, key
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code not in {"NoSuchKey", "404"}:
                raise

    print(f"[send_reminders] No schedule file found in s3://{bucket}")
    return [], None


def _schedule_matches_today(row, today):
    try:
        scheduled_date = datetime.fromisoformat(row["week_start"]).date()
    except (KeyError, TypeError, ValueError):
        print(f"[send_reminders] Skipping invalid schedule row: {row}")
        return False

    return scheduled_date == today


def _send_reminder_email(row):
    # To be implemented.
    print(f"[send_reminders] Reminder pending for {row.get('name', 'unknown member')}")


# ---------------------------------------------------------------------------
# sync_members
# ---------------------------------------------------------------------------

def run_sync_members(s3, bucket, members_key, mwl_token):
    """Fetch current members from MyWebLog and persist them in S3."""
    print("[sync_members] Fetching members from MyWebLog...")

    members = fetch_current_members(mwl_token)
    rows = [{"member_number": number, "name": name} for name, number in members]
    _write_csv(s3, bucket, members_key, MEMBERS_FIELDS, rows)

    print(f"[sync_members] {len(members)} members written to s3://{bucket}/{members_key}")
    return {"synced": len(members)}


# ---------------------------------------------------------------------------
# send_reminders
# ---------------------------------------------------------------------------

def run_send_reminders(s3, bucket, today=None):
    """Send reminders for schedule rows that match today's date."""
    today = today or datetime.utcnow().date()
    rows, schedule_key = _load_schedule_rows(s3, bucket)

    if schedule_key is None:
        return {"checked": 0, "matched": 0}

    matching_rows = [row for row in rows if _schedule_matches_today(row, today)]

    for row in matching_rows:
        _send_reminder_email(row)

    print(f"[send_reminders] {len(matching_rows)} reminders matched for {today.isoformat()}")
    return {"checked": len(rows), "matched": len(matching_rows)}


# ---------------------------------------------------------------------------
# Lambda entry point
# ---------------------------------------------------------------------------

def lambda_handler(event, context):
    bucket = os.environ["SCHEDULE_BUCKET"]
    members_key = os.environ["MEMBERS_KEY"]
    mwl_token = os.environ["MWL_TOKEN"]

    s3 = _s3()
    results = {}

    try:
        results["sync_members"] = run_sync_members(s3, bucket, members_key, mwl_token)
    except Exception as exc:
        print(f"[sync_members] ERROR: {exc}")
        results["sync_members"] = {"error": str(exc)}

    try:
        results["send_reminders"] = run_send_reminders(s3, bucket)
    except Exception as exc:
        print(f"[send_reminders] ERROR: {exc}")
        results["send_reminders"] = {"error": str(exc)}

    print(f"Cron job complete: {results}")
    return results
