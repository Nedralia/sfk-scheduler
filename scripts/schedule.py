import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path
import random


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_PREVIOUS_SCHEDULE_FILE = DATA_DIR / "previous_schedule.csv"
DEFAULT_OUTPUT_FILE = DATA_DIR / "schedule.csv"


def load_members(filename):
    with open(filename, newline='', encoding="utf-8") as f:
        return [
            (row["name"].strip(), row.get("member_number", "").strip())
            for row in csv.DictReader(f)
        ]


def load_names(filename):
    return [name for name, _ in load_members(filename)]


def load_previous_schedule(filename):
    try:
        with open(filename, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            data = list(reader)

            if not data:
                return set(), None

            assigned = {row["name"] for row in data}
            last_date = max(datetime.fromisoformat(row["week_start"]) for row in data)
            return assigned, last_date + timedelta(weeks=1)
    except FileNotFoundError:
        return set(), None


def align_to_monday(date):
    return date - timedelta(days=date.weekday())


def generate_schedule(start_date, members, excluded, already_assigned):
    excluded_names = set(excluded)
    already_assigned_names = set(already_assigned)
    available = [
        (name, number)
        for name, number in members
        if name not in excluded_names and name not in already_assigned_names
    ]

    if not available:
        raise ValueError("No available members left to schedule.")

    random.shuffle(available)

    schedule = []
    date = align_to_monday(start_date)

    for name, member_number in available:
        iso_year, week_number, _ = date.isocalendar()
        schedule.append((
            date.strftime("%Y-%m-%d"),
            week_number,
            iso_year,
            name,
            member_number,
        ))
        date += timedelta(weeks=1)

    return schedule


def save_csv(schedule, filename):
    filename.parent.mkdir(parents=True, exist_ok=True)

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["week_start", "week_number", "year", "name", "member_number"])
        writer.writerows(schedule)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate the club cleaning schedule.")
    parser.add_argument(
        "--start-date",
        help="Schedule start date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Path to the output schedule CSV file.",
    )
    parser.add_argument(
        "--previous-schedule",
        type=Path,
        default=DEFAULT_PREVIOUS_SCHEDULE_FILE,
        help="Path to a previous schedule CSV file used to avoid duplicate assignments.",
    )
    parser.add_argument(
        "--force-reset",
        action="store_true",
        help="Ignore previous schedule data and start a fresh rotation.",
    )
    return parser.parse_args()


def resolve_start_date(start_date_arg):
    if start_date_arg:
        return datetime.strptime(start_date_arg, "%Y-%m-%d")

    start_date_input = input("Enter start date (YYYY-MM-DD): ")
    return datetime.strptime(start_date_input, "%Y-%m-%d")


def main():
    args = parse_args()
    start_date = resolve_start_date(args.start_date)
    output_file = args.output
    previous_schedule_file = args.previous_schedule

    members = load_members(DATA_DIR / "members.csv")
    excluded = load_names(DATA_DIR / "excluded.csv")

    if args.force_reset:
        already_assigned, next_date = set(), None
    else:
        already_assigned, next_date = load_previous_schedule(previous_schedule_file)

    if next_date:
        start_date = max(start_date, next_date)

    schedule = generate_schedule(
        start_date=start_date,
        members=members,
        excluded=excluded,
        already_assigned=already_assigned,
    )

    save_csv(schedule, output_file)

    print(f"\nSchedule created: {len(schedule)} weeks")
    print(f"File written: {output_file}")


if __name__ == "__main__":
    main()

