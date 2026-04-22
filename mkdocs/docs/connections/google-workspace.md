# Google Workspace

Gmail, Google Calendar, Google Drive, Google Meet, Google Contacts — one OAuth flow connects all of them.

## Available actions

**Gmail:**

- `send_gmail` — compose + send
- `list_gmail` — list messages by query
- `get_gmail` — read one message
- `read_top_emails` — inbox summary

**Calendar:**

- `create_google_meet` — event with Meet link
- `check_calendar_availability` — busy/free slots

**Drive:**

- `list_drive_files` — list files/folders
- `create_drive_folder` — create a folder
- `move_drive_file` — move a file or folder

## Connect

| Command | What it does |
|---|---|
| `/google login` | Authenticate via Google OAuth (opens browser) |
| `/google status` | Show connected accounts |
| `/google logout [email]` | Remove an account |

## Prerequisites

Uses **PKCE** — only a Client ID is required (no secret).

=== "Embedded (easy)"
    Release builds include a CraftOS Client ID. Just run `/google login`.

=== "Your own OAuth app"
    1. [Google Cloud Console](https://console.cloud.google.com/) → Credentials
    2. "Create Credentials" → OAuth client ID → **Desktop application** type
    3. Copy the Client ID
    4. Enable Gmail, Calendar, Drive, People APIs
    5. Set `GOOGLE_CLIENT_ID` in `.env` (skip the secret — PKCE doesn't need it)
    6. Run `/google login`

Scopes requested: Gmail modify, Calendar, Drive, Contacts (read-only), UserInfo. Review the consent screen carefully.

## Troubleshooting

**"access_denied" on consent screen** — your Google Workspace admin may have restricted third-party apps. Ask them to allow the CraftOS Client ID, or create your own under your project.

**"invalid_grant" on refresh** — your refresh token was revoked. Run `/google logout <email>` then `/google login`.

**Emails not sending** — check the `send_gmail` action's `to` field formatting; `"Bob <bob@example.com>"` vs bare addresses both work.

## Related

- [Outlook](outlook.md) — Microsoft's equivalent
- [Credentials](credentials.md)
- [Connections overview](index.md)
