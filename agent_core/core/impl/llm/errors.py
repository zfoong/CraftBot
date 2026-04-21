# -*- coding: utf-8 -*-
"""
LLM Error Classification Module.

Provides user-friendly error messages for LLM-related failures.
Uses proper exception types and HTTP status codes - no string pattern matching.
"""



from typing import Optional

# Import provider exception types
try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import requests
except ImportError:
    requests = None


# User-friendly messages
MSG_AUTH = "Unable to connect to AI service. Please check your API key in Settings."
MSG_CONSECUTIVE_FAILURE = (
    "LLM calls have failed {count} consecutive times. "
    "Task aborted to prevent infinite retries. Please check your LLM configuration."
)


class LLMConsecutiveFailureError(Exception):
    """Raised when LLM calls fail too many times consecutively.

    This exception signals that the task should be aborted to prevent
    infinite retry loops that flood logs and waste resources.
    """

    def __init__(self, failure_count: int, last_error: Optional[Exception] = None):
        self.failure_count = failure_count
        self.last_error = last_error
        message = MSG_CONSECUTIVE_FAILURE.format(count=failure_count)
        if last_error:
            message += f" Last error: {last_error}"
        super().__init__(message)
MSG_MODEL = "The selected AI model is not available. Please check your model settings."
MSG_CONFIG = "AI service configuration error. The selected model may not support required features."
MSG_RATE_LIMIT = "AI service is rate-limited. Please wait a moment and try again."
MSG_SERVICE = "AI service is temporarily unavailable. Please try again later."
MSG_CONNECTION = "Unable to reach AI service. Please check your internet connection."
MSG_GENERIC = "An error occurred with the AI service. Please check your LLM configuration."


def classify_llm_error(error: Exception) -> str:
    """Classify an LLM error and return a user-friendly message.

    Uses exception types and HTTP status codes for classification.

    Args:
        error: The exception from the LLM call.

    Returns:
        A user-friendly error message.
    """
    # Check OpenAI exceptions
    if openai is not None:
        msg = _classify_openai_error(error)
        if msg:
            return msg

    # Check Anthropic exceptions
    if anthropic is not None:
        msg = _classify_anthropic_error(error)
        if msg:
            return msg

    # Check requests exceptions (BytePlus, remote/Ollama)
    if requests is not None:
        msg = _classify_requests_error(error)
        if msg:
            return msg

    # Check for status_code attribute on any exception
    status_code = _get_status_code(error)
    if status_code:
        return _message_from_status_code(status_code)

    # Generic fallback
    return MSG_GENERIC


def _classify_openai_error(error: Exception) -> Optional[str]:
    """Classify OpenAI SDK exceptions."""
    if isinstance(error, openai.AuthenticationError):
        return MSG_AUTH
    if isinstance(error, openai.PermissionDeniedError):
        return MSG_AUTH
    if isinstance(error, openai.NotFoundError):
        return MSG_MODEL
    if isinstance(error, openai.BadRequestError):
        return MSG_CONFIG
    if isinstance(error, openai.RateLimitError):
        return MSG_RATE_LIMIT
    if isinstance(error, openai.InternalServerError):
        return MSG_SERVICE
    if isinstance(error, openai.APIConnectionError):
        return MSG_CONNECTION
    if isinstance(error, openai.APITimeoutError):
        return MSG_CONNECTION
    if isinstance(error, openai.APIStatusError):
        return _message_from_status_code(error.status_code)
    return None


def _classify_anthropic_error(error: Exception) -> Optional[str]:
    """Classify Anthropic SDK exceptions."""
    if isinstance(error, anthropic.AuthenticationError):
        return MSG_AUTH
    if isinstance(error, anthropic.PermissionDeniedError):
        return MSG_AUTH
    if isinstance(error, anthropic.NotFoundError):
        return MSG_MODEL
    if isinstance(error, anthropic.BadRequestError):
        return MSG_CONFIG
    if isinstance(error, anthropic.RateLimitError):
        return MSG_RATE_LIMIT
    if isinstance(error, anthropic.InternalServerError):
        return MSG_SERVICE
    if isinstance(error, anthropic.APIConnectionError):
        return MSG_CONNECTION
    if isinstance(error, anthropic.APITimeoutError):
        return MSG_CONNECTION
    if isinstance(error, anthropic.APIStatusError):
        return _message_from_status_code(error.status_code)
    return None


def _classify_requests_error(error: Exception) -> Optional[str]:
    """Classify requests library exceptions (for BytePlus/Ollama)."""
    if isinstance(error, requests.exceptions.HTTPError):
        if error.response is not None:
            return _message_from_status_code(error.response.status_code)
        return MSG_SERVICE
    if isinstance(error, requests.exceptions.ConnectionError):
        return MSG_CONNECTION
    if isinstance(error, requests.exceptions.Timeout):
        return MSG_CONNECTION
    return None


def _get_status_code(error: Exception) -> Optional[int]:
    """Extract HTTP status code from exception if available."""
    # Check for status_code attribute
    if hasattr(error, "status_code"):
        return getattr(error, "status_code", None)
    # Check for response.status_code (requests-style)
    if hasattr(error, "response") and hasattr(error.response, "status_code"):
        return error.response.status_code
    return None


def _message_from_status_code(status_code: int) -> str:
    """Map HTTP status code to user-friendly message."""
    if status_code == 401 or status_code == 403:
        return MSG_AUTH
    if status_code == 404:
        return MSG_MODEL
    if status_code == 400:
        return MSG_CONFIG
    if status_code == 429:
        return MSG_RATE_LIMIT
    if 500 <= status_code < 600:
        return MSG_SERVICE
    return MSG_GENERIC
