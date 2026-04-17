import pytest
from unittest.mock import MagicMock, patch
from agent_core.core.impl.vlm.interface import VLMInterface

PLAIN_RESPONSE = {"content": "raw text output", "tokens_used": 5}

def _make_vlm(provider="openai"):
    """Create a VLMInterface with mocked internals."""
    with patch("agent_core.core.impl.vlm.interface.VLMInterface.__init__", return_value=None):
        vlm = VLMInterface.__new__(VLMInterface)
        vlm.provider = provider
        vlm.model = "gpt-4o"
        vlm.temperature = 0.5
        vlm._get_token_count = lambda: 0
        vlm._set_token_count = lambda x: None
        vlm._report_usage = None
        vlm._CODE_BLOCK_RE = VLMInterface._CODE_BLOCK_RE
        return vlm

def test_openai_json_mode_true_uses_json_method():
    """describe_image_bytes with json_mode=True (default) → _openai_describe_bytes."""
    vlm = _make_vlm("openai")
    vlm._openai_describe_bytes = MagicMock(return_value=PLAIN_RESPONSE)
    vlm._openai_describe_bytes_plain = MagicMock(return_value=PLAIN_RESPONSE)
    vlm.describe_image_bytes(b"img", json_mode=True)
    vlm._openai_describe_bytes.assert_called_once()
    vlm._openai_describe_bytes_plain.assert_not_called()

def test_openai_json_mode_false_uses_plain_method():
    """describe_image_bytes with json_mode=False → _openai_describe_bytes_plain."""
    vlm = _make_vlm("openai")
    vlm._openai_describe_bytes = MagicMock(return_value=PLAIN_RESPONSE)
    vlm._openai_describe_bytes_plain = MagicMock(return_value=PLAIN_RESPONSE)
    vlm.describe_image_bytes(b"img", json_mode=False)
    vlm._openai_describe_bytes_plain.assert_called_once()
    vlm._openai_describe_bytes.assert_not_called()

def test_default_json_mode_is_true():
    """Calling describe_image_bytes without json_mode defaults to True (no regression)."""
    vlm = _make_vlm("openai")
    vlm._openai_describe_bytes = MagicMock(return_value=PLAIN_RESPONSE)
    vlm._openai_describe_bytes_plain = MagicMock(return_value=PLAIN_RESPONSE)
    vlm.describe_image_bytes(b"img")  # no json_mode arg
    vlm._openai_describe_bytes.assert_called_once()

def test_gemini_unaffected_by_json_mode():
    """Gemini always uses _gemini_describe_bytes regardless of json_mode flag."""
    vlm = _make_vlm("gemini")
    vlm._gemini_describe_bytes = MagicMock(return_value=PLAIN_RESPONSE)
    vlm.describe_image_bytes(b"img", json_mode=False)
    vlm._gemini_describe_bytes.assert_called_once()
    vlm.describe_image_bytes(b"img", json_mode=True)
    assert vlm._gemini_describe_bytes.call_count == 2
