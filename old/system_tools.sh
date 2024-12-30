#!/usr/bin/env bash

advanced_system_tools_menu() {
    # Check if user has sudo access
    if ! sudo -v; then
        gum style --foreground 1 "This script requires sudo access"
        return 1
    fi

    while true; do
        CHOICE=$(gum choose \
            "Show Docker Paths" \
            "Setup Docker Networks" \
            "Setup Docker Volumes" \
            "Back to Main Menu")

        case "$CHOICE" in
            "Show Docker Paths")     show_docker_paths ;;
            "Setup Docker Networks") setup_docker_networks ;;
            "Setup Docker Volumes")  setup_docker_volumes ;;
            "Back to Main Menu")     return ;;
        esac
    done
}

show_docker_paths() {
    echo "📂 Docker System Paths:"
    echo "Docker Root Dir: $(sudo docker info --format '{{.DockerRootDir}}')"
    echo "Container Config: /etc/docker"
    echo "Data Root: $(sudo docker info --format '{{.DataRoot}}')"
    echo -e "\n🔍 Docker Info:"
    sudo docker info --format '{{.Name}}: {{.ServerVersion}}'
    gum confirm "Press Enter to continue"
}

setup_docker_networks() {
    while true; do
        local ACTION=$(gum choose \
            "List Networks" \
            "Create Network" \
            "Delete Network" \
            "Back")

        case "$ACTION" in
            "List Networks")
                echo "📋 Current Docker Networks:"
                sudo docker network ls
                gum confirm "Press Enter to continue"
                ;;
            "Create Network")
                local name=$(gum input --placeholder "Enter network name")
                if [ -n "$name" ]; then
                    local driver=$(gum choose "bridge" "overlay" "host" "none")
                    echo "🌐 Creating network: $name (driver: $driver)"
                    if sudo docker network create --driver "$driver" "$name"; then
                        gum style --foreground 2 "Network created successfully"
                    else
                        gum style --foreground 1 "Failed to create network"
                    fi
                fi
                ;;
            "Delete Network")
                local networks=$(sudo docker network ls --format "{{.Name}}" | grep -v "bridge\|host\|none")
                if [ -z "$networks" ]; then
                    gum style --foreground 3 "No custom networks found"
                    continue
                fi
                local network=$(echo "$networks" | gum choose --header "Select network to delete:")
                if [ -n "$network" ]; then
                    if gum confirm "Are you sure you want to delete $network?"; then
                        if sudo docker network rm "$network"; then
                            gum style --foreground 2 "Network deleted successfully"
                        else
                            gum style --foreground 1 "Failed to delete network"
                        fi
                    fi
                fi
                ;;
            "Back")
                break
                ;;
        esac
    done
}

setup_docker_volumes() {
    while true; do
        local ACTION=$(gum choose \
            "List Volumes" \
            "Create Volume" \
            "Delete Volume" \
            "Back")

        case "$ACTION" in
            "List Volumes")
                echo "📋 Current Docker Volumes:"
                sudo docker volume ls
                gum confirm "Press Enter to continue"
                ;;
            "Create Volume")
                local name=$(gum input --placeholder "Enter volume name")
                if [ -n "$name" ]; then
                    echo "💾 Creating volume: $name"
                    if sudo docker volume create "$name"; then
                        gum style --foreground 2 "Volume created successfully"
                    else
                        gum style --foreground 1 "Failed to create volume"
                    fi
                fi
                ;;
            "Delete Volume")
                local volumes=$(sudo docker volume ls --format "{{.Name}}")
                if [ -z "$volumes" ]; then
                    gum style --foreground 3 "No volumes found"
                    continue
                fi
                local volume=$(echo "$volumes" | gum choose --header "Select volume to delete:")
                if [ -n "$volume" ]; then
                    if gum confirm "Are you sure you want to delete $volume?"; then
                        if sudo docker volume rm "$volume"; then
                            gum style --foreground 2 "Volume deleted successfully"
                        else
                            gum style --foreground 1 "Failed to delete volume"
                        fi
                    fi
                fi
                ;;
            "Back")
                break
                ;;
        esac
    done
}