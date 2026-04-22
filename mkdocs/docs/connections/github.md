# GitHub

Interact with GitHub repositories — issues, pull requests, files, and workflows.

## Available actions

Typical GitHub operations (exact names may vary — see [Actions catalogue](../reference/actions.md)):

- List / read / create / close / comment on issues
- List / read / create / review / merge pull requests
- Read / write files in a branch
- Search code / issues / commits
- Trigger / view workflow runs

## Connect

| Command | What it does |
|---|---|
| `/github login <personal_access_token>` | Connect with a PAT |
| `/github status` | Show connected accounts |
| `/github logout` | Remove credentials |

## Prerequisites

1. [github.com/settings/tokens](https://github.com/settings/tokens) → Generate new token (classic or fine-grained)
2. For **classic**: scopes `repo`, `workflow`, `read:org`, `read:user`
3. For **fine-grained**: select the repos you want the agent to access, enable Contents R/W, Issues R/W, PRs R/W, Actions read
4. Run `/github login <token>`

## Token tips

- **Never commit a PAT.** Use `.env` or the credential store.
- **Fine-grained tokens** are strongly preferred — they scope to specific repos and expire.
- For org access, the org must allow fine-grained tokens (Settings → Developer settings).

## Troubleshooting

**"Bad credentials"** — token is expired or revoked. Regenerate on GitHub and `/github login <new>`.

**"Resource not accessible by integration"** — fine-grained token lacks the needed permission. Regenerate with the right scope.

**Rate limited** — GitHub allows 5000 authenticated requests/hour per user. High-volume tasks may hit the limit; back off or batch.

## Related

- [Jira](jira.md) — issue tracker alternative
- [Credentials](credentials.md)
- [Connections overview](index.md)
