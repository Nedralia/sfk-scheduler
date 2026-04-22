"""
Reminder log — records every email that has been successfully sent.

The log is stored as a CSV in S3 with the columns:
    sent_at, week_start, name, email

Functions are pure / injectable to keep them easily testable.
"""

import csv
import io

LOG_FIELDNAMES = ["sent_at", "week_start", "name", "email"]


def load_log(s3_client, bucket, key):
    """Return the log as a list of dicts.  Returns an empty list if the object
    does not exist yet (first run)."""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read().decode("utf-8")
        return list(csv.DictReader(io.StringIO(content)))
    except s3_client.exceptions.NoSuchKey:
        return []
    except Exception as exc:  # e.g. ClientError with NoSuchKey code
        # boto3 raises botocore.exceptions.ClientError; check error code
        error_code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
        if error_code in ("NoSuchKey", "404"):
            return []
        raise


def already_sent(log_rows, week_start, email):
    """Return True if a reminder has already been sent for this week/recipient."""
    for row in log_rows:
        if row["week_start"] == week_start and row["email"] == email:
            return True
    return False


def build_log_entry(sent_at, week_start, name, email):
    """Return a single log row dict."""
    return {
        "sent_at": sent_at,
        "week_start": week_start,
        "name": name,
        "email": email,
    }


def write_log(s3_client, bucket, key, log_rows):
    """Write the full log back to S3."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=LOG_FIELDNAMES)
    writer.writeheader()
    writer.writerows(log_rows)
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=buf.getvalue().encode("utf-8"),
        ContentType="text/csv",
    )
