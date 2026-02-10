"""
Stub credential client for local-only mode.

In CraftOS backend, this module provides a CredentialClient that fetches
credentials from the backend API. In WhiteCollarAgent (local TUI), we use
local file storage only, so this module returns None.
"""


class CredentialClient:
    """Placeholder credential client class for type checking."""
    pass


def get_credential_client():
    """Return None - local mode uses CredentialsStore (file-based) instead."""
    return None
