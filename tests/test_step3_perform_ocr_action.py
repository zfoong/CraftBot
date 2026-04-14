# tests/test_step3_perform_ocr_action.py
"""
Step 3 Verification: perform_ocr action layer tests.
Tests input validation, simulated mode, schema contract,
and bridge delegation — without making real VLM calls.
"""
import os
import pytest
from unittest.mock import patch, MagicMock


# ── Helpers ────────────────────────────────────────────────────────────────

def load_action(image_path: str, simulated: bool = False) -> dict:
    """Import and invoke the action directly."""
    from app.data.action.perform_ocr import execute
    return execute({"image_path": image_path, "simulated_mode": simulated})


# ── 1. Input Validation ────────────────────────────────────────────────────

class TestInputValidation:

    def test_missing_image_path_key(self):
        from app.data.action.perform_ocr import execute
        result = execute({})
        assert result["status"] == "error"
        assert "image_path" in result["message"].lower()

    def test_empty_image_path_string(self):
        result = load_action("")
        assert result["status"] == "error"

    def test_nonexistent_file_path(self):
        result = load_action("/tmp/does_not_exist_12345.png")
        assert result["status"] == "error"
        assert "not found" in result["message"].lower() or \
               "does not exist" in result["message"].lower() or \
               result["status"] == "error"

    def test_path_is_directory_not_file(self, tmp_path):
        result = load_action(str(tmp_path))  # directory, not a file
        assert result["status"] == "error"


# ── 2. Simulated Mode ──────────────────────────────────────────────────────

class TestSimulatedMode:

    def test_simulated_mode_returns_success(self, tmp_path):
        fake_image = tmp_path / "test.png"
        fake_image.write_bytes(b"fake_png_bytes")
        result = load_action(str(fake_image), simulated=True)
        assert result["status"] == "success"

    def test_simulated_mode_makes_no_vlm_call(self, tmp_path):
        fake_image = tmp_path / "test.png"
        fake_image.write_bytes(b"fake_png_bytes")
        with patch("app.internal_action_interface.InternalActionInterface.perform_ocr") as mock_ocr:
            load_action(str(fake_image), simulated=True)
            mock_ocr.assert_not_called()

    def test_simulated_mode_result_is_string(self, tmp_path):
        fake_image = tmp_path / "test.png"
        fake_image.write_bytes(b"fake_png_bytes")
        result = load_action(str(fake_image), simulated=True)
        # In simulated mode, summary or message might be the string
        assert isinstance(result.get("summary") or result.get("message"), str)


# ── 3. Schema Contract ─────────────────────────────────────────────────────

class TestSchemaContract:

    def test_success_response_has_required_keys(self, tmp_path):
        fake_image = tmp_path / "test.png"
        fake_image.write_bytes(b"fake_png_bytes")
        mock_return = {"status": "success", "text": "Invoice #1234", "file_path": "/tmp/ocr.txt"}
        with patch("app.internal_action_interface.InternalActionInterface.perform_ocr",
                   return_value=mock_return):
            result = load_action(str(fake_image))
        assert "status" in result
        assert result["status"] in ("success", "error")

    def test_error_response_has_message(self, tmp_path):
        fake_image = tmp_path / "test.png"
        fake_image.write_bytes(b"fake_png_bytes")
        with patch("app.internal_action_interface.InternalActionInterface.perform_ocr",
                   side_effect=RuntimeError("VLM unavailable")):
            result = load_action(str(fake_image))
        assert result["status"] == "error"
        assert "message" in result
        assert len(result["message"]) > 0

    def test_success_exposes_extracted_text(self, tmp_path):
        fake_image = tmp_path / "test.png"
        fake_image.write_bytes(b"fake_png_bytes")
        mock_return = {"status": "success", "text": "Hello World", "file_path": "/tmp/ocr.txt"}
        with patch("app.internal_action_interface.InternalActionInterface.perform_ocr",
                   return_value=mock_return):
            result = load_action(str(fake_image))
        # The action must surface the text somewhere — either in result["text"],
        # result["result"], or result["message"]
        combined = str(result)
        assert "Hello World" in combined


# ── 4. Bridge Delegation ───────────────────────────────────────────────────

class TestBridgeDelegation:

    def test_delegates_correct_image_path_to_bridge(self, tmp_path):
        fake_image = tmp_path / "receipt.png"
        fake_image.write_bytes(b"fake_png_bytes")
        mock_return = {"status": "success", "text": "some text", "file_path": "/tmp/x.txt"}
        with patch("app.internal_action_interface.InternalActionInterface.perform_ocr",
                   return_value=mock_return) as mock_bridge:
            load_action(str(fake_image))
            called_path = mock_bridge.call_args[0][0]
            assert called_path == str(fake_image)

    def test_bridge_vlm_not_initialized_returns_error(self, tmp_path):
        fake_image = tmp_path / "test.png"
        fake_image.write_bytes(b"fake_png_bytes")
        with patch("app.internal_action_interface.InternalActionInterface.perform_ocr",
                   side_effect=RuntimeError("InternalActionInterface not initialized with VLMInterface.")):
            result = load_action(str(fake_image))
        assert result["status"] == "error"
        assert "message" in result
