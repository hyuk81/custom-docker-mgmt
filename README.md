# Docker Management Tool

A comprehensive command-line tool for managing Docker containers, backups, and system configuration.

## Features

- **Container Operations**
  - List all containers with status
  - Start, stop, and restart containers
  - Delete containers with optional volume cleanup
  - Show detailed container information (ports, networks, mounts, size)

- **Backup & Restore**
  - Create container backups including:
    - Container configuration
    - Volume data (with proper permissions)
    - Port mappings
    - Environment variables
    - Network settings
    - Labels and other metadata
  - Restore containers with:
    - Original configuration
    - Volume data
    - Network settings
    - Port mappings
    - Environment variables
    - Labels
  - Automatic backup naming with timestamps
  - Safe volume handling during backup/restore

- **Installation & Configuration**
  - Check Docker installation status
  - Install and configure Yacht (Docker Web UI)
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
- sudo privileges (for certain operations)

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
   chmod +x docker-mgmt
   ```

## Usage

Run the tool in interactive mode:
```bash
./docker-mgmt --interactive
# or
python -m docker_mgmt --interactive
```

### Main Menu Options

1. **Container Operations**
   - List and manage running containers
   - Start, stop, restart containers
   - Delete containers with optional volume cleanup
   - Show detailed container information

2. **Backup & Restore**
   - Create comprehensive backups of containers
   - Restore containers with all original settings
   - Manage backup files
   - Safe volume handling

3. **Installation & Config**
   - Install and configure Yacht (Docker Web UI)
   - Configure Docker settings
   - Manage permissions

4. **System Tools**
   - Clean up Docker resources
   - Show disk usage
   - System maintenance

## Data Storage

- Backups are stored in `~/.docker_backups/`
- Each backup includes:
  - Container configuration (config.json)
  - Volume data
  - Complete container metadata

## Security Features

- Safe volume handling with read-only source mounts
- Proper permission management for backups
- Volume data preservation by default
- Optional cleanup of sensitive data
- Confirmation prompts for destructive operations

## Troubleshooting

1. **Permission Issues**
   - The tool uses sudo only when necessary
   - Volume operations are handled safely
   - Proper ownership is maintained for backup files

2. **Docker Not Running**
   - Automatic Docker status check
   - Clear error messages
   - Guided resolution steps

3. **Backup/Restore Issues**
   - Volumes are preserved by default
   - Clear prompts for data cleanup
   - Safe handling of container states

4. **Container Management**
   - Detailed container information
   - Safe deletion with optional cleanup
   - Proper handling of running containers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add docstrings for new functions
- Maintain proper error handling
- Keep user interaction consistent
- Preserve data safety features

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.