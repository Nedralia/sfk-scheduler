import pytest
from datetime import datetime
from sfk_scheduler.schedule import align_to_monday, generate_schedule

MEMBERS = [("Anna Svensson", "101"), ("Bo Lindqvist", "102"), ("Carl Berg", "103")]


# --- align_to_monday ---

def test_align_to_monday_already_monday():
    d = datetime(2026, 4, 20)  # Monday
    assert align_to_monday(d) == d


def test_align_to_monday_from_wednesday():
    d = datetime(2026, 4, 22)  # Wednesday
    assert align_to_monday(d) == datetime(2026, 4, 20)


def test_align_to_monday_from_sunday():
    d = datetime(2026, 4, 26)  # Sunday
    assert align_to_monday(d) == datetime(2026, 4, 20)


# --- generate_schedule ---

def test_generate_schedule_returns_one_row_per_member_without_end_date():
    start = datetime(2026, 4, 20)
    result = generate_schedule(start, MEMBERS, excluded=[], already_assigned=set())
    assert len(result) == len(MEMBERS)


def test_generate_schedule_row_has_expected_fields():
    start = datetime(2026, 4, 20)
    result = generate_schedule(start, MEMBERS, excluded=[], already_assigned=set())
    week_start, week_number, year, name, member_number, status = result[0]
    assert week_start == "2026-04-20"
    assert isinstance(week_number, int)
    assert isinstance(year, int)
    assert name in [m[0] for m in MEMBERS]
    assert member_number in [m[1] for m in MEMBERS]
    assert status == ""


def test_generate_schedule_weeks_advance_by_one():
    start = datetime(2026, 4, 20)
    result = generate_schedule(start, MEMBERS, excluded=[], already_assigned=set())
    dates = [r[0] for r in result]
    for i in range(1, len(dates)):
        prev = datetime.strptime(dates[i - 1], "%Y-%m-%d")
        curr = datetime.strptime(dates[i], "%Y-%m-%d")
        assert (curr - prev).days == 7


def test_generate_schedule_respects_end_date():
    start = datetime(2026, 4, 20)
    end = datetime(2026, 5, 10)
    result = generate_schedule(start, MEMBERS, excluded=[], already_assigned=set(), end_date=end)
    for row in result:
        assert datetime.strptime(row[0], "%Y-%m-%d") <= end


def test_generate_schedule_excludes_members():
    start = datetime(2026, 4, 20)
    result = generate_schedule(start, MEMBERS, excluded=["Bo Lindqvist"], already_assigned=set())
    names = [r[3] for r in result]
    assert "Bo Lindqvist" not in names


def test_generate_schedule_skips_already_assigned():
    start = datetime(2026, 4, 20)
    result = generate_schedule(
        start, MEMBERS, excluded=[], already_assigned={"Anna Svensson", "Bo Lindqvist"}
    )
    # Carl Berg should be first since the others were already assigned
    assert result[0][3] == "Carl Berg"


def test_generate_schedule_recycles_members_with_end_date():
    start = datetime(2026, 4, 20)
    end = datetime(2026, 7, 20)  # ~13 weeks — more than 3 members
    result = generate_schedule(start, MEMBERS, excluded=[], already_assigned=set(), end_date=end)
    assert len(result) > len(MEMBERS)


def test_generate_schedule_stops_after_one_pass_without_end_date():
    start = datetime(2026, 4, 20)
    result = generate_schedule(start, MEMBERS, excluded=[], already_assigned=set(), end_date=None)
    assert len(result) == len(MEMBERS)


def test_generate_schedule_raises_when_all_excluded():
    with pytest.raises(ValueError, match="No eligible members"):
        generate_schedule(
            datetime(2026, 4, 20),
            MEMBERS,
            excluded=[m[0] for m in MEMBERS],
            already_assigned=set(),
        )


def test_generate_schedule_all_assigned_restarts_from_full_pool():
    start = datetime(2026, 4, 20)
    all_names = {m[0] for m in MEMBERS}
    result = generate_schedule(start, MEMBERS, excluded=[], already_assigned=all_names)
    # When all are already assigned, it should restart with everyone eligible
    assert len(result) == len(MEMBERS)


def test_generate_schedule_start_date_aligned_to_monday():
    # Pass a Wednesday — schedule should start on the Monday of that week
    start = datetime(2026, 4, 22)  # Wednesday
    result = generate_schedule(start, MEMBERS, excluded=[], already_assigned=set())
    assert result[0][0] == "2026-04-20"
