import json
import pytest
from unittest.mock import patch, MagicMock

import sfk_scheduler.postmark as postmark
from sfk_scheduler.postmark import build_send_url, PostmarkEmailService

BASE_URL = "https://api.postmarkapp.com/email"
SERVER_TOKEN = "pm-token"
FROM_EMAIL = "scheduler@example.com"


def test_build_send_url_returns_default_url():
    assert build_send_url() == BASE_URL


def test_build_send_url_uses_custom_base_url():
    assert build_send_url(base_url="https://custom.host/email") == "https://custom.host/email"


def _mock_urlopen_response(payload):
    data = json.dumps(payload).encode()
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    import io
    mock_resp.read = io.BytesIO(data).read
    return mock_resp


def test_service_send_email_makes_post_request():
    service = PostmarkEmailService(SERVER_TOKEN, FROM_EMAIL)

    with patch("sfk_scheduler.postmark.request.urlopen") as mock_urlopen, \
         patch("sfk_scheduler.postmark.json.load", return_value={"MessageID": "abc"}):
        mock_urlopen.return_value = _mock_urlopen_response({"MessageID": "abc"})
        service.send_email("user@example.com", "Subject", "Body")
        req = mock_urlopen.call_args[0][0]
        assert req.method == "POST"


def test_service_send_email_includes_headers_and_payload():
    service = PostmarkEmailService(SERVER_TOKEN, FROM_EMAIL)

    with patch("sfk_scheduler.postmark.request.urlopen") as mock_urlopen, \
         patch("sfk_scheduler.postmark.json.load", return_value={"MessageID": "abc"}):
        mock_urlopen.return_value = _mock_urlopen_response({"MessageID": "abc"})
        service.send_email("user@example.com", "Subject", "Body")
        req = mock_urlopen.call_args[0][0]

    assert req.get_header("Accept") == "application/json"
    assert req.get_header("Content-type") == "application/json"
    assert req.get_header("X-postmark-server-token") == SERVER_TOKEN
    payload = json.loads(req.data.decode("utf-8"))
    assert payload["From"] == FROM_EMAIL
    assert payload["To"] == "user@example.com"
    assert payload["Subject"] == "Subject"
    assert payload["TextBody"] == "Body"


def test_service_send_email_includes_message_stream_when_set():
    service = PostmarkEmailService(SERVER_TOKEN, FROM_EMAIL, message_stream="outbound")

    with patch("sfk_scheduler.postmark.request.urlopen") as mock_urlopen, \
         patch("sfk_scheduler.postmark.json.load", return_value={"MessageID": "abc"}):
        mock_urlopen.return_value = _mock_urlopen_response({"MessageID": "abc"})
        service.send_email("user@example.com", "Subject", "Body")
        req = mock_urlopen.call_args[0][0]

    payload = json.loads(req.data.decode("utf-8"))
    assert payload["MessageStream"] == "outbound"


def test_service_send_email_raises_on_http_error():
    from urllib import error as urllib_error
    http_err = urllib_error.HTTPError(
        url="https://example.com", code=422, msg="Unprocessable", hdrs={}, fp=None
    )
    http_err.read = lambda: b"Bad payload"
    service = PostmarkEmailService(SERVER_TOKEN, FROM_EMAIL)

    with patch("sfk_scheduler.postmark.request.urlopen", side_effect=http_err):
        with pytest.raises(RuntimeError, match="Postmark request failed"):
            service.send_email("user@example.com", "Subject", "Body")


def test_service_send_email_raises_on_url_error():
    from urllib import error as urllib_error
    url_err = urllib_error.URLError(reason="Name resolution failed")
    service = PostmarkEmailService(SERVER_TOKEN, FROM_EMAIL)

    with patch("sfk_scheduler.postmark.request.urlopen", side_effect=url_err):
        with pytest.raises(RuntimeError, match="Could not connect to Postmark"):
            service.send_email("user@example.com", "Subject", "Body")


def test_service_send_email_returns_api_response():
    expected = {"MessageID": "abc", "ErrorCode": 0}
    service = PostmarkEmailService(SERVER_TOKEN, FROM_EMAIL)

    with patch("sfk_scheduler.postmark.request.urlopen") as mock_urlopen, \
         patch("sfk_scheduler.postmark.json.load", return_value=expected):
        mock_urlopen.return_value = _mock_urlopen_response(expected)
        result = service.send_email("user@example.com", "Subject", "Body")

    assert result == expected


def test_module_default_service_reads_env_once(monkeypatch):
    monkeypatch.setenv("POSTMARK_SERVER_TOKEN", SERVER_TOKEN)
    monkeypatch.setenv("POSTMARK_FROM_EMAIL", FROM_EMAIL)
    postmark._default_service = None
    mock_service = MagicMock()
    mock_service.send_email.return_value = {"ok": True}

    with patch("sfk_scheduler.postmark.PostmarkEmailService.from_env", return_value=mock_service) as mock_from_env:
        postmark.send_email("user@example.com", "Subject", "Body")
        postmark.send_reminder_email("user2@example.com", "Subject2", "Body2")

    assert mock_from_env.call_count == 1
    assert mock_service.send_email.call_count == 2
    postmark._default_service = None
