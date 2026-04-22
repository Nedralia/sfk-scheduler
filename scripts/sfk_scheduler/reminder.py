def build_reminder(row):
    return {
        "name": row["name"],
        "email": row.get("email", ""),
        "week_start": row["week_start"],
        "week_number": row["week_number"],
        "subject": "Club House Cleaning Reminder",
        "body": (
            f"Hello {row['name']},\n\n"
            "Reminder that you are scheduled to clean the club house on:\n\n"
            f"{row['week_start']} (Week {row['week_number']})\n\n"
            "Thank you!"
        ),
    }


def find_due_reminders(rows, target_date):
    return [
        build_reminder(row)
        for row in rows
        if row["week_start"] == target_date
    ]
