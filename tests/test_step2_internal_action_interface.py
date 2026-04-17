# tests/test_step2_internal_action_interface.py
# -*- coding: utf-8 -*-
"""
Step 2 Verification Suite — InternalActionInterface Extensions
Tests for: perform_ocr() and understand_video() classmethods

Run with:
    python -m pytest tests/test_step2_internal_action_interface.py -v

ALL tests must pass. Zero real API calls. Zero real file system dependency
outside of tempfile — all workspace writes use a patched AGENT_WORKSPACE_ROOT.

PREREQUISITE: Step 1 tests must already be passing before running these.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock


# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def _reset_iai():
    """Reset InternalActionInterface class-level state between tests."""
    from app.internal_action_interface import InternalActionInterface
    InternalActionInterface.vlm_interface = None
    InternalActionInterface.llm_interface = None
    InternalActionInterface.task_manager = None
    InternalActionInterface.state_manager = None


def _inject_mock_vlm(mock_vlm=None):
    """Inject a mock VLMInterface into InternalActionInterface."""
    from app.internal_action_interface import InternalActionInterface
    if mock_vlm is None:
        mock_vlm = MagicMock()
    InternalActionInterface.vlm_interface = mock_vlm
    return mock_vlm


# ─────────────────────────────────────────────────────────────────
# SECTION A: Method Existence & Signatures
# ─────────────────────────────────────────────────────────────────

class TestMethodExistence(unittest.TestCase):
    """
    VERIFY: Both new classmethods exist and are classmethods (not staticmethods
    or instance methods), matching the pattern of describe_image().
    """

    def test_perform_ocr_exists(self):
        from app.internal_action_interface import InternalActionInterface
        self.assertTrue(
            hasattr(InternalActionInterface, "perform_ocr"),
            "FAIL: InternalActionInterface.perform_ocr not found. "
            "Add it to app/internal_action_interface.py"
        )

    def test_understand_video_exists(self):
        from app.internal_action_interface import InternalActionInterface
        self.assertTrue(
            hasattr(InternalActionInterface, "understand_video"),
            "FAIL: InternalActionInterface.understand_video not found. "
            "Add it to app/internal_action_interface.py"
        )

    def test_perform_ocr_is_classmethod(self):
        """perform_ocr must be a classmethod, not a staticmethod or instance method."""
        from app.internal_action_interface import InternalActionInterface
        method = InternalActionInterface.__dict__.get("perform_ocr")
        self.assertIsInstance(
            method, classmethod,
            "FAIL: perform_ocr must be a @classmethod (matching describe_image pattern)."
        )

    def test_understand_video_is_classmethod(self):
        """understand_video must be a classmethod."""
        from app.internal_action_interface import InternalActionInterface
        method = InternalActionInterface.__dict__.get("understand_video")
        self.assertIsInstance(
            method, classmethod,
            "FAIL: understand_video must be a @classmethod."
        )

    def test_perform_ocr_accepts_image_path(self):
        """perform_ocr must accept image_path as its first positional argument."""
        import inspect
        from app.internal_action_interface import InternalActionInterface
        sig = inspect.signature(InternalActionInterface.perform_ocr)
        params = list(sig.parameters.keys())
        self.assertIn("image_path", params,
            f"FAIL: perform_ocr must accept 'image_path'. Got params: {params}")

    def test_understand_video_accepts_video_path_and_query(self):
        """understand_video must accept video_path and query parameters."""
        import inspect
        from app.internal_action_interface import InternalActionInterface
        sig = inspect.signature(InternalActionInterface.understand_video)
        params = list(sig.parameters.keys())
        self.assertIn("video_path", params,
            f"FAIL: understand_video must accept 'video_path'. Got: {params}")
        self.assertIn("query", params,
            f"FAIL: understand_video must accept 'query'. Got: {params}")

    def tearDown(self):
        _reset_iai()


# ─────────────────────────────────────────────────────────────────
# SECTION B: VLM Guard — RuntimeError when not initialized
# ─────────────────────────────────────────────────────────────────

class TestVLMGuard(unittest.TestCase):
    """
    VERIFY: Both methods raise RuntimeError when vlm_interface is None,
    matching the guard pattern of describe_image() and describe_screen().
    """

    def setUp(self):
        _reset_iai()

    def test_perform_ocr_raises_when_vlm_not_initialized(self):
        from app.internal_action_interface import InternalActionInterface
        # vlm_interface is None (default state)
        with self.assertRaises(RuntimeError) as ctx:
            InternalActionInterface.perform_ocr("/some/image.png")
        self.assertIn(
            "VLMInterface", str(ctx.exception),
            "FAIL: RuntimeError message must mention 'VLMInterface' to match "
            "existing error message pattern in describe_image/describe_screen."
        )

    def test_understand_video_raises_when_vlm_not_initialized(self):
        from app.internal_action_interface import InternalActionInterface
        with self.assertRaises(RuntimeError) as ctx:
            InternalActionInterface.understand_video("/some/video.mp4")
        self.assertIn(
            "VLMInterface", str(ctx.exception),
            "FAIL: RuntimeError message must mention 'VLMInterface'."
        )

    def tearDown(self):
        _reset_iai()


# ─────────────────────────────────────────────────────────────────
# SECTION C: perform_ocr — Return Contract
# ─────────────────────────────────────────────────────────────────

class TestPerformOcrReturnContract(unittest.TestCase):
    """
    VERIFY: perform_ocr returns a dict with the correct keys,
    correct types, and saves extracted text to AGENT_WORKSPACE_ROOT.
    """

    def setUp(self):
        _reset_iai()
        self.tmp_workspace = tempfile.mkdtemp()

    def _run_perform_ocr(self, ocr_text="Hello World\nLine 2\nLine 3"):
        """Helper: run perform_ocr with a temp image and mocked VLM."""
        mock_vlm = MagicMock()
        mock_vlm.describe_image_ocr.return_value = ocr_text
        _inject_mock_vlm(mock_vlm)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"fake_png")
            image_path = f.name

        try:
            with patch("app.internal_action_interface.AGENT_WORKSPACE_ROOT", self.tmp_workspace):
                from app.internal_action_interface import InternalActionInterface
                result = InternalActionInterface.perform_ocr(image_path)
        finally:
            os.unlink(image_path)

        return result, mock_vlm

    def test_returns_dict(self):
        result, _ = self._run_perform_ocr()
        self.assertIsInstance(result, dict,
            "FAIL: perform_ocr must return a dict, not a plain string.")

    def test_return_dict_has_required_keys(self):
        """Must have: status, summary, file_path, file_saved."""
        result, _ = self._run_perform_ocr()
        for key in ("status", "summary", "file_path", "file_saved"):
            self.assertIn(key, result,
                f"FAIL: perform_ocr return dict is missing key '{key}'.")

    def test_status_is_success_on_happy_path(self):
        result, _ = self._run_perform_ocr()
        self.assertEqual(result["status"], "success",
            "FAIL: status must be 'success' on happy path.")

    def test_file_saved_is_true(self):
        result, _ = self._run_perform_ocr()
        self.assertTrue(result["file_saved"],
            "FAIL: file_saved must be True after successful OCR.")

    def test_file_path_exists_on_disk(self):
        """The file_path in the result must be a real file that was written."""
        result, _ = self._run_perform_ocr("Invoice #1234\nTotal: $99.99")
        self.assertTrue(
            os.path.isfile(result["file_path"]),
            f"FAIL: file_path '{result['file_path']}' does not exist on disk. "
            "perform_ocr must write the extracted text to workspace."
        )

    def test_file_content_matches_ocr_output(self):
        """The saved file must contain the raw OCR text exactly as returned by VLM."""
        ocr_text = "CONFIDENTIAL\nProject Alpha\nBudget: $1,000,000"
        result, _ = self._run_perform_ocr(ocr_text)

        with open(result["file_path"], "r", encoding="utf-8") as f:
            saved_content = f.read()

        self.assertEqual(saved_content, ocr_text,
            "FAIL: Saved file content does not match OCR output. "
            "The raw text must be written verbatim — no modification.")

    def test_file_saved_to_agent_workspace_root(self):
        """The saved file must be inside AGENT_WORKSPACE_ROOT, not a temp dir."""
        result, _ = self._run_perform_ocr()
        self.assertTrue(
            result["file_path"].startswith(self.tmp_workspace),
            f"FAIL: File saved to '{result['file_path']}' but expected "
            f"it to be inside AGENT_WORKSPACE_ROOT='{self.tmp_workspace}'. "
            "Do not hardcode paths — use AGENT_WORKSPACE_ROOT from app.config."
        )

    def test_file_has_txt_extension(self):
        """Output file must be a .txt file (readable by do_chat_with_attachments)."""
        result, _ = self._run_perform_ocr()
        self.assertTrue(
            result["file_path"].endswith(".txt"),
            f"FAIL: Output file must have .txt extension. Got: '{result['file_path']}'"
        )

    def test_summary_does_not_contain_full_text(self):
        """
        Summary must be a SHORT description, not the full OCR text.
        The whole point of saving to file is to keep the agent context lean.
        If summary == full text, the TUI flooding problem is not solved.
        """
        long_text = "Line\n" * 200  # 200 lines, definitely not a summary
        result, _ = self._run_perform_ocr(long_text)
        self.assertLess(
            len(result["summary"]), len(long_text),
            "FAIL: summary contains the full OCR text. It must be a short "
            "description (e.g. 'OCR complete: 200 lines, 1000 characters') "
            "to prevent context window flooding."
        )

    def test_summary_mentions_line_or_char_count(self):
        """Summary must be informative — mention lines or characters extracted."""
        result, _ = self._run_perform_ocr("Hello\nWorld")
        summary_lower = result["summary"].lower()
        has_count_info = (
            "line" in summary_lower or
            "char" in summary_lower or
            "word" in summary_lower or
            "extracted" in summary_lower
        )
        self.assertTrue(has_count_info,
            f"FAIL: summary '{result['summary']}' is not informative. "
            "It must mention lines/characters extracted so the agent knows what happened.")

    def test_calls_describe_image_ocr_not_describe_image(self):
        """
        CRITICAL: Must call vlm_interface.describe_image_ocr(), NOT
        vlm_interface.describe_image(). Using describe_image is exactly
        the existing bug that Issue #155 was filed for.
        """
        mock_vlm = MagicMock()
        mock_vlm.describe_image_ocr.return_value = "Some text"
        _inject_mock_vlm(mock_vlm)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"fake_png")
            image_path = f.name

        try:
            with patch("app.internal_action_interface.AGENT_WORKSPACE_ROOT", self.tmp_workspace):
                from app.internal_action_interface import InternalActionInterface
                InternalActionInterface.perform_ocr(image_path)
        finally:
            os.unlink(image_path)

        mock_vlm.describe_image_ocr.assert_called_once()
        mock_vlm.describe_image.assert_not_called()

    def test_user_prompt_forwarded_to_vlm(self):
        """Optional user_prompt must be passed through to vlm.describe_image_ocr."""
        mock_vlm = MagicMock()
        mock_vlm.describe_image_ocr.return_value = "text"
        _inject_mock_vlm(mock_vlm)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"fake_png")
            image_path = f.name

        try:
            with patch("app.internal_action_interface.AGENT_WORKSPACE_ROOT", self.tmp_workspace):
                from app.internal_action_interface import InternalActionInterface
                InternalActionInterface.perform_ocr(image_path, user_prompt="Focus on prices only.")
        finally:
            os.unlink(image_path)

        call_kwargs = mock_vlm.describe_image_ocr.call_args
        # Check the user_prompt was forwarded (positional or keyword)
        all_args = list(call_kwargs.args) + list(call_kwargs.kwargs.values())
        self.assertIn("Focus on prices only.", all_args,
            "FAIL: user_prompt was not forwarded to vlm_interface.describe_image_ocr(). "
            "The OCR method must pass user_prompt through.")

    def tearDown(self):
        _reset_iai()
        import shutil
        shutil.rmtree(self.tmp_workspace, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────
# SECTION D: understand_video — Return Contract
# ─────────────────────────────────────────────────────────────────

class TestUnderstandVideoReturnContract(unittest.TestCase):
    """
    VERIFY: understand_video returns a correct dict, saves summary to
    workspace, truncates summary to prevent TUI flooding, and
    forwards all parameters correctly to vlm_interface.
    """

    def setUp(self):
        _reset_iai()
        self.tmp_workspace = tempfile.mkdtemp()

    def _run_understand_video(self, summary_text="The video shows a presentation.", query=None, max_frames=8):
        mock_vlm = MagicMock()
        mock_vlm.describe_video_frames.return_value = summary_text
        _inject_mock_vlm(mock_vlm)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake_mp4")
            video_path = f.name

        try:
            with patch("app.internal_action_interface.AGENT_WORKSPACE_ROOT", self.tmp_workspace):
                from app.internal_action_interface import InternalActionInterface
                result = InternalActionInterface.understand_video(
                    video_path, query=query, max_frames=max_frames
                )
        finally:
            os.unlink(video_path)

        return result, mock_vlm

    def test_returns_dict(self):
        result, _ = self._run_understand_video()
        self.assertIsInstance(result, dict,
            "FAIL: understand_video must return a dict.")

    def test_return_dict_has_required_keys(self):
        result, _ = self._run_understand_video()
        for key in ("status", "summary", "file_path", "file_saved"):
            self.assertIn(key, result,
                f"FAIL: understand_video return dict is missing key '{key}'.")

    def test_status_is_success_on_happy_path(self):
        result, _ = self._run_understand_video()
        self.assertEqual(result["status"], "success")

    def test_file_saved_is_true(self):
        result, _ = self._run_understand_video()
        self.assertTrue(result["file_saved"])

    def test_file_path_exists_on_disk(self):
        result, _ = self._run_understand_video("A meeting recording with 3 participants.")
        self.assertTrue(
            os.path.isfile(result["file_path"]),
            f"FAIL: file_path '{result['file_path']}' does not exist. "
            "understand_video must write the full summary to workspace."
        )

    def test_full_summary_saved_to_file(self):
        """The full, untruncated summary must be in the saved file."""
        long_summary = "Frame description. " * 100  # deliberately long
        result, _ = self._run_understand_video(long_summary)

        with open(result["file_path"], "r", encoding="utf-8") as f:
            saved = f.read()

        self.assertEqual(saved, long_summary,
            "FAIL: The saved file must contain the FULL summary. "
            "Truncation only applies to the return dict's 'summary' key.")

    def test_summary_in_return_dict_is_truncated_for_long_content(self):
        """
        For long video summaries, the 'summary' key in the returned dict
        must be truncated (<=500 chars + ellipsis) to prevent context flooding.
        The full content is in the file — the dict summary is just a preview.
        """
        long_summary = "X" * 2000
        result, _ = self._run_understand_video(long_summary)
        self.assertLessEqual(
            len(result["summary"]), 510,  # 500 + len("...")
            f"FAIL: summary in return dict is {len(result['summary'])} chars. "
            "Must be truncated to ~500 chars to prevent agent context flooding."
        )

    def test_short_summary_not_truncated(self):
        """Short summaries (<=500 chars) must be returned as-is without ellipsis."""
        short_summary = "A quick 30-second tutorial on Python loops."
        result, _ = self._run_understand_video(short_summary)
        self.assertEqual(result["summary"], short_summary,
            "FAIL: Short summary was unexpectedly truncated or modified.")

    def test_file_saved_to_agent_workspace_root(self):
        result, _ = self._run_understand_video()
        self.assertTrue(
            result["file_path"].startswith(self.tmp_workspace),
            f"FAIL: File saved to wrong location. Expected inside "
            f"AGENT_WORKSPACE_ROOT='{self.tmp_workspace}'."
        )

    def test_file_has_txt_extension(self):
        result, _ = self._run_understand_video()
        self.assertTrue(result["file_path"].endswith(".txt"),
            "FAIL: Output file must be .txt")

    def test_video_filename_distinct_from_ocr_filename(self):
        """
        Video summary files must have a distinct filename prefix from OCR files
        to avoid confusion in workspace (e.g. 'video_summary_' vs 'ocr_result_').
        """
        result, _ = self._run_understand_video()
        filename = os.path.basename(result["file_path"])
        self.assertFalse(
            filename.startswith("ocr_"),
            f"FAIL: Video summary file '{filename}' starts with 'ocr_'. "
            "Video and OCR output files must have distinct prefixes."
        )

    def test_calls_describe_video_frames_not_describe_image(self):
        """Must delegate to vlm_interface.describe_video_frames(), not describe_image()."""
        mock_vlm = MagicMock()
        mock_vlm.describe_video_frames.return_value = "summary"
        _inject_mock_vlm(mock_vlm)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake_mp4")
            video_path = f.name

        try:
            with patch("app.internal_action_interface.AGENT_WORKSPACE_ROOT", self.tmp_workspace):
                from app.internal_action_interface import InternalActionInterface
                InternalActionInterface.understand_video(video_path)
        finally:
            os.unlink(video_path)

        mock_vlm.describe_video_frames.assert_called_once()
        mock_vlm.describe_image.assert_not_called()

    def test_query_forwarded_to_vlm(self):
        """The query parameter must be forwarded to describe_video_frames."""
        mock_vlm = MagicMock()
        mock_vlm.describe_video_frames.return_value = "answer"
        _inject_mock_vlm(mock_vlm)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake_mp4")
            video_path = f.name

        try:
            with patch("app.internal_action_interface.AGENT_WORKSPACE_ROOT", self.tmp_workspace):
                from app.internal_action_interface import InternalActionInterface
                InternalActionInterface.understand_video(video_path, query="What is on slide 3?")
        finally:
            os.unlink(video_path)

        call_kwargs = mock_vlm.describe_video_frames.call_args
        all_args = list(call_kwargs.args) + list(call_kwargs.kwargs.values())
        self.assertIn("What is on slide 3?", all_args,
            "FAIL: query not forwarded to describe_video_frames.")

    def test_max_frames_forwarded_to_vlm(self):
        """max_frames must be forwarded to describe_video_frames."""
        mock_vlm = MagicMock()
        mock_vlm.describe_video_frames.return_value = "summary"
        _inject_mock_vlm(mock_vlm)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake_mp4")
            video_path = f.name

        try:
            with patch("app.internal_action_interface.AGENT_WORKSPACE_ROOT", self.tmp_workspace):
                from app.internal_action_interface import InternalActionInterface
                InternalActionInterface.understand_video(video_path, max_frames=12)
        finally:
            os.unlink(video_path)

        call_kwargs = mock_vlm.describe_video_frames.call_args
        all_args = list(call_kwargs.args) + list(call_kwargs.kwargs.values())
        self.assertIn(12, all_args,
            "FAIL: max_frames=12 was not forwarded to describe_video_frames.")

    def tearDown(self):
        _reset_iai()
        import shutil
        shutil.rmtree(self.tmp_workspace, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────
# SECTION E: Regression — existing methods untouched
# ─────────────────────────────────────────────────────────────────

class TestRegressionExistingMethods(unittest.TestCase):
    """
    REGRESSION GUARD: Ensure describe_image(), describe_screen(),
    and initialize() still work exactly as before Step 2.
    """

    def setUp(self):
        _reset_iai()
        self.tmp_workspace = tempfile.mkdtemp()

    def test_describe_image_still_raises_when_vlm_none(self):
        from app.internal_action_interface import InternalActionInterface
        with self.assertRaises(RuntimeError):
            InternalActionInterface.describe_image("/any/path.png")

    def test_describe_image_still_returns_string(self):
        """describe_image must still return str (not dict) — contract unchanged."""
        mock_vlm = MagicMock()
        mock_vlm.describe_image.return_value = "A photo of a cat."
        _inject_mock_vlm(mock_vlm)

        from app.internal_action_interface import InternalActionInterface
        result = InternalActionInterface.describe_image("/fake/path.png")
        self.assertIsInstance(result, str,
            "REGRESSION: describe_image must still return str, not dict.")
        self.assertEqual(result, "A photo of a cat.")

    def test_initialize_still_sets_vlm_interface(self):
        """initialize() must still correctly set vlm_interface class attribute."""
        from app.internal_action_interface import InternalActionInterface

        mock_vlm = MagicMock()
        mock_llm = MagicMock()
        mock_task = MagicMock()
        mock_state = MagicMock()

        InternalActionInterface.initialize(
            llm_interface=mock_llm,
            task_manager=mock_task,
            state_manager=mock_state,
            vlm_interface=mock_vlm,
        )

        self.assertIs(InternalActionInterface.vlm_interface, mock_vlm,
            "REGRESSION: initialize() no longer sets vlm_interface correctly.")

    def test_new_methods_do_not_shadow_describe_image(self):
        """
        perform_ocr and understand_video must not accidentally override
        or shadow describe_image on the class.
        """
        from app.internal_action_interface import InternalActionInterface
        # All three must coexist independently
        self.assertTrue(hasattr(InternalActionInterface, "describe_image"))
        self.assertTrue(hasattr(InternalActionInterface, "perform_ocr"))
        self.assertTrue(hasattr(InternalActionInterface, "understand_video"))

        # describe_image must still delegate to vlm.describe_image
        mock_vlm = MagicMock()
        mock_vlm.describe_image.return_value = "original image description"
        _inject_mock_vlm(mock_vlm)

        result = InternalActionInterface.describe_image("/fake.png")
        mock_vlm.describe_image.assert_called_once()
        # describe_image_ocr must NOT have been called
        mock_vlm.describe_image_ocr.assert_not_called()

    def tearDown(self):
        _reset_iai()
        import shutil
        shutil.rmtree(self.tmp_workspace, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
