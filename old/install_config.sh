#!/usr/bin/env bash
set -e -u -o pipefail

###############################################################################
# Helper function to run Docker commands with sudo if needed
###############################################################################
docker_cmd() {
    if [ "${USE_SUDO:-false}" = true ]; then
        sudo docker "$@"
    else
        docker "$@"
    fi
}

###############################################################################
# Docker Installation & Configuration Menu
###############################################################################
docker_install_config_menu() {
    while true; do
        CHOICE=$(gum choose \
            "Check Docker Status" \
            "Install / Reinstall Docker" \
            "Install Yacht" \
            "Configure Docker" \
            "Change Docker Root Directory" \
            "Back to Main Menu")

        case "$CHOICE" in
            "Check Docker Status")                    
                check_docker_status
                ;;
            "Install / Reinstall Docker")
                install_or_reinstall_docker
                ;;
            "Install Yacht")
                install_yacht
                ;;
            "Configure Docker")
                configure_docker
                ;;
            "Change Docker Root Directory")
                change_docker_root
                ;;
            "Back to Main Menu")
                return
                ;;
        esac
    done
}

###############################################################################
# 1) Check Docker Status
###############################################################################
check_docker_status() {
    echo "🔍 Checking Docker status..."

    if ! command -v docker &> /dev/null; then
        gum style --foreground 1 "Docker is not installed."
        return 1
    fi

    # Display Docker version & info
    echo "Docker Version:"
    docker_cmd version

    echo -e "\nDocker Info:"
    docker_cmd info

    # Simple pause
    gum confirm "Press Enter to continue"
}

###############################################################################
# 2) Install or Reinstall Docker
###############################################################################
install_or_reinstall_docker() {
    if command -v docker &> /dev/null; then
        if gum confirm "Docker is already installed. Do you want to reinstall?"; then
            reinstall_docker
        fi
    else
        perform_docker_install
    fi
}

###############################################################################
# Perform a Fresh Docker Install
###############################################################################
perform_docker_install() {
    echo "🚀 Installing Docker..."

    # Update package index
    if ! sudo apt-get update; then
        gum style --foreground 1 "Failed to update package index."
        return 1
    fi

    # Install prerequisites
    if ! sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release; then
        gum style --foreground 1 "Failed to install Docker prerequisites."
        return 1
    fi

    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
        sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    # Set up the stable repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
        https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker Engine
    if ! sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io; then
        gum style --foreground 1 "Failed to install Docker."
        return 1
    fi

    # Add current user to docker group for non-root usage
    sudo usermod -aG docker "$USER"

    gum style --foreground 2 "Docker installed successfully!"
    gum style --foreground 3 "Please log out and back in for group changes to take effect."
}

###############################################################################
# Reinstall Docker
###############################################################################
reinstall_docker() {
    echo "🔄 Reinstalling Docker..."

    # Stop all running containers
    if docker_cmd ps -q | grep -q .; then
        if ! docker_cmd stop $(docker_cmd ps -q); then
            gum style --foreground 1 "Failed to stop containers."
            return 1
        fi
    fi

    # Remove Docker packages
    if ! sudo apt-get remove -y docker docker-engine docker.io containerd runc; then
        gum style --foreground 3 "No old Docker packages to remove (or removal failed)."
    fi

    # Perform a fresh install
    perform_docker_install
}

###############################################################################
# 3) Install Yacht (Using Docker Run)
###############################################################################
install_yacht() {
    echo "⛵ Installing Yacht (Docker Web UI)..."

    # According to official docs:
    #   docker volume create yacht
    #   docker run -d \
    #     -p 8000:8000 \
    #     -v /var/run/docker.sock:/var/run/docker.sock \
    #     -v yacht:/config \
    #     --name yacht selfhostedpro/yacht

    # 1) Create yacht volume
    gum style --bold "Creating 'yacht' volume..."
    if ! docker_cmd volume create yacht; then
        gum style --foreground 1 "Failed to create 'yacht' volume."
        return 1
    fi

    # 2) Run the container on port 8000
    gum style --bold "Starting Yacht container on port 8000..."
    if docker_cmd run -d \
        --name yacht \
        -p 8000:8000 \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v yacht:/config \
        selfhostedpro/yacht; then

        gum style --foreground 2 "✅ Yacht container is running!"

        echo
        echo "Access Yacht at: http://localhost:8000"
        echo "Default credentials:"
        echo " ➜ Username: admin@yacht.local"
        echo " ➜ Password: pass"
        echo
        gum style --foreground 3 "Please change the default password after first login."

    else
        gum style --foreground 1 "❌ Failed to run Yacht container."
        return 1
    fi
}

