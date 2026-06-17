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

from sfk_scheduler.mailgun import send_email
from sfk_scheduler.myweblog import fetch_current_members
from sfk_scheduler.reminder_log import already_sent, build_log_entry, load_log, write_log
from sfk_scheduler.schedule import generate_schedule


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
# auto_generate
# ---------------------------------------------------------------------------

def _compute_end_date(today):
    try:
        return today.replace(year=today.year + 1) - timedelta(days=1)
    except ValueError:
        # today is Feb 29 on a leap year
        return today.replace(year=today.year + 1, day=28) - timedelta(days=1)


def run_auto_generate(s3, bucket, schedule_key, members_key, excluded_key):
    """Extend the schedule when fewer than THRESHOLD_DAYS of weeks remain."""
    print("[auto_generate] Checking schedule...")

    today = datetime.utcnow()
    schedule_rows = _read_csv(s3, bucket, schedule_key)

    if not schedule_rows:
        print("[auto_generate] No schedule found — skipping (seed manually with CLI)")
        return {"action": "skipped", "reason": "no_schedule"}

    last_date = max(datetime.fromisoformat(r["week_start"]) for r in schedule_rows)
    remaining = (last_date - today).days
    print(f"[auto_generate] Last scheduled: {last_date.date()}, {remaining} days remaining")

    if remaining > THRESHOLD_DAYS:
        print("[auto_generate] Schedule sufficient — nothing to do")
        return {"action": "skipped", "reason": "sufficient"}

    members_rows = _read_csv(s3, bucket, members_key)
    members = [(r["name"].strip(), r.get("member_number", "").strip()) for r in members_rows]

    excluded_rows = _read_csv(s3, bucket, excluded_key)
    excluded = [r["name"].strip() for r in excluded_rows]

    already_assigned = {r["name"] for r in schedule_rows}
    next_start = last_date + timedelta(weeks=1)
    end_date = _compute_end_date(today)

    new_entries = generate_schedule(
        start_date=next_start,
        members=members,
        excluded=excluded,
        already_assigned=already_assigned,
        end_date=end_date,
    )

    merged = list(schedule_rows)
    for entry in new_entries:
        merged.append({
            "week_start": entry[0],
            "week_number": entry[1],
            "year": entry[2],
            "name": entry[3],
            "member_number": entry[4],
            "status": entry[5],
        })

    _write_csv(s3, bucket, schedule_key, SCHEDULE_FIELDS, merged)

    print(f"[auto_generate] Extended schedule by {len(new_entries)} weeks")
    return {"action": "extended", "new_weeks": len(new_entries)}


# ---------------------------------------------------------------------------
# send_reminder
# ---------------------------------------------------------------------------

def run_send_reminder(s3, bucket, schedule_key, log_key, mailgun_api_key, mailgun_domain):
    """Send the weekly cleaning reminder when today matches a scheduled week_start."""
    print("[send_reminder] Checking schedule...")

    today = datetime.utcnow().strftime("%Y-%m-%d")
    schedule_rows = _read_csv(s3, bucket, schedule_key)

    row = next((r for r in schedule_rows if r["week_start"] == today), None)

    if not row:
        print(f"[send_reminder] No assignment for {today} — skipping")
        return {"sent": False, "reason": "no_assignment"}

    email = row.get("email", "")
    if not email:
        print(f"[send_reminder] No email for {row['name']} — skipping")
        return {"sent": False, "reason": "no_email"}

    log_rows = load_log(s3, bucket, log_key)

    if already_sent(log_rows, today, email):
        print(f"[send_reminder] Already sent to {email} for {today} — skipping")
        return {"sent": False, "reason": "already_sent"}

    name = row["name"]
    week_number = row["week_number"]
    subject = f"Cleaning reminder — week {week_number}"
    body = (
        f"Hello {name},\n\n"
        f"This is a reminder that you are scheduled to clean the club house this week.\n\n"
        f"Week starting: {today} (week {week_number})\n\n"
        "Thank you!"
    )

    send_email(api_key=mailgun_api_key, domain=mailgun_domain, to=email, subject=subject, body=body)

    sent_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    log_entry = build_log_entry(sent_at=sent_at, week_start=today, name=name, email=email)
    log_rows.append(log_entry)
    write_log(s3, bucket, log_key, log_rows)

    print(f"[send_reminder] Sent reminder to {email} ({name})")
    return {"sent": True, "to": email}


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

    try:
        results["auto_generate"] = run_auto_generate(
            s3, bucket, schedule_key, members_key, excluded_key
        )
    except Exception as exc:
        print(f"[auto_generate] ERROR: {exc}")
        results["auto_generate"] = {"error": str(exc)}

    try:
        results["send_reminder"] = run_send_reminder(
            s3, bucket, schedule_key, log_key, mailgun_api_key, mailgun_domain
        )
    except Exception as exc:
        print(f"[send_reminder] ERROR: {exc}")
        results["send_reminder"] = {"error": str(exc)}

    print(f"Cron job complete: {results}")
    return results
