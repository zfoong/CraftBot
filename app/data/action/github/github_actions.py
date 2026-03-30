from agent_core import action


_NO_CRED_MSG = "No GitHub credential. Use /github login first."


# ------------------------------------------------------------------
# Issues
# ------------------------------------------------------------------

@action(
    name="list_github_issues",
    description="List issues for a GitHub repository.",
    action_sets=["github"],
    input_schema={
        "repo": {"type": "string", "description": "Repository in owner/repo format.", "example": "octocat/hello-world"},
        "state": {"type": "string", "description": "Filter by state: open, closed, all.", "example": "open"},
        "per_page": {"type": "integer", "description": "Max results.", "example": 30},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
async def list_github_issues(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.github import GitHubClient
        client = GitHubClient()
        if not client.has_credentials():
            return {"status": "error", "message": _NO_CRED_MSG}
        result = await client.list_issues(
            input_data["repo"],
            state=input_data.get("state", "open"),
            per_page=input_data.get("per_page", 30),
        )
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@action(
    name="get_github_issue",
    description="Get details of a specific GitHub issue or PR by number.",
    action_sets=["github"],
    input_schema={
        "repo": {"type": "string", "description": "Repository in owner/repo format.", "example": "octocat/hello-world"},
        "number": {"type": "integer", "description": "Issue or PR number.", "example": 1},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
async def get_github_issue(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.github import GitHubClient
        client = GitHubClient()
        if not client.has_credentials():
            return {"status": "error", "message": _NO_CRED_MSG}
        result = await client.get_issue(input_data["repo"], input_data["number"])
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@action(
    name="create_github_issue",
    description="Create a new issue in a GitHub repository.",
    action_sets=["github"],
    input_schema={
        "repo": {"type": "string", "description": "Repository in owner/repo format.", "example": "octocat/hello-world"},
        "title": {"type": "string", "description": "Issue title.", "example": "Bug: login fails"},
        "body": {"type": "string", "description": "Issue body (markdown).", "example": ""},
        "labels": {"type": "string", "description": "Comma-separated labels.", "example": "bug,urgent"},
        "assignees": {"type": "string", "description": "Comma-separated GitHub usernames to assign.", "example": ""},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
    parallelizable=False,
)
async def create_github_issue(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.github import GitHubClient
        client = GitHubClient()
        if not client.has_credentials():
            return {"status": "error", "message": _NO_CRED_MSG}
        labels_str = input_data.get("labels", "")
        labels = [l.strip() for l in labels_str.split(",") if l.strip()] if labels_str else None
        assignees_str = input_data.get("assignees", "")
        assignees = [a.strip() for a in assignees_str.split(",") if a.strip()] if assignees_str else None
        result = await client.create_issue(
            input_data["repo"],
            input_data["title"],
            body=input_data.get("body", ""),
            labels=labels,
            assignees=assignees,
        )
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@action(
    name="close_github_issue",
    description="Close a GitHub issue.",
    action_sets=["github"],
    input_schema={
        "repo": {"type": "string", "description": "Repository in owner/repo format.", "example": "octocat/hello-world"},
        "number": {"type": "integer", "description": "Issue number.", "example": 1},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
    parallelizable=False,
)
async def close_github_issue(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.github import GitHubClient
        client = GitHubClient()
        if not client.has_credentials():
            return {"status": "error", "message": _NO_CRED_MSG}
        result = await client.close_issue(input_data["repo"], input_data["number"])
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ------------------------------------------------------------------
# Comments
# ------------------------------------------------------------------

@action(
    name="add_github_comment",
    description="Add a comment to a GitHub issue or PR.",
    action_sets=["github"],
    input_schema={
        "repo": {"type": "string", "description": "Repository in owner/repo format.", "example": "octocat/hello-world"},
        "number": {"type": "integer", "description": "Issue or PR number.", "example": 1},
        "body": {"type": "string", "description": "Comment body (markdown).", "example": "Fixed in commit abc123."},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
    parallelizable=False,
)
async def add_github_comment(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.github import GitHubClient
        client = GitHubClient()
        if not client.has_credentials():
            return {"status": "error", "message": _NO_CRED_MSG}
        result = await client.create_comment(input_data["repo"], input_data["number"], input_data["body"])
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ------------------------------------------------------------------
# Labels
# ------------------------------------------------------------------

@action(
    name="add_github_labels",
    description="Add labels to a GitHub issue or PR.",
    action_sets=["github"],
    input_schema={
        "repo": {"type": "string", "description": "Repository in owner/repo format.", "example": "octocat/hello-world"},
        "number": {"type": "integer", "description": "Issue or PR number.", "example": 1},
        "labels": {"type": "string", "description": "Comma-separated labels to add.", "example": "bug,priority-high"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
    parallelizable=False,
)
async def add_github_labels(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.github import GitHubClient
        client = GitHubClient()
        if not client.has_credentials():
            return {"status": "error", "message": _NO_CRED_MSG}
        labels = [l.strip() for l in input_data["labels"].split(",") if l.strip()]
        if not labels:
            return {"status": "error", "message": "No labels provided."}
        result = await client.add_labels(input_data["repo"], input_data["number"], labels)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ------------------------------------------------------------------
# Pull Requests
# ------------------------------------------------------------------

@action(
    name="list_github_prs",
    description="List pull requests for a GitHub repository.",
    action_sets=["github"],
    input_schema={
        "repo": {"type": "string", "description": "Repository in owner/repo format.", "example": "octocat/hello-world"},
        "state": {"type": "string", "description": "Filter: open, closed, all.", "example": "open"},
        "per_page": {"type": "integer", "description": "Max results.", "example": 30},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
async def list_github_prs(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.github import GitHubClient
        client = GitHubClient()
        if not client.has_credentials():
            return {"status": "error", "message": _NO_CRED_MSG}
        result = await client.list_pull_requests(
            input_data["repo"],
            state=input_data.get("state", "open"),
            per_page=input_data.get("per_page", 30),
        )
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ------------------------------------------------------------------
# Repos & Search
# ------------------------------------------------------------------

@action(
    name="list_github_repos",
    description="List repositories for the authenticated GitHub user.",
    action_sets=["github"],
    input_schema={
        "per_page": {"type": "integer", "description": "Max repos to return.", "example": 30},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
async def list_github_repos(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.github import GitHubClient
        client = GitHubClient()
        if not client.has_credentials():
            return {"status": "error", "message": _NO_CRED_MSG}
        result = await client.list_repos(per_page=input_data.get("per_page", 30))
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@action(
    name="search_github_issues",
    description="Search GitHub issues and PRs using GitHub search syntax.",
    action_sets=["github"],
    input_schema={
        "query": {"type": "string", "description": "GitHub search query (e.g. 'repo:owner/repo is:open label:bug').", "example": "repo:octocat/hello-world is:open"},
        "per_page": {"type": "integer", "description": "Max results.", "example": 20},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
async def search_github_issues(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.github import GitHubClient
        client = GitHubClient()
        if not client.has_credentials():
            return {"status": "error", "message": _NO_CRED_MSG}
        result = await client.search_issues(input_data["query"], per_page=input_data.get("per_page", 20))
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ------------------------------------------------------------------
# Watch Settings
# ------------------------------------------------------------------

@action(
    name="set_github_watch_tag",
    description="Set a mention tag for the GitHub listener. Only comments containing this tag (e.g. '@craftbot') will trigger events.",
    action_sets=["github"],
    input_schema={
        "tag": {"type": "string", "description": "Tag to watch for. Empty = disabled.", "example": "@craftbot"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
    parallelizable=False,
)
def set_github_watch_tag(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.github import GitHubClient
        client = GitHubClient()
        if not client.has_credentials():
            return {"status": "error", "message": _NO_CRED_MSG}
        tag = input_data.get("tag", "").strip()
        client.set_watch_tag(tag)
        if tag:
            return {"status": "success", "message": f"Now only triggering on comments containing '{tag}'."}
        return {"status": "success", "message": "Watch tag disabled. Triggering on all notifications."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@action(
    name="set_github_watch_repos",
    description="Set which repositories the GitHub listener watches. Only events from these repos will trigger.",
    action_sets=["github"],
    input_schema={
        "repos": {"type": "string", "description": "Comma-separated repos in owner/repo format. Empty = all repos.", "example": "octocat/hello-world,myorg/myrepo"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
    parallelizable=False,
)
def set_github_watch_repos(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.github import GitHubClient
        client = GitHubClient()
        if not client.has_credentials():
            return {"status": "error", "message": _NO_CRED_MSG}
        repos_str = input_data.get("repos", "")
        repos = [r.strip() for r in repos_str.split(",") if r.strip()] if repos_str else []
        client.set_watch_repos(repos)
        if repos:
            return {"status": "success", "message": f"Watching repos: {', '.join(repos)}"}
        return {"status": "success", "message": "Watching all repos."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
