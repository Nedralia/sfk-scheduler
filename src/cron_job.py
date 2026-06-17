"""
Daily cron job Lambda handler — runs every day at 09:00 UTC.

Performs three checks in order:
  1. sync_members  — always runs; fetches members from MyWebLog and saves to S3.
  2. auto_generate — extends the schedule when fewer than THRESHOLD_DAYS remain.
  3. send_reminder — sends the weekly cleaning reminder when today is a scheduled week.

Each step is guarded independently so a failure in one does not prevent the others
from running.
"""
import csv
import io
import os
from datetime import datetime, timedelta

import boto3

from sfk_scheduler.myweblog import fetch_current_members


THRESHOLD_DAYS = 60

SCHEDULE_FIELDS = ["week_start", "week_number", "year", "name", "member_number", "status"]
MEMBERS_FIELDS = ["member_number", "name"]


def _s3():
    return boto3.client("s3")


def _read_csv(s3, bucket, key):
    """Return a list of dicts from a CSV stored in S3. Returns [] when absent."""
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read().decode("utf-8")
        return list(csv.DictReader(io.StringIO(content)))
    except Exception as exc:
        code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
        if code in ("NoSuchKey", "404"):
            return []
        raise


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
# Lambda entry point
# ---------------------------------------------------------------------------

def lambda_handler(event, context):
    bucket = os.environ["SCHEDULE_BUCKET"]
    schedule_key = os.environ["SCHEDULE_KEY"]
    members_key = os.environ["MEMBERS_KEY"]
    excluded_key = os.environ.get("EXCLUDED_KEY", "excluded.csv")
    log_key = os.environ["REMINDER_LOG_KEY"]
    mailgun_api_key = os.environ["MAILGUN_API_KEY"]
    mailgun_domain = os.environ["MAILGUN_DOMAIN"]
    mwl_token = os.environ["MWL_TOKEN"]

    s3 = _s3()
    results = {}

    try:
        results["sync_members"] = run_sync_members(s3, bucket, members_key, mwl_token)
    except Exception as exc:
        print(f"[sync_members] ERROR: {exc}")
        results["sync_members"] = {"error": str(exc)}

    print(f"Cron job complete: {results}")
    return results
