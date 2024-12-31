"""Tests for installation menu functionality."""
import pytest
from unittest.mock import patch, MagicMock
from ..ui.menu_handlers import installation_menu
from ..utils.docker_utils import run_docker_command

@pytest.fixture
def mock_console():
    with patch('docker_mgmt.ui.menu_handlers.console') as mock:
        yield mock

@pytest.fixture
def mock_docker_command():
    with patch('docker_mgmt.ui.menu_handlers.run_docker_command') as mock:
        yield mock

def test_check_docker_installation_both_installed(mock_console, mock_docker_command):
    """Test when both Docker and Docker Compose are installed."""
    # Mock the responses
    mock_docker_command.side_effect = [
        "Docker version 24.0.7",  # Docker version
        "Docker Compose version v2.21.0"  # Docker Compose version
    ]
    
    # Mock the menu to return 0 (Check Docker installation) and then None (exit)
    with patch('docker_mgmt.ui.menu_handlers.Menu.show', side_effect=[0, None]):
        with patch('builtins.input'):  # Mock the "Press Enter to continue"
            installation_menu()
    
    # Verify the correct messages were printed
    mock_console.print.assert_any_call("[green]✓ Docker is installed:[/green] Docker version 24.0.7")
    mock_console.print.assert_any_call("[green]✓ Docker Compose is installed:[/green] Docker Compose version v2.21.0")

def test_check_docker_installation_none_installed(mock_console, mock_docker_command):
    """Test when neither Docker nor Docker Compose are installed."""
    # Mock the responses to return None (not installed)
    mock_docker_command.return_value = None
    
    # Mock the menu to return 0 (Check Docker installation) and then None (exit)
    with patch('docker_mgmt.ui.menu_handlers.Menu.show', side_effect=[0, None]):
        with patch('builtins.input'):  # Mock the "Press Enter to continue"
            installation_menu()
    
    # Verify the correct messages were printed
    mock_console.print.assert_any_call("[red]✗ Docker is not installed[/red]")
    mock_console.print.assert_any_call("[red]✗ Docker Compose is not installed[/red]")

def test_check_docker_installation_only_docker(mock_console, mock_docker_command):
    """Test when only Docker is installed but not Docker Compose."""
    # Mock the responses
    mock_docker_command.side_effect = [
        "Docker version 24.0.7",  # Docker version
        None  # Docker Compose not installed
    ]
    
    # Mock the menu to return 0 (Check Docker installation) and then None (exit)
    with patch('docker_mgmt.ui.menu_handlers.Menu.show', side_effect=[0, None]):
        with patch('builtins.input'):  # Mock the "Press Enter to continue"
            installation_menu()
    
    # Verify the correct messages were printed
    mock_console.print.assert_any_call("[green]✓ Docker is installed:[/green] Docker version 24.0.7")
    mock_console.print.assert_any_call("[red]✗ Docker Compose is not installed[/red]") 