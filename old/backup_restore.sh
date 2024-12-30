#!/usr/bin/env bash

BACKUP_DIR="${HOME}/.docker_backups"

docker_backup_restore() {
    # Check if user has sudo access
    if ! sudo -v; then
        gum style --foreground 1 "This script requires sudo access"
        return 1
    fi

    while true; do
        ACTION=$(gum choose \
            "Backup Container" \
            "Restore Container" \
            "Backup All Containers" \
            "System Backup" \
            "System Restore" \
            "List Backups" \
            "Delete Backup" \
            "Back to Main Menu")

        case "$ACTION" in
            "Backup Container")     backup_container_menu ;;
            "Restore Container")    restore_container_menu ;;
            "Backup All Containers") backup_all_containers ;;
            "System Backup")        backup_docker_config ;;
            "System Restore")       restore_docker_config ;;
            "List Backups")         list_backups ;;
            "Delete Backup")        delete_backup ;;
            "Back to Main Menu")    return ;;
        esac
    done
}

backup_container_menu() {
    local containers=$(sudo docker ps -a --format "{{.Names}}")
    if [ -z "$containers" ]; then
        gum style --foreground 3 "No containers found"
        return
    fi

    local container=$(echo "$containers" | gum choose --header "Select container to backup:")
    if [ -n "$container" ]; then
        backup_single_container "$container"
    fi
}

backup_single_container() {
    local container=$1
    mkdir -p "$BACKUP_DIR"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/${container}_${timestamp}.tar"
    
    echo "📦 Backing up container: $container"
    if sudo docker export "$container" > "$backup_file"; then
        sudo chown "$USER:$USER" "$backup_file"
        gum style --foreground 2 "Container backup successful: $backup_file"
    else
        gum style --foreground 1 "Failed to backup container"
        return 1
    fi
}

restore_container_menu() {
    local backups=$(ls -1 "$BACKUP_DIR"/*.tar 2>/dev/null)
    if [ -z "$backups" ]; then
        gum style --foreground 3 "No backups found in $BACKUP_DIR"
        return
    fi

    local backup=$(echo "$backups" | gum choose --header "Select backup to restore:")
    if [ -n "$backup" ]; then
        local new_name=$(gum input --placeholder "Enter new container name")
        if [ -n "$new_name" ]; then
            restore_container_backup "$backup" "$new_name"
        fi
    fi
}

restore_container_backup() {
    local backup_file=$1
    local new_name=$2
    
    echo "📦 Restoring container from backup: $backup_file"
    if sudo docker import "$backup_file" "$new_name"; then
        gum style --foreground 2 "Container restored successfully as $new_name"
    else
        gum style --foreground 1 "Failed to restore container"
        return 1
    fi
}

backup_all_containers() {
    local containers=$(sudo docker ps -a --format "{{.Names}}")
    if [ -z "$containers" ]; then
        gum style --foreground 3 "No containers found"
        return
    fi

    mkdir -p "$BACKUP_DIR"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local success=0
    local total=0

    echo "📦 Backing up all containers..."
    while read -r container; do
        ((total++))
        if backup_single_container "$container"; then
            ((success++))
        fi
    done <<< "$containers"

    gum style --foreground 2 "Backup complete: $success/$total containers backed up successfully"
}

backup_docker_config() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local config_backup="${BACKUP_DIR}/docker_config_${timestamp}.tar.gz"
    
    mkdir -p "$BACKUP_DIR"
    echo "💾 Backing up Docker configuration..."
    
    if sudo tar -czf "$config_backup" -C / etc/docker 2>/dev/null; then
        sudo chown "$USER:$USER" "$config_backup"
        gum style --foreground 2 "Docker configuration backed up successfully: $config_backup"
    else
        gum style --foreground 1 "Failed to backup Docker configuration"
    fi
}

restore_docker_config() {
    local backups=$(ls -1 "$BACKUP_DIR"/docker_config_*.tar.gz 2>/dev/null)
    if [ -z "$backups" ]; then
        gum style --foreground 3 "No configuration backups found"
        return
    fi

    local backup=$(echo "$backups" | gum choose --header "Select configuration backup to restore:")
    if [ -n "$backup" ] && gum confirm "Are you sure you want to restore this configuration?"; then
        echo "💾 Restoring Docker configuration..."
        if sudo tar -xzf "$backup" -C /; then
            gum style --foreground 2 "Docker configuration restored successfully"
            gum style --foreground 3 "Please restart Docker daemon to apply changes"
        else
            gum style --foreground 1 "Failed to restore Docker configuration"
        fi
    fi
}

list_backups() {
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]; then
        gum style --foreground 3 "No backups found"
        return
    fi

    echo "📋 Available Backups:"
    ls -lh "$BACKUP_DIR"
    gum confirm "Press Enter to continue"
}

delete_backup() {
    local backups=$(ls -1 "$BACKUP_DIR"/* 2>/dev/null)
    if [ -z "$backups" ]; then
        gum style --foreground 3 "No backups found"
        return
    fi

    local backup=$(echo "$backups" | gum choose --header "Select backup to delete:")
    if [ -n "$backup" ] && gum confirm "Are you sure you want to delete this backup?"; then
        if rm "$backup"; then
            gum style --foreground 2 "Backup deleted successfully"
        else
            gum style --foreground 1 "Failed to delete backup"
        fi
    fi
}

# etc.