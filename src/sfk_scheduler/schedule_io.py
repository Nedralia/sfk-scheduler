import csv
from datetime import datetime
from pathlib import Path


def load_previous_schedule(filename, before_date):
    try:
        with open(filename, newline="", encoding="utf-8") as f:
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


def save_schedule_csv(kept_rows, schedule, filename):
    Path(filename).parent.mkdir(parents=True, exist_ok=True)

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


def get_last_scheduled_date(schedule_file):
    try:
        with open(schedule_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            dates = [datetime.fromisoformat(row["week_start"]) for row in reader]
    except FileNotFoundError:
        return None

    return max(dates) if dates else None
