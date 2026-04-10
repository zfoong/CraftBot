# -*- coding: utf-8 -*-
"""
Token counting utilities using tiktoken.

Provides a cached tokenizer and token counting functions used
across agent_core and app layers.
"""

import tiktoken

# Ensure tiktoken extension encodings (cl100k_base, etc.) are registered.
# Required for tiktoken >= 0.12 and PyInstaller frozen builds.
try:
    import tiktoken_ext.openai_public  # noqa: F401
except ImportError:
    pass

_tokenizer = None


def _get_tokenizer():
    """Get or create the tiktoken tokenizer (cached for performance)."""
    global _tokenizer
    if _tokenizer is None:
        try:
            _tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # Fallback: use o200k_base if cl100k_base is unavailable
            _tokenizer = tiktoken.get_encoding("o200k_base")
    return _tokenizer


def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string using tiktoken."""
    if not text:
        return 0
    return len(_get_tokenizer().encode(text))
