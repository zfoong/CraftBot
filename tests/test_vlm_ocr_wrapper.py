import os
import pytest
import tempfile
from unittest.mock import MagicMock, patch
from agent_core.core.impl.vlm.interface import VLMInterface

def _make_vlm():
    with patch("agent_core.core.impl.vlm.interface.VLMInterface.__init__", return_value=None):
        vlm = VLMInterface.__new__(VLMInterface)
        vlm.provider = "openai"
        vlm.model = "gpt-4o"
        vlm.temperature = 0.5
        vlm._get_token_count = lambda: 0
        vlm._set_token_count = lambda x: None
        vlm._report_usage = None
        vlm._CODE_BLOCK_RE = VLMInterface._CODE_BLOCK_RE
        return vlm

def test_ocr_calls_describe_image_bytes_with_json_mode_false(tmp_path):
    """describe_image_ocr must delegate to describe_image_bytes with json_mode=False."""
    img_file = tmp_path / "test.png"
    img_file.write_bytes(b"fakeimgdata")
    vlm = _make_vlm()
    vlm.describe_image_bytes = MagicMock(return_value="extracted text")
    vlm.describe_image_ocr(str(img_file))
    call_kwargs = vlm.describe_image_bytes.call_args.kwargs
    assert call_kwargs.get("json_mode") == False, \
        "describe_image_ocr must pass json_mode=False"

def test_ocr_system_prompt_is_ocr_focused(tmp_path):
    """The system prompt passed by OCR must mention OCR/extraction, not description."""
    img_file = tmp_path / "test.png"
    img_file.write_bytes(b"fakeimgdata")
    vlm = _make_vlm()
    vlm.describe_image_bytes = MagicMock(return_value="text")
    vlm.describe_image_ocr(str(img_file))
    sys_prompt = vlm.describe_image_bytes.call_args.kwargs.get("system_prompt", "")
    assert "OCR" in sys_prompt or "extract" in sys_prompt.lower()

def test_ocr_no_provider_routing_in_method():
    """describe_image_ocr source must not contain a provider routing switch."""
    import inspect
    src = inspect.getsource(VLMInterface.describe_image_ocr)
    assert "self.provider" not in src, \
        "describe_image_ocr still contains provider routing — refactor incomplete"
    assert "elif self.provider ==" not in src, \
        "describe_image_ocr still contains provider routing switch"

def test_ocr_raises_on_missing_file():
    vlm = _make_vlm()
    with pytest.raises(FileNotFoundError):
        vlm.describe_image_ocr("/nonexistent/path/image.png")
