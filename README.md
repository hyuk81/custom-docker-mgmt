# Docker Management Tool

A comprehensive command-line tool for managing Docker containers, backups, and system configuration.

## Features

- **Container Operations**
  - Start, stop, and restart containers
  - Delete containers with cleanup of associated resources
  - Show detailed container information
  - Manage container backups and restores

- **Backup & Restore**
  - Create container backups with volume data
  - Restore containers from backups
  - Browse and manage backup files
  - Automatic backup naming with timestamps

- **Installation & Configuration**
  - Check Docker installation status
  - Install Docker and Docker Compose
  - Update Docker installation
  - Configure Docker daemon settings
  - Change Docker root directory
  - Configure user permissions

- **System Tools**
  - Clean up unused containers
  - Clean up unused volumes
  - Clean up unused networks
  - Clean up unused images
  - Clean up build cache
  - Show disk usage
  - System-wide cleanup

## Requirements

- Python 3.8 or higher
- Docker
- sudo privileges

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/custom-docker-mgmt.git
   cd custom-docker-mgmt
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Unix/macOS
   # or
   .\venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Make the script executable:
   ```bash
   chmod +x docker_manager.py
   ```

## Development Setup

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt  # If you have additional dev dependencies
   ```

2. Set up pre-commit hooks:
   ```bash
   pre-commit install  # If you use pre-commit for code quality
   ```

3. Run tests:
   ```bash
   python -m pytest tests/  # If you have tests
   ```

## Usage

Run the tool in interactive mode:
```bash
./docker_manager.py --interactive
```

### Main Menu Options

1. **Container Operations**
   - List and manage running containers
   - Perform container-specific operations

2. **Backup & Restore**
   - Create backups of containers with their data
   - Restore containers from backups
   - Browse backup files

3. **Installation & Config**
   - Check and manage Docker installation
   - Configure Docker daemon
   - Change Docker root directory
   - Manage user permissions

4. **System Tools**
   - Clean up Docker resources
   - Show disk usage
   - Perform system-wide cleanup

## Configuration

The tool stores:
- Backups in `~/.docker_backups/`
- Docker configuration in `/etc/docker/daemon.json`

## Security

- Requires sudo privileges for Docker operations
- Handles sensitive operations with user confirmation
- Validates paths and permissions before operations

## Troubleshooting

1. **Permission Denied**
   - Ensure your user is in the docker group
   - Run the tool with appropriate permissions

2. **Docker Not Running**
   - Check Docker daemon status
   - Use Installation & Config menu to fix issues

3. **Space Issues**
   - Use System Tools to clean up resources
   - Check available space before operations

4. **Python Environment Issues**
   - Make sure to use Python 3.8 or higher
   - Use `python3` command if `python` is not found
   - Ensure all dependencies are installed correctly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add docstrings for new functions
- Update tests for new features
- Keep commits atomic and well-documented

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Docker CLI for inspiration
- Rich library for terminal UI
- Textual library for file browsing
- Typer for command-line interface