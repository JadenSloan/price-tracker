"""Populate database from existing JSON files."""

import json
from pathlib import Path

from src.storage import repository as repo

ACTIVE_JSON = Path("data/active/grailed_listings.json")
SOLD_JSON = Path("data/sold/grailed_sold.json")


def main() -> None:
    repo.create_tables()

    active = json.loads(ACTIVE_JSON.read_text())
    for listing in active:
        repo.save_active_listing(listing)
    print(f"Loaded {len(active)} active listings")

    sold = json.loads(SOLD_JSON.read_text())
    count = repo.bulk_insert_sold_listings(sold)
    print(f"Loaded {count} sold listings")


if __name__ == "__main__":
    main()
