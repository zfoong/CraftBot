# Twitter

Post tweets, read timelines, search, manage followers via the Twitter / X API v2.

## Available actions

- Post / delete tweet
- Read user timeline
- Search tweets
- Follow / unfollow
- Reply to tweet

Exact names in [Actions catalogue](../reference/actions.md).

## Connect

| Command | What it does |
|---|---|
| `/twitter login <api_key> <api_secret> <access_token> <access_secret>` | Connect with developer app creds |
| `/twitter status` | Show connection status |
| `/twitter logout` | Remove credentials |

## Prerequisites

1. [developer.twitter.com](https://developer.twitter.com/en/portal/dashboard) → create a project and app
2. Enable "User authentication settings" — OAuth 2.0 or OAuth 1.0a (this page assumes 1.0a for `POST` endpoints)
3. Permissions: Read + Write (or Read + Write + DM)
4. Keys and tokens tab → copy:
    - API Key + API Secret (app-level)
    - Access Token + Secret (user-level)
5. Run `/twitter login` with all four

## Pricing note

Twitter/X API is tiered. Free tier has strict limits (~1500 tweets/month). Read endpoints need paid tier for volume.

## Troubleshooting

**403 Forbidden on POST** — app permissions are Read-only. In the portal → User authentication settings, set Read + Write, then **regenerate** access tokens (old ones still have Read-only).

**"Rate limit exceeded"** — free tier resets every 15 minutes (different windows per endpoint). Check `x-rate-limit-reset` headers in errors.

## Related

- [Credentials](credentials.md)
- [Connections overview](index.md)
