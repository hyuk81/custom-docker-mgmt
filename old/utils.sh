#!/usr/bin/env bash

log_debug() {
    if [ "${DEBUG:-false}" = true ]; then
        echo "[DEBUG] $*"
    fi
}

fatal_error() {
    gum style --foreground 1 "❌ Fatal error: $*"
    exit 1
}

check_prerequisites() {
    # Check sudo access first
    if ! sudo -v; then
        fatal_error "This script requires sudo access to manage Docker"
    fi

    # Check gum
    if ! command -v gum &> /dev/null; then
        fatal_error "Gum is not installed. Please run ./charmsetup.sh or install gum first."
    fi

    # Check jq
    if ! command -v jq &> /dev/null; then
        fatal_error "jq is not installed. Please install it (e.g. sudo apt-get install -y jq)."
    fi

    # Check Docker installation
    if ! command -v docker &> /dev/null; then
        fatal_error "Docker is not installed. Please install Docker first."
    fi

    # Check Docker service status and start if needed
    if ! sudo systemctl is-active --quiet docker; then
        echo "🔄 Docker service is not running. Attempting to start..."
        if ! sudo systemctl start docker; then
            fatal_error "Failed to start Docker service. Please check 'systemctl status docker' for details"
        fi
        gum style --foreground 2 "Docker service started successfully"
    fi

    # Test Docker connectivity with sudo first
    if ! sudo docker info &>/dev/null; then
        fatal_error "Cannot connect to Docker daemon even with sudo. Please check Docker installation"
    fi

    # Now check if we need to add user to docker group
    if ! groups "$USER" | grep -q "docker"; then
        echo "🔧 Adding user to docker group..."
        if ! sudo usermod -aG docker "$USER"; then
            fatal_error "Failed to add user to docker group"
        fi
        
        # Set USE_SUDO for this session since group changes haven't taken effect
        export USE_SUDO=true
        gum style --foreground 3 "You have been added to the docker group."
        gum style --foreground 3 "Using sudo for this session."
        gum style --foreground 3 "Please log out and log back in for group changes to take effect."
    else
        # User is in docker group, test direct access
        if ! docker info &>/dev/null; then
            export USE_SUDO=true
            gum style --foreground 3 "Using sudo for Docker commands due to permission issues."
        fi
    fi

    # Optional: netstat check
    if ! command -v netstat &> /dev/null; then
        log_debug "netstat not found. If netstat usage fails below, install the 'net-tools' package."
    fi
}