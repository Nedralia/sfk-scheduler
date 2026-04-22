import csv
import pytest
from datetime import datetime
from pathlib import Path
from sfk_scheduler.schedule_io import (
    load_previous_schedule,
    save_schedule_csv,
    get_last_scheduled_date,
)

HEADER = ["week_start", "week_number", "year", "name", "member_number"]

ROWS = [
    {"week_start": "2026-01-05", "week_number": "2", "year": "2026", "name": "Anna Svensson", "member_number": "101"},
    {"week_start": "2026-01-12", "week_number": "3", "year": "2026", "name": "Bo Lindqvist", "member_number": "102"},
    {"week_start": "2026-01-19", "week_number": "4", "year": "2026", "name": "Carl Berg", "member_number": "103"},
]


def _write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(rows)


# --- load_previous_schedule ---

def test_load_previous_schedule_keeps_rows_before_date(tmp_path):
    f = tmp_path / "schedule.csv"
    _write_csv(f, ROWS)
    cutoff = datetime(2026, 1, 19)
    kept, _ = load_previous_schedule(f, cutoff)
    assert len(kept) == 2
    assert all(datetime.fromisoformat(r["week_start"]) < cutoff for r in kept)


def test_load_previous_schedule_returns_assigned_names(tmp_path):
    f = tmp_path / "schedule.csv"
    _write_csv(f, ROWS)
    cutoff = datetime(2026, 1, 19)
    _, assigned = load_previous_schedule(f, cutoff)
    assert assigned == {"Anna Svensson", "Bo Lindqvist"}


def test_load_previous_schedule_returns_empty_when_file_missing(tmp_path):
    kept, assigned = load_previous_schedule(tmp_path / "missing.csv", datetime(2026, 1, 1))
    assert kept == []
    assert assigned == set()


def test_load_previous_schedule_returns_empty_when_file_is_header_only(tmp_path):
    f = tmp_path / "schedule.csv"
    f.write_text(",".join(HEADER) + "\n")
    kept, assigned = load_previous_schedule(f, datetime(2026, 6, 1))
    assert kept == []
    assert assigned == set()


def test_load_previous_schedule_all_rows_after_cutoff_returns_empty(tmp_path):
    f = tmp_path / "schedule.csv"
    _write_csv(f, ROWS)
    cutoff = datetime(2026, 1, 1)
    kept, assigned = load_previous_schedule(f, cutoff)
    assert kept == []
    assert assigned == set()


# --- save_schedule_csv ---

def test_save_schedule_csv_writes_header(tmp_path):
    f = tmp_path / "schedule.csv"
    save_schedule_csv([], [], f)
    lines = f.read_text().splitlines()
    assert lines[0] == "week_start,week_number,year,name,member_number"


def test_save_schedule_csv_writes_kept_rows(tmp_path):
    f = tmp_path / "schedule.csv"
    save_schedule_csv(ROWS[:1], [], f)
    lines = f.read_text().splitlines()
    assert "Anna Svensson" in lines[1]


def test_save_schedule_csv_appends_new_schedule_rows(tmp_path):
    f = tmp_path / "schedule.csv"
    new_row = ("2026-01-26", 5, 2026, "Dana Eriksson", "104")
    save_schedule_csv([], [new_row], f)
    lines = f.read_text().splitlines()
    assert "Dana Eriksson" in lines[1]


def test_save_schedule_csv_creates_parent_directories(tmp_path):
    f = tmp_path / "sub" / "dir" / "schedule.csv"
    save_schedule_csv([], [], f)
    assert f.exists()


def test_save_schedule_csv_kept_rows_before_new_rows(tmp_path):
    f = tmp_path / "schedule.csv"
    new_row = ("2026-01-26", 5, 2026, "Dana Eriksson", "104")
    save_schedule_csv(ROWS[:1], [new_row], f)
    lines = f.read_text().splitlines()
    assert "Anna Svensson" in lines[1]
    assert "Dana Eriksson" in lines[2]


# --- get_last_scheduled_date ---

def test_get_last_scheduled_date_returns_max_date(tmp_path):
    f = tmp_path / "schedule.csv"
    _write_csv(f, ROWS)
    result = get_last_scheduled_date(f)
    assert result == datetime(2026, 1, 19)


def test_get_last_scheduled_date_returns_none_when_file_missing(tmp_path):
    result = get_last_scheduled_date(tmp_path / "missing.csv")
    assert result is None


def test_get_last_scheduled_date_returns_none_when_no_rows(tmp_path):
    f = tmp_path / "schedule.csv"
    f.write_text(",".join(HEADER) + "\n")
    result = get_last_scheduled_date(f)
    assert result is None
