import csv
from pathlib import Path


def load_members(filename):
    with open(filename, newline="", encoding="utf-8") as f:
        return [
            (row["name"].strip(), row.get("member_number", "").strip())
            for row in csv.DictReader(f)
        ]


def load_names(filename):
    return [name for name, _ in load_members(filename)]


def write_members_csv(members, output_file):
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["member_number", "name"])
        for name, member_number in members:
            writer.writerow([member_number, name])
