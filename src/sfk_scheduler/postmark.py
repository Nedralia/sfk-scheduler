import json
import os
from urllib import error, request

POSTMARK_API_URL = "https://api.postmarkapp.com/email"

_default_service = None


def build_send_url(base_url=POSTMARK_API_URL):
    return base_url


class PostmarkEmailService:
    def __init__(self, server_token, from_email, message_stream=None, base_url=POSTMARK_API_URL):
        self.server_token = server_token
        self.from_email = from_email
        self.message_stream = message_stream
        self.base_url = base_url

    @classmethod
    def from_env(cls):
        message_stream = os.environ.get("POSTMARK_MESSAGE_STREAM")
        return cls(
            server_token=os.environ["POSTMARK_SERVER_TOKEN"],
            from_email=os.environ["POSTMARK_FROM_EMAIL"],
            message_stream=message_stream or None,
        )

    def send_email(self, to, subject, body):
        payload = {
            "From": self.from_email,
            "To": to,
            "Subject": subject,
            "TextBody": body,
        }

        if self.message_stream:
            payload["MessageStream"] = self.message_stream

        req = request.Request(
            build_send_url(self.base_url),
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")
        req.add_header("X-Postmark-Server-Token", self.server_token)

        try:
            with request.urlopen(req, timeout=30) as response:
                return json.load(response)
        except error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Postmark request failed with HTTP {exc.code}: {body_text}"
            ) from exc
        except error.URLError as exc:
            raise RuntimeError(f"Could not connect to Postmark: {exc.reason}") from exc


def get_default_service():
    global _default_service
    if _default_service is None:
        _default_service = PostmarkEmailService.from_env()
    return _default_service


def send_email(to, subject, body):
    return get_default_service().send_email(to=to, subject=subject, body=body)


def send_reminder_email(to, subject, body):
    return send_email(to=to, subject=subject, body=body)