###############################################################################
# 4) Configure Docker
###############################################################################
configure_docker() {
    echo "⚙️  Configuring Docker..."
    local config_file="/etc/docker/daemon.json"

    # Ensure /etc/docker exists
    sudo mkdir -p /etc/docker

    if [ -f "$config_file" ]; then
        local current_config
        current_config=$(sudo cat "$config_file")
    else
        local current_config="{}"
    fi

    # Show a mini configuration menu
    local OPTION=$(gum choose \
        "Set Log Level" \
        "Set Max Container Size" \
        "Enable/Disable IPv6" \
        "Back")

    case "$OPTION" in
        "Set Log Level")
            local level
            level=$(gum choose "debug" "info" "warn" "error")
            echo "$current_config" | \
                jq ". + {\"log-level\": \"$level\"}" | \
                sudo tee "$config_file" >/dev/null
            ;;
        "Set Max Container Size")
            local size
            size=$(gum input --placeholder "Enter size (e.g., 10G)")
            echo "$current_config" | \
                jq ". + {\"storage-opts\": [\"dm.basesize=$size\"]}" | \
                sudo tee "$config_file" >/dev/null
            ;;
        "Enable/Disable IPv6")
            if gum confirm "Enable IPv6?"; then
                echo "$current_config" | \
                    jq '. + {"ipv6": true}' | \
                    sudo tee "$config_file" >/dev/null
            else
                echo "$current_config" | \
                    jq '. + {"ipv6": false}' | \
                    sudo tee "$config_file" >/dev/null
            fi
            ;;
        "Back")
            return
            ;;
    esac

    # Ask user to restart Docker to apply changes
    if gum confirm "Restart Docker daemon to apply changes?"; then
        sudo systemctl restart docker
        gum style --foreground 2 "Docker configuration updated and service restarted."
    else
        gum style --foreground 3 "Configuration saved but not applied (restart required)."
    fi
}

###############################################################################
# 5) Change Docker Root Directory
###############################################################################
change_docker_root() {
    echo "📂 Changing Docker Root Directory..."

    # Get new directory
    local new_root
    new_root=$(gum input --placeholder "Enter new Docker root directory path")
    if [ -z "$new_root" ]; then
        return
    fi

    # Create directory if it doesn't exist
    if ! sudo mkdir -p "$new_root"; then
        gum style --foreground 1 "Failed to create directory."
        return 1
    fi

    # Load existing daemon.json config or create new
    local config_file="/etc/docker/daemon.json"
    sudo mkdir -p /etc/docker

    local current_config
    if [ -f "$config_file" ]; then
        current_config=$(sudo cat "$config_file")
    else
        current_config="{}"
    fi

    # Update JSON with new data-root
    echo "$current_config" | \
        jq ". + {\"data-root\": \"$new_root\"}" | \
        sudo tee "$config_file" >/dev/null

    # Confirm the user wants to proceed with stopping Docker and moving data
    if gum confirm "This will stop Docker service and move all data. Continue?"; then
        # Stop Docker
        sudo systemctl stop docker

        # Move data from /var/lib/docker (or existing root) to new_root
        if [ -d "/var/lib/docker" ]; then
            sudo rsync -aP /var/lib/docker/ "$new_root/"
            sudo mv /var/lib/docker /var/lib/docker.old
        fi

        # Start Docker
        sudo systemctl start docker

        # Verify
        if docker info | grep -q "Docker Root Dir: $new_root"; then
            gum style --foreground 2 "Docker root directory changed successfully!"
            if gum confirm "Remove old Docker directory (/var/lib/docker.old)?"; then
                sudo rm -rf /var/lib/docker.old
            fi
        else
            gum style --foreground 1 "Failed to change Docker root directory."
            # Rollback
            gum style --foreground 3 "Rolling back to the old directory..."
            sudo systemctl stop docker
            sudo rm -rf "$new_root"
            sudo mv /var/lib/docker.old /var/lib/docker
            sudo systemctl start docker
        fi
    fi
}