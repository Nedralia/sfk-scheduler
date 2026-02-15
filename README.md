# Club House Cleaning Schedule Automation

This project automatically generates and maintains a weekly cleaning
schedule for a club house.\
It ensures fair rotation, avoids double assignments, excludes
special-role members, and sends automatic email reminders.

The system is designed to run automatically using cron jobs.

------------------------------------------------------------------------

## Features

-   Generates weekly cleaning schedules
-   Each member is scheduled only once per year
-   Supports excluded members
-   Continues automatically from previous schedules
-   All scheduled weeks start on Mondays
-   ISO week numbers included
-   Automatic email reminders sent 3 days before assigned week
-   Automatically generates new schedules when 2 months remain
-   CSV output (Excel compatible)
-   No external Python dependencies

------------------------------------------------------------------------

## Project Structure

    club-cleaning-scheduler/
    ├── schedule.py                  # Schedule generator
    ├── send_reminders.py           # Daily email reminder sender
    ├── auto_generate_schedule.py   # Auto schedule regeneration
    ├── members.csv                 # Member list
    ├── excluded.csv                # Excluded members
    ├── previous_schedule.csv       # Optional existing schedule
    ├── schedule.csv                # Generated output
    └── README.md

------------------------------------------------------------------------

## File Descriptions

### schedule.py

Generates a weekly cleaning schedule based on:

-   A start date
-   A list of members
-   A list of excluded members
-   An optional previous schedule

Rules:

-   Each person is assigned only once per year
-   All weeks start on Mondays
-   ISO week number is included
-   Output is written to `schedule.csv`

------------------------------------------------------------------------

### send_reminders.py

Reads `schedule.csv` daily and:

-   Finds who is scheduled 3 days in advance
-   Sends an email reminder to that person

Intended to run automatically using cron.

------------------------------------------------------------------------

### auto_generate_schedule.py

Monitors `schedule.csv` and:

-   Detects when less than 60 days remain in the schedule
-   Automatically runs `schedule.py` to generate new future schedules

Intended to run daily using cron.

------------------------------------------------------------------------

### members.csv

List of all club members.

Format:

``` csv
name
Alice
Bob
Charlie
```

------------------------------------------------------------------------

### excluded.csv

List of members excluded from cleaning duty.

Format:

``` csv
name
BoardMember1
BoardMember2
```

------------------------------------------------------------------------

### previous_schedule.csv (optional)

Used to continue scheduling within the same year without duplicates.

Format:

``` csv
week_start,week_number,year,name
2026-01-05,2,2026,Alice
```

------------------------------------------------------------------------

### schedule.csv

Generated output file containing the cleaning schedule.

Format:

``` csv
week_start,week_number,year,name
2026-02-16,8,2026,Bob
```

------------------------------------------------------------------------

## Usage

Generate a new schedule:

``` bash
python schedule.py
```

Run reminders manually:

``` bash
python send_reminders.py
```

Check if schedule needs to be regenerated:

``` bash
python auto_generate_schedule.py
```

------------------------------------------------------------------------

## License

MIT License
