"""Integration-specific command implementation.

All connect / disconnect / status operations go through the centralised
``integration_settings`` module so that terminal, browser, and agent
share the same logic and side-effects (e.g. platform-listener startup).
"""


from typing import List

from app.ui_layer.commands.base import Command, CommandResult
from app.external_comms.integration_settings import (
    INTEGRATION_REGISTRY,
    get_integration_info,
    get_integration_auth_type,
    connect_integration_token,
    connect_integration_oauth,
    connect_integration_interactive,
    disconnect_integration as _disconnect_integration,
)
from app.credentials.handlers import INTEGRATION_HANDLERS


class IntegrationCommand(Command):
    """Command for a specific integration."""

    def __init__(self, controller, integration_name: str) -> None:
        super().__init__(controller)
        self._integration_name = integration_name
        self._handler = INTEGRATION_HANDLERS.get(integration_name)

    @property
    def name(self) -> str:
        return f"/{self._integration_name}"

    @property
    def description(self) -> str:
        info = INTEGRATION_REGISTRY.get(self._integration_name)
        if info:
            return f"{info['name']} — {info['description']}"
        return f"Manage {self._integration_name} integration"

    @property
    def usage(self) -> str:
        return f"/{self._integration_name} <subcommand>"

    @property
    def help_text(self) -> str:
        lines = [f"Manage {self._integration_name} integration.", ""]

        if self._handler:
            if hasattr(self._handler, "get_commands"):
                commands = self._handler.get_commands()
                if commands:
                    lines.append("Commands:")
                    for cmd_name, cmd_desc in commands.items():
                        lines.append(f"  {cmd_name} - {cmd_desc}")
                    lines.append("")

        lines.append("Common commands:")
        lines.append("  connect    - Connect to integration")
        lines.append("  disconnect - Disconnect from integration")
        lines.append("  status     - Show connection status")

        return "\n".join(lines)

    async def execute(
        self,
        args: List[str],
        adapter_id: str = "",
    ) -> CommandResult:
        if self._integration_name not in INTEGRATION_REGISTRY:
            return CommandResult(
                success=False,
                message=f"Integration not available: {self._integration_name}",
            )

        if not args:
            return CommandResult(success=True, message=self.help_text)

        subcommand = args[0].lower()
        sub_args = args[1:]

        if subcommand == "status":
            return await self._show_status()
        elif subcommand == "connect":
            return await self._connect(sub_args)
        elif subcommand == "disconnect":
            return await self._disconnect()

        # Delegate handler-specific subcommands (login-qr, invite, etc.)
        if self._handler:
            try:
                success, message = await self._handler.handle(subcommand, sub_args)
                return CommandResult(success=success, message=message)
            except Exception as e:
                return CommandResult(success=False, message=f"Command error: {e}")

        return CommandResult(
            success=False,
            message=f"Unknown command: {subcommand}\nUse /help {self._integration_name} for usage.",
        )

    async def _show_status(self) -> CommandResult:
        """Show integration status via the centralised integration_settings module."""
        try:
            info = get_integration_info(self._integration_name)
            if not info:
                return CommandResult(success=False, message="Integration not found.")

            lines = [f"{info['name']} integration status:", ""]
            lines.append(f"  Connected: {'Yes' if info['connected'] else 'No'}")

            for account in info.get("accounts", []):
                display = account.get("display", "")
                acct_id = account.get("id", "")
                if display and acct_id and display != acct_id:
                    lines.append(f"  Account: {display} ({acct_id})")
                else:
                    lines.append(f"  Account: {display or acct_id}")

            return CommandResult(success=True, message="\n".join(lines))
        except Exception as e:
            return CommandResult(success=False, message=f"Failed to get status: {e}")

    async def _connect(self, args: List[str]) -> CommandResult:
        """Connect via the centralised integration_settings module.

        Determines the correct auth flow (token / oauth / interactive)
        based on the integration's auth_type and the arguments provided.
        """
        try:
            auth_type = get_integration_auth_type(self._integration_name)
            info = INTEGRATION_REGISTRY.get(self._integration_name, {})
            fields = info.get("fields", [])

            # Token-based: args should provide credential values in field order
            if auth_type in ("token", "both", "token_with_interactive") and (args or fields):
                credentials: dict[str, str] = {}
                for i, field in enumerate(fields):
                    if i < len(args):
                        credentials[field["key"]] = args[i]

                if credentials:
                    success, message = await connect_integration_token(
                        self._integration_name, credentials
                    )
                    return CommandResult(success=success, message=message)

                # No args provided — show required fields
                if fields:
                    field_list = ", ".join(f["label"] for f in fields)
                    return CommandResult(
                        success=False,
                        message=f"Usage: /{self._integration_name} connect <{field_list}>",
                    )

            # OAuth-based
            if auth_type in ("oauth", "both"):
                success, message = await connect_integration_oauth(self._integration_name)
                return CommandResult(success=success, message=message)

            # Interactive (QR code, etc.)
            if auth_type in ("interactive", "token_with_interactive"):
                success, message = await connect_integration_interactive(self._integration_name)
                return CommandResult(success=success, message=message)

            return CommandResult(
                success=False,
                message=f"Unsupported auth type '{auth_type}' for {self._integration_name}.",
            )
        except Exception as e:
            return CommandResult(success=False, message=f"Connection failed: {e}")

    async def _disconnect(self) -> CommandResult:
        """Disconnect via the centralised integration_settings module."""
        try:
            success, message = await _disconnect_integration(self._integration_name)
            return CommandResult(success=success, message=message)
        except Exception as e:
            return CommandResult(success=False, message=f"Disconnect failed: {e}")
