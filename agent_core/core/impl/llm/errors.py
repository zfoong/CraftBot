# -*- coding: utf-8 -*-
"""
LLM Error Classification Module.

Provides user-friendly error messages for LLM-related failures.
Technical details are preserved in logs while users see clear,
actionable messages.
"""

from __future__ import annotations


def classify_llm_error(error: Exception) -> str:
    """Classify an LLM error and return a user-friendly message.

    Analyzes the error to determine the root cause and returns
    an appropriate message for end users. Technical details
    should be logged separately.

    Args:
        error: The exception from the LLM call.

    Returns:
        A user-friendly error message.
    """
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()

    # Authentication issues (API key wrong/missing/expired)
    if _is_auth_error(error_str, error_type):
        return "Unable to connect to AI service. Please check your API key in Settings."

    # Model not supported or not found
    if _is_model_error(error_str, error_type):
        return "The selected AI model is not available. Please check your model settings."

    # Bad configuration (invalid parameters, unsupported features)
    if _is_config_error(error_str, error_type):
        return "AI service configuration error. The selected model may not support required features."

    # Rate limiting
    if _is_rate_limit_error(error_str, error_type):
        return "AI service is rate-limited. Please wait a moment and try again."

    # Service unavailable (server errors, maintenance)
    if _is_service_error(error_str, error_type):
        return "AI service is temporarily unavailable. Please try again later."

    # Connection/network issues
    if _is_connection_error(error_str, error_type):
        return "Unable to reach AI service. Please check your internet connection."

    # Generic fallback
    return "An error occurred with the AI service. Please check your LLM configuration."


def _is_auth_error(error_str: str, error_type: str) -> bool:
    """Check if error is authentication-related."""
    auth_patterns = [
        "401",
        "403",
        "unauthorized",
        "authentication",
        "invalid_api_key",
        "invalid api key",
        "api key",
        "apikey",
        "credential",
        "permission denied",
        "access denied",
    ]
    auth_types = ["authenticationerror", "permissionerror"]
    return any(p in error_str for p in auth_patterns) or error_type in auth_types


def _is_model_error(error_str: str, error_type: str) -> bool:
    """Check if error is model-related."""
    model_patterns = [
        "model_not_found",
        "model not found",
        "does not exist",
        "invalid model",
        "unknown model",
        "no such model",
        "model is not available",
    ]
    # 404 specifically for model endpoints
    if "404" in error_str and "model" in error_str:
        return True
    return any(p in error_str for p in model_patterns)


def _is_config_error(error_str: str, error_type: str) -> bool:
    """Check if error is configuration-related."""
    config_patterns = [
        "400",
        "bad request",
        "invalid_request",
        "invalid request",
        "invalid parameter",
        "json_schema",
        "output_config",
        "not supported",
        "unsupported",
    ]
    config_types = ["badrequesterror", "validationerror"]
    return any(p in error_str for p in config_patterns) or error_type in config_types


def _is_rate_limit_error(error_str: str, error_type: str) -> bool:
    """Check if error is rate-limit-related."""
    rate_patterns = [
        "429",
        "rate_limit",
        "rate limit",
        "too many requests",
        "quota exceeded",
        "throttl",
    ]
    rate_types = ["ratelimiterror"]
    return any(p in error_str for p in rate_patterns) or error_type in rate_types


def _is_service_error(error_str: str, error_type: str) -> bool:
    """Check if error is service-availability-related."""
    service_patterns = [
        "500",
        "502",
        "503",
        "504",
        "internal server error",
        "service unavailable",
        "bad gateway",
        "gateway timeout",
        "overloaded",
        "maintenance",
    ]
    service_types = ["internalservererror", "serviceunavailableerror"]
    return any(p in error_str for p in service_patterns) or error_type in service_types


def _is_connection_error(error_str: str, error_type: str) -> bool:
    """Check if error is connection-related."""
    conn_patterns = [
        "timeout",
        "timed out",
        "connection refused",
        "connection error",
        "connection reset",
        "network",
        "unreachable",
        "dns",
        "resolve",
    ]
    conn_types = ["connectionerror", "timeouterror", "connecttimeout"]
    return any(p in error_str for p in conn_patterns) or error_type in conn_types
