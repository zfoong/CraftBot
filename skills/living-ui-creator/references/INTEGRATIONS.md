# External Integrations (Google, Discord, Slack, etc.)

CraftBot has connected external services (Gmail, YouTube, Discord, Slack, Notion, etc.).
Living UIs can access these through a built-in integration bridge — **do NOT build OAuth flows, API key management, or credential storage yourself.**

The template includes `backend/services/integration_client.py`. Use it:

```python
from services.integration_client import integration

# Check what integrations are connected
integrations = await integration.get_integrations()
# [{"id": "google_workspace", "connected": true}, {"id": "slack", "connected": true}, ...]

# Make an authenticated API call (CraftBot injects credentials automatically)
result = await integration.request(
    integration="google_workspace",
    method="GET",
    url="https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",
)
if result.get("status") == 200:
    channels = result["data"]
```

## Available Integrations

google_workspace (Gmail, Calendar, Drive, YouTube), slack, discord, notion, telegram, github, jira, linkedin, twitter, outlook, whatsapp

## Rules

- NEVER implement OAuth or credential management — the bridge handles all auth
- NEVER ask users for API keys — CraftBot already has their connected accounts
- NEVER store tokens or secrets in the Living UI code or database
- Use `integration.available` to check if the bridge is connected before making calls
- Show a helpful message if an integration is not connected (e.g., "Connect Google in CraftBot settings")
