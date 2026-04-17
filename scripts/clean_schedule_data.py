import csv
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
SCHEDULE_HEADER = ["week_start", "week_number", "year", "name"]


def reset_csv(file_path):
    with open(file_path, "w", newline="", encoding="utf-8") as file_handle:
        writer = csv.writer(file_handle)
        writer.writerow(SCHEDULE_HEADER)


def main():
    schedule_file = DATA_DIR / "schedule.csv"
    previous_schedule_file = DATA_DIR / "previous_schedule.csv"

    reset_csv(schedule_file)
    reset_csv(previous_schedule_file)

    print(f"Cleared: {schedule_file}")
    print(f"Cleared: {previous_schedule_file}")


if __name__ == "__main__":
    main()