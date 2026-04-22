import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path
import random


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_PREVIOUS_SCHEDULE_FILE = DATA_DIR / "schedule.csv"
DEFAULT_OUTPUT_FILE = DATA_DIR / "schedule.csv"


def load_members(filename):
    with open(filename, newline='', encoding="utf-8") as f:
        return [
            (row["name"].strip(), row.get("member_number", "").strip())
            for row in csv.DictReader(f)
        ]


def load_names(filename):
    return [name for name, _ in load_members(filename)]


def load_previous_schedule(filename, before_date):
    try:
        with open(filename, newline='', encoding="utf-8") as f:
            data = list(csv.DictReader(f))

        if not data:
            return [], set()

        kept_rows = [
            row for row in data
            if datetime.fromisoformat(row["week_start"]) < before_date
        ]
        assigned_names = {row["name"] for row in kept_rows}
        return kept_rows, assigned_names
    except FileNotFoundError:
        return [], set()


def align_to_monday(date):
    return date - timedelta(days=date.weekday())


def generate_schedule(start_date, members, excluded, already_assigned, end_date=None):
    excluded_names = set(excluded)
    eligible = [
        (name, number)
        for name, number in members
        if name not in excluded_names
    ]

    if not eligible:
        raise ValueError("No eligible members to schedule (all are excluded).")

    already_assigned_names = set(already_assigned)
    first_round = [m for m in eligible if m[0] not in already_assigned_names]

    if not first_round:
        first_round = list(eligible)

    random.shuffle(first_round)

    queue = list(first_round)
    schedule = []
    date = align_to_monday(start_date)

    while True:
        if end_date and date > end_date:
            break

        if not queue:
            if end_date is None:
                break
            next_round = list(eligible)
            random.shuffle(next_round)
            queue = next_round

        name, member_number = queue.pop(0)
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


def save_csv(kept_rows, schedule, filename):
    filename.parent.mkdir(parents=True, exist_ok=True)

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["week_start", "week_number", "year", "name", "member_number"])
        for row in kept_rows:
            writer.writerow([
                row["week_start"],
                row["week_number"],
                row["year"],
                row["name"],
                row.get("member_number", ""),
            ])
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
    parser.add_argument(
        "--end-date",
        help="Schedule end date in YYYY-MM-DD format. No weeks beyond this date will be added.",
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
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d") if args.end_date else None
    output_file = args.output
    previous_schedule_file = args.previous_schedule

    members = load_members(DATA_DIR / "members.csv")
    excluded = load_names(DATA_DIR / "excluded.csv")

    if args.force_reset:
        kept_rows, already_assigned = [], set()
    else:
        kept_rows, already_assigned = load_previous_schedule(previous_schedule_file, start_date)

    schedule = generate_schedule(
        start_date=start_date,
        members=members,
        excluded=excluded,
        already_assigned=already_assigned,
        end_date=end_date,
    )

    save_csv(kept_rows, schedule, output_file)

    print(f"\nSchedule kept:  {len(kept_rows)} weeks")
    print(f"Schedule added: {len(schedule)} weeks")
    print(f"File written:   {output_file}")


if __name__ == "__main__":
    main()

