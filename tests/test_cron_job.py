import sys
from datetime import date
from pathlib import Path

from botocore.exceptions import ClientError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import cron_job


class _FakeBody:
    def __init__(self, text):
        self.text = text

    def read(self):
        return self.text.encode("utf-8")


class _FakeS3:
    def __init__(self, payloads=None, missing_keys=None):
        self.payloads = payloads or {}
        self.missing_keys = set(missing_keys or [])
        self.put_calls = []

    def get_object(self, Bucket, Key):
        if Key in self.missing_keys:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "missing"}},
                "GetObject",
            )

        return {"Body": _FakeBody(self.payloads[Key])}

    def put_object(self, **kwargs):
        self.put_calls.append(kwargs)


def test_load_schedule_rows_falls_back_to_legacy_key():
    s3 = _FakeS3(
        payloads={
            "schedule.csv": (
                "week_start,week_number,year,name,member_number,status\n"
                "2026-06-17,25,2026,Anna Svensson,101,\n"
            )
        },
        missing_keys={"data/schedule.csv"},
    )

    rows, key = cron_job._load_schedule_rows(s3, "bucket-name")

    assert key == "schedule.csv"
    assert rows == [{
        "week_start": "2026-06-17",
        "week_number": "25",
        "year": "2026",
        "name": "Anna Svensson",
        "member_number": "101",
        "status": "",
    }]


def test_run_send_reminders_sends_for_rows_matching_today(monkeypatch):
    today = date(2026, 6, 17)
    s3 = _FakeS3(
        payloads={
            "data/schedule.csv": (
                "week_start,week_number,year,name,member_number,status\n"
                "2026-06-17,25,2026,Anna Svensson,101,\n"
                "2026-06-24,26,2026,Bo Lindqvist,102,\n"
            )
        }
    )
    reminded = []

    monkeypatch.setattr(cron_job, "_send_reminder_email", lambda row: reminded.append(row["name"]))

    result = cron_job.run_send_reminders(s3, "bucket-name", today=today)

    assert result == {"checked": 2, "matched": 1}
    assert reminded == ["Anna Svensson"]


def test_run_send_reminders_returns_empty_when_schedule_is_missing():
    s3 = _FakeS3(missing_keys={"data/schedule.csv", "schedule.csv"})

    result = cron_job.run_send_reminders(s3, "bucket-name", today=date(2026, 6, 17))

    assert result == {"checked": 0, "matched": 0}


def test_lambda_handler_runs_sync_and_reminders(monkeypatch):
    monkeypatch.setenv("SCHEDULE_BUCKET", "bucket-name")
    monkeypatch.setenv("MEMBERS_KEY", "members.csv")
    monkeypatch.setenv("MWL_TOKEN", "secret-token")
    monkeypatch.setattr(cron_job, "_s3", lambda: object())
    monkeypatch.setattr(
        cron_job,
        "run_sync_members",
        lambda s3, bucket, members_key, mwl_token: {
            "bucket": bucket,
            "members_key": members_key,
            "token": mwl_token,
        },
    )
    monkeypatch.setattr(
        cron_job,
        "run_send_reminders",
        lambda s3, bucket: {"bucket": bucket, "matched": 1},
    )

    result = cron_job.lambda_handler({}, {})

    assert result == {
        "sync_members": {
            "bucket": "bucket-name",
            "members_key": "members.csv",
            "token": "secret-token",
        },
        "send_reminders": {"bucket": "bucket-name", "matched": 1},
    }
