# LinkedIn

View profile, post updates, search jobs, fetch connections, send messages.

## Available actions

- `get_linkedin_profile` — your profile + connections count
- `create_linkedin_post` — publish a text / image post
- `search_linkedin_jobs` — search postings
- `get_linkedin_connections` — list your connections
- `send_linkedin_message` — DM a connection
- `send_message_to_recipients` — message multiple people
- `respond_to_invitation` — accept/ignore connection requests

## Connect

| Command | What it does |
|---|---|
| `/linkedin login` | OAuth via browser |
| `/linkedin status` | Show connected accounts |
| `/linkedin logout [linkedin_id]` | Remove account |

## Prerequisites

OAuth 2.0 with client secret (no PKCE).

Set `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET` in `.env`, or use embedded.

Your own OAuth app:

1. [linkedin.com/developers](https://www.linkedin.com/developers/)
2. Create an app associated with a company page
3. Under "Auth" add the redirect URL `http://localhost:8765`
4. Request the scopes: `openid`, `profile`, `email`, `w_member_social`, `r_basicprofile`
5. Copy Client ID + Client Secret to `.env`

## Troubleshooting

**"unauthorized_scope_error"** — LinkedIn has tightened which apps can request `r_basicprofile` and similar scopes. You may need to apply for LinkedIn Marketing Developer Platform access.

**Post fails with "TEXT_TOO_LONG"** — LinkedIn limits posts to 3000 chars. Trim before calling `create_linkedin_post`.

## Related

- [Credentials](credentials.md)
- [Connections overview](index.md)
