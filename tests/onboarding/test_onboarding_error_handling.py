# -*- coding: utf-8 -*-
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from agent_core.core.impl.onboarding.manager import OnboardingManager
from agent_core.core.impl.onboarding.state import OnboardingState

@pytest.fixture
def onboarding_manager():
    # Reset singleton-like instance for testing
    manager = OnboardingManager()
    manager._state = OnboardingState()
    return manager

def test_save_state_error_bubbles_up(onboarding_manager):
    """Test that OSError during file write propagates through OnboardingManager."""
    with patch("agent_core.core.impl.onboarding.state.get_onboarding_config_file") as mock_get_file:
        mock_get_file.return_value = Path("/tmp/fake_state.json")
        with patch("pathlib.Path.write_text") as mock_write:
            mock_write.side_effect = OSError("Disk full")
            
            # Test mark_hard_complete
            with pytest.raises(OSError) as excinfo:
                onboarding_manager.mark_hard_complete(agent_name="TestAgent")
            assert "Disk full" in str(excinfo.value)
            
            # Test mark_soft_complete
            with pytest.raises(OSError) as excinfo:
                onboarding_manager.mark_soft_complete()
            assert "Disk full" in str(excinfo.value)
            
            # Test reset_soft_onboarding
            with pytest.raises(OSError) as excinfo:
                onboarding_manager.reset_soft_onboarding()
            assert "Disk full" in str(excinfo.value)
            
            # Test reset_all
            with pytest.raises(OSError) as excinfo:
                onboarding_manager.reset_all()
            assert "Disk full" in str(excinfo.value)

            # Test save
            with pytest.raises(OSError) as excinfo:
                onboarding_manager.save()
            assert "Disk full" in str(excinfo.value)

def test_save_state_permission_error_bubbles_up(onboarding_manager):
    """Test that PermissionError during file write propagates."""
    with patch("agent_core.core.impl.onboarding.state.get_onboarding_config_file") as mock_get_file:
        mock_get_file.return_value = Path("/tmp/fake_state.json")
        with patch("pathlib.Path.write_text") as mock_write:
            mock_write.side_effect = PermissionError("Permission denied")
            
            with pytest.raises(PermissionError) as excinfo:
                onboarding_manager.save()
            assert "Permission denied" in str(excinfo.value)
