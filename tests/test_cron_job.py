import csv
import io
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from cron_job import (
    SCHEDULE_FIELDS,
    lambda_handler,
    run_auto_generate,
    should_run_auto_generate,
)

MEMBERS_FIELDS = ["member_number", "name"]

SCHEDULE_ROWS = [
    {
        "week_start": "2026-02-16",
        "week_number": "8",
        "year": "2026",
        "name": "Anna Svensson",
        "member_number": "101",
        "status": "",
    },
    {
        "week_start": "2026-02-23",
        "week_number": "9",
        "year": "2026",
        "name": "Bo Lindqvist",
        "member_number": "102",
        "status": "completed",
    },
]

MEMBER_ROWS = [
    {"member_number": "101", "name": "Anna Svensson"},
    {"member_number": "102", "name": "Bo Lindqvist"},
    {"member_number": "103", "name": "Carl Berg"},
]

EXCLUDED_ROWS = [
    {"member_number": "", "name": "Bo Lindqvist"},
]


def _make_csv(fieldnames, rows):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def _mock_s3(schedule_rows=None, member_rows=None, excluded_rows=None):
    payloads = {
        "data/schedule.csv": _make_csv(SCHEDULE_FIELDS, schedule_rows or []),
        "members.csv": _make_csv(MEMBERS_FIELDS, member_rows or MEMBER_ROWS),
        "excluded.csv": _make_csv(MEMBERS_FIELDS, excluded_rows or EXCLUDED_ROWS),
    }
    mock_s3 = MagicMock()
    mock_s3.get_object.side_effect = lambda Bucket, Key: {
        "Body": MagicMock(read=lambda: payloads[Key].encode("utf-8"))
    }
    return mock_s3


def test_should_run_auto_generate_only_on_march_first():
    assert should_run_auto_generate(datetime(2026, 3, 1)) is True
    assert should_run_auto_generate(datetime(2026, 3, 2)) is False
    assert should_run_auto_generate(datetime(2026, 2, 28)) is False


def test_run_auto_generate_skips_when_not_march_first():
    mock_s3 = _mock_s3()

    result = run_auto_generate(
        mock_s3,
        "test-bucket",
        "data/schedule.csv",
        "members.csv",
        "excluded.csv",
        datetime(2026, 2, 28),
    )

    mock_s3.get_object.assert_not_called()
    mock_s3.put_object.assert_not_called()
    assert result == {"ran": False, "reason": "not_march_1"}


def test_run_auto_generate_skips_when_existing_schedule_is_missing():
    mock_s3 = _mock_s3(schedule_rows=[])

    result = run_auto_generate(
        mock_s3,
        "test-bucket",
        "data/schedule.csv",
        "members.csv",
        "excluded.csv",
        datetime(2026, 3, 1),
    )

    mock_s3.put_object.assert_not_called()
    assert result == {"ran": False, "reason": "missing_schedule"}


def test_run_auto_generate_raises_for_invalid_existing_schedule_date():
    mock_s3 = _mock_s3(schedule_rows=[
        {
            "week_start": "not-a-date",
            "week_number": "8",
            "year": "2026",
            "name": "Anna Svensson",
            "member_number": "101",
            "status": "",
        },
    ])

    with pytest.raises(RuntimeError, match="Invalid schedule date"):
        run_auto_generate(
            mock_s3,
            "test-bucket",
            "data/schedule.csv",
            "members.csv",
            "excluded.csv",
            datetime(2026, 3, 1),
        )


def test_run_auto_generate_skips_when_schedule_already_covers_target_window():
    mock_s3 = _mock_s3(schedule_rows=[
        {
            "week_start": "2027-02-22",
            "week_number": "8",
            "year": "2027",
            "name": "Anna Svensson",
            "member_number": "101",
            "status": "",
        },
    ])

    result = run_auto_generate(
        mock_s3,
        "test-bucket",
        "data/schedule.csv",
        "members.csv",
        "excluded.csv",
        datetime(2026, 3, 1),
    )

    mock_s3.put_object.assert_not_called()
    assert result == {
        "ran": False,
        "reason": "up_to_date",
        "last_date": "2027-02-22",
    }


