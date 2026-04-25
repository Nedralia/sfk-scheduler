# Club House Cleaning Schedule Automation

This project automatically generates and maintains a weekly cleaning
schedule for a club house.\
It ensures fair rotation, avoids double assignments, excludes
special-role members, and prepares reminder payloads for future delivery.

The system is designed to run automatically using cron jobs.

------------------------------------------------------------------------

## Features

-   Generates weekly cleaning schedules
-   Each member is scheduled only once per year
-   Supports excluded members
-   Continues automatically from previous schedules
-   All scheduled weeks start on Mondays
-   ISO week numbers included
-   Reminder payloads generated 3 days before the assigned week
-   Automatically generates new schedules when 2 months remain
-   CSV output (Excel compatible)
-   No external Python dependencies
-   A backend that runs on AWS

------------------------------------------------------------------------

## Project Structure

    club-cleaning-scheduler/
    ├── scripts/
    │   ├── schedule.py             # Schedule generator
    │   ├── send_reminder.py        # Daily email reminder sender
    │   ├── auto_generate_schedule.py
    │   ├── clean_schedule_data.py  # Resets generated schedule data
    │   └── sync_members.py         # Fetches members from MyWebLog
    ├── data/
    │   ├── members.csv             # Member list
    │   ├── excluded.csv            # Excluded members
    │   ├── previous_schedule.csv   # Optional existing schedule
    │   └── schedule.csv            # Generated output
    └── README.md

------------------------------------------------------------------------

## File Descriptions

### scripts/schedule.py

Generates a weekly cleaning schedule based on:

-   A start date
-   A list of members
-   A list of excluded members
-   An optional previous schedule

Rules:

-   Each person is assigned only once per year
-   All weeks start on Mondays
-   ISO week number is included
-   Output is written to `data/schedule.csv`

------------------------------------------------------------------------

### scripts/send_reminder.py

Reads `data/schedule.csv` daily and:

-   Finds who is scheduled 3 days in advance
-   Builds reminder payloads for a future delivery provider

Intended to run automatically using cron.

------------------------------------------------------------------------

### scripts/auto_generate_schedule.py

Monitors `data/schedule.csv` and:

-   Detects when less than 60 days remain in the schedule
-   Automatically runs `scripts/schedule.py` to generate new future schedules

Intended to run daily using cron.

------------------------------------------------------------------------

### scripts/clean_schedule_data.py

Resets generated schedule files by:

-   Clearing `data/schedule.csv`
-   Recreating `data/previous_schedule.csv`

Use this when you want to start scheduling from a clean state.

------------------------------------------------------------------------

### scripts/sync_members.py

Fetches the current active member list from MyWebLog API v4 and writes it to `data/members.csv`.

Required environment variables:

-   `MWL_TOKEN`

------------------------------------------------------------------------

### data/members.csv

List of all club members.

Format:

``` csv
name
Alice
Bob
Charlie
```

------------------------------------------------------------------------

### data/excluded.csv

List of members excluded from cleaning duty.

Format:

``` csv
name
BoardMember1
BoardMember2
```

------------------------------------------------------------------------

### data/previous_schedule.csv (optional)

Used to continue scheduling within the same year without duplicates.

Format:

``` csv
week_start,week_number,year,name,member_number,status
2026-01-05,2,2026,Alice,101,
```

------------------------------------------------------------------------

### data/schedule.csv

Generated output file containing the cleaning schedule.

Format:

``` csv
week_start,week_number,year,name,member_number,status
2026-02-16,8,2026,Bob,102,completed
```

------------------------------------------------------------------------

## Usage

Generate a new schedule:

``` bash
python scripts/schedule.py
```

Generate a new schedule non-interactively:

``` bash
python scripts/schedule.py --start-date 2026-04-15
```

Generate a new schedule with custom input and output files:

``` bash
python scripts/schedule.py --start-date 2026-04-15 --previous-schedule data/previous_schedule.csv --output data/schedule.csv
```

Generate a fresh schedule and ignore previous assignments:

``` bash
python scripts/schedule.py --start-date 2026-04-15 --force-reset
```

Run reminders manually:

``` bash
python scripts/send_reminder.py
```

Check if schedule needs to be regenerated:

``` bash
python scripts/auto_generate_schedule.py
```

Clean existing schedule data:

``` bash
python scripts/clean_schedule_data.py
```

Fetch current members from MyWebLog:

``` bash
python scripts/sync_members.py
```

------------------------------------------------------------------------

## AWS Infrastructure

Terraform files for AWS live in `infrastructure/`.

The Terraform setup provisions:

-   An S3 bucket for `data/schedule.csv`
-   A Lambda function for `scripts/send_reminder.py`
-   IAM policies for CloudWatch Logs and S3 reads
-   A daily EventBridge trigger

Quick start:

``` bash
cp infrastructure/terraform.tfvars.example infrastructure/terraform.tfvars
terraform -chdir=infrastructure init
terraform -chdir=infrastructure plan
terraform -chdir=infrastructure apply
```

------------------------------------------------------------------------

## Version control

Git is used for version control and is stored on GitHub.

### Commits

Commit messages should follow these guidelines.

1. Should contian a brief title of what the change has done.
2. The title must be 80 characters or less
3. Can contain a longer description explaining why the change was made.

## License

MIT License
