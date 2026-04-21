"""Diagnostic environment for the "trace mouse" action."""

from diagnostic.framework import ActionTestCase


def get_test_case() -> ActionTestCase:
    return ActionTestCase(
        name="trace mouse",
        base_input={},
        skip_reason=(
            "Requires active OS-level mouse tracking via pyautogui, unavailable in diagnostics."
        ),
    )
