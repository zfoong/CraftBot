"""MCP settings management for the TUI interface."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Any

from core.logger import logger
from core.mcp.mcp_config import MCPConfig, MCPServerConfig

# Default MCP config path
MCP_CONFIG_PATH = Path("core/config/mcp_config.json")


# Common MCP server templates for easy installation
MCP_SERVER_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "filesystem": {
        "name": "filesystem",
        "description": "Read, write, and manage files and directories",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
    },
    "memory": {
        "name": "memory",
        "description": "Knowledge graph for storing and retrieving entities and relations",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"],
    },
    "fetch": {
        "name": "fetch",
        "description": "Fetch content from URLs and web pages",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-fetch"],
    },
    "github": {
        "name": "github",
        "description": "GitHub API integration for repositories, issues, and PRs",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": ""},
    },
    "postgres": {
        "name": "postgres",
        "description": "PostgreSQL database operations",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres"],
        "env": {"POSTGRES_CONNECTION_STRING": ""},
    },
    "sqlite": {
        "name": "sqlite",
        "description": "SQLite database operations",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "database.db"],
    },
    "puppeteer": {
        "name": "puppeteer",
        "description": "Browser automation and web scraping",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
    },
    "brave-search": {
        "name": "brave-search",
        "description": "Web search using Brave Search API",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env": {"BRAVE_API_KEY": ""},
    },
    "google-maps": {
        "name": "google-maps",
        "description": "Google Maps API for location services",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-google-maps"],
        "env": {"GOOGLE_MAPS_API_KEY": ""},
    },
    "slack": {
        "name": "slack",
        "description": "Slack workspace integration",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"],
        "env": {"SLACK_BOT_TOKEN": "", "SLACK_TEAM_ID": ""},
    },
}


def load_mcp_config() -> MCPConfig:
    """Load MCP configuration from file."""
    try:
        return MCPConfig.load(MCP_CONFIG_PATH)
    except Exception as e:
        logger.error(f"Failed to load MCP config: {e}")
        return MCPConfig()


def save_mcp_config(config: MCPConfig) -> bool:
    """Save MCP configuration to file."""
    try:
        config.save(MCP_CONFIG_PATH)
        logger.info(f"Saved MCP config to {MCP_CONFIG_PATH}")
        return True
    except Exception as e:
        logger.error(f"Failed to save MCP config: {e}")
        return False


def list_mcp_servers() -> List[Dict[str, Any]]:
    """Get list of configured MCP servers with their status."""
    config = load_mcp_config()
    servers = []
    for server in config.mcp_servers:
        servers.append({
            "name": server.name,
            "description": server.description,
            "enabled": server.enabled,
            "transport": server.transport,
            "command": server.command,
            "action_set": server.resolved_action_set_name,
            "env": server.env,
        })
    return servers


def get_template_env_vars(template_name: str) -> Dict[str, str]:
    """Get the environment variables needed by a template."""
    if template_name in MCP_SERVER_TEMPLATES:
        return MCP_SERVER_TEMPLATES[template_name].get("env", {})
    return {}


def get_server_env_vars(server_name: str) -> Dict[str, str]:
    """Get the environment variables for an existing server."""
    config = load_mcp_config()
    server = config.get_server_by_name(server_name)
    if server:
        return server.env
    return {}


def add_mcp_server(
    name: str,
    description: str = "",
    transport: str = "stdio",
    command: Optional[str] = None,
    args: Optional[List[str]] = None,
    url: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    enabled: bool = True,
) -> tuple[bool, str]:
    """
    Add a new MCP server configuration.

    Returns:
        Tuple of (success, message)
    """
    config = load_mcp_config()

    # Check if server already exists
    if config.get_server_by_name(name):
        return False, f"Server '{name}' already exists"

    try:
        server = MCPServerConfig(
            name=name,
            description=description,
            transport=transport,
            command=command,
            args=args or [],
            url=url,
            env=env or {},
            enabled=enabled,
        )
        config.add_server(server)
        save_mcp_config(config)
        return True, f"Added MCP server: {name}"
    except ValueError as e:
        return False, str(e)


def add_mcp_server_from_template(template_name: str, enabled: bool = True) -> tuple[bool, str]:
    """
    Add an MCP server from a predefined template.

    Returns:
        Tuple of (success, message)
    """
    if template_name not in MCP_SERVER_TEMPLATES:
        available = ", ".join(MCP_SERVER_TEMPLATES.keys())
        return False, f"Unknown template '{template_name}'. Available: {available}"

    template = MCP_SERVER_TEMPLATES[template_name]
    config = load_mcp_config()

    # Check if server already exists
    if config.get_server_by_name(template["name"]):
        return False, f"Server '{template['name']}' already exists"

    try:
        server = MCPServerConfig(
            name=template["name"],
            description=template.get("description", ""),
            transport=template.get("transport", "stdio"),
            command=template.get("command"),
            args=template.get("args", []),
            url=template.get("url"),
            env=template.get("env", {}),
            enabled=enabled,
        )
        config.add_server(server)
        save_mcp_config(config)

        # Check if any env vars need configuration
        env_vars = template.get("env", {})
        empty_vars = [k for k, v in env_vars.items() if not v]
        if empty_vars:
            return True, f"Added MCP server: {template['name']}. Note: Configure environment variables: {', '.join(empty_vars)}"
        return True, f"Added MCP server: {template['name']}"
    except ValueError as e:
        return False, str(e)


def remove_mcp_server(name: str) -> tuple[bool, str]:
    """
    Remove an MCP server configuration.

    Returns:
        Tuple of (success, message)
    """
    config = load_mcp_config()

    if not config.get_server_by_name(name):
        return False, f"Server '{name}' not found"

    config.remove_server(name)
    save_mcp_config(config)
    return True, f"Removed MCP server: {name}"


def enable_mcp_server(name: str) -> tuple[bool, str]:
    """
    Enable an MCP server.

    Returns:
        Tuple of (success, message)
    """
    config = load_mcp_config()

    if not config.get_server_by_name(name):
        return False, f"Server '{name}' not found"

    config.enable_server(name)
    save_mcp_config(config)
    return True, f"Enabled MCP server: {name}"


def disable_mcp_server(name: str) -> tuple[bool, str]:
    """
    Disable an MCP server.

    Returns:
        Tuple of (success, message)
    """
    config = load_mcp_config()

    if not config.get_server_by_name(name):
        return False, f"Server '{name}' not found"

    config.disable_server(name)
    save_mcp_config(config)
    return True, f"Disabled MCP server: {name}"


def get_available_templates() -> List[Dict[str, str]]:
    """Get list of available MCP server templates."""
    templates = []
    for name, template in MCP_SERVER_TEMPLATES.items():
        templates.append({
            "name": name,
            "description": template.get("description", ""),
        })
    return templates


def update_mcp_server_env(name: str, env_key: str, env_value: str) -> tuple[bool, str]:
    """
    Update an environment variable for an MCP server.

    Returns:
        Tuple of (success, message)
    """
    config = load_mcp_config()
    server = config.get_server_by_name(name)

    if not server:
        return False, f"Server '{name}' not found"

    server.env[env_key] = env_value
    save_mcp_config(config)
    return True, f"Updated {env_key} for server '{name}'"
