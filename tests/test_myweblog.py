import json
import pytest
from unittest.mock import MagicMock, patch
from sfk_scheduler.myweblog import (
    build_headers,
    build_users_url,
    parse_api_response,
    fetch_users_page,
    fetch_current_members,
)

BASE_URL = "https://api.myweblog.se/main/v4/users/"


# --- build_headers ---

def test_build_headers_includes_authorization():
    headers = build_headers("mytoken", "req-123")
    assert headers["Authorization"] == "Bearer mytoken"


def test_build_headers_includes_request_id():
    headers = build_headers("mytoken", "req-123")
    assert headers["Request-Id"] == "req-123"


def test_build_headers_includes_content_type():
    headers = build_headers("mytoken", "req-123")
    assert headers["Content-Type"] == "application/json"


# --- build_users_url ---

def test_build_users_url_contains_base_url():
    url = build_users_url(BASE_URL, offset=0)
    assert url.startswith(BASE_URL)


def test_build_users_url_includes_offset():
    url = build_users_url(BASE_URL, offset=100)
    assert "offset=100" in url


def test_build_users_url_includes_limit():
    url = build_users_url(BASE_URL, offset=0, page_size=250)
    assert "limit=250" in url


def test_build_users_url_includes_active_filter():
    url = build_users_url(BASE_URL, offset=0)
    assert "active=1" in url


# --- parse_api_response ---

def test_parse_api_response_returns_users_list():
    payload = {"users": [{"name": "Anna"}]}
    assert parse_api_response(payload) == [{"name": "Anna"}]


def test_parse_api_response_raises_on_api_errors():
    payload = {"errors": [{"message": "Unauthorized"}]}
    with pytest.raises(RuntimeError, match="Unauthorized"):
        parse_api_response(payload)


def test_parse_api_response_raises_when_no_users_key():
    with pytest.raises(ValueError, match="Could not find a users list"):
        parse_api_response({"data": []})


def test_parse_api_response_raises_for_non_dict():
    with pytest.raises(ValueError, match="Could not find a users list"):
        parse_api_response([{"name": "Anna"}])


def test_parse_api_response_raises_when_users_is_not_list():
    with pytest.raises(ValueError, match="Could not find a users list"):
        parse_api_response({"users": "not a list"})


# --- fetch_users_page ---

def _make_response(payload):
    data = json.dumps(payload).encode()
    mock = MagicMock()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    mock.read.return_value = data
    # Make json.load work by providing a file-like read
    import io
    mock_io = io.BytesIO(data)
    mock.read = mock_io.read
    return mock


def test_fetch_users_page_returns_users(monkeypatch):
    users = [{"first_name": "Anna", "last_name": "Svensson", "member_number": "1"}]
    payload = {"users": users}

    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("sfk_scheduler.myweblog.request.urlopen") as mock_urlopen, \
         patch("sfk_scheduler.myweblog.json.load", return_value=payload):
        mock_urlopen.return_value = mock_resp
        result = fetch_users_page("token", offset=0, base_url=BASE_URL)

    assert result == users


def test_fetch_users_page_raises_on_http_error(monkeypatch):
    from urllib import error as urllib_error
    http_err = urllib_error.HTTPError(
        url=BASE_URL, code=401, msg="Unauthorized", hdrs={}, fp=None
    )
    http_err.read = lambda: b'{"errors": [{"message": "Invalid token"}]}'

    with patch("sfk_scheduler.myweblog.request.urlopen", side_effect=http_err):
        with pytest.raises(RuntimeError):
            fetch_users_page("bad_token", offset=0, base_url=BASE_URL)


def test_fetch_users_page_raises_on_url_error():
    from urllib import error as urllib_error
    url_err = urllib_error.URLError(reason="Name resolution failed")

    with patch("sfk_scheduler.myweblog.request.urlopen", side_effect=url_err):
        with pytest.raises(RuntimeError, match="Could not connect"):
            fetch_users_page("token", offset=0, base_url=BASE_URL)


# --- fetch_current_members ---

def test_fetch_current_members_single_page(monkeypatch):
    users = [
        {"first_name": "Anna", "last_name": "Svensson", "member_number": "1"},
        {"first_name": "Bo", "last_name": "Lindqvist", "member_number": "2"},
    ]

    with patch("sfk_scheduler.myweblog.fetch_users_page", return_value=users):
        result = fetch_current_members("token", base_url=BASE_URL, page_size=500)

    assert ("Anna Svensson", "1") in result
    assert ("Bo Lindqvist", "2") in result


def test_fetch_current_members_paginates_until_short_page(monkeypatch):
    page1 = [{"first_name": f"User{i}", "last_name": "X", "member_number": str(i)} for i in range(2)]
    page2 = [{"first_name": "Last", "last_name": "User", "member_number": "99"}]

    pages = iter([page1, page2])

    with patch("sfk_scheduler.myweblog.fetch_users_page", side_effect=lambda *a, **kw: next(pages)):
        result = fetch_current_members("token", base_url=BASE_URL, page_size=2)

    names = [r[0] for r in result]
    assert "Last User" in names
