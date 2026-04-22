# Instructions for Copilot

This file contains instruction for the Copilot agent to generate clean code
in a way that is consistent with the project's coding style and guidelines.
Please follow these instructions when writing code for this project.

## Programming Language
The programming languages to use in this project are Python for scripting and Terraform for infrastructure. Please write code in these languages and follow the conventions and best practices for each language.

### Scripting
The primary programming language for this project is Python. Please write code in Python and follow the conventions and best practices for Python development.

### Infrastructure
For the AWS backend infrastructure use Terraform to define and manage the infrastructure as code. Follow Terraform best practices and conventions when writing the infrastructure code.

## Coding Style
- Follow PEP 8 style guide for Python code.
- Use meaningful variable and function names that clearly describe their purpose.
- Write modular and reusable code by breaking down complex functions into smaller, more focused functions.

## Naming Conventions
- Use snake_case for variable and function names in Python.
- Use PascalCase for class names in Python.
- Use descriptive names for files and directories that reflect their purpose and content.

## Project structure
- Organize code into logical modules and packages based on functionality.
- Keep related code together and separate different concerns into different files or directories.
- Use a clear and consistent directory structure that makes it easy to navigate the project.

```
src/
  generate_schedule.py    # CLI: generate or extend the cleaning schedule
  auto_generate.py        # CLI: auto-extend the schedule when nearing its end
  sync_members.py         # CLI: sync members from MyWebLog API
  clean_data.py           # CLI: reset CSV files to header-only

  sfk_scheduler/          # Library package — pure, testable modules
    config.py             # Env file loading and config value resolution
    members.py            # Member name/number normalisation logic
    member_io.py          # Member CSV read/write
    schedule.py           # Scheduling algorithm
    schedule_io.py        # Schedule CSV read/write
    myweblog.py           # MyWebLog API client

infrastructure/           # Terraform (AWS S3 for schedule storage)

tests/                    # pytest unit tests, one file per source module
  test_auto_generate.py
  test_config.py
  test_member_io.py
  test_members.py
  test_myweblog.py
  test_schedule.py
  test_schedule_io.py

data/                     # CSV data files (members, schedule, excluded)
```

## Testing
- All functions in `src/sfk_scheduler/` and pure functions in CLI scripts must have unit tests.
- Tests live in `tests/`, with one test file per source module (e.g. `test_schedule.py` for `schedule.py`).
- Use `pytest`. Configuration is in `pytest.ini` at the project root; `pythonpath = src` is set so tests import the package directly.
- Use `tmp_path` for file I/O tests and `monkeypatch` for environment variables.
- Use `unittest.mock.patch` for HTTP calls and subprocesses — do not make real network or subprocess calls in tests.
- Run the full suite with `python -m pytest` from the project root.
