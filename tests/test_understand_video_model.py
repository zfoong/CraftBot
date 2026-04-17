import pytest
from unittest.mock import patch, MagicMock
import os

def test_understand_video_uses_configured_model():
    """understand_video must use get_vlm_model(), not hardcode gemini-1.5-pro."""
    mock_file = MagicMock()
    mock_file.state.name = "ACTIVE"
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.return_value = MagicMock(text="video summary")

    with patch("os.path.isfile", return_value=True), \
         patch("app.config.get_api_key", return_value="fake-key"), \
         patch("app.config.get_vlm_model", return_value="gemini-2.0-flash") as mock_get_model, \
         patch("google.generativeai.configure"), \
         patch("google.generativeai.upload_file", return_value=mock_file), \
         patch("google.generativeai.get_file", return_value=mock_file), \
         patch("google.generativeai.GenerativeModel", return_value=mock_model_instance) as mock_gm, \
         patch("google.generativeai.delete_file"), \
         patch("builtins.open", MagicMock()), \
         patch("app.config.AGENT_WORKSPACE_ROOT", "/tmp"):
        from app.data.action.understand_video import understand_video
        understand_video({"video_path": "/fake/video.mp4"})
        called_model_name = mock_gm.call_args[0][0]
        assert called_model_name == "gemini-2.0-flash", \
            f"Expected gemini-2.0-flash from config, got {called_model_name}"

def test_understand_video_falls_back_when_config_missing():
    """If get_vlm_model() returns None, fall back to gemini-1.5-pro."""
    mock_file = MagicMock()
    mock_file.state.name = "ACTIVE"
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.return_value = MagicMock(text="summary")

    with patch("os.path.isfile", return_value=True), \
         patch("app.config.get_api_key", return_value="fake-key"), \
         patch("app.config.get_vlm_model", return_value=None), \
         patch("google.generativeai.configure"), \
         patch("google.generativeai.upload_file", return_value=mock_file), \
         patch("google.generativeai.get_file", return_value=mock_file), \
         patch("google.generativeai.GenerativeModel", return_value=mock_model_instance) as mock_gm, \
         patch("google.generativeai.delete_file"), \
         patch("builtins.open", MagicMock()), \
         patch("app.config.AGENT_WORKSPACE_ROOT", "/tmp"):
        from app.data.action.understand_video import understand_video
        understand_video({"video_path": "/fake/video.mp4"})
        called_model_name = mock_gm.call_args[0][0]
        assert called_model_name == "gemini-1.5-pro", \
            f"Expected fallback gemini-1.5-pro, got {called_model_name}"
