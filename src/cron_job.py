"""
Daily cron job Lambda handler — runs every day at 09:00 UTC.

The cron job currently runs the member sync step.
"""

import csv
import io
import os

import boto3

from sfk_scheduler.myweblog import fetch_current_members


MEMBERS_FIELDS = ["member_number", "name"]


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
    members_key = os.environ["MEMBERS_KEY"]
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
