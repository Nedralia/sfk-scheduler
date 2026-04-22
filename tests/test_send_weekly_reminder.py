import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from send_weekly_reminder import find_assignment_for_date, build_reminder_email, lambda_handler

ROWS = [
    {"week_start": "2026-04-20", "week_number": "17", "year": "2026", "name": "Anna Svensson", "member_number": "101", "email": "anna@example.com"},
    {"week_start": "2026-04-27", "week_number": "18", "year": "2026", "name": "Bo Lindqvist", "member_number": "102", "email": "bo@example.com"},
]


# --- find_assignment_for_date ---

def test_find_assignment_for_date_returns_matching_row():
    row = find_assignment_for_date(ROWS, "2026-04-20")
    assert row["name"] == "Anna Svensson"


def test_find_assignment_for_date_returns_none_when_no_match():
    assert find_assignment_for_date(ROWS, "2026-05-04") is None


def test_find_assignment_for_date_matches_exact_date():
    row = find_assignment_for_date(ROWS, "2026-04-27")
    assert row["name"] == "Bo Lindqvist"


# --- build_reminder_email ---

def test_build_reminder_email_returns_correct_email_address():
    email, _, _ = build_reminder_email(ROWS[0])
    assert email == "anna@example.com"


def test_build_reminder_email_subject_contains_week_number():
    _, subject, _ = build_reminder_email(ROWS[0])
    assert "17" in subject


def test_build_reminder_email_body_contains_name():
    _, _, body = build_reminder_email(ROWS[0])
    assert "Anna Svensson" in body


def test_build_reminder_email_body_contains_week_start():
    _, _, body = build_reminder_email(ROWS[0])
    assert "2026-04-20" in body


def test_build_reminder_email_returns_empty_email_when_missing():
    row = {**ROWS[0], "email": ""}
    email, _, _ = build_reminder_email(row)
    assert email == ""


# --- lambda_handler ---

def _make_s3_rows(rows):
    import csv, io
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def test_lambda_handler_sends_email_for_matching_date(monkeypatch):
    monkeypatch.setenv("SCHEDULE_BUCKET", "test-bucket")
    monkeypatch.setenv("SCHEDULE_KEY", "schedule.csv")
    monkeypatch.setenv("MAILGUN_API_KEY", "key-test")
    monkeypatch.setenv("MAILGUN_DOMAIN", "mg.example.com")

    csv_content = _make_s3_rows(ROWS)

    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: csv_content.encode())}

    with patch("send_weekly_reminder.boto3.client", return_value=mock_s3), \
         patch("send_weekly_reminder.datetime") as mock_dt, \
         patch("send_weekly_reminder.send_email") as mock_send:

        mock_dt.utcnow.return_value.strftime.return_value = "2026-04-20"
        result = lambda_handler({}, {})

    mock_send.assert_called_once()
    assert result["sent"] is True
    assert result["recipient"] == "anna@example.com"


def test_lambda_handler_returns_not_sent_when_no_assignment(monkeypatch):
    monkeypatch.setenv("SCHEDULE_BUCKET", "test-bucket")
    monkeypatch.setenv("SCHEDULE_KEY", "schedule.csv")
    monkeypatch.setenv("MAILGUN_API_KEY", "key-test")
    monkeypatch.setenv("MAILGUN_DOMAIN", "mg.example.com")

    csv_content = _make_s3_rows(ROWS)

    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: csv_content.encode())}

    with patch("send_weekly_reminder.boto3.client", return_value=mock_s3), \
         patch("send_weekly_reminder.datetime") as mock_dt, \
         patch("send_weekly_reminder.send_email") as mock_send:

        mock_dt.utcnow.return_value.strftime.return_value = "2026-12-01"
        result = lambda_handler({}, {})

    mock_send.assert_not_called()
    assert result["sent"] is False


def test_lambda_handler_returns_not_sent_when_no_email(monkeypatch):
    monkeypatch.setenv("SCHEDULE_BUCKET", "test-bucket")
    monkeypatch.setenv("SCHEDULE_KEY", "schedule.csv")
    monkeypatch.setenv("MAILGUN_API_KEY", "key-test")
    monkeypatch.setenv("MAILGUN_DOMAIN", "mg.example.com")

    rows_no_email = [{**ROWS[0], "email": ""}]
    csv_content = _make_s3_rows(rows_no_email)

    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: csv_content.encode())}

    with patch("send_weekly_reminder.boto3.client", return_value=mock_s3), \
         patch("send_weekly_reminder.datetime") as mock_dt, \
         patch("send_weekly_reminder.send_email") as mock_send:

        mock_dt.utcnow.return_value.strftime.return_value = "2026-04-20"
        result = lambda_handler({}, {})

    mock_send.assert_not_called()
    assert result["sent"] is False
    assert result["reason"] == "no_email"
