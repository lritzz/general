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
        ("fields[]", "agency_names"),
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


def plain_language_summary(abstract, title, agency_names=None):
    """Generate a 2–3 sentence plain-language summary using Claude API if available."""
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    agency_str = ", ".join(agency_names) if agency_names else "a federal agency"

    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            prompt = (
                f"The following is the abstract of a proposed federal rule titled "
                f'"{title}" published by {agency_str} in the Federal Register.\n\n'
                f"Abstract:\n{abstract or '(no abstract provided)'}\n\n"
                "Write a 2–3 sentence plain-language summary that explains: "
                "(1) what the rule proposes to do and (2) who it affects. "
                "Avoid jargon. Be direct and factual. Return only the summary, no preamble."
            )
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text.strip()
        except Exception as exc:
            print(f"⚠️  Claude API summary failed ({exc}); falling back to abstract.")

    # Fallback: use the abstract, trimmed to a reasonable length
    if not abstract:
        return f"This proposed rule from {agency_str} concerns: {title}. See the full text for details."
    sentences = abstract.replace("\n", " ").split(". ")
    summary = ". ".join(sentences[:3]).strip()
    if not summary.endswith("."):
        summary += "."
    return summary


def build_email(rule):
    title = rule.get("title", "Unknown Title")
    pub_date = rule.get("publication_date", "Unknown Date")
    url = rule.get("html_url", "N/A")
    agency_names = rule.get("agency_names", [])
    summary = plain_language_summary(rule.get("abstract"), title, agency_names)

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
    port = int(os.environ.get("EMAIL_PORT", "587"))
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