def test_run_auto_generate_appends_to_existing_schedule():
    mock_s3 = _mock_s3(schedule_rows=SCHEDULE_ROWS)
    appended = [
        ("2026-03-02", 10, 2026, "Carl Berg", "103", ""),
        ("2026-03-09", 11, 2026, "Anna Svensson", "101", ""),
    ]

    with patch("cron_job.generate_schedule", return_value=appended) as mock_generate:
        result = run_auto_generate(
            mock_s3,
            "test-bucket",
            "data/schedule.csv",
            "members.csv",
            "excluded.csv",
            datetime(2026, 3, 1),
        )

    mock_generate.assert_called_once_with(
        start_date=datetime(2026, 3, 2),
        members=[
            ("Anna Svensson", "101"),
            ("Bo Lindqvist", "102"),
            ("Carl Berg", "103"),
        ],
        excluded=["Bo Lindqvist"],
        already_assigned={"Anna Svensson", "Bo Lindqvist"},
        end_date=datetime(2027, 2, 28),
    )

    body = mock_s3.put_object.call_args.kwargs["Body"].decode("utf-8")
    written_rows = list(csv.DictReader(io.StringIO(body)))
    assert written_rows == SCHEDULE_ROWS + [
        {
            "week_start": "2026-03-02",
            "week_number": "10",
            "year": "2026",
            "name": "Carl Berg",
            "member_number": "103",
            "status": "",
        },
        {
            "week_start": "2026-03-09",
            "week_number": "11",
            "year": "2026",
            "name": "Anna Svensson",
            "member_number": "101",
            "status": "",
        },
    ]
    assert result == {
        "ran": True,
        "added": 2,
        "from": "2026-03-02",
        "to": "2026-03-09",
    }


def test_run_auto_generate_handles_empty_generated_rows():
    mock_s3 = _mock_s3(schedule_rows=SCHEDULE_ROWS)

    with patch("cron_job.generate_schedule", return_value=[]):
        result = run_auto_generate(
            mock_s3,
            "test-bucket",
            "data/schedule.csv",
            "members.csv",
            "excluded.csv",
            datetime(2026, 3, 1),
        )

    mock_s3.put_object.assert_not_called()
    assert result == {"ran": False, "reason": "no_rows_added"}


def test_lambda_handler_reports_auto_generate_result(monkeypatch):
    monkeypatch.setenv("SCHEDULE_BUCKET", "test-bucket")
    monkeypatch.setenv("SCHEDULE_KEY", "data/schedule.csv")
    monkeypatch.setenv("MEMBERS_KEY", "members.csv")
    monkeypatch.setenv("EXCLUDED_KEY", "excluded.csv")
    monkeypatch.setenv("REMINDER_LOG_KEY", "reminder_log.csv")
    monkeypatch.setenv("MAILGUN_API_KEY", "key-test")
    monkeypatch.setenv("MAILGUN_DOMAIN", "mg.example.com")
    monkeypatch.setenv("MWL_TOKEN", "token")

    today = datetime(2026, 3, 1)

    with patch("cron_job._s3", return_value="mock-s3"), \
         patch("cron_job._utc_now", return_value=today), \
         patch("cron_job.run_sync_members", return_value={"synced": 3}) as mock_sync, \
         patch("cron_job.run_auto_generate", return_value={"ran": True, "added": 5}) as mock_auto:
        result = lambda_handler({}, {})

    mock_sync.assert_called_once_with("mock-s3", "test-bucket", "members.csv", "token")
    mock_auto.assert_called_once_with(
        "mock-s3",
        "test-bucket",
        "data/schedule.csv",
        "members.csv",
        "excluded.csv",
        today,
    )
    assert result == {
        "sync_members": {"synced": 3},
        "auto_generate": {"ran": True, "added": 5},
    }
