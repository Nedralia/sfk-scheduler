import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sfk_scheduler.schedule_io import get_last_scheduled_date

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
SCHEDULE_FILE = DATA_DIR / "schedule.csv"
GENERATE_SCRIPT = SCRIPT_DIR / "generate_schedule.py"
THRESHOLD_DAYS = 60


def compute_end_date(today):
    try:
        one_year_ahead = today.replace(year=today.year + 1)
    except ValueError:
        # today is Feb 29 on a leap year; land on Feb 28 next year
        one_year_ahead = today.replace(year=today.year + 1, day=28)
    return one_year_ahead - timedelta(days=1)


def needs_extension(last_date, today, threshold_days=THRESHOLD_DAYS):
    return (last_date - today).days <= threshold_days


def main():
    today = datetime.today()
    end_date = compute_end_date(today).strftime("%Y-%m-%d")
    last_date = get_last_scheduled_date(SCHEDULE_FILE)

    if not last_date:
        print("No schedule found. Generating new schedule.")
        subprocess.run(
            [
                sys.executable,
                str(GENERATE_SCRIPT),
                "--start-date", today.strftime("%Y-%m-%d"),
                "--end-date", end_date,
            ],
            check=True,
        )
        return

    remaining_days = (last_date - today).days

    print(f"Last scheduled week: {last_date.date()}")
    print(f"Days remaining: {remaining_days}")

    if needs_extension(last_date, today):
        next_start = (last_date + timedelta(weeks=1)).strftime("%Y-%m-%d")
        print(f"⚠ Schedule nearing end → extending from {next_start} to {end_date}")

        subprocess.run(
            [
                sys.executable,
                str(GENERATE_SCRIPT),
                "--start-date", next_start,
                "--end-date", end_date,
                "--previous-schedule", str(SCHEDULE_FILE),
            ],
            check=True,
        )
    else:
        print("Schedule still sufficient — nothing to do")


if __name__ == "__main__":
    main()

