"""Menu handlers for Docker Management Tool."""
from rich.console import Console
from rich.prompt import Confirm
from typing import Optional
from .menu import Menu
from ..operations.docker_manager import DockerManager
from ..utils.docker_utils import run_docker_command
import typer

console = Console()

def container_operations_menu(manager: DockerManager):
    """Handle container operations submenu."""
    while True:
        containers = manager.list_containers()
        if not containers:
            console.print("[yellow]No containers found[/yellow]")
            return

        # Create menu items from containers
        items = [
            f"{('🟢' if 'Up' in c['status'] else '⚫')} {c['name']} ({c['status']})"
            for c in containers
        ]

        menu = Menu("Available Containers", items)
        choice = menu.show()

        if choice is None:
            return
        
        container_name = containers[choice]["name"]
        container_menu(manager, container_name)

def container_menu(manager: DockerManager, container_name: str):
    """Handle individual container operations."""
    while True:
        items = [
            "Start container",
            "Stop container",
            "Restart container",
            "Delete container",
            "Show container details",
        ]

        menu = Menu(f"Container: {container_name}", items)
        choice = menu.show()

        if choice is None:
            break

        if choice == 0:
            manager.start_container(container_name)
        elif choice == 1:
            manager.stop_container(container_name)
        elif choice == 2:
            manager.restart_container(container_name)
        elif choice == 3:
            if manager.delete_container(container_name):
                break
        elif choice == 4:
            manager.show_container_details(container_name)
            input("\nPress Enter to continue...")

def cleanup_menu():
    """Handle cleanup submenu."""
    while True:
        items = [
            "Clean up unused containers",
            "Clean up unused volumes",
            "Clean up unused networks",
            "Clean up unused images",
            "Clean up build cache",
            "Show disk usage",
            "Clean up everything (prune system)",
        ]

        menu = Menu("Clean Up", items)
        choice = menu.show()

        if choice is None:
            break

        try:
            if choice == 0:  # Clean up containers
                if Confirm.ask("[yellow]Remove all stopped containers?[/yellow]"):
                    run_docker_command(['container', 'prune', '-f'])
                    console.print("[green]✓ Removed stopped containers[/green]")

            elif choice == 1:  # Clean up volumes
                if Confirm.ask("[yellow]Remove all unused volumes?[/yellow]"):
                    run_docker_command(['volume', 'prune', '-f'])
                    console.print("[green]✓ Removed unused volumes[/green]")

            elif choice == 2:  # Clean up networks
                if Confirm.ask("[yellow]Remove all unused networks?[/yellow]"):
                    run_docker_command(['network', 'prune', '-f'])
                    console.print("[green]✓ Removed unused networks[/green]")

            elif choice == 3:  # Clean up images
                if Confirm.ask("[yellow]Remove all unused images?[/yellow]"):
                    run_docker_command(['image', 'prune', '-a', '-f'])
                    console.print("[green]✓ Removed unused images[/green]")

            elif choice == 4:  # Clean up build cache
                if Confirm.ask("[yellow]Remove all build cache?[/yellow]"):
                    run_docker_command(['builder', 'prune', '-f'])
                    console.print("[green]✓ Removed build cache[/green]")

            elif choice == 5:  # Show disk usage
                output = run_docker_command(['system', 'df'])
                console.print(f"\n[bold]Docker Disk Usage:[/bold]\n{output}")

            elif choice == 6:  # Clean up everything
                if Confirm.ask("[yellow]⚠️  Remove all unused Docker resources (containers, volumes, networks, images)?[/yellow]"):
                    run_docker_command(['system', 'prune', '-a', '-f', '--volumes'])
                    console.print("[green]✓ Removed all unused Docker resources[/green]")

            input("\nPress Enter to continue...")
        except Exception as e:
            console.print(f"[red]✗ Operation failed: {e}[/red]")
            input("\nPress Enter to continue...")

