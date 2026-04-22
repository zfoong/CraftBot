# Notion

Search pages and databases, create pages, query databases, update page properties.

## Available actions

- `search_notion` — full-text search across your workspace
- `get_notion_page` — read a page with blocks
- `create_notion_page` — create in a parent page or database
- `query_notion_database` — filter a database with Notion's query syntax
- `update_notion_page` — update properties or add blocks

## Connect

| Command | What it does |
|---|---|
| `/notion invite` | Authorize the CraftOS integration (OAuth) |
| `/notion login <integration_token>` | Use your own Notion integration |
| `/notion status` | Show connected workspaces |
| `/notion logout [workspace_id]` | Remove a workspace |

## Prerequisites

=== "Invite (easy)"
    Requires `NOTION_SHARED_CLIENT_ID` and `NOTION_SHARED_CLIENT_SECRET`. Release builds have these embedded.

=== "Login (your own integration)"
    1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
    2. "New integration" → internal or public
    3. Copy the Integration Secret
    4. **Share specific pages with the integration** in Notion (integrations don't see pages by default)
    5. Run `/notion login <secret>`

## Troubleshooting

**"object_not_found"** — the integration doesn't have access to that page. In Notion, open the page → "Add connections" → select your integration.

**Database queries return empty** — check the filter syntax. Notion uses its own filter object format (not SQL). See the [Notion API docs](https://developers.notion.com/reference/post-database-query).

## Related

- [Credentials](credentials.md)
- [Connections overview](index.md)
