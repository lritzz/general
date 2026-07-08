#!/usr/bin/env python3
"""Check the Federal Register for new proposed rules and print them as JSON.

Unlike check_federal_register.py (which emails lucy.ritzmann@governingforimpact.org),
this script has no side effects other than updating its own state file. It is meant to
be invoked from a live Claude Code session, which reads the JSON on stdout and uses it
to send a push notification / chat message for each new rule, then commits the updated
state file back to the repo.

Uses a separate state file (state/last_push_document_number.txt) from the email
workflow's state file, so the two notification channels can be seeded/reset
independently.
"""

import json
import sys
from pathlib import Path

import requests

STATE_FILE = Path(__file__).parent.parent / "state" / "last_push_document_number.txt"
FR_API = "https://www.federalregister.gov/api/v1/documents.json"

HEADERS = {
    "User-Agent": "nprms-monitor/1.0 (lucy.ritzmann@governingforimpact.org)"
}


def fetch_latest_rules(per_page=10):
    params = [
        ("conditions[type][]", "PRORULE"),
        ("order", "newest"),
        ("per_page", str(per_page)),
        ("fields[]", "title"),
        ("fields[]", "publication_date"),
        ("fields[]", "html_url"),
        ("fields[]", "abstract"),
        ("fields[]", "document_number"),
    ]
    resp = requests.get(FR_API, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json().get("results", [])


def load_seen():
    if STATE_FILE.exists():
        content = STATE_FILE.read_text().strip()
        if content:
            return set(content.splitlines())
    return set()


def save_seen(doc_numbers):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text("\n".join(sorted(doc_numbers)) + "\n")


def main():
    init_mode = "--init" in sys.argv

    try:
        rules = fetch_latest_rules()
    except requests.RequestException as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(1)

    seen = load_seen()
    new_rules = [r for r in rules if r["document_number"] not in seen]

    if init_mode:
        all_numbers = {r["document_number"] for r in rules}
        save_seen(seen | all_numbers)
        print(json.dumps({"initialized": len(all_numbers)}))
        return

    if new_rules:
        save_seen(seen | {r["document_number"] for r in new_rules})

    print(json.dumps({"new_rules": new_rules}, indent=2))


if __name__ == "__main__":
    main()
