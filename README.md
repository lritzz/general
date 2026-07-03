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

In addition to email, new proposed rules can be delivered as a phone push notification plus a message in the Claude app. This channel works differently from the email one:

- Push notifications and Claude-app messages can only be sent by an **active Claude Code session** — GitHub Actions has no way to trigger them directly.
- To get this on a recurring basis, set up a **Claude Code on the web Trigger** (scheduled or webhook) pointed at this repo, with a prompt such as: *"Check `state/last_document_number.txt` on the default branch against the Federal Register API (or web search if the API is unreachable) for any proposed rule not yet in the file. If found, send a push notification and a chat message with Subject `New Federal Register proposed rule: <title>`, and body containing the plain-language summary, publication date, and link."*
- `state/push_notified.txt` tracks which document numbers have already been delivered through this channel, separately from the email dedup state in `state/last_document_number.txt`, so the two channels don't interfere with each other.
- Within a single interactive Claude session, the same check can also be run on a short-lived cron loop (`CronCreate`), but that only lasts for the session's lifetime (max 7 days) — a Trigger is the durable option.
