"""Lambda handler for routing API requests."""
import base64
import csv
import io
import json
import os
from datetime import datetime, timedelta, timezone

import boto3

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}
SCHEDULE_CSV_FIELDS = [
    "week_start",
    "week_number",
    "year",
    "name",
    "member_number",
    "status",
    "completion_comment",
    "completed_at",
]


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body),
    }


def _utc_now():
    return datetime.now(timezone.utc)


def _parse_json_body(event):
    raw_body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw_body = base64.b64decode(raw_body).decode("utf-8")
    try:
        return json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON payload.") from exc


def _s3():
    return boto3.client("s3")


def _read_schedule_rows(s3, bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    content = response["Body"].read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(content)))


def _write_schedule_rows(s3, bucket, key, rows):
    discovered_fields = []
    discovered_field_set = set()
    for row in rows:
        for field in row.keys():
            if field not in SCHEDULE_CSV_FIELDS and field not in discovered_field_set:
                discovered_fields.append(field)
                discovered_field_set.add(field)

    fieldnames = SCHEDULE_CSV_FIELDS + discovered_fields
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=buf.getvalue().encode("utf-8"),
        ContentType="text/csv",
    )


def _find_assignment_index(rows, member_number, week_start):
    normalized_member_number = str(member_number).strip()
    for index, row in enumerate(rows):
        if row.get("week_start") == week_start and row.get("member_number", "").strip() == normalized_member_number:
            return index
    return None


def _is_completed(status):
    normalized = str(status or "").strip().lower()
    return normalized in {
        "completed",
        "done",
        "true",
        "1",
        "yes",
        "y",
        "checked",
        "check",
        "ok",
        "✓",
        "✔",
    }


def lambda_handler(event, context):
    """Entry point for the Lambda function triggered by API Gateway."""
    method = event.get("httpMethod", "GET").upper()
    path = event.get("path", "/")

    if method == "OPTIONS":
        return _response(200, {"status": "ok"})

    routes = {
        ("GET", "/health"): health_handler,
        ("POST", "/cleaning/complete"): complete_cleaning_handler,
    }

    handler = routes.get((method, path), not_found_handler)
    return handler(event)


def health_handler(event):
    """Health-check endpoint."""
    return _response(200, {"status": "ok", "message": "API is functional."})


def complete_cleaning_handler(event):
    """Register completed weekly cleaning and mark schedule row as completed."""
    try:
        payload = _parse_json_body(event)
    except ValueError as exc:
        return _response(400, {"status": "error", "message": str(exc)})

    member_number = str(payload.get("member_number", "")).strip()
    cleaned_fridge = bool(payload.get("cleaned_fridge"))
    vacuumed_floors = bool(payload.get("vacuumed_floors"))
    emptied_trash = bool(payload.get("emptied_trash"))
    comment = str(payload.get("comment", "")).strip()

    if not member_number:
        return _response(400, {"status": "error", "message": "member_number is required."})

    if not cleaned_fridge or not vacuumed_floors or not emptied_trash:
        return _response(
            400,
            {
                "status": "error",
                "message": "All cleaning checklist items must be confirmed.",
            },
        )

    bucket = os.environ.get("SCHEDULE_BUCKET")
    key = os.environ.get("SCHEDULE_KEY")
    if not bucket or not key:
        return _response(
            500,
            {"status": "error", "message": "Schedule storage is not configured."},
        )

    s3 = _s3()
    rows = _read_schedule_rows(s3, bucket, key)
    now = _utc_now()
    # week_start is the Monday date of the current assignment week.
    week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")

    index = _find_assignment_index(rows, member_number, week_start)
    if index is None:
        return _response(
            404,
            {
                "status": "error",
                "message": "No assignment found for this member in the current week.",
            },
        )

    if _is_completed(rows[index].get("status", "")):
        return _response(
            409,
            {
                "status": "error",
                "message": "This assignment is already marked as completed.",
            },
        )

    rows[index]["status"] = "completed"
    rows[index]["completion_comment"] = comment
    rows[index]["completed_at"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_schedule_rows(s3, bucket, key, rows)

    return _response(
        200,
        {
            "status": "ok",
            "message": "Cleaning assignment marked as completed.",
            "week_start": week_start,
            "member_number": member_number,
        },
    )


def not_found_handler(event):
    """Not Found handler for unmatched routes."""
    return _response(404, {"status": "error", "message": "Resource not found."})
