import json
from urllib import error, parse, request
from uuid import uuid4

from sfk_scheduler.members import normalize_members


def parse_api_response(payload):
    if isinstance(payload, dict):
        if payload.get("errors"):
            error_messages = "; ".join(
                item.get("message", "Unknown API error")
                for item in payload["errors"]
                if isinstance(item, dict)
            )
            raise RuntimeError(f"MyWebLog API error: {error_messages}")

        users = payload.get("users")
        if isinstance(users, list):
            return users

    raise ValueError("Could not find a users list in the MyWebLog response.")

MYWEBLOG_API_URL = "https://api.myweblog.se/main/v4/users/"
DEFAULT_PAGE_SIZE = 500


def build_headers(token, request_id):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Request-Id": request_id,
    }


def build_users_url(base_url, offset, page_size=DEFAULT_PAGE_SIZE):
    query = parse.urlencode(
        {
            "active": 1,
            "verbose": "true",
            "limit": page_size,
            "offset": offset,
        }
    )
    return f"{base_url}?{query}"


def fetch_users_page(token, offset, base_url=MYWEBLOG_API_URL, page_size=DEFAULT_PAGE_SIZE):
    request_id = str(uuid4())
    api_request = request.Request(
        build_users_url(base_url, offset, page_size),
        headers=build_headers(token, request_id),
        method="GET",
    )

    try:
        with request.urlopen(api_request, timeout=30) as response:
            payload = json.load(response)
    except error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace")

        try:
            payload = json.loads(response_body)
            parse_api_response(payload)
        except (json.JSONDecodeError, ValueError):
            pass
        except RuntimeError as api_error:
            raise RuntimeError(str(api_error)) from exc

        raise RuntimeError(
            f"MyWebLog request failed with HTTP {exc.code}: {response_body}"
        ) from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not connect to MyWebLog: {exc.reason}") from exc

    return parse_api_response(payload)


def fetch_current_members(token, base_url=MYWEBLOG_API_URL, page_size=DEFAULT_PAGE_SIZE):
    all_users = []
    offset = 0

    while True:
        users = fetch_users_page(token, offset, base_url=base_url, page_size=page_size)
        all_users.extend(users)

        if len(users) < page_size:
            break

        offset += page_size

    return normalize_members(all_users)
