"""Integration files. Every .py here is autoloaded at startup.

To add a new integration, drop a single file with:
  - a credential dataclass
  - an IntegrationSpec
  - an IntegrationHandler subclass decorated with @register_handler
  - a BasePlatformClient subclass decorated with @register_client

See github.py for the canonical shape.
"""
