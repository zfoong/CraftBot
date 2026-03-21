# -*- coding: utf-8 -*-
"""
Protocol definition for DatabaseInterface.

This module defines the DatabaseInterfaceProtocol that specifies the
interface for persistence operations. The protocol enables structural
typing for database operations across different agent implementations.
"""

from typing import Any, Dict, List, Optional, Protocol


class DatabaseInterfaceProtocol(Protocol):
    """
    Protocol for database persistence operations.

    This defines the minimal interface that a database implementation
    must provide for use by shared agent code.
    """

    def list_actions(
        self,
        *,
        default: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return stored actions optionally filtered by the default flag.

        Args:
            default: When provided, only return actions whose default field
                matches the boolean value.

        Returns:
            List of action dictionaries that satisfy the filter.
        """
        ...

    def get_action(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a stored action by name.

        Args:
            name: The human-readable name used to identify the action.

        Returns:
            The action dictionary when found, otherwise None.
        """
        ...

    def store_action(self, action_dict: Dict[str, Any]) -> None:
        """
        Persist an action definition to disk.

        Args:
            action_dict: Action payload to store, expected to include a name
                field used for the filename.
        """
        ...

    def delete_action(self, name: str) -> None:
        """
        Remove an action definition from disk.

        Args:
            name: Name of the action to delete.
        """
        ...

    def set_agent_info(self, info: Dict[str, Any], key: str = "singleton") -> None:
        """
        Persist arbitrary agent configuration under the provided key.

        Args:
            info: Mapping of configuration fields to store.
            key: Logical namespace under which the configuration is saved.
        """
        ...

    def get_agent_info(self, key: str = "singleton") -> Optional[Dict[str, Any]]:
        """
        Load persisted agent configuration for the given key.

        Args:
            key: Namespace key used when persisting the configuration.

        Returns:
            A configuration dictionary when present, otherwise None.
        """
        ...
