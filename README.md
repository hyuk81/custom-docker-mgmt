# Custom Docker Management Tools

A collection of interactive CLI tools for managing Docker containers with style, powered by [Charm](https://charm.sh/) tools like Gum and BubbleTea.

## 🎯 Project Goals

- Create user-friendly, interactive CLI tools for Docker container management
- Simplify common Docker operations with beautiful TUI interfaces
- Provide efficient backup and restore functionality for containers
- Make Docker management more accessible and enjoyable

## 🛠️ Features

### Current Features
- [ ] Container Management
  - [ ] Interactive container selection
  - [ ] Start/Stop/Restart containers
  - [ ] Container health monitoring
  - [ ] Docker environment setup
    - [ ] Automatic Docker installation
    - [ ] Docker Compose installation
    - [ ] System prerequisites check and setup
  
- [ ] Backup & Restore
  - [ ] Interactive Backup Management
    - [ ] Visual folder navigation and selection
    - [ ] Create new folders on-the-fly
    - [ ] Backup name suggestions based on container
    - [ ] Backup compression options
  - [ ] Backup container volumes
  - [ ] Export container configurations
  - [ ] Interactive Restore Process
    - [ ] Visual backup location browser
    - [ ] Backup integrity verification
    - [ ] Preview backup contents
  - [ ] Scheduled automatic backups
    - [ ] Customizable retention policies
    - [ ] Backup rotation management

- [ ] System Management
  - [ ] Disk space monitoring
  - [ ] Resource usage visualization
  - [ ] Log management
  - [ ] Backup storage management
    - [ ] Storage space monitoring
    - [ ] Old backup cleanup
    - [ ] Backup size estimation

## 🔧 Technical Stack

- **Programming Language**: Go
- **UI Framework**: 
  - [Bubble Tea](https://github.com/charmbracelet/bubbletea) - Terminal UI framework
  - [Gum](https://github.com/charmbracelet/gum) - Shell script glamour
  - [Lip Gloss](https://github.com/charmbracelet/lipgloss) - Style definitions
  - [Bubbles](https://github.com/charmbracelet/bubbles) - Common TUI components
- **Container Runtime**: Docker
- **File System**: 
  - [Walk](https://golang.org/pkg/path/filepath/#Walk) - Directory traversal
  - [OS](https://golang.org/pkg/os/) - File operations

## 📁 Project Structure