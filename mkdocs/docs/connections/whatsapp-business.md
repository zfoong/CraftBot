# WhatsApp Business

Connect via Meta's official WhatsApp Business Platform (Cloud API). Higher limits, production-grade, requires a Meta app and verified phone number.

For quick personal use without Meta setup, see [WhatsApp Web](whatsapp-web.md).

## Available actions

- `send_whatsapp_business_message` — send text
- `send_whatsapp_business_template` — send templated messages (required for 24-hour-window exits)
- `send_whatsapp_business_media` — send image / document / audio
- `get_whatsapp_business_messages` — list incoming messages (via webhook)

## Connect

| Command | What it does |
|---|---|
| `/whatsapp_business login <access_token> <phone_number_id>` | Connect with Meta API credentials |
| `/whatsapp_business status` | Show connection status |
| `/whatsapp_business logout` | Remove credentials |

## Prerequisites

1. [Meta for Developers](https://developers.facebook.com/) → create an app → Business type
2. Add **WhatsApp** product
3. Configure a phone number (test or verified production)
4. Copy the **temporary access token** (lasts 23 hours) — for permanent setup, generate a System User token
5. Copy the **Phone Number ID**
6. Run `/whatsapp_business login <token> <phone_number_id>`

## 24-hour message window

Meta limits free-form messages to 24 hours after the user last messaged you. Outside that window, you must use **template messages** pre-approved in Meta Business Manager. The agent uses `send_whatsapp_business_template` for those.

## Troubleshooting

**"Recipient not opted in"** — the user needs to message your business number first (or you need a template in the right category and their consent).

**"Token expired"** — temporary tokens last 23 hours. Use a System User with a permanent token for production.

**Webhook for inbound messages** — not configured by default. To receive messages, set up a webhook in Meta and point it at your CraftBot instance.

## Related

- [WhatsApp Web](whatsapp-web.md) — simpler alternative
- [Credentials](credentials.md)
- [Connections overview](index.md)
