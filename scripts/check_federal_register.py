#!/usr/bin/env python3
"""Monitor the Federal Register for new proposed rules and send email notifications."""

import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests

STATE_FILE = Path(__file__).parent.parent / "state" / "last_document_number.txt"
FR_API = "https://www.federalregister.gov/api/v1/documents.json"
EMAIL_TO = os.environ.get("EMAIL_TO", "lucy.ritzmann@governingforimpact.org")

HEADERS = {
    "User-Agent": "nprms-monitor/1.0 (lucy.ritzmann@governingforimpact.org)"
}


def fetch_latest_rules(per_page=5):
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


def plain_language_summary(abstract, title):
    """Trim and lightly clean the Federal Register abstract for email."""
    if not abstract:
        return f"This proposed rule concerns: {title}. See the full text for details."
    # Federal Register abstracts are already concise; truncate if unusually long
    if len(abstract) > 1000:
        abstract = abstract[:997] + "..."
    return abstract


def build_email(rule):
    title = rule.get("title", "Unknown Title")
    pub_date = rule.get("publication_date", "Unknown Date")
    url = rule.get("html_url", "N/A")
    summary = plain_language_summary(rule.get("abstract"), title)

    subject = f"New Federal Register proposed rule: {title}"
    body = f"""\
A new proposed rule has been published in the Federal Register.

{summary}

Publication Date: {pub_date}
Full Text: {url}

---
This notification is sent automatically whenever a new proposed rule is published.
To stop receiving these emails, disable the workflow at:
https://github.com/lritzz/nprms/actions
"""
    return subject, body


def send_email(subject, body):
    host = os.environ.get("EMAIL_HOST", "")
    port_str = os.environ.get("EMAIL_PORT", "")
    port = int(port_str) if port_str.strip() else 587
    user = os.environ.get("EMAIL_USER", "")
    password = os.environ.get("EMAIL_PASSWORD", "")
    from_addr = os.environ.get("EMAIL_FROM") or user

    if not all([host, user, password]):
        print(
            "⚠️  Email secrets not configured. Printing draft instead:\n"
            f"To: {EMAIL_TO}\nSubject: {subject}\n\n{body}"
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = EMAIL_TO
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(host, port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)

    print(f"✅ Email sent to {EMAIL_TO}")
    print(f"   Subject: {subject}")


def main():
    init_mode = "--init" in sys.argv  # populate state without sending emails

    try:
        rules = fetch_latest_rules(per_page=10)
    except requests.RequestException as exc:
        print(f"❌ Failed to fetch Federal Register: {exc}", file=sys.stderr)
        sys.exit(1)

    if not rules:
        print("No proposed rules returned by API.")
        return

    seen = load_seen()
    new_rules = [r for r in rules if r["document_number"] not in seen]

    if not new_rules:
        print(f"No new proposed rules (checked {len(rules)} most recent).")
        return

    if init_mode:
        # Seed state silently — no emails on first setup
        all_numbers = {r["document_number"] for r in rules}
        save_seen(seen | all_numbers)
        print(
            f"Initialized state with {len(all_numbers)} document(s). "
            "Future new rules will trigger email notifications."
        )
        return

    for rule in new_rules:
        subject, body = build_email(rule)
        send_email(subject, body)
        seen.add(rule["document_number"])
        print(f"Processed: {rule['document_number']} — {rule.get('title', '')[:80]}")

    save_seen(seen)


if __name__ == "__main__":
    main()
