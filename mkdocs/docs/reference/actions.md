# Actions catalogue

Every built-in action grouped by domain. For detailed schemas, inspect the source in [`app/data/action/`](../concepts/action.md) — each file is one action with its full `@action(...)` metadata.

For how actions fit the architecture, see the [Actions concept](../concepts/action.md).

## Core task management

| Action | Purpose |
|---|---|
| `task_start` | Create a new [task session](../concepts/task-session.md) (simple or complex) |
| `task_update_todos` | Add / reorder / edit todos in a complex task |
| `task_end` | Mark the task complete |
| `set_mode` | Switch task mode mid-flight (e.g. simple → complex) |
| `send_message` | Reply to the user |
| `send_message_with_attachment` | Reply with a file attached |
| `ignore` | Skip this trigger without doing anything (used in conversation mode) |
| `wait` | Sleep for N seconds before the next action |

## File operations (`file_operations`)

| Action | Purpose |
|---|---|
| `read_file` | Paginated read with offset/limit |
| `write_file` | Create/overwrite a file |
| `stream_edit` | Line-range edits |
| `stream_read` | Line-by-line read for large files |
| `grep_files` | ripgrep-style search with context |
| `find_files` | Glob-style file discovery |
| `list_folder` | Directory listing |

## Web (`web_research`)

| Action | Purpose |
|---|---|
| `web_search` | Search via Google CSE (requires `google_cse_id`) |
| `web_fetch` | HTTP GET with HTML-to-markdown conversion |
| `open_browser` | Launch a URL in the user's default browser |
| `http_request` | Arbitrary HTTP call (GET/POST/etc.) |

## Shell & code (`shell`)

| Action | Purpose |
|---|---|
| `run_shell` | Universal shell exec — see [CLI-anything](../commands/cli-anything.md) |
| `run_python` | Execute a Python snippet |

## Documents (`document_processing`)

| Action | Purpose |
|---|---|
| `read_pdf` | Extract text from a PDF |
| `create_pdf` | Generate a PDF |
| `convert_to_markdown` | Any → markdown (docx, html, rtf) |
| `describe_image` | VLM-powered image description |
| `generate_image` | Text → image via the configured image model |

## Clipboard (`clipboard`)

- `clipboard_read` · `clipboard_write`

## Memory

- `memory_search` — query the [memory](../concepts/memory.md) system

## Proactive & scheduler

| Action | Purpose |
|---|---|
| `recurring_read` | Read tasks from `PROACTIVE.md` |
| `recurring_add` | Add a new proactive task |
| `recurring_update_task` | Modify an existing task |
| `recurring_remove` | Delete a proactive task |
| `schedule_task` | Add a one-off / recurring entry to the scheduler |
| `schedule_task_toggle` | Enable / disable a scheduled task |
| `scheduled_task_list` | List all scheduled tasks |
| `remove_scheduled_task` | Remove a scheduled task |

## GUI (`gui_interaction`)

Only available when [GUI mode](../interfaces/gui-vision.md) is on:

- `mouse_click` · `mouse_move` · `mouse_drag` · `mouse_trace`
- `keyboard_type` · `keyboard_hotkey`
- `scroll`
- `open_application` · `open_browser`

## Integration actions

Dynamic — each integration contributes its own. Enabled when the integration is connected.

| Integration | Action prefix / directory |
|---|---|
| [Discord](../connections/discord.md) | `send_discord_*`, `get_discord_*`, `add_discord_*` |
| [Slack](../connections/slack.md) | `*_slack_*` |
| [Telegram](../connections/telegram-bot.md) | `*_telegram_*` |
| [Notion](../connections/notion.md) | `*_notion_*` |
| [Google Workspace](../connections/google-workspace.md) | `send_gmail`, `list_gmail`, `get_gmail`, `create_google_meet`, `check_calendar_availability`, `list_drive_files`, `create_drive_folder`, `move_drive_file` |
| [LinkedIn](../connections/linkedin.md) | `*_linkedin_*` |
| [Outlook](../connections/outlook.md) | `*_outlook_*` |
| [WhatsApp](../connections/whatsapp-web.md) | `*_whatsapp_*` |
| [GitHub](../connections/github.md) | (see `app/data/action/github/`) |
| [Jira](../connections/jira.md) | (see `app/data/action/jira/`) |
| [Twitter](../connections/twitter.md) | (see `app/data/action/twitter/`) |

## Integration management

Always available — lets the agent help users connect/disconnect services:

| Action | Purpose |
|---|---|
| `list_available_integrations` | List every integration + connection state |
| `connect_integration` | Start OAuth / token flow |
| `disconnect_integration` | Remove credentials |
| `check_integration_status` | Status of one integration |

## MCP tools

Dynamically added when MCP servers connect. Named `<server_name>:<tool_name>`. See [MCP servers](../connections/mcp.md).

## Action sets summary

| Set | Contents |
|---|---|
| `core` | Task management + send_message + integration mgmt + run_shell |
| `file_operations` | File I/O |
| `web_research` | Web search + fetch |
| `document_processing` | PDF / DOCX / image |
| `clipboard` | Clipboard read/write |
| `shell` | Shell + Python exec |
| `gui_interaction` | Mouse/keyboard/screenshot (GUI mode only) |

## Related

- [Actions concept](../concepts/action.md)
- [Skill & action selection](../concepts/skill-selection.md)
- [Custom action](../develop/custom-action.md) — build your own
- [MCP servers](../connections/mcp.md) — actions from MCP
