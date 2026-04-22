import sys
import pytest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from auto_generate import compute_end_date, needs_extension


# --- compute_end_date ---

def test_compute_end_date_is_one_year_minus_one_day():
    today = datetime(2026, 4, 22)
    result = compute_end_date(today)
    assert result == datetime(2027, 4, 21)


def test_compute_end_date_handles_leap_year_boundary():
    today = datetime(2024, 2, 29)
    result = compute_end_date(today)
    # 2025 has no Feb 29 → lands on Feb 28 next year, minus 1 day = Feb 27
    assert result == datetime(2025, 2, 27)


def test_compute_end_date_preserves_month_and_day():
    today = datetime(2026, 6, 15)
    result = compute_end_date(today)
    assert result == datetime(2027, 6, 14)


# --- needs_extension ---

def test_needs_extension_returns_true_when_within_threshold():
    today = datetime(2026, 4, 22)
    last_date = today + timedelta(days=59)
    assert needs_extension(last_date, today, threshold_days=60) is True


def test_needs_extension_returns_true_when_exactly_at_threshold():
    today = datetime(2026, 4, 22)
    last_date = today + timedelta(days=60)
    assert needs_extension(last_date, today, threshold_days=60) is True


def test_needs_extension_returns_false_when_beyond_threshold():
    today = datetime(2026, 4, 22)
    last_date = today + timedelta(days=61)
    assert needs_extension(last_date, today, threshold_days=60) is False


def test_needs_extension_returns_true_when_already_past():
    today = datetime(2026, 4, 22)
    last_date = today - timedelta(days=1)
    assert needs_extension(last_date, today) is True


def test_needs_extension_uses_default_threshold():
    today = datetime(2026, 4, 22)
    last_date = today + timedelta(days=30)
    assert needs_extension(last_date, today) is True
