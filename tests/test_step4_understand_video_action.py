# tests/test_step4_understand_video_action.py

import pytest
from unittest.mock import patch

def load_action(video_path: str, query: str = "", simulated: bool = False) -> dict:
    from app.data.action.understand_video import execute
    return execute({
        "video_path": video_path,
        "query": query,
        "simulated_mode": simulated,
    })


class TestInputValidation:

    def test_missing_video_path_key(self):
        from app.data.action.understand_video import execute
        result = execute({})
        assert result["status"] == "error"
        assert "video_path" in result["message"].lower()

    def test_empty_video_path_string(self):
        result = load_action("")
        assert result["status"] == "error"

    def test_nonexistent_file_path(self):
        result = load_action("/tmp/does_not_exist_98765.mp4")
        assert result["status"] == "error"

    def test_path_is_directory_not_file(self, tmp_path):
        result = load_action(str(tmp_path))
        assert result["status"] == "error"


class TestSimulatedMode:

    def test_simulated_mode_returns_success(self, tmp_path):
        fake_video = tmp_path / "test.mp4"
        fake_video.write_bytes(b"fake_video_bytes")
        result = load_action(str(fake_video), simulated=True)
        assert result["status"] == "success"

    def test_simulated_mode_makes_no_vlm_call(self, tmp_path):
        fake_video = tmp_path / "test.mp4"
        fake_video.write_bytes(b"fake_video_bytes")
        with patch("app.internal_action_interface.InternalActionInterface.understand_video") as mock_bridge:
            load_action(str(fake_video), simulated=True)
            mock_bridge.assert_not_called()


class TestSchemaContract:

    def test_success_response_has_required_keys(self, tmp_path):
        fake_video = tmp_path / "clip.mp4"
        fake_video.write_bytes(b"fake_video_bytes")

        mock_return = {
            "status": "success",
            "summary": "A person walks into a room.",
            "preview": "A person walks...",
            "file_path": "/tmp/video_summary.txt",
        }
        with patch("app.internal_action_interface.InternalActionInterface.understand_video",
                   return_value=mock_return):
            result = load_action(str(fake_video), query="What happens?")

        assert result["status"] == "success"
        for key in ("summary", "file_path"):
            assert key in result

    def test_error_response_has_message(self, tmp_path):
        fake_video = tmp_path / "clip.mp4"
        fake_video.write_bytes(b"fake_video_bytes")

        with patch("app.internal_action_interface.InternalActionInterface.understand_video",
                   side_effect=RuntimeError("VLM unavailable")):
            result = load_action(str(fake_video))

        assert result["status"] == "error"
        assert "message" in result
        assert len(result["message"]) > 0


class TestBridgeDelegation:

    def test_delegates_correct_video_path_and_query(self, tmp_path):
        fake_video = tmp_path / "scene.mp4"
        fake_video.write_bytes(b"fake_video_bytes")

        mock_return = {
            "status": "success",
            "summary": "Some summary",
            "preview": "Some...",
            "file_path": "/tmp/video_summary.txt",
        }
        with patch("app.internal_action_interface.InternalActionInterface.understand_video",
                   return_value=mock_return) as mock_bridge:
            load_action(str(fake_video), query="Who is present?")

            # Verify bridge call arguments
            # In some versions of mock, call_args[0] is positional args
            called_args = mock_bridge.call_args[0]
            assert called_args[0] == str(fake_video)
            assert mock_bridge.call_args[1].get('query') == "Who is present?" or called_args[1] == "Who is present?"

    def test_bridge_vlm_not_initialized_returns_error(self, tmp_path):
        fake_video = tmp_path / "scene.mp4"
        fake_video.write_bytes(b"fake_video_bytes")

        with patch("app.internal_action_interface.InternalActionInterface.understand_video",
                   side_effect=RuntimeError("InternalActionInterface not initialized with VLMInterface.")):
            result = load_action(str(fake_video))

        assert result["status"] == "error"
        assert "message" in result
