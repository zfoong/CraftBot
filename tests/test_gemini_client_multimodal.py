import base64
import pytest
from unittest.mock import patch, MagicMock
from agent_core.core.llm.google_gemini_client import GeminiClient

FAKE_RESPONSE = {
    "candidates": [{"content": {"parts": [{"text": "ok"}]}, "finishReason": "STOP"}],
    "usageMetadata": {"totalTokenCount": 10, "promptTokenCount": 8, "candidatesTokenCount": 2}
}

@pytest.fixture
def client():
    return GeminiClient(api_key="fake-key")

def test_single_image_produces_one_inlinedata_part(client):
    """Passing image_bytes alone → exactly 1 inlineData in parts."""
    with patch.object(client, "_post_json", return_value=FAKE_RESPONSE) as mock_post:
        client.generate_multimodal("gemini-2.0-flash", text="hi", image_bytes=b"img1")
        # mock_post.call_args.args[1] is the payload
        payload = mock_post.call_args.args[1]
        parts = payload["contents"][0]["parts"]
        inline_parts = [p for p in parts if "inlineData" in p]
        assert len(inline_parts) == 1

def test_multi_image_produces_correct_count(client):
    """Passing image_bytes_list of N images → exactly N inlineData parts."""
    with patch.object(client, "_post_json", return_value=FAKE_RESPONSE) as mock_post:
        client.generate_multimodal("gemini-2.0-flash", text="hi", image_bytes_list=[b"a", b"b", b"c"])
        payload = mock_post.call_args.args[1]
        parts = payload["contents"][0]["parts"]
        inline_parts = [p for p in parts if "inlineData" in p]
        assert len(inline_parts) == 3

def test_neither_image_raises_valueerror(client):
    """Passing neither image_bytes nor image_bytes_list → ValueError."""
    with pytest.raises(ValueError):
        client.generate_multimodal("gemini-2.0-flash", text="hi")

def test_single_image_backwards_compat_response(client):
    """Single-image call returns same response structure as before the refactor."""
    with patch.object(client, "_post_json", return_value=FAKE_RESPONSE):
        result = client.generate_multimodal("gemini-2.0-flash", text="hi", image_bytes=b"img")
        assert result["content"] == "ok"
        assert result["tokens_used"] == 10

def test_generate_multimodal_multi_image_no_longer_exists(client):
    """The old method must be gone."""
    assert not hasattr(client, "generate_multimodal_multi_image"), \
        "generate_multimodal_multi_image was not removed"
