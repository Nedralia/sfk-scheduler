import csv
from datetime import datetime, timedelta
import subprocess
import sys
import os


SCHEDULE_FILE = "schedule.csv"
GENERATE_SCRIPT = "schedule.py"
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
        subprocess.run([sys.executable, GENERATE_SCRIPT])
        return

    remaining_days = (last_date - today).days

    print(f"Last scheduled week: {last_date.date()}")
    print(f"Days remaining: {remaining_days}")

    if remaining_days <= THRESHOLD_DAYS:
        print("⚠ Schedule nearing end → generating new schedule")

        subprocess.run([sys.executable, GENERATE_SCRIPT])
    else:
        print("Schedule still sufficient — nothing to do")


if __name__ == "__main__":
    main()

