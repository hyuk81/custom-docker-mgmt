"""Main entry point for Docker Management Tool."""
import typer
from rich.console import Console
from pathlib import Path
from docker_mgmt.operations.docker_manager import DockerManager
from docker_mgmt.ui.menu import Menu
from docker_mgmt.ui.menu_handlers import (
    container_operations_menu,
    system_tools_menu,
    backup_menu,
    installation_menu,
)

app = typer.Typer()
console = Console()

@app.command()
def main(interactive: bool = typer.Option(False, "--interactive", "-i", help="Start interactive mode")):
    """Docker Management Tools"""
    if interactive:
        manager = DockerManager()
        # Don't return early if prerequisites check fails
        manager.check_prerequisites()

        while True:
            items = [
                "Container Operations",
                "Backup & Restore",
                "Installation & Config",
                "System Tools",
                "Exit"
            ]

            menu = Menu("Docker Management Tools", items)
            # Special case for main menu: don't show "Back"
            choice = menu.show(show_back=False)

            if choice is None or choice == 4:  # Exit
                console.print("\n👋 Goodbye!")
                break

            if choice == 0:
                if not manager.check_prerequisites():
                    console.print("[yellow]! Docker must be running to manage containers[/yellow]")
                    continue
                container_operations_menu(manager)
            elif choice == 1:
                if not manager.check_prerequisites():
                    console.print("[yellow]! Docker must be running to manage backups[/yellow]")
                    continue
                backup_menu(manager)
            elif choice == 2:
                installation_menu()
            elif choice == 3:
                system_tools_menu()

if __name__ == "__main__":
    app() 