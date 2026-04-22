import os
import pytest
from pathlib import Path
from sfk_scheduler.config import load_env_file, get_config_value


def test_load_env_file_missing_file(tmp_path):
    result = load_env_file(tmp_path / "nonexistent.env")
    assert result == {}


def test_load_env_file_parses_key_value_pairs(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\nBAZ=qux\n")
    result = load_env_file(env)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_load_env_file_ignores_comments(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# comment\nKEY=value\n")
    result = load_env_file(env)
    assert result == {"KEY": "value"}


def test_load_env_file_ignores_blank_lines(tmp_path):
    env = tmp_path / ".env"
    env.write_text("\nKEY=value\n\n")
    result = load_env_file(env)
    assert result == {"KEY": "value"}


def test_load_env_file_ignores_lines_without_equals(tmp_path):
    env = tmp_path / ".env"
    env.write_text("NOEQUALSSIGN\nKEY=value\n")
    result = load_env_file(env)
    assert result == {"KEY": "value"}


def test_load_env_file_value_with_equals_sign(tmp_path):
    env = tmp_path / ".env"
    env.write_text("KEY=val=ue\n")
    result = load_env_file(env)
    assert result == {"KEY": "val=ue"}


def test_load_env_file_strips_whitespace(tmp_path):
    env = tmp_path / ".env"
    env.write_text("  KEY  =  value  \n")
    result = load_env_file(env)
    assert result == {"KEY": "value"}


def test_get_config_value_from_env_values():
    result = get_config_value("MY_KEY", {"MY_KEY": "from_file"})
    assert result == "from_file"


def test_get_config_value_prefers_os_environ(monkeypatch):
    monkeypatch.setenv("MY_KEY", "from_env")
    result = get_config_value("MY_KEY", {"MY_KEY": "from_file"})
    assert result == "from_env"


def test_get_config_value_returns_none_when_missing(monkeypatch):
    monkeypatch.delenv("MY_KEY", raising=False)
    result = get_config_value("MY_KEY", {})
    assert result is None
