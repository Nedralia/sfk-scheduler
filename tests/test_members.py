import pytest
from sfk_scheduler.members import (
    normalize_member_name,
    normalize_member_number,
    normalize_members,
)


# --- normalize_member_name ---

def test_normalize_member_name_first_last():
    assert normalize_member_name({"first_name": "Anna", "last_name": "Svensson"}) == "Anna Svensson"


def test_normalize_member_name_firstname_lastname_keys():
    assert normalize_member_name({"firstname": "Bo", "lastname": "Lindqvist"}) == "Bo Lindqvist"


def test_normalize_member_name_swedish_keys():
    assert normalize_member_name({"fornamn": "Carl", "efternamn": "Berg"}) == "Carl Berg"


def test_normalize_member_name_fallback_to_full_name():
    assert normalize_member_name({"full_name": "Dana Eriksson"}) == "Dana Eriksson"


def test_normalize_member_name_fallback_to_name():
    assert normalize_member_name({"name": "Erik Larsson"}) == "Erik Larsson"


def test_normalize_member_name_strips_whitespace():
    assert normalize_member_name({"first_name": "  Anna ", "last_name": " Svensson "}) == "Anna Svensson"


def test_normalize_member_name_returns_none_when_empty():
    assert normalize_member_name({}) is None


def test_normalize_member_name_returns_none_for_blank_values():
    assert normalize_member_name({"first_name": "", "last_name": ""}) is None


# --- normalize_member_number ---

def test_normalize_member_number_from_member_number():
    assert normalize_member_number({"member_number": "1234"}) == "1234"


def test_normalize_member_number_from_membership_number():
    assert normalize_member_number({"membership_number": "5678"}) == "5678"


def test_normalize_member_number_from_member_id():
    assert normalize_member_number({"member_id": "99"}) == "99"


def test_normalize_member_number_strips_whitespace():
    assert normalize_member_number({"member_number": "  42  "}) == "42"


def test_normalize_member_number_returns_empty_when_missing():
    assert normalize_member_number({}) == ""


# --- normalize_members ---

def test_normalize_members_returns_sorted_list():
    users = [
        {"first_name": "Zara", "last_name": "A", "member_number": "2"},
        {"first_name": "Anna", "last_name": "B", "member_number": "1"},
    ]
    result = normalize_members(users)
    assert result == [("Anna B", "1"), ("Zara A", "2")]


def test_normalize_members_deduplicates_by_name():
    users = [
        {"first_name": "Anna", "last_name": "B", "member_number": "1"},
        {"first_name": "Anna", "last_name": "B", "member_number": "1"},
    ]
    result = normalize_members(users)
    assert len(result) == 1


def test_normalize_members_skips_entries_with_no_name():
    users = [
        {"first_name": "", "last_name": ""},
        {"first_name": "Anna", "last_name": "B", "member_number": "1"},
    ]
    result = normalize_members(users)
    assert result == [("Anna B", "1")]


def test_normalize_members_raises_when_empty():
    with pytest.raises(RuntimeError, match="no members"):
        normalize_members([])


def test_normalize_members_raises_when_all_names_empty():
    with pytest.raises(RuntimeError, match="no members"):
        normalize_members([{"first_name": "", "last_name": ""}])
