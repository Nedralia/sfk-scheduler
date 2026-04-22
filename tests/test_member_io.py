import pytest
from sfk_scheduler.member_io import load_members, load_names, write_members_csv


def _write_members_csv(path, rows):
    path.write_text("member_number,name\n" + "\n".join(f"{num},{name}" for num, name in rows) + "\n")


# --- load_members ---

def test_load_members_returns_name_number_tuples(tmp_path):
    f = tmp_path / "members.csv"
    _write_members_csv(f, [("101", "Anna Svensson"), ("102", "Bo Lindqvist")])
    result = load_members(f)
    assert result == [("Anna Svensson", "101"), ("Bo Lindqvist", "102")]


def test_load_members_strips_whitespace(tmp_path):
    f = tmp_path / "members.csv"
    f.write_text("member_number,name\n 101 , Anna Svensson \n")
    result = load_members(f)
    assert result == [("Anna Svensson", "101")]


def test_load_members_missing_member_number_defaults_to_empty(tmp_path):
    f = tmp_path / "members.csv"
    f.write_text("name\nAnna Svensson\n")
    result = load_members(f)
    assert result == [("Anna Svensson", "")]


def test_load_members_empty_file_returns_empty_list(tmp_path):
    f = tmp_path / "members.csv"
    f.write_text("member_number,name\n")
    result = load_members(f)
    assert result == []


# --- load_names ---

def test_load_names_returns_only_names(tmp_path):
    f = tmp_path / "members.csv"
    _write_members_csv(f, [("101", "Anna Svensson"), ("102", "Bo Lindqvist")])
    result = load_names(f)
    assert result == ["Anna Svensson", "Bo Lindqvist"]


def test_load_names_empty_file_returns_empty_list(tmp_path):
    f = tmp_path / "members.csv"
    f.write_text("member_number,name\n")
    result = load_names(f)
    assert result == []


# --- write_members_csv ---

def test_write_members_csv_creates_file_with_header(tmp_path):
    f = tmp_path / "out.csv"
    write_members_csv([("Anna Svensson", "101"), ("Bo Lindqvist", "102")], f)
    lines = f.read_text().splitlines()
    assert lines[0] == "member_number,name"


def test_write_members_csv_writes_rows(tmp_path):
    f = tmp_path / "out.csv"
    write_members_csv([("Anna Svensson", "101"), ("Bo Lindqvist", "102")], f)
    lines = f.read_text().splitlines()
    assert lines[1] == "101,Anna Svensson"
    assert lines[2] == "102,Bo Lindqvist"


def test_write_members_csv_creates_parent_directories(tmp_path):
    f = tmp_path / "sub" / "dir" / "out.csv"
    write_members_csv([("Anna Svensson", "101")], f)
    assert f.exists()


def test_write_members_csv_roundtrip(tmp_path):
    f = tmp_path / "members.csv"
    original = [("Anna Svensson", "101"), ("Bo Lindqvist", "102")]
    write_members_csv(original, f)
    result = load_members(f)
    assert result == original
