# WhatsApp Web

Connect your personal WhatsApp via the web client (Playwright-driven). No official API fees, no Meta app setup — just scan a QR code.

For the Business API with Meta app credentials, see [WhatsApp Business](whatsapp-business.md).

## Available actions

- `send_whatsapp_web_text_message` — send a text message
- `send_whatsapp_web_media_message` — send an image / file
- `get_whatsapp_chat_history` — read recent messages from a chat
- `get_whatsapp_unread_chats` — list unread chats
- `search_whatsapp_contact` — find a contact by name

## Connect

| Command | What it does |
|---|---|
| `/whatsapp login [phone_number]` | Open WhatsApp Web and show QR |
| `/whatsapp status` | Show all WhatsApp connections |
| `/whatsapp logout [id]` | Remove a connection |

## Prerequisites

- [Playwright](https://playwright.dev/) with Chromium:

    ```bash
    pip install playwright
    playwright install chromium
    ```

- The `/whatsapp login` command launches WhatsApp Web in a controlled Chromium instance and displays the QR. Scan it with your phone (WhatsApp → ⋯ → Linked devices → Link a device).

## Session persistence

The browser profile is saved in the credential store so you don't re-scan on every run. If your phone ends the linked-device session (WhatsApp does this periodically), you'll need to re-scan.

## Troubleshooting

**"Playwright not installed"** — `pip install playwright && playwright install chromium`. On Linux you may also need system libraries (`playwright install-deps`).

**QR expired** — the WhatsApp Web QR rotates every ~1 minute. If you miss the window, re-run `/whatsapp login`.

**Chromium can't launch** — headless mode is used by default. For debugging, launch with a visible window by setting `PLAYWRIGHT_HEADLESS=false`.

## Limitations

- WhatsApp Web has rate limits that kick in at moderate volume — don't spam.
- Reading messages works but doesn't mark them as read on your phone's WhatsApp unless you actually open the chat.
- Voice/video calls are not supported.

## Related

- [WhatsApp Business](whatsapp-business.md) — official API route
- [Credentials](credentials.md)
- [Connections overview](index.md)