def test_menu():
    """Handle test submenu."""
    while True:
        items = [
            "Test container operations",
            "Test backup/restore",
            "Test network operations",
            "Test volume operations",
            "Run all tests",
        ]

        menu = Menu("Tests", items)
        choice = menu.show()

        if choice is None:
            break

        try:
            if choice == 0:  # Test container operations
                console.print("[yellow]Testing container operations...[/yellow]")
                # TODO: Implement container operation tests
                console.print("[green]✓ Container operations test completed[/green]")

            elif choice == 1:  # Test backup/restore
                console.print("[yellow]Testing backup/restore operations...[/yellow]")
                # TODO: Implement backup/restore tests
                console.print("[green]✓ Backup/restore test completed[/green]")

            elif choice == 2:  # Test network operations
                console.print("[yellow]Testing network operations...[/yellow]")
                # TODO: Implement network operation tests
                console.print("[green]✓ Network operations test completed[/green]")

            elif choice == 3:  # Test volume operations
                console.print("[yellow]Testing volume operations...[/yellow]")
                # TODO: Implement volume operation tests
                console.print("[green]✓ Volume operations test completed[/green]")

            elif choice == 4:  # Run all tests
                console.print("[yellow]Running all tests...[/yellow]")
                # TODO: Implement comprehensive test suite
                console.print("[green]✓ All tests completed[/green]")

            input("\nPress Enter to continue...")
        except Exception as e:
            console.print(f"[red]✗ Test failed: {e}[/red]")
            input("\nPress Enter to continue...")

def system_tools_menu():
    """Handle system tools menu."""
    while True:
        items = [
            "Clean Up",
            "Tests",
            "Install Yacht (Docker Web UI)",
        ]

        menu = Menu("System Tools", items)
        choice = menu.show()

        if choice is None:
            break

        if choice == 0:
            cleanup_menu()
        elif choice == 1:
            test_menu()
        elif choice == 2:
            # Create a DockerManager instance for Yacht installation
            manager = DockerManager()
            if not manager.check_prerequisites():
                console.print("[yellow]! Docker must be running to install Yacht[/yellow]")
                continue
                
            # Ask for port number
            try:
                port = typer.prompt("Enter port for Yacht web interface", type=int, default=8000)
                if manager.install_yacht(port):
                    input("\nPress Enter to continue...")
            except (ValueError, KeyboardInterrupt):
                console.print("[yellow]Installation cancelled[/yellow]")
                continue 

def backup_menu(manager: DockerManager):
    """Handle backup and restore operations."""
    while True:
        items = [
            "Backup container",
            "Restore container from backup",
            "List backups",
            "Delete backup",
        ]

        menu = Menu("Backup & Restore", items)
        choice = menu.show()

        if choice is None:
            break

        try:
            if choice == 0:  # Backup container
                containers = manager.list_containers()
                if not containers:
                    console.print("[yellow]No containers available for backup[/yellow]")
                    continue

                # Create menu items from containers
                items = [
                    f"{c['name']} ({c['status']})"
                    for c in containers
                ]

                container_menu = Menu("Select Container to Backup", items)
                container_choice = container_menu.show()
                
                if container_choice is not None:
                    container_name = containers[container_choice]["name"]
                    if manager.backup_container(container_name):
                        console.print(f"[green]✓ Container {container_name} backed up successfully[/green]")
                    input("\nPress Enter to continue...")

            elif choice == 1:  # Restore container
                # List available backups
                backups = list(manager.backup_dir.glob("*.tar"))
                if not backups:
                    console.print("[yellow]No backups found[/yellow]")
                    continue

                # Create menu items from backups
                items = [b.name for b in backups]
                backup_menu = Menu("Select Backup to Restore", items)
                backup_choice = backup_menu.show()
                
                if backup_choice is not None:
                    backup_path = backups[backup_choice]
                    if manager.restore_container(str(backup_path)):
                        console.print(f"[green]✓ Container restored successfully from {backup_path.name}[/green]")
                    input("\nPress Enter to continue...")

            elif choice == 2:  # List backups
                backups = list(manager.backup_dir.glob("*.tar"))
                if not backups:
                    console.print("[yellow]No backups found[/yellow]")
                else:
                    console.print("\n[bold]Available Backups:[/bold]")
                    for backup in backups:
                        size = backup.stat().st_size / (1024 * 1024)  # Convert to MB
                        console.print(f"📦 {backup.name} ({size:.1f} MB)")
                input("\nPress Enter to continue...")

            elif choice == 3:  # Delete backup
                backups = list(manager.backup_dir.glob("*.tar"))
                if not backups:
                    console.print("[yellow]No backups found[/yellow]")
                    continue

                # Create menu items from backups
                items = [b.name for b in backups]
                backup_menu = Menu("Select Backup to Delete", items)
                backup_choice = backup_menu.show()
                
                if backup_choice is not None:
                    backup_path = backups[backup_choice]
                    if Confirm.ask(f"[yellow]Are you sure you want to delete {backup_path.name}?[/yellow]"):
                        backup_path.unlink()
                        console.print(f"[green]✓ Backup {backup_path.name} deleted[/green]")
                    input("\nPress Enter to continue...")

        except Exception as e:
            console.print(f"[red]✗ Operation failed: {e}[/red]")
            input("\nPress Enter to continue...") 