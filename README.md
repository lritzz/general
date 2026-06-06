# NPRMS — Federal Register Proposed Rule Monitor

Automatically emails `lucy.ritzmann@governingforimpact.org` whenever a new proposed rule is published in the Federal Register.

## How it works

- A GitHub Actions workflow runs **every hour on weekdays** (plus once each weekend day).
- It queries the [Federal Register API](https://www.federalregister.gov/developers/api/v1) for the newest proposed rules.
- Any rule not already in `state/last_document_number.txt` is treated as new: a notification email is sent and the state file is updated.

## Email format

**Subject:** `New Federal Register proposed rule: <title>`

**Body:**
- Plain-language 2–3 sentence summary (written by Claude if `ANTHROPIC_API_KEY` is set; otherwise derived from the Federal Register abstract)
- Publication date
- Direct link to the full rule text

## Setup — required GitHub secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Example | Required? |
|---|---|---|
| `EMAIL_HOST` | `smtp.gmail.com` | Yes |
| `EMAIL_PORT` | `587` | Yes |
| `EMAIL_USER` | `yourname@gmail.com` | Yes |
| `EMAIL_PASSWORD` | App password (not your login password) | Yes |
| `EMAIL_FROM` | `yourname@gmail.com` | No (defaults to EMAIL_USER) |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | No (enables plain-language summaries via Claude) |

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
