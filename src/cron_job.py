"""
Daily cron job Lambda handler — runs every day at 09:00 UTC.

Performs three checks in order:
  1. sync_members  — always runs; fetches members from MyWebLog and saves to S3.
  2. auto_generate — on March 1, extends the S3-backed schedule up to one year ahead.
  3. send_reminder — sends the weekly cleaning reminder when today is a scheduled week.

Each step is guarded independently so a failure in one does not prevent the others
from running.
"""
import csv
import io
import os
from datetime import datetime, timedelta, timezone

import boto3

from sfk_scheduler.myweblog import fetch_current_members
from sfk_scheduler.schedule import generate_schedule


SCHEDULE_FIELDS = ["week_start", "week_number", "year", "name", "member_number", "status"]
MEMBERS_FIELDS = ["member_number", "name"]
AUTO_GENERATE_MONTH = 3
AUTO_GENERATE_DAY = 1


def _s3():
    return boto3.client("s3")


def _utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


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


def _load_members(rows):
    return [
        (row["name"].strip(), row.get("member_number", "").strip())
        for row in rows
        if row.get("name")
    ]


def _load_names(rows):
    return [name for name, _ in _load_members(rows)]


def _compute_end_date(today):
    try:
        one_year_ahead = today.replace(year=today.year + 1)
    except ValueError:
        # Feb 29 does not exist in non-leap years, so fall back to Feb 28 first.
        one_year_ahead = today.replace(year=today.year + 1, day=28)
    return one_year_ahead - timedelta(days=1)


def _schedule_rows_to_dicts(schedule_rows):
    return [
        {
            "week_start": week_start,
            "week_number": str(week_number),
            "year": str(year),
            "name": name,
            "member_number": member_number,
            "status": status,
        }
        for week_start, week_number, year, name, member_number, status in schedule_rows
    ]


def should_run_auto_generate(today):
    return today.month == AUTO_GENERATE_MONTH and today.day == AUTO_GENERATE_DAY


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


def run_auto_generate(s3, bucket, schedule_key, members_key, excluded_key, today):
    """Extend the existing schedule in S3 on March 1, up to one year ahead."""
    if not should_run_auto_generate(today):
        print("[auto_generate] Skipping — only runs on March 1")
        return {"ran": False, "reason": "not_march_1"}

    existing_rows = _read_csv(s3, bucket, schedule_key)
    if not existing_rows:
        print("[auto_generate] Skipping — no existing schedule found in S3")
        return {"ran": False, "reason": "missing_schedule"}

    try:
        last_date = max(datetime.fromisoformat(row["week_start"]) for row in existing_rows)
    except ValueError as exc:
        raise RuntimeError(f"Invalid schedule date in s3://{bucket}/{schedule_key}") from exc
    target_end = _compute_end_date(today)

    next_start = last_date + timedelta(weeks=1)

    if next_start > target_end:
        print(f"[auto_generate] Schedule already covers through {last_date.date()}")
        return {"ran": False, "reason": "up_to_date", "last_date": last_date.strftime("%Y-%m-%d")}

    members = _load_members(_read_csv(s3, bucket, members_key))
    excluded = _load_names(_read_csv(s3, bucket, excluded_key))

    schedule_rows = generate_schedule(
        start_date=next_start,
        members=members,
        excluded=excluded,
        already_assigned={row["name"] for row in existing_rows if row.get("name")},
        end_date=target_end,
    )
    appended_rows = _schedule_rows_to_dicts(schedule_rows)

    if not appended_rows:
        print("[auto_generate] No additional weeks were generated")
        return {"ran": False, "reason": "no_rows_added"}

    combined_rows = list(existing_rows) + appended_rows

    _write_csv(s3, bucket, schedule_key, SCHEDULE_FIELDS, combined_rows)
    print(
        f"[auto_generate] Added {len(appended_rows)} weeks "
        f"from {appended_rows[0]['week_start']} to {appended_rows[-1]['week_start']}"
    )
    return {
        "ran": True,
        "added": len(appended_rows),
        "from": appended_rows[0]["week_start"],
        "to": appended_rows[-1]["week_start"],
    }


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
    today = _utc_now()

    try:
        results["sync_members"] = run_sync_members(s3, bucket, members_key, mwl_token)
    except Exception as exc:
        print(f"[sync_members] ERROR: {exc}")
        results["sync_members"] = {"error": str(exc)}

    try:
        results["auto_generate"] = run_auto_generate(
            s3,
            bucket,
            schedule_key,
            members_key,
            excluded_key,
            today,
        )
    except Exception as exc:
        print(f"[auto_generate] ERROR: {exc}")
        results["auto_generate"] = {"error": str(exc)}

    print(f"Cron job complete: {results}")
    return results
