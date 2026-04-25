import random
from datetime import timedelta


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
            "",
        ))
        date += timedelta(weeks=1)

    return schedule
