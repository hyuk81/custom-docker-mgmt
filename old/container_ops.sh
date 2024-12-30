#!/usr/bin/env bash

# Helper function to run Docker commands with sudo if needed
docker_cmd() {
    if [ "${USE_SUDO:-false}" = true ]; then
        sudo docker "$@"
    else
        docker "$@"
    fi
}

container_operations() {
    while true; do
        CHOICE=$(gum choose \
            "List Containers" \
            "Start Container" \
            "Stop Container" \
            "Restart Container" \
            "Delete Container" \
            "Container Health" \
            "Back to Main Menu")

        case "$CHOICE" in
            "List Containers")    list_containers ;;
            "Start Container")    start_container ;;
            "Stop Container")     stop_container ;;
            "Restart Container")  restart_container ;;
            "Delete Container")   delete_container ;;
            "Container Health")   container_health ;;
            "Back to Main Menu")  return ;;
        esac
    done
}

list_containers() {
    echo "📋 Listing all containers..."
    if ! docker_cmd ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}"; then
        gum style --foreground 1 "Failed to list containers"
        return 1
    fi
    gum confirm "Press Enter to continue"
}

start_container() {
    local containers=$(docker_cmd ps -a --filter "status=exited" --format "{{.Names}}")
    if [ -z "$containers" ]; then
        gum style --foreground 3 "No stopped containers found"
        return
    fi

    local container=$(echo "$containers" | gum choose --header "Select container to start:")
    if [ -n "$container" ]; then
        echo "🚀 Starting container: $container"
        if docker_cmd start "$container"; then
            gum style --foreground 2 "Container started successfully"
        else
            gum style --foreground 1 "Failed to start container"
        fi
    fi
}

stop_container() {
    local containers=$(docker_cmd ps --format "{{.Names}}")
    if [ -z "$containers" ]; then
        gum style --foreground 3 "No running containers found"
        return
    fi

    local container=$(echo "$containers" | gum choose --header "Select container to stop:")
    if [ -n "$container" ]; then
        echo "🛑 Stopping container: $container"
        if docker_cmd stop "$container"; then
            gum style --foreground 2 "Container stopped successfully"
        else
            gum style --foreground 1 "Failed to stop container"
        fi
    fi
}

restart_container() {
    local containers=$(docker_cmd ps -a --format "{{.Names}}")
    if [ -z "$containers" ]; then
        gum style --foreground 3 "No containers found"
        return
    fi

    local container=$(echo "$containers" | gum choose --header "Select container to restart:")
    if [ -n "$container" ]; then
        echo "🔄 Restarting container: $container"
        if docker_cmd restart "$container"; then
            gum style --foreground 2 "Container restarted successfully"
        else
            gum style --foreground 1 "Failed to restart container"
        fi
    fi
}

delete_container() {
    local containers=$(docker_cmd ps -a --format "{{.Names}}")
    if [ -z "$containers" ]; then
        gum style --foreground 3 "No containers found"
        return
    fi

    local container=$(echo "$containers" | gum choose --header "Select container to delete:")
    if [ -n "$container" ]; then
        if gum confirm "Are you sure you want to delete $container?"; then
            echo "🗑️ Deleting container: $container"
            if docker_cmd rm -f "$container"; then
                gum style --foreground 2 "Container deleted successfully"
            else
                gum style --foreground 1 "Failed to delete container"
            fi
        fi
    fi
}

container_health() {
    local containers=$(docker_cmd ps --format "{{.Names}}")
    if [ -z "$containers" ]; then
        gum style --foreground 3 "No running containers found"
        return
    fi

    local container=$(echo "$containers" | gum choose --header "Select container to check health:")
    if [ -n "$container" ]; then
        echo "🏥 Checking health for container: $container"
        echo "Container Stats:"
        docker_cmd stats --no-stream "$container"
        echo -e "\nContainer Logs (last 10 lines):"
        docker_cmd logs --tail 10 "$container"
        gum confirm "Press Enter to continue"
    fi
}