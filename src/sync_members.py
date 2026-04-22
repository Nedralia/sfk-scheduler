from pathlib import Path

from sfk_scheduler.config import load_env_file, get_config_value
from sfk_scheduler.myweblog import fetch_current_members
from sfk_scheduler.member_io import write_members_csv

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
ENV_FILE = PROJECT_ROOT / ".env"
MEMBERS_FILE = DATA_DIR / "members.csv"

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

