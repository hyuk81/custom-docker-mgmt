# Docker Management Tool

A comprehensive command-line tool for managing Docker containers, backups, and system configuration.

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/hyuk81/custom-docker-mgmt.git
   cd custom-docker-mgmt
   ```

2. Activate the included virtual environment:
   ```bash
   source venv/bin/activate
   ```

3. Run the tool:
   ```bash
   ./docker-mgmt --interactive
   ```

## Features

- Container Operations
  - Start/Stop/Restart containers
  - Delete containers with volume cleanup
  - Show detailed container information

- Backup & Restore
  - Backup containers with their volumes
  - Restore containers from backups
  - Manage backup files

- Installation & Configuration
  - Check Docker installation
  - Install/Update Docker
  - Configure Docker daemon
  - Manage user permissions

- System Tools
  - Clean up unused resources
  - Install Yacht (Docker Web UI)
  - Run system tests

## Requirements

- Linux-based operating system
- Python 3.8 or higher (included in pre-built release)
- Docker (will be installed by the tool if not present)