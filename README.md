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

In addition to email, new proposed rules can be reported as a phone push notification and
a chat message from a live Claude Code session, using `scripts/check_federal_register_push.py`.

This script mirrors `check_federal_register.py` but:
- Tracks its own dedup state in `state/last_push_document_number.txt` (separate from the
  email workflow's state file, so the two channels don't interfere with each other).
- Prints new rules as JSON instead of sending email — a Claude session reads that JSON and
  is responsible for actually sending the push notification / chat message.

**Important limitation:** push notifications and Claude app messages can only be sent by an
*active Claude Code session* — plain GitHub Actions runners (which power the email workflow
above) have no way to trigger them. So, unlike the email workflow, this is not fully
"set and forget" on GitHub's infrastructure alone. To get push notifications every time a
new proposed rule is published, you need one of:

1. A recurring **Trigger** configured for this repo in the Claude Code on the web dashboard
   (see [the docs](https://code.claude.com/docs/en/claude-code-on-the-web)), scheduled on the
   same cadence as the email workflow (hourly on weekdays). Each firing starts a fresh session
   that runs the push-check script and notifies on anything new. This is the durable option.
2. A session-scoped recurring check (e.g. via the `CronCreate` tool) kept alive in an open
   Claude Code session — bounded to that session's lifetime and, at most, 7 days.

To seed the push state without notifying about already-published rules, run:

```
python scripts/check_federal_register_push.py --init
```
