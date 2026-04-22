# Outlook

Microsoft 365 / Outlook via the Microsoft Graph API.

## Available actions

- Send, read, search emails
- List calendar events, create / update events
- List / upload / download OneDrive files
- Access contacts

*(Exact action names match Gmail/Drive counterparts with `outlook_` / `graph_` prefix — see [Actions catalogue](../reference/actions.md).)*

## Connect

| Command | What it does |
|---|---|
| `/outlook login` | OAuth via browser |
| `/outlook status` | Show connected accounts |
| `/outlook logout [email]` | Remove an account |

## Prerequisites

Uses **PKCE** — only a Client ID needed.

=== "Embedded (easy)"
    Release builds include a CraftOS Client ID.

=== "Your own OAuth app"
    1. [Azure Portal](https://portal.azure.com/) → App registrations
    2. "New registration" — single tenant or multi-tenant (for personal + work accounts)
    3. Authentication → add platform → Mobile/desktop → redirect URI `http://localhost:8765`
    4. API permissions → add Microsoft Graph scopes: `Mail.ReadWrite`, `Mail.Send`, `Calendars.ReadWrite`, `Files.ReadWrite`, `User.Read`
    5. Overview → copy Application (client) ID
    6. Set `OUTLOOK_CLIENT_ID` in `.env`
    7. Run `/outlook login`

## Troubleshooting

**"AADSTS9002313"** — you registered the app as single-tenant but are signing in with a personal account. Switch the app to multi-tenant or register a second Client ID.

**Token refresh fails** — Microsoft tokens have short lives; refresh happens automatically. If it keeps failing, try `/outlook logout` then `/outlook login`.

## Related

- [Google Workspace](google-workspace.md) — Google's equivalent
- [Credentials](credentials.md)
- [Connections overview](index.md)
