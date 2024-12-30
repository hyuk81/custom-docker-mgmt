#!/usr/bin/env bash
set -e -u -o pipefail

DEBUG=false
if [ "${1:-}" = "--debug" ]; then
    DEBUG=true
fi

# Source utils first for prerequisite checking
source ./utils.sh

# Check all prerequisites (including Docker installation and permissions)
check_prerequisites

# Source remaining scripts after prerequisites are confirmed
source ./container_ops.sh
source ./backup_restore.sh
source ./install_config.sh
source ./system_tools.sh

show_main_menu() {
    while true; do
        echo "🐳 Docker Management Tools"
        
        CHOICE=$(gum choose \
            "Container Operations" \
            "Backup & Restore" \
            "Installation & Config" \
            "System Tools" \
            "Exit")

        case "$CHOICE" in
            "Container Operations")
                container_operations
                ;;
            "Backup & Restore")
                docker_backup_restore
                ;;
            "Installation & Config")
                docker_install_config_menu
                ;;
            "System Tools")
                advanced_system_tools_menu
                ;;
            "Exit")
                echo "👋 Goodbye!"
                exit 0
                ;;
        esac
    done
}

# Start the application
show_main_menu