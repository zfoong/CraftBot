# -*- coding: utf-8 -*-
"""
Step 1 Verification Suite — VLM Interface Extensions
Tests for: describe_image_ocr, describe_video_frames, _openai_describe_bytes_plain,
           _gemini_describe_video_frames, _multi_frame_describe_fallback,
           GeminiClient.generate_multimodal_multi_image

Run with:
    python -m pytest tests/test_step1_vlm_interface.py -v

ALL tests must pass. Zero real API calls are made.
Zero imports of app.* are required — only agent_core.
"""

from __future__ import annotations

import base64
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

# ─────────────────────────────────────────────────────────────────
# SECTION A: GeminiClient.generate_multimodal_multi_image
# ─────────────────────────────────────────────────────────────────

class TestGeminiClientMultiImage(unittest.TestCase):
    """
    VERIFY: GeminiClient.generate_multimodal_multi_image exists and
    constructs the correct payload (one inlineData part per frame).
    """

    def _make_client(self):
        from agent_core.core.llm.google_gemini_client import GeminiClient
        client = GeminiClient.__new__(GeminiClient)
        client._api_key = "fake-key"
        client._api_base = "https://generativelanguage.googleapis.com"
        client._api_version = "v1beta"
        client._timeout = 30
        return client

    def test_method_exists(self):
        """generate_multimodal_multi_image must exist on GeminiClient."""
        from agent_core.core.llm.google_gemini_client import GeminiClient
        self.assertTrue(
            hasattr(GeminiClient, "generate_multimodal_multi_image"),
            "FAIL: GeminiClient.generate_multimodal_multi_image not found. "
            "Add it to agent_core/core/llm/google_gemini_client.py"
        )

    def test_payload_contains_multiple_inline_data_parts(self):
        """The API payload must contain one inlineData entry per frame passed in."""
        client = self._make_client()
        fake_response = {
            "candidates": [{"content": {"parts": [{"text": "video summary"}]}, "finishReason": "STOP"}],
            "usageMetadata": {"totalTokenCount": 100, "promptTokenCount": 80, "candidatesTokenCount": 20},
        }

        captured_payload = {}

        def fake_post(path, payload):
            captured_payload.update(payload)
            return fake_response

        client._post_json = fake_post

        frame_bytes = [b"frame1_bytes", b"frame2_bytes", b"frame3_bytes"]
        result = client.generate_multimodal_multi_image(
            "gemini-2.5-flash",
            text="What is happening?",
            image_bytes_list=frame_bytes,
            system_prompt="Analyse these frames.",
            temperature=0.5,
            json_mode=False,
        )

        # Assert return shape
        self.assertIn("content", result)
        self.assertIn("tokens_used", result)
        self.assertEqual(result["content"], "video summary")

        # Assert payload structure: must have text part + 3 inlineData parts
        parts = captured_payload["contents"][0]["parts"]
        inline_parts = [p for p in parts if "inlineData" in p]
        text_parts = [p for p in parts if "text" in p]

        self.assertEqual(len(inline_parts), 3,
            f"Expected 3 inlineData parts, got {len(inline_parts)}")
        self.assertEqual(len(text_parts), 1,
            f"Expected 1 text part, got {len(text_parts)}")

        # Assert each frame is correctly base64-encoded in the payload
        for i, (part, raw) in enumerate(zip(inline_parts, frame_bytes)):
            expected_b64 = base64.b64encode(raw).decode()
            actual_b64 = part["inlineData"]["data"]
            self.assertEqual(actual_b64, expected_b64,
                f"Frame {i+1}: base64 mismatch in payload")

    def test_system_prompt_is_included(self):
        """systemInstruction must be present in payload when system_prompt is given."""
        client = self._make_client()
        fake_response = {
            "candidates": [{"content": {"parts": [{"text": "ok"}]}, "finishReason": "STOP"}],
            "usageMetadata": {"totalTokenCount": 10, "promptTokenCount": 8, "candidatesTokenCount": 2},
        }
        captured = {}
        client._post_json = lambda path, payload: (captured.update(payload), fake_response)[1]

        client.generate_multimodal_multi_image(
            "gemini-2.5-flash",
            text="Describe",
            image_bytes_list=[b"img"],
            system_prompt="You are an expert.",
        )
        self.assertIn("systemInstruction", captured,
            "FAIL: systemInstruction missing from payload when system_prompt is provided")

    def test_no_system_prompt_omits_key(self):
        """systemInstruction must be absent when system_prompt is None."""
        client = self._make_client()
        fake_response = {
            "candidates": [{"content": {"parts": [{"text": "ok"}]}, "finishReason": "STOP"}],
            "usageMetadata": {"totalTokenCount": 5},
        }
        captured = {}
        client._post_json = lambda path, payload: (captured.update(payload), fake_response)[1]

        client.generate_multimodal_multi_image(
            "gemini-2.5-flash",
            text="Describe",
            image_bytes_list=[b"img"],
            system_prompt=None,
        )
        self.assertNotIn("systemInstruction", captured,
            "FAIL: systemInstruction should be absent when no system_prompt is given")


# ─────────────────────────────────────────────────────────────────
# SECTION B: VLMInterface._openai_describe_bytes_plain
# ─────────────────────────────────────────────────────────────────

class TestOpenAIDescribeBytesPlain(unittest.TestCase):
    """
    VERIFY: _openai_describe_bytes_plain exists and does NOT set
    response_format=json_object (that would break raw OCR text output).
    """

    def _make_vlm(self):
        """Instantiate VLMInterface in deferred mode so no real API calls are made."""
        with patch("app.models.factory.ModelFactory.create") as mock_create:
            mock_create.return_value = {
                "model": "gpt-4o",
                "client": MagicMock(),
                "gemini_client": None,
                "remote_url": None,
                "anthropic_client": None,
                "initialized": True,
                "byteplus": None,
                "provider": "openai",
            }
            from agent_core.core.impl.vlm.interface import VLMInterface
            vlm = VLMInterface(provider="openai", deferred=True)
            vlm.provider = "openai"
        return vlm

    def test_method_exists(self):
        """_openai_describe_bytes_plain must exist on VLMInterface."""
        from agent_core.core.impl.vlm.interface import VLMInterface
        self.assertTrue(
            hasattr(VLMInterface, "_openai_describe_bytes_plain"),
            "FAIL: _openai_describe_bytes_plain not found on VLMInterface. "
            "Add it to agent_core/core/impl/vlm/interface.py"
        )

    def test_no_response_format_json_object(self):
        """
        CRITICAL: _openai_describe_bytes_plain must NOT pass
        response_format={'type': 'json_object'} to the OpenAI client.
        OCR returns raw text — json_object enforces a JSON wrapper and breaks it.
        """
        vlm = self._make_vlm()

        mock_choice = MagicMock()
        mock_choice.message.content = "Hello World\nLine 2"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 20

        vlm.client = MagicMock()
        vlm.client.chat.completions.create.return_value = mock_response

        vlm._openai_describe_bytes_plain(b"fake_image_bytes", "sys prompt", "Extract text")

        call_kwargs = vlm.client.chat.completions.create.call_args[1]
        self.assertNotIn("response_format", call_kwargs,
            "FAIL: response_format is present in _openai_describe_bytes_plain. "
            "Remove it — OCR must return raw text, not JSON.")

    def test_returns_dict_with_content_and_tokens(self):
        """Must return dict with 'content' and 'tokens_used' keys."""
        vlm = self._make_vlm()

        mock_choice = MagicMock()
        mock_choice.message.content = "Extracted: Invoice #1234"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 40
        mock_response.usage.completion_tokens = 15
        vlm.client = MagicMock()
        vlm.client.chat.completions.create.return_value = mock_response

        result = vlm._openai_describe_bytes_plain(b"img", None, "Extract text")

        self.assertIsInstance(result, dict)
        self.assertIn("content", result)
        self.assertIn("tokens_used", result)
        self.assertEqual(result["content"], "Extracted: Invoice #1234")
        self.assertEqual(result["tokens_used"], 55)

    def test_max_tokens_is_at_least_4096(self):
        """
        OCR may produce large amounts of text. max_tokens must be >= 4096.
        """
        vlm = self._make_vlm()
        mock_choice = MagicMock()
        mock_choice.message.content = "text"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        vlm.client = MagicMock()
        vlm.client.chat.completions.create.return_value = mock_response

        vlm._openai_describe_bytes_plain(b"img", None, "Extract text")

        call_kwargs = vlm.client.chat.completions.create.call_args[1]
        max_tokens = call_kwargs.get("max_tokens", call_kwargs.get("max_completion_tokens", 0))
        self.assertGreaterEqual(max_tokens, 4096,
            f"FAIL: max_tokens={max_tokens}. OCR needs at least 4096 to handle large text blocks.")


# ─────────────────────────────────────────────────────────────────
# SECTION C: VLMInterface.describe_image_ocr
# ─────────────────────────────────────────────────────────────────

class TestDescribeImageOcr(unittest.TestCase):
    """
    VERIFY: describe_image_ocr exists, routes to the correct provider branch,
    uses an OCR-specific system prompt, and handles FileNotFoundError.
    """

    def _make_vlm_patched(self, provider="openai"):
        with patch("app.models.factory.ModelFactory.create") as mock_create:
            mock_create.return_value = {
                "model": "gpt-4o",
                "client": MagicMock(),
                "gemini_client": None,
                "remote_url": None,
                "anthropic_client": None,
                "initialized": True,
                "byteplus": None,
                "provider": provider,
            }
            from agent_core.core.impl.vlm.interface import VLMInterface
            vlm = VLMInterface(provider=provider, deferred=True)
            vlm.provider = provider
        return vlm

    def test_method_exists(self):
        from agent_core.core.impl.vlm.interface import VLMInterface
        self.assertTrue(
            hasattr(VLMInterface, "describe_image_ocr"),
            "FAIL: describe_image_ocr not found on VLMInterface. "
            "Add it to agent_core/core/impl/vlm/interface.py"
        )

    def test_raises_file_not_found_for_missing_path(self):
        """Must raise FileNotFoundError when the image path does not exist."""
        vlm = self._make_vlm_patched()
        with self.assertRaises(FileNotFoundError):
            vlm.describe_image_ocr("/nonexistent/path/image.png")

    def test_routes_to_plain_method_for_openai(self):
        """
        For provider='openai', describe_image_ocr must call
        _openai_describe_bytes_plain (not _openai_describe_bytes).
        This ensures json_object response format is not applied.
        """
        vlm = self._make_vlm_patched(provider="openai")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"fake_png_data")
            tmp_path = f.name

        try:
            vlm._openai_describe_bytes_plain = MagicMock(
                return_value={"content": "INVOICE\nTotal: $100", "tokens_used": 30}
            )
            vlm._openai_describe_bytes = MagicMock()

            result = vlm.describe_image_ocr(tmp_path)

            vlm._openai_describe_bytes_plain.assert_called_once()
            vlm._openai_describe_bytes.assert_not_called()
            self.assertEqual(result, "INVOICE\nTotal: $100")
        finally:
            os.unlink(tmp_path)

    def test_system_prompt_contains_ocr_keywords(self):
        """
        The system prompt passed to the provider must contain OCR-specific
        language ('OCR', 'extract', 'text') — not a generic description prompt.
        """
        vlm = self._make_vlm_patched(provider="openai")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"fake_png_data")
            tmp_path = f.name

        try:
            captured_sys_prompt = {}

            def capture_plain(image_bytes, sys_prompt, user_prompt):
                captured_sys_prompt["sys"] = sys_prompt or ""
                return {"content": "Hello", "tokens_used": 10}

            vlm._openai_describe_bytes_plain = capture_plain
            vlm.describe_image_ocr(tmp_path)

            sys_lower = captured_sys_prompt.get("sys", "").lower()
            self.assertTrue(
                "ocr" in sys_lower or "extract" in sys_lower or "text" in sys_lower,
                f"FAIL: OCR system prompt does not mention OCR/extraction. Got: '{captured_sys_prompt.get('sys')}'"
            )
        finally:
            os.unlink(tmp_path)

    def test_returns_string(self):
        """describe_image_ocr must return a string, not a dict."""
        vlm = self._make_vlm_patched(provider="openai")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"fake_png_data")
            tmp_path = f.name

        try:
            vlm._openai_describe_bytes_plain = MagicMock(
                return_value={"content": "TEXT FROM IMAGE", "tokens_used": 20}
            )
            result = vlm.describe_image_ocr(tmp_path)
            self.assertIsInstance(result, str)
        finally:
            os.unlink(tmp_path)


# ─────────────────────────────────────────────────────────────────
# SECTION D: VLMInterface.describe_video_frames
# ─────────────────────────────────────────────────────────────────

class TestDescribeVideoFrames(unittest.TestCase):
    """
    VERIFY: describe_video_frames exists, handles missing file,
    handles missing opencv gracefully, and calls the correct
    provider path (Gemini native vs. fallback).
    """

    def _make_vlm_patched(self, provider="openai"):
        with patch("app.models.factory.ModelFactory.create") as mock_create:
            mock_create.return_value = {
                "model": "gpt-4o",
                "client": MagicMock(),
                "gemini_client": None,
                "remote_url": None,
                "anthropic_client": None,
                "initialized": True,
                "byteplus": None,
                "provider": provider,
            }
            from agent_core.core.impl.vlm.interface import VLMInterface
            vlm = VLMInterface(provider=provider, deferred=True)
            vlm.provider = provider
        return vlm

    def test_method_exists(self):
        from agent_core.core.impl.vlm.interface import VLMInterface
        self.assertTrue(
            hasattr(VLMInterface, "describe_video_frames"),
            "FAIL: describe_video_frames not found on VLMInterface."
        )

    def test_raises_file_not_found_for_missing_video(self):
        """Must raise FileNotFoundError when the video path does not exist."""
        vlm = self._make_vlm_patched()
        with self.assertRaises(FileNotFoundError):
            vlm.describe_video_frames("/nonexistent/video.mp4")

    def test_raises_runtime_error_when_opencv_missing(self):
        """
        When opencv is not installed, describe_video_frames must raise
        a RuntimeError with an actionable install message — not an ImportError.
        This ensures a clean error surface for the user.
        """
        vlm = self._make_vlm_patched()

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake_mp4_data")
            tmp_path = f.name

        try:
            with patch.dict(sys.modules, {"cv2": None}):
                with self.assertRaises(RuntimeError) as ctx:
                    vlm.describe_video_frames(tmp_path)
                self.assertIn("opencv", str(ctx.exception).lower(),
                    "FAIL: RuntimeError message must mention 'opencv' to guide the user.")
        finally:
            os.unlink(tmp_path)

    def test_gemini_uses_native_multi_image_method(self):
        """
        For provider='gemini', describe_video_frames must call
        _gemini_describe_video_frames (native multi-image path).
        It must NOT fall back to the sequential per-frame fallback.
        """
        vlm = self._make_vlm_patched(provider="gemini")

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake_mp4_data")
            tmp_path = f.name

        try:
            mock_cv2 = MagicMock()
            mock_cap = MagicMock()
            mock_cap.get.return_value = 30.0
            mock_cap.read.return_value = (True, MagicMock())
            mock_cv2.VideoCapture.return_value = mock_cap
            mock_cv2.imencode.return_value = (True, MagicMock(tobytes=lambda: b"frame"))

            vlm._gemini_describe_video_frames = MagicMock(return_value="Gemini video summary")
            vlm._multi_frame_describe_fallback = MagicMock(return_value="fallback summary")

            with patch.dict(sys.modules, {"cv2": mock_cv2}):
                result = vlm.describe_video_frames(tmp_path, max_frames=2)

            vlm._gemini_describe_video_frames.assert_called_once()
            vlm._multi_frame_describe_fallback.assert_not_called()
            self.assertEqual(result, "Gemini video summary")
        finally:
            os.unlink(tmp_path)

    def test_non_gemini_uses_fallback(self):
        """
        For provider='openai', describe_video_frames must call
        _multi_frame_describe_fallback (sequential frame path).
        """
        vlm = self._make_vlm_patched(provider="openai")

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake_mp4_data")
            tmp_path = f.name

        try:
            mock_cv2 = MagicMock()
            mock_cap = MagicMock()
            mock_cap.get.return_value = 30.0
            mock_cap.read.return_value = (True, MagicMock())
            mock_cv2.VideoCapture.return_value = mock_cap
            mock_cv2.imencode.return_value = (True, MagicMock(tobytes=lambda: b"frame"))

            vlm._gemini_describe_video_frames = MagicMock(return_value="should not be called")
            vlm._multi_frame_describe_fallback = MagicMock(return_value="OpenAI fallback summary")

            with patch.dict(sys.modules, {"cv2": mock_cv2}):
                result = vlm.describe_video_frames(tmp_path, max_frames=2)

            vlm._multi_frame_describe_fallback.assert_called_once()
            vlm._gemini_describe_video_frames.assert_not_called()
            self.assertEqual(result, "OpenAI fallback summary")
        finally:
            os.unlink(tmp_path)


# ─────────────────────────────────────────────────────────────────
# SECTION E: Regression — existing describe_image still works
# ─────────────────────────────────────────────────────────────────

class TestRegressionDescribeImage(unittest.TestCase):
    """
    REGRESSION GUARD: Ensure existing describe_image and describe_image_bytes
    are untouched and still produce the same output contract.
    This confirms Step 1 did not break any existing functionality.
    """

    def _make_vlm_patched(self):
        with patch("app.models.factory.ModelFactory.create") as mock_create:
            mock_create.return_value = {
                "model": "gpt-4o",
                "client": MagicMock(),
                "gemini_client": None,
                "remote_url": None,
                "anthropic_client": None,
                "initialized": True,
                "byteplus": None,
                "provider": "openai",
            }
            from agent_core.core.impl.vlm.interface import VLMInterface
            vlm = VLMInterface(provider="openai", deferred=True)
            vlm.provider = "openai"
        return vlm

    def test_describe_image_still_raises_on_missing_file(self):
        """describe_image must still raise FileNotFoundError (unchanged)."""
        vlm = self._make_vlm_patched()
        with self.assertRaises(FileNotFoundError):
            vlm.describe_image("/does/not/exist.png")

    def test_describe_image_bytes_returns_string(self):
        """describe_image_bytes must still return a plain string."""
        vlm = self._make_vlm_patched()

        mock_choice = MagicMock()
        mock_choice.message.content = '{"content": "A cat"}'
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        vlm.client = MagicMock()
        vlm.client.chat.completions.create.return_value = mock_response

        result = vlm.describe_image_bytes(b"fake_image", user_prompt="Describe this image.")
        self.assertIsInstance(result, str)

    def test_describe_image_bytes_uses_json_response_format(self):
        """
        REGRESSION: The ORIGINAL describe_image_bytes must still use
        response_format=json_object (this is the existing contract).
        It should NOT be affected by the plain-text OCR variant.
        """
        vlm = self._make_vlm_patched()

        mock_choice = MagicMock()
        mock_choice.message.content = '{"content": "A dog"}'
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        vlm.client = MagicMock()
        vlm.client.chat.completions.create.return_value = mock_response

        vlm.describe_image_bytes(b"fake_image", user_prompt="Describe this.")

        call_kwargs = vlm.client.chat.completions.create.call_args[1]
        # Original describe_image_bytes should still request json_object
        self.assertIn("response_format", call_kwargs,
            "REGRESSION: describe_image_bytes lost response_format=json_object. "
            "Only the new _openai_describe_bytes_plain should omit it.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
