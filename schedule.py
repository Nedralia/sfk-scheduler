import csv
from datetime import datetime, timedelta
import random


def load_names(filename):
    with open(filename, newline='', encoding="utf-8") as f:
        return [row["name"].strip() for row in csv.DictReader(f)]


def load_previous_schedule(filename):
    try:
        with open(filename, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            data = list(reader)
            assigned = {row["name"] for row in data}
            last_date = max(datetime.fromisoformat(row["week_start"]) for row in data)
            return assigned, last_date + timedelta(weeks=1)
    except FileNotFoundError:
        return set(), None


def align_to_monday(date):
    return date - timedelta(days=date.weekday())


def generate_schedule(start_date, members, excluded, already_assigned):
    available = list(set(members) - set(excluded) - set(already_assigned))

    if not available:
        raise ValueError("No available members left to schedule.")

    random.shuffle(available)

    schedule = []
    date = align_to_monday(start_date)

    for person in available:
        iso_year, week_number, _ = date.isocalendar()
        schedule.append((
            date.strftime("%Y-%m-%d"),
            week_number,
            person
        ))
        date += timedelta(weeks=1)

    return schedule


def save_csv(schedule, filename):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["week_start", "week_number", "year", "name"])
        writer.writerows(schedule)


def main():
    start_date_input = input("Enter start date (YYYY-MM-DD): ")
    start_date = datetime.strptime(start_date_input, "%Y-%m-%d")

    members = load_names("members.csv")
    excluded = load_names("excluded.csv")

    already_assigned, next_date = load_previous_schedule("previous_schedule.csv")

    if next_date:
        start_date = max(start_date, next_date)

    schedule = generate_schedule(
        start_date=start_date,
        members=members,
        excluded=excluded,
        already_assigned=already_assigned,
    )

    save_csv(schedule, "schedule.csv")

    print(f"\nSchedule created: {len(schedule)} weeks")
    print("File written: schedule.csv")


if __name__ == "__main__":
    main()

