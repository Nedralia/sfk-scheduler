"""
Unit tests for Lambda handler in API routing.
"""
import io
import json
from datetime import datetime
from unittest.mock import patch

from src.sfk_scheduler.api.lambda_handler import lambda_handler


class _FakeS3:
    def __init__(self, initial_csv):
        self._csv = initial_csv

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self._csv.encode("utf-8"))}

    def put_object(self, Bucket, Key, Body, ContentType):
        self._csv = Body.decode("utf-8")

    @property
    def csv_content(self):
        return self._csv


def test_health_check():
    """
    Test the health endpoint of the API Lambda handler.
    """
    event = {
        "path": "/health",
        "httpMethod": "GET",
    }
    context = {}

    # Call the Lambda function
    response = lambda_handler(event, context)

    # Assert the response
    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {
        "status": "ok",
        "message": "API is functional."
    }


def test_not_found():
    """
    Test a non-existent route.
    """
    event = {
        "path": "/non-existent",
        "httpMethod": "GET",
    }
    context = {}

    # Call the Lambda function
    response = lambda_handler(event, context)

    # Assert the response
    assert response["statusCode"] == 404
    assert json.loads(response["body"]) == {
        "status": "error",
        "message": "Resource not found."
    }


def test_complete_cleaning_marks_schedule_row(monkeypatch):
    initial_csv = (
        "week_start,week_number,year,name,member_number,status\n"
        "2026-07-06,28,2026,Jane Doe,1001,\n"
    )
    fake_s3 = _FakeS3(initial_csv)
    monkeypatch.setenv("SCHEDULE_BUCKET", "test-bucket")
    monkeypatch.setenv("SCHEDULE_KEY", "data/schedule.csv")

    event = {
        "path": "/cleaning/complete",
        "httpMethod": "POST",
        "body": json.dumps(
            {
                "member_number": "1001",
                "cleaned_fridge": True,
                "vacuumed_floors": True,
                "emptied_trash": True,
                "comment": "Done before dinner.",
            }
        ),
    }

    with (
        patch("src.sfk_scheduler.api.lambda_handler._s3", return_value=fake_s3),
        patch("src.sfk_scheduler.api.lambda_handler._utc_now", return_value=datetime(2026, 7, 8, 12, 0, 0)),
    ):
        response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "ok"
    assert body["week_start"] == "2026-07-06"
    assert "completion_comment" in fake_s3.csv_content
    assert "completed" in fake_s3.csv_content
    assert "Done before dinner." in fake_s3.csv_content


def test_complete_cleaning_requires_all_checkboxes():
    event = {
        "path": "/cleaning/complete",
        "httpMethod": "POST",
        "body": json.dumps(
            {
                "member_number": "1001",
                "cleaned_fridge": True,
                "vacuumed_floors": True,
                "emptied_trash": False,
            }
        ),
    }

    response = lambda_handler(event, {})
    assert response["statusCode"] == 400
    assert json.loads(response["body"])["message"] == "All cleaning checklist items must be confirmed."


def test_complete_cleaning_requires_current_week_assignment(monkeypatch):
    initial_csv = (
        "week_start,week_number,year,name,member_number,status\n"
        "2026-07-13,29,2026,Jane Doe,1001,\n"
    )
    fake_s3 = _FakeS3(initial_csv)
    monkeypatch.setenv("SCHEDULE_BUCKET", "test-bucket")
    monkeypatch.setenv("SCHEDULE_KEY", "data/schedule.csv")

    event = {
        "path": "/cleaning/complete",
        "httpMethod": "POST",
        "body": json.dumps(
            {
                "member_number": "1001",
                "cleaned_fridge": True,
                "vacuumed_floors": True,
                "emptied_trash": True,
            }
        ),
    }

    with (
        patch("src.sfk_scheduler.api.lambda_handler._s3", return_value=fake_s3),
        patch("src.sfk_scheduler.api.lambda_handler._utc_now", return_value=datetime(2026, 7, 8, 12, 0, 0)),
    ):
        response = lambda_handler(event, {})

    assert response["statusCode"] == 404
    assert json.loads(response["body"])["message"] == "No assignment found for this member in the current week."
