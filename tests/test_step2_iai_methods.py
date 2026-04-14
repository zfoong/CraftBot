# -*- coding: utf-8 -*-
import unittest
from unittest.mock import MagicMock, patch, mock_open
import os
from datetime import datetime
import asyncio

# Mocking the constants before import if necessary, but app.config should be fine
import sys
from unittest.mock import PropertyMock

class TestStep2InternalInterface(unittest.TestCase):
    def setUp(self):
        # We need to mock InternalActionInterface dependencies
        self.iai_patcher = patch('app.internal_action_interface.InternalActionInterface', autospec=True)
        # However, we want to test the ACTUAL methods on InternalActionInterface
        # So we import it and patch its class attributes
        
        from app.internal_action_interface import InternalActionInterface
        self.iai = InternalActionInterface
        self.iai.vlm_interface = MagicMock()
        self.iai.state_manager = MagicMock()
        self.iai.ui_adapter = MagicMock()

    @patch('os.path.join', side_effect=lambda *args: "/".join(args))
    @patch('builtins.open', new_callable=mock_open)
    @patch('app.internal_action_interface.AGENT_WORKSPACE_ROOT', "/mock/workspace")
    def test_perform_ocr_saves_file_and_returns_dict(self, mock_file, mock_join):
        # Setup
        self.iai.vlm_interface.describe_image_ocr.return_value = "Extracted Text Content"
        
        # Execute
        result = self.iai.perform_ocr("some_image.jpg", user_prompt="Test Prompt")
        
        # Verify call to VLM
        self.iai.vlm_interface.describe_image_ocr.assert_called_once_with("some_image.jpg", user_prompt="Test Prompt")
        
        # Verify file saving
        mock_file.assert_called_once()
        handle = mock_file()
        handle.write.assert_called_once_with("Extracted Text Content")
        
        # Verify return dict
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['file_saved'])
        self.assertIn('ocr_result_', result['file_path'])
        self.assertIn('OCR complete', result['summary'])

    @patch('os.path.join', side_effect=lambda *args: "/".join(args))
    @patch('builtins.open', new_callable=mock_open)
    @patch('app.internal_action_interface.AGENT_WORKSPACE_ROOT', "/mock/workspace")
    def test_understand_video_saves_file_and_returns_dict(self, mock_file, mock_join):
        # Setup
        self.iai.vlm_interface.describe_video_frames.return_value = "Video Summary Content"
        
        # Execute
        result = self.iai.understand_video("some_video.mp4", query="What happens?")
        
        # Verify call to VLM
        self.iai.vlm_interface.describe_video_frames.assert_called_once_with(
            "some_video.mp4", query="What happens?", max_frames=8
        )
        
        # Verify file saving
        mock_file.assert_called_once()
        handle = mock_file()
        handle.write.assert_called_once_with("Video Summary Content")
        
        # Verify return dict
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['file_saved'])
        self.assertIn('video_summary_', result['file_path'])
        self.assertEqual(result['summary'], "Video Summary Content")

if __name__ == '__main__':
    unittest.main()
