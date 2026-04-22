import argparse
from datetime import datetime
from pathlib import Path

from sfk_scheduler.member_io import load_members, load_names
from sfk_scheduler.schedule_io import load_previous_schedule, save_schedule_csv
from sfk_scheduler.schedule import generate_schedule

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_SCHEDULE_FILE = DATA_DIR / "schedule.csv"


def parse_args():
    parser = argparse.ArgumentParser(description="Generate the club cleaning schedule.")
    parser.add_argument(
        "--start-date",
        help="Schedule start date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_SCHEDULE_FILE,
        help="Path to the output schedule CSV file.",
    )
    parser.add_argument(
        "--previous-schedule",
        type=Path,
        default=DEFAULT_SCHEDULE_FILE,
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

    members = load_members(DATA_DIR / "members.csv")
    excluded = load_names(DATA_DIR / "excluded.csv")

    if args.force_reset:
        kept_rows, already_assigned = [], set()
    else:
        kept_rows, already_assigned = load_previous_schedule(args.previous_schedule, start_date)

    schedule = generate_schedule(
        start_date=start_date,
        members=members,
        excluded=excluded,
        already_assigned=already_assigned,
        end_date=end_date,
    )

    save_schedule_csv(kept_rows, schedule, args.output)

    print(f"\nSchedule kept:  {len(kept_rows)} weeks")
    print(f"Schedule added: {len(schedule)} weeks")
    print(f"File written:   {args.output}")


if __name__ == "__main__":
    main()

