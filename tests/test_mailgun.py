import json
import pytest
from unittest.mock import patch, MagicMock
from sfk_scheduler.mailgun import build_send_url, send_email

BASE_URL = "https://api.mailgun.net/v3"
DOMAIN = "mg.example.com"
API_KEY = "key-test123"


# --- build_send_url ---

def test_build_send_url_includes_domain():
    url = build_send_url(DOMAIN)
    assert DOMAIN in url


def test_build_send_url_ends_with_messages():
    url = build_send_url(DOMAIN)
    assert url.endswith("/messages")


def test_build_send_url_uses_custom_base_url():
    url = build_send_url(DOMAIN, base_url="https://custom.host/v3")
    assert url.startswith("https://custom.host/v3")


# --- send_email ---

def _mock_urlopen_response(payload):
    data = json.dumps(payload).encode()
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    import io
    mock_resp.read = io.BytesIO(data).read
    return mock_resp


def test_send_email_makes_post_request():
    with patch("sfk_scheduler.mailgun.request.urlopen") as mock_urlopen, \
         patch("sfk_scheduler.mailgun.json.load", return_value={"id": "abc", "message": "Queued"}):
        mock_urlopen.return_value = _mock_urlopen_response({"id": "abc"})
        send_email(API_KEY, DOMAIN, "user@example.com", "Subject", "Body")
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        assert req.method == "POST"


def test_send_email_includes_authorization_header():
    import base64
    expected_token = base64.b64encode(f"api:{API_KEY}".encode()).decode()

    with patch("sfk_scheduler.mailgun.request.urlopen") as mock_urlopen, \
         patch("sfk_scheduler.mailgun.json.load", return_value={"id": "abc"}):
        mock_urlopen.return_value = _mock_urlopen_response({"id": "abc"})
        send_email(API_KEY, DOMAIN, "user@example.com", "Subject", "Body")
        req = mock_urlopen.call_args[0][0]
        assert f"Basic {expected_token}" in req.get_header("Authorization")


def test_send_email_raises_on_http_error():
    from urllib import error as urllib_error
    http_err = urllib_error.HTTPError(
        url="https://example.com", code=401, msg="Unauthorized", hdrs={}, fp=None
    )
    http_err.read = lambda: b"Forbidden"

    with patch("sfk_scheduler.mailgun.request.urlopen", side_effect=http_err):
        with pytest.raises(RuntimeError, match="Mailgun request failed"):
            send_email(API_KEY, DOMAIN, "user@example.com", "Subject", "Body")


def test_send_email_raises_on_url_error():
    from urllib import error as urllib_error
    url_err = urllib_error.URLError(reason="Name resolution failed")

    with patch("sfk_scheduler.mailgun.request.urlopen", side_effect=url_err):
        with pytest.raises(RuntimeError, match="Could not connect to Mailgun"):
            send_email(API_KEY, DOMAIN, "user@example.com", "Subject", "Body")


def test_send_email_returns_api_response():
    expected = {"id": "<msg-id>", "message": "Queued. Thank you."}

    with patch("sfk_scheduler.mailgun.request.urlopen") as mock_urlopen, \
         patch("sfk_scheduler.mailgun.json.load", return_value=expected):
        mock_urlopen.return_value = _mock_urlopen_response(expected)
        result = send_email(API_KEY, DOMAIN, "user@example.com", "Subject", "Body")

    assert result == expected
