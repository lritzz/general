# NPRMS — Federal Register Proposed Rule Monitor

Automatically emails `lucy.ritzmann@governingforimpact.org` whenever a new proposed rule is published in the Federal Register.

## How it works

- A GitHub Actions workflow runs **every hour on weekdays** (plus once each weekend day).
- It queries the [Federal Register API](https://www.federalregister.gov/developers/api/v1) for the newest proposed rules.
- Any rule not already in `state/last_document_number.txt` is treated as new: a notification email is sent and the state file is updated.

## Email format

**Subject:** `New Federal Register proposed rule: <title>`

**Body:**
- Plain-language summary (from the Federal Register abstract)
- Publication date
- Direct link to the full rule text

## Setup — required GitHub secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Example |
|---|---|
| `EMAIL_HOST` | `smtp.gmail.com` |
| `EMAIL_PORT` | `587` |
| `EMAIL_USER` | `yourname@gmail.com` |
| `EMAIL_PASSWORD` | App password (not your login password) |
| `EMAIL_FROM` | `yourname@gmail.com` (optional — defaults to EMAIL_USER) |

### Gmail app password

1. Enable 2-factor authentication on your Google account.
2. Go to **Google Account → Security → App passwords**.
3. Create a new app password and paste it as `EMAIL_PASSWORD`.

## First run / initialization

To seed the state file without sending emails for already-published rules:

1. Go to **Actions → Federal Register Proposed Rule Monitor → Run workflow**.
2. Check the **"Seed state without sending emails"** checkbox.
3. Click **Run workflow**.

After that, every new rule will trigger an email automatically.

## Manual trigger

You can also trigger the workflow manually at any time via the **Run workflow** button in the Actions tab.

## Push / Claude app notifications

In addition to email, a separate Claude Code scheduled task checks for new proposed rules and sends a push notification plus a message in the Claude app. It tracks the last rule it notified about in `state/last_pushed_document_number.txt`, distinct from the email pipeline's `state/last_document_number.txt`, so the two channels don't interfere with each other.

Since that scheduled task runs in a sandboxed session that cannot reach `federalregister.gov` directly (network policy), it primarily relies on `state/rule_log.json` — a rolling log of full rule details (title, publication date, URL, abstract) written by this workflow's script (`scripts/check_federal_register.py`) whenever it detects a new rule via the official API. This file is the reliable source of truth for the push-notification task; if it should ever be empty or stale, the task falls back to manual web research and flags results as best-effort.

**Note:** the scheduled Federal Register workflow above only runs when it lives on the repository's default branch. If this file was updated on a non-default branch, merge those changes to default so the hourly check (and `state/rule_log.json`) stay live.
