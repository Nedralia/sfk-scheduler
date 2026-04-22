import json
import os
from pathlib import Path
from urllib import error, parse, request
from uuid import uuid4

from sfk_scheduler.members import parse_api_response, normalize_members
from sfk_scheduler.io import write_members_csv

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
ENV_FILE = PROJECT_ROOT / ".env"
MEMBERS_FILE = DATA_DIR / "members.csv"
MYWEBLOG_API_URL = "https://api.myweblog.se/main/v4/users/"
DEFAULT_PAGE_SIZE = 500


def load_env_file(env_file):
	env_values = {}

	if not env_file.exists():
		return env_values

	with open(env_file, encoding="utf-8") as file_handle:
		for raw_line in file_handle:
			line = raw_line.strip()

			if not line or line.startswith("#") or "=" not in line:
				continue

			key, value = line.split("=", 1)
			env_values[key.strip()] = value.strip()

	return env_values


def get_config_value(name, env_values):
	return os.environ.get(name) or env_values.get(name)


def build_headers(token, request_id):
	return {
		"Authorization": f"Bearer {token}",
		"Content-Type": "application/json",
		"Request-Id": request_id,
	}


def build_users_url(offset):
	query = parse.urlencode(
		{
			"active": 1,
			"verbose": "true",
			"limit": DEFAULT_PAGE_SIZE,
			"offset": offset,
		}
	)
	return f"{MYWEBLOG_API_URL}?{query}"


def fetch_users_page(token, offset):
	request_id = str(uuid4())
	api_request = request.Request(
		build_users_url(offset),
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

		raise RuntimeError(f"MyWebLog request failed with HTTP {exc.code}: {response_body}") from exc
	except error.URLError as exc:
		raise RuntimeError(f"Could not connect to MyWebLog: {exc.reason}") from exc

	return parse_api_response(payload)


def fetch_current_members(token):
	all_users = []
	offset = 0

	while True:
		users = fetch_users_page(token, offset)
		all_users.extend(users)

		if len(users) < DEFAULT_PAGE_SIZE:
			break

		offset += DEFAULT_PAGE_SIZE

	return normalize_members(all_users)


def main():
	env_values = load_env_file(ENV_FILE)
	token = get_config_value("MWL_TOKEN", env_values)

	if not token:
		raise RuntimeError("Missing MWL_TOKEN in .env or environment.")

	members = fetch_current_members(token)
	write_members_csv(members, MEMBERS_FILE)

	print(f"Fetched {len(members)} members from MyWebLog")
	print(f"File written: {MEMBERS_FILE}")


if __name__ == "__main__":
	main()

