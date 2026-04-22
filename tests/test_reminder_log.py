import csv
import io
import pytest
from unittest.mock import MagicMock
from botocore.exceptions import ClientError

from sfk_scheduler.reminder_log import (
    already_sent,
    build_log_entry,
    load_log,
    write_log,
    LOG_FIELDNAMES,
)

BUCKET = "test-bucket"
KEY = "reminder_log.csv"


def _make_s3_body(rows):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=LOG_FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _mock_s3_with_content(rows):
    s3 = MagicMock()
    s3.get_object.return_value = {"Body": MagicMock(read=lambda: _make_s3_body(rows))}
    # expose exceptions like real boto3 client does
    s3.exceptions.NoSuchKey = type("NoSuchKey", (Exception,), {})
    return s3


def _mock_s3_no_object():
    s3 = MagicMock()
    error = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
        "GetObject",
    )
    s3.get_object.side_effect = error
    s3.exceptions.NoSuchKey = type("NoSuchKey", (Exception,), {})
    return s3


# --- load_log ---

def test_load_log_returns_empty_list_when_object_missing():
    s3 = _mock_s3_no_object()
    result = load_log(s3, BUCKET, KEY)
    assert result == []


def test_load_log_returns_rows_from_csv():
    rows = [{"sent_at": "2026-04-21T07:00:00Z", "week_start": "2026-04-20", "name": "Anna", "email": "anna@example.com"}]
    s3 = _mock_s3_with_content(rows)
    result = load_log(s3, BUCKET, KEY)
    assert len(result) == 1
    assert result[0]["email"] == "anna@example.com"


def test_load_log_returns_multiple_rows():
    rows = [
        {"sent_at": "2026-04-14T07:00:00Z", "week_start": "2026-04-13", "name": "Bo", "email": "bo@example.com"},
        {"sent_at": "2026-04-21T07:00:00Z", "week_start": "2026-04-20", "name": "Anna", "email": "anna@example.com"},
    ]
    s3 = _mock_s3_with_content(rows)
    result = load_log(s3, BUCKET, KEY)
    assert len(result) == 2


# --- already_sent ---

LOG_ROWS = [
    {"sent_at": "2026-04-21T07:00:00Z", "week_start": "2026-04-20", "name": "Anna", "email": "anna@example.com"},
]


def test_already_sent_returns_true_when_matching_entry_exists():
    assert already_sent(LOG_ROWS, "2026-04-20", "anna@example.com") is True


def test_already_sent_returns_false_for_different_date():
    assert already_sent(LOG_ROWS, "2026-04-27", "anna@example.com") is False


def test_already_sent_returns_false_for_different_email():
    assert already_sent(LOG_ROWS, "2026-04-20", "other@example.com") is False


def test_already_sent_returns_false_for_empty_log():
    assert already_sent([], "2026-04-20", "anna@example.com") is False


# --- build_log_entry ---

def test_build_log_entry_contains_all_fields():
    entry = build_log_entry("2026-04-21T07:00:00Z", "2026-04-20", "Anna", "anna@example.com")
    assert entry["sent_at"] == "2026-04-21T07:00:00Z"
    assert entry["week_start"] == "2026-04-20"
    assert entry["name"] == "Anna"
    assert entry["email"] == "anna@example.com"


# --- write_log ---

def test_write_log_calls_put_object():
    s3 = MagicMock()
    rows = [{"sent_at": "2026-04-21T07:00:00Z", "week_start": "2026-04-20", "name": "Anna", "email": "anna@example.com"}]
    write_log(s3, BUCKET, KEY, rows)
    s3.put_object.assert_called_once()


def test_write_log_uses_correct_bucket_and_key():
    s3 = MagicMock()
    rows = [{"sent_at": "2026-04-21T07:00:00Z", "week_start": "2026-04-20", "name": "Anna", "email": "anna@example.com"}]
    write_log(s3, BUCKET, KEY, rows)
    call_kwargs = s3.put_object.call_args[1]
    assert call_kwargs["Bucket"] == BUCKET
    assert call_kwargs["Key"] == KEY


def test_write_log_body_contains_written_row():
    s3 = MagicMock()
    rows = [{"sent_at": "2026-04-21T07:00:00Z", "week_start": "2026-04-20", "name": "Anna", "email": "anna@example.com"}]
    write_log(s3, BUCKET, KEY, rows)
    body = s3.put_object.call_args[1]["Body"].decode("utf-8")
    assert "anna@example.com" in body


def test_write_log_includes_header_row():
    s3 = MagicMock()
    write_log(s3, BUCKET, KEY, [])
    body = s3.put_object.call_args[1]["Body"].decode("utf-8")
    assert "sent_at" in body
    assert "week_start" in body
