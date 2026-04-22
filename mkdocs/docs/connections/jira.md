# Jira

Interact with Jira Cloud — issues, projects, boards, sprints, transitions.

## Available actions

- List / search issues (JQL supported)
- Get issue details (description, comments, links)
- Create issue
- Transition issue (To Do → In Progress → Done)
- Add comment
- Assign issue

See [Actions catalogue](../reference/actions.md) for exact names and schemas.

## Connect

| Command | What it does |
|---|---|
| `/jira login <email> <api_token> <workspace_url>` | Connect with API token |
| `/jira status` | Show connected workspaces |
| `/jira logout [workspace]` | Remove workspace |

## Prerequisites

1. [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens) → Create API token
2. Note your Jira URL (`https://<your-workspace>.atlassian.net`)
3. Run `/jira login <your-email> <api-token> <your-workspace>.atlassian.net`

## JQL quick reference

Most search actions accept JQL:

```
project = PROJ AND status = "In Progress" AND assignee = currentUser()
```

The agent can also be given natural-language queries — it'll translate them to JQL internally via the action's description.

## Troubleshooting

**401 Unauthorized** — the API token is for your *own* user; it can't impersonate. Make sure the email matches the account that generated the token.

**"Issue does not exist"** on a known issue — the user token may not have "Browse projects" permission for that project. Ask a project admin.

## Related

- [GitHub](github.md) — dev workflow alternative
- [Credentials](credentials.md)
- [Connections overview](index.md)
