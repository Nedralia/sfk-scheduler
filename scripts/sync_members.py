import csv
import json
import os
from pathlib import Path
from urllib import error, parse, request
from uuid import uuid4


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


def normalize_member_name(member):
	first_name = str(
		member.get("first_name")
		or member.get("firstname")
		or member.get("fornamn")
		or ""
	).strip()
	last_name = str(
		member.get("last_name")
		or member.get("lastname")
		or member.get("efternamn")
		or ""
	).strip()
	full_name = f"{first_name} {last_name}".strip()

	if not full_name:
		full_name = str(member.get("full_name") or member.get("name") or "").strip()

	if not full_name:
		return None

	return full_name


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

	normalized_members = sorted(
		{
			member_name
			for member_name in (normalize_member_name(member) for member in all_users)
			if member_name
		}
	)

	if not normalized_members:
		raise RuntimeError("MyWebLog returned no members.")

	return normalized_members


def write_members_csv(members, output_file):
	output_file.parent.mkdir(parents=True, exist_ok=True)

	with open(output_file, "w", newline="", encoding="utf-8") as file_handle:
		writer = csv.writer(file_handle)
		writer.writerow(["name"])
		for member in members:
			writer.writerow([member])


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

