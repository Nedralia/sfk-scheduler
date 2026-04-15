import csv
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
SCHEDULE_FILE = DATA_DIR / "schedule.csv"
GENERATE_SCRIPT = SCRIPT_DIR / "schedule.py"
THRESHOLD_DAYS = 60


def get_last_scheduled_date():
    with open(SCHEDULE_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        dates = [datetime.fromisoformat(row["week_start"]) for row in reader]

    if not dates:
        return None

    return max(dates)


def main():
    today = datetime.today()
    last_date = get_last_scheduled_date()

    if not last_date:
        print("No schedule found. Generating new schedule.")
        subprocess.run([sys.executable, str(GENERATE_SCRIPT)], check=True)
        return

    remaining_days = (last_date - today).days

    print(f"Last scheduled week: {last_date.date()}")
    print(f"Days remaining: {remaining_days}")

    if remaining_days <= THRESHOLD_DAYS:
        print("⚠ Schedule nearing end → generating new schedule")

        subprocess.run([sys.executable, str(GENERATE_SCRIPT)], check=True)
    else:
        print("Schedule still sufficient — nothing to do")


if __name__ == "__main__":
    main()

