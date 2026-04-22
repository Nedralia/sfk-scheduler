import json
from urllib import error, parse, request

MAILGUN_API_URL = "https://api.mailgun.net/v3"


def build_send_url(domain, base_url=MAILGUN_API_URL):
    return f"{base_url}/{domain}/messages"


def send_email(api_key, domain, to, subject, body, base_url=MAILGUN_API_URL):
    """Send a plain-text email via the Mailgun API.

    Raises RuntimeError on HTTP or network errors.
    """
    url = build_send_url(domain, base_url)
    data = parse.urlencode(
        {
            "from": f"SFK Scheduler <scheduler@{domain}>",
            "to": to,
            "subject": subject,
            "text": body,
        }
    ).encode()

    credentials = f"api:{api_key}".encode()
    import base64
    auth_header = "Basic " + base64.b64encode(credentials).decode()

    req = request.Request(url, data=data, method="POST")
    req.add_header("Authorization", auth_header)

    try:
        with request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Mailgun request failed with HTTP {exc.code}: {body_text}"
        ) from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not connect to Mailgun: {exc.reason}") from exc
