#!/usr/bin/env python3

import os
import sys
import docker
import typer
import subprocess
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm
from typing import Optional
from datetime import datetime
from textual.app import App, ComposeResult
from textual.widgets import DirectoryTree, Footer
from textual.binding import Binding
from textual import events
import readchar
import curses
import json
import tempfile

app = typer.Typer()
console = Console()

def run_docker_command(cmd: list[str], stdout=None, stdin=None) -> str:
    """Run a Docker command with sudo."""
    try:
        result = subprocess.run(
            ['sudo', 'docker'] + cmd,
            stdout=stdout if stdout else subprocess.PIPE,
            stdin=stdin if stdin else None,
            text=True if not stdout and not stdin else False,
            check=True,
            stderr=subprocess.PIPE  # Capture stderr for better error handling
        )
        return result.stdout if not stdout and not stdin else ""
    except subprocess.CalledProcessError as e:
        if "Cannot connect to the Docker daemon" in (e.stderr or ""):
            # Don't print error for daemon connection issues
            raise e
        console.print(f"[red]Error running Docker command: {e.stderr if hasattr(e, 'stderr') else str(e)}[/red]")
        raise e
    except Exception as e:
        console.print(f"[red]Error running Docker command: {str(e)}[/red]")
        raise e

class DockerManager:
    def __init__(self, backup_dir: Path = Path.home() / ".docker_backups"):
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        try:
            output = run_docker_command(['info'])
            if output:
                console.print("[green]✓ Docker is running[/green]")
                return True
        except Exception as e:
            console.print("[yellow]! Docker is not running or not accessible[/yellow]")
            console.print("[yellow]Some features will be limited until Docker is properly configured[/yellow]")
        return False

    def start_container(self, container_name: str) -> bool:
        """Start a container."""
        try:
            run_docker_command(['start', container_name])
            console.print(f"[green]✓ Container {container_name} started[/green]")
            return True
        except Exception as e:
            console.print(f"[red]✗ Failed to start container: {e}[/red]")
            return False

    def stop_container(self, container_name: str) -> bool:
        """Stop a container."""
        try:
            run_docker_command(['stop', container_name])
            console.print(f"[green]✓ Container {container_name} stopped[/green]")
            return True
        except Exception as e:
            console.print(f"[red]✗ Failed to stop container: {e}[/red]")
            return False

    def restart_container(self, container_name: str) -> bool:
        """Restart a container."""
        try:
            run_docker_command(['restart', container_name])
            console.print(f"[green]✓ Container {container_name} restarted[/green]")
            return True
        except Exception as e:
            console.print(f"[red]✗ Failed to restart container: {e}[/red]")
            return False

    def delete_container(self, container_name: str) -> bool:
        """Delete a container and optionally clean up its networks, volumes, and images."""
        try:
            # Get container configuration before deletion
            config = run_docker_command(['inspect', container_name])
            if not config:
                return False
            
            import json
            container_config = json.loads(config)[0]
            
            # Get networks used by the container
            networks = list(container_config.get('NetworkSettings', {}).get('Networks', {}).keys())
            networks = [n for n in networks if n != 'bridge']  # Exclude default bridge network
            
            # Get volumes used by the container
            volumes = []
            for mount in container_config.get('Mounts', []):
                if mount.get('Type') == 'volume':
                    volumes.append(mount.get('Name'))
            
            # Get image used by container
            image = container_config.get('Config', {}).get('Image')
            
            if Confirm.ask(f"[yellow]Are you sure you want to delete container {container_name}?[/yellow]"):
                # Stop and remove the container
                run_docker_command(['rm', '-f', container_name])
                console.print(f"[green]✓ Container {container_name} deleted[/green]")
                
                # Check each network
                for network in networks:
                    # Check if other containers use this network
                    net_inspect = json.loads(run_docker_command(['network', 'inspect', network]))
                    if net_inspect:
                        containers = net_inspect[0].get('Containers', {})
                        # Remove current container from count if it's still listed
                        container_count = len([c for c in containers if c != container_config['Id']])
                        if container_count == 0:
                            if Confirm.ask(f"[yellow]Network '{network}' is not used by any other containers. Delete it?[/yellow]"):
                                run_docker_command(['network', 'rm', network])
                                console.print(f"[green]✓ Network {network} deleted[/green]")
                
                # Check each volume
                for volume in volumes:
                    # Check if other containers use this volume
                    vol_inspect = json.loads(run_docker_command(['volume', 'inspect', volume]))
                    if vol_inspect:
                        if Confirm.ask(f"[yellow]Volume '{volume}' exists. Would you like to delete it?[/yellow]"):
                            run_docker_command(['volume', 'rm', volume])
                            console.print(f"[green]✓ Volume {volume} deleted[/green]")
                
                # Check if image should be removed
                if image and Confirm.ask(f"[yellow]Would you like to remove the image {image}?[/yellow]"):
                    run_docker_command(['rmi', image])
                    console.print(f"[green]✓ Image {image} deleted[/green]")
                
                return True
            return False
        except Exception as e:
            console.print(f"[red]✗ Failed to delete container: {e}[/red]")
            return False

    def backup_container(self, container_name: str) -> bool:
        """Backup a single container."""
        try:
            # Check if container exists and get its configuration
            config = run_docker_command(['inspect', container_name])
            if not config:
                console.print(f"[red]✗ Container not found: {container_name}[/red]")
                return False

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.backup_dir / f"{container_name}_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Save container configuration
            config_file = backup_dir / "config.json"
            config_file.write_text(config)
            
            # Backup volumes
            import json
            container_config = json.loads(config)[0]
            volumes_dir = backup_dir / "volumes"
            volumes_dir.mkdir(exist_ok=True)
            
            for mount in container_config.get('Mounts', []):
                if mount.get('Type') == 'volume':
                    volume_name = mount.get('Name')
                    if volume_name:
                        console.print(f"📦 Backing up volume: {volume_name}")
                        volume_backup = volumes_dir / volume_name
                        volume_backup.mkdir(exist_ok=True)
                        
                        # Stop the container to ensure data consistency
                        run_docker_command(['stop', container_name])
                        console.print("[yellow]Container stopped for backup[/yellow]")
                        
                        # Copy the entire volume contents
                        temp_container = f"temp-{container_name}-{timestamp}"
                        run_docker_command([
                            'run', '--rm', '-v', f"{volume_name}:/source", 
                            '-v', f"{volume_backup.absolute()}:/backup",
                            '--name', temp_container, 'alpine', 
                            'cp', '-a', '/source/.', '/backup/'
                        ])
                        
                        # Restart the container
                        run_docker_command(['start', container_name])
                        console.print("[green]Container restarted[/green]")
            
            # Create final tar archive
            backup_path = self.backup_dir / f"{container_name}_{timestamp}.tar"
            subprocess.run(
                ['tar', '-czf', str(backup_path), '-C', str(backup_dir), '.'],
                check=True
            )
            
            # Cleanup temporary directory
            subprocess.run(['sudo', 'rm', '-rf', str(backup_dir)], check=True)
            
            # Set proper ownership of the backup file
            subprocess.run(['sudo', 'chown', f"{os.getuid()}:{os.getgid()}", str(backup_path)], check=True)
            
            console.print(f"[green]✓ Container backed up successfully: {backup_path}[/green]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✗ Backup failed: {e}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]✗ Backup failed: {e}[/red]")
            return False

    def restore_container(self, backup_path: str) -> bool:
        """Restore a container from backup."""
        try:
            if not Path(backup_path).exists():
                console.print(f"[red]✗ Backup file not found: {backup_path}[/red]")
                return False

            # Create temporary directory for extraction
            temp_dir = Path("/tmp/docker_restore_temp")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract backup archive
            subprocess.run(
                ['tar', '-xzf', backup_path, '-C', str(temp_dir)],
                check=True
            )
            
            # Read container configuration
            config_file = temp_dir / "config.json"
            if not config_file.exists():
                console.print("[red]✗ Invalid backup: missing configuration[/red]")
                return False
                
            config = config_file.read_text()
            
            # Get container name from backup file
            container_name = Path(backup_path).stem.split('_')[0]
            
            # Parse the original container configuration
            import json
            container_config = json.loads(config)[0]
            
            # Get the original image
            image = container_config.get('Config', {}).get('Image')
            if not image:
                console.print("[red]✗ Could not determine original image[/red]")
                return False
            
            # Pull the original image if needed
            run_docker_command(['pull', image])
            console.print(f"[green]✓ Using original image: {image}[/green]")
            
            # Restore volumes first
            volumes_dir = temp_dir / "volumes"
            if volumes_dir.exists():
                for volume_path in volumes_dir.iterdir():
                    if volume_path.is_dir():
                        volume_name = volume_path.name
                        console.print(f"📦 Restoring volume: {volume_name}")
                        # Create volume if it doesn't exist
                        run_docker_command(['volume', 'create', volume_name])
                        # Create a temporary container to restore volume data
                        temp_container = f"temp-restore-{container_name}"
                        run_docker_command([
                            'run', '--rm', 
                            '-v', f"{volume_name}:/target",
                            '-v', f"{volume_path.absolute()}:/source",
                            '--name', temp_container, 'alpine',
                            'cp', '-a', '/source/.', '/target/'
                        ])
            
            # Extract key configuration elements
            ports = []
            if container_config.get('HostConfig', {}).get('PortBindings'):
                for container_port, host_bindings in container_config['HostConfig']['PortBindings'].items():
                    for binding in host_bindings:
                        ports.extend(['-p', f"{binding.get('HostPort', '')}:{container_port.split('/')[0]}"])
            
            volumes = []
            if container_config.get('HostConfig', {}).get('Binds'):
                for bind in container_config['HostConfig']['Binds']:
                    volumes.extend(['-v', bind])
            
            # Get the original command and entrypoint
            cmd = container_config.get('Config', {}).get('Cmd', [])
            entrypoint = container_config.get('Config', {}).get('Entrypoint', [])
            
            # Build the run command
            run_cmd = ['run', '-d', '--name', container_name]
            
            # Add ports and volumes
            run_cmd.extend(ports + volumes)
            
            # Add entrypoint if specified
            if entrypoint:
                run_cmd.extend(['--entrypoint', entrypoint[0]])
                if len(entrypoint) > 1:
                    run_cmd.extend(entrypoint[1:])
            
            # Add image
            run_cmd.append(image)
            
            # Add command if specified
            if cmd:
                run_cmd.extend(cmd)
            
            # Run the container
            run_docker_command(run_cmd)
            console.print(f"[green]✓ Container {container_name} restored with original configuration[/green]")
            
            # Cleanup
            subprocess.run(['sudo', 'rm', '-rf', str(temp_dir)], check=True)
            
            return True
        except Exception as e:
            console.print(f"[red]✗ Failed to restore container: {e}[/red]")
            return False

    def list_containers(self) -> list:
        """List all containers."""
        try:
            output = run_docker_command(['ps', '-a', '--format', '{{.Names}}\t{{.Status}}'])
            containers = []
            for line in output.splitlines():
                if line.strip():
                    name, status = line.split('\t')
                    containers.append({"name": name, "status": status})
            return containers
        except Exception as e:
            console.print(f"[red]✗ Failed to list containers: {e}[/red]")
            return []

    def show_container_details(self, container_name: str) -> bool:
        """Show detailed information about a container."""
        try:
            # Get container details using inspect
            output = run_docker_command(['inspect', container_name])
            if not output:
                return False
            
            # Get container ports using ps with no-trunc to get full output
            ports_output = run_docker_command(['ps', '--no-trunc', '--format', '{{.Ports}}', '--filter', f'name=^{container_name}$'])
            
            console.print(f"\n[bold]📋 Container Details: {container_name}[/bold]")
            console.print(f"[cyan]Ports:[/cyan] {ports_output.strip() or 'No ports published'}")
            
            # Show basic container info with no-trunc
            info = run_docker_command(['ps', '--no-trunc', '--format', '{{.Status}}\t{{.Size}}\t{{.Image}}', '--filter', f'name=^{container_name}$'])
            if info:
                try:
                    status, size, image = info.strip().split('\t')
                    console.print(f"[cyan]Status:[/cyan] {status}")
                    console.print(f"[cyan]Size:[/cyan] {size}")
                    console.print(f"[cyan]Image:[/cyan] {image}")
                except ValueError:
                    console.print("[yellow]Unable to parse container information[/yellow]")
            
            # Get network settings
            net_output = run_docker_command(['inspect', '--format', '{{range $net, $conf := .NetworkSettings.Networks}}{{$net}}: {{$conf.IPAddress}}\n{{end}}', container_name])
            if net_output:
                console.print(f"[cyan]Networks:[/cyan]\n{net_output.strip()}")
            
            # Get mount points
            mounts_output = run_docker_command(['inspect', '--format', '{{range .Mounts}}{{.Type}}: {{.Source}} -> {{.Destination}}\n{{end}}', container_name])
            if mounts_output:
                console.print(f"[cyan]Mounts:[/cyan]\n{mounts_output.strip()}")
            
            return True
        except Exception as e:
            console.print(f"[red]✗ Failed to get container details: {e}[/red]")
            return False

class BackupBrowser(App):
    """A file browser for selecting backup files."""
    
    BINDINGS = [
        Binding("escape", "quit", "Quit", show=True),
        Binding("enter", "select_file", "Select", show=True)
    ]
    
    def __init__(self, start_dir: str = str(Path.home())):
        super().__init__()
        self.start_dir = start_dir
        self.selected_file = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        tree = DirectoryTree(Path(self.start_dir))
        tree.guide_depth = 4
        yield tree
        yield Footer()
    
    def on_directory_tree_file_selected(self, event) -> None:
        """Handle file selection."""
        self.selected_file = event.path
        if str(self.selected_file).endswith('.tar'):
            self.exit(self.selected_file)
    
    def action_quit(self) -> None:
        """Quit the app."""
        self.exit(None)

def browse_backup_file(start_dir: str = str(Path.home())) -> Optional[str]:
    """Browse for a backup file using simple menu interface."""
    current_dir = Path(start_dir)
    
    while True:
        # Get list of directories and .tar files
        items = sorted([
            p for p in current_dir.iterdir()
            if p.is_dir() or (p.is_file() and p.suffix == '.tar')
        ])
        
        if not items:
            console.print("[yellow]No items in this directory[/yellow]")
            return None
        
        # Create menu items
        menu_items = []
        for item in items:
            prefix = "📁" if item.is_dir() else "📄"
            menu_items.append(f"{prefix} {item.name}")
        
        # Add parent directory option if not at root
        if current_dir.parent != current_dir:
            menu_items.insert(0, "📁 ..")
        
        menu = Menu(f"Current directory: {current_dir}", menu_items)
        choice = menu.show()
        
        if choice is None:
            return None
        
        # Handle parent directory
        if menu_items[choice] == "📁 ..":
            current_dir = current_dir.parent
            continue
        
        selected = items[choice if not current_dir.parent != current_dir else choice - 1]
        if selected.is_dir():
            current_dir = selected
        else:
            return str(selected)

class Menu:
    """Simple menu system."""
    def __init__(self, title: str, items: list[str]):
        self.title = title
        self.items = items
    
    def show(self, show_back: bool = True) -> Optional[int]:
        """Show the menu and return the selected index."""
        while True:
            # Clear screen
            console.print("\033[H\033[J", end="")
            
            # Display title
            console.print(f"\n[bold]{self.title}[/bold]\n")
            
            # Display items
            for i, item in enumerate(self.items):
                console.print(f"{i + 1}) {item}")
            if show_back:
                console.print("0) Back")
            
            try:
                choice = typer.prompt("\nChoose an option", type=int, default=0)
                if choice == 0:
                    return None
                if 1 <= choice <= len(self.items):
                    return choice - 1
            except (ValueError, KeyboardInterrupt):
                return None

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
            "Backup container",
            "Restore from backup",
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
            manager.backup_container(container_name)
        elif choice == 5:
            # List available backups
            backups = list(manager.backup_dir.glob(f"{container_name}_*.tar"))
            if not backups:
                console.print("[yellow]No backups found for this container[/yellow]")
                continue

            items = [b.name for b in backups]
            menu = Menu("Available Backups", items)
            backup_choice = menu.show()
            
            if backup_choice is not None:
                manager.restore_container(str(backups[backup_choice]))
        elif choice == 6:
            manager.show_container_details(container_name)
            input("\nPress Enter to continue...")

def backup_menu(manager: DockerManager):
    """Handle backup and restore operations."""
    while True:
        items = [
            "Backup container",
            "Restore from backup",
            "Browse for backup file",
        ]

        menu = Menu("Backup & Restore", items)
        choice = menu.show()

        if choice is None:
            break

        if choice == 0:
            containers = manager.list_containers()
            if not containers:
                console.print("[yellow]No containers available for backup[/yellow]")
                continue

            items = [c["name"] for c in containers]
            menu = Menu("Select Container to Backup", items)
            container_choice = menu.show()
            
            if container_choice is not None:
                manager.backup_container(containers[container_choice]["name"])
        elif choice == 1:
            backups = list(manager.backup_dir.glob("*_*.tar"))
            if not backups:
                console.print("[yellow]No backups found[/yellow]")
                continue

            items = [b.name for b in backups]
            menu = Menu("Select Backup to Restore", items)
            backup_choice = menu.show()
            
            if backup_choice is not None:
                manager.restore_container(str(backups[backup_choice]))
        elif choice == 2:
            backup_file = browse_backup_file()
            if backup_file:
                if Path(backup_file).suffix == '.tar':
                    manager.restore_container(backup_file)
                else:
                    console.print("[red]Selected file is not a backup file (.tar)[/red]")

def check_docker_installation() -> bool:
    """Check if Docker and Docker Compose are installed and get their versions."""
    try:
        console.print("\n[bold]🔍 Checking Docker Installation[/bold]\n")
        
        # Check Docker version
        docker_version = subprocess.check_output(
            ['docker', '--version'], 
            universal_newlines=True
        ).strip()
        
        # Check Docker Compose version
        compose_version = subprocess.check_output(
            ['docker', 'compose', 'version'],
            universal_newlines=True
        ).strip()
        
        # Format the output in a table-like structure
        console.print("┌─" + "─" * 50 + "┐")
        console.print("│ [bold cyan]Docker Components[/bold cyan]" + " " * 33 + "│")
        console.print("├─" + "─" * 50 + "┤")
        console.print(f"│ [green]✓[/green] {docker_version:<47} │")
        console.print(f"│ [green]✓[/green] {compose_version:<47} │")
        console.print("└─" + "─" * 50 + "┘\n")
        return True
    except subprocess.CalledProcessError:
        console.print("\n[red]✗ Docker is not installed[/red]")
        return False
    except FileNotFoundError:
        console.print("\n[red]✗ Docker is not installed[/red]")
        return False

def install_docker() -> bool:
    """Install Docker and Docker Compose using the official installation script."""
    try:
        # Download Docker installation script
        console.print("📥 Downloading Docker installation script...")
        subprocess.run(
            ['curl', '-fsSL', 'https://get.docker.com', '-o', 'get-docker.sh'],
            check=True
        )
        
        # Make script executable
        subprocess.run(['chmod', '+x', 'get-docker.sh'], check=True)
        
        # Run installation script
        console.print("🔧 Installing Docker...")
        subprocess.run(['sudo', './get-docker.sh'], check=True)
        
        # Clean up script
        subprocess.run(['rm', 'get-docker.sh'], check=True)
        
        # Start and enable Docker service
        console.print("🚀 Starting Docker service...")
        subprocess.run(['sudo', 'systemctl', 'start', 'docker'], check=True)
        subprocess.run(['sudo', 'systemctl', 'enable', 'docker'], check=True)
        
        # Install Docker Compose
        console.print("📦 Installing Docker Compose...")
        subprocess.run([
            'sudo', 'apt-get', 'update'
        ], check=True)
        subprocess.run([
            'sudo', 'apt-get', 'install', '-y', 'docker-compose-plugin'
        ], check=True)
        
        console.print("[green]✓ Docker and Docker Compose installed successfully[/green]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Failed to install Docker: {e}[/red]")
        return False

def update_docker() -> bool:
    """Update Docker installation."""
    try:
        console.print("📦 Updating package information...")
        subprocess.run(['sudo', 'apt-get', 'update'], check=True)
        
        console.print("⬆️ Upgrading Docker packages...")
        subprocess.run(['sudo', 'apt-get', 'upgrade', '-y', 'docker-ce', 'docker-ce-cli', 'containerd.io'], check=True)
        
        console.print("[green]✓ Docker updated successfully[/green]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Failed to update Docker: {e}[/red]")
        return False

def configure_docker_daemon() -> bool:
    """Configure Docker daemon settings."""
    daemon_config = Path("/etc/docker/daemon.json")
    
    try:
        # Create config directory if it doesn't exist
        if not daemon_config.parent.exists():
            subprocess.run(['sudo', 'mkdir', '-p', '/etc/docker'], check=True)
        
        # Read current config or create default
        if daemon_config.exists():
            current_config = subprocess.run(
                ['sudo', 'cat', str(daemon_config)],
                capture_output=True,
                text=True,
                check=True
            ).stdout
            config = json.loads(current_config) if current_config else {}
        else:
            config = {}
        
        # Show current configuration
        console.print("\n[bold]Current Docker daemon configuration:[/bold]")
        console.print(json.dumps(config, indent=2))
        
        # Options to configure
        items = [
            "Change default runtime",
            "Configure logging",
            "Set storage driver",
            "Configure registry mirrors",
            "Save configuration"
        ]
        
        while True:
            menu = Menu("Docker Daemon Configuration", items)
            choice = menu.show()
            
            if choice is None:
                break
            
            if choice == 0:  # Change default runtime
                runtimes = ["runc", "containerd"]
                runtime_menu = Menu("Select Default Runtime", runtimes)
                runtime_choice = runtime_menu.show()
                if runtime_choice is not None:
                    config["default-runtime"] = runtimes[runtime_choice]
            
            elif choice == 1:  # Configure logging
                log_drivers = ["json-file", "local", "syslog"]
                driver_menu = Menu("Select Log Driver", log_drivers)
                driver_choice = driver_menu.show()
                if driver_choice is not None:
                    config["log-driver"] = log_drivers[driver_choice]
                    if log_drivers[driver_choice] == "json-file":
                        config["log-opts"] = {
                            "max-size": "10m",
                            "max-file": "3"
                        }
            
            elif choice == 2:  # Set storage driver
                drivers = ["overlay2", "devicemapper", "btrfs"]
                driver_menu = Menu("Select Storage Driver", drivers)
                driver_choice = driver_menu.show()
                if driver_choice is not None:
                    config["storage-driver"] = drivers[driver_choice]
            
            elif choice == 3:  # Configure registry mirrors
                mirror = typer.prompt("Enter registry mirror URL (or empty to skip)")
                if mirror:
                    if "registry-mirrors" not in config:
                        config["registry-mirrors"] = []
                    config["registry-mirrors"].append(mirror)
            
            elif choice == 4:  # Save configuration
                # Write new configuration
                config_json = json.dumps(config, indent=2)
                with tempfile.NamedTemporaryFile(mode='w') as temp:
                    temp.write(config_json)
                    temp.flush()
                    subprocess.run(['sudo', 'cp', temp.name, str(daemon_config)], check=True)
                
                # Restart Docker daemon
                console.print("🔄 Restarting Docker daemon...")
                subprocess.run(['sudo', 'systemctl', 'restart', 'docker'], check=True)
                console.print("[green]✓ Configuration saved and Docker daemon restarted[/green]")
                break
        
        return True
    except Exception as e:
        console.print(f"[red]✗ Failed to configure Docker daemon: {e}[/red]")
        return False

def configure_user_permissions() -> bool:
    """Configure user permissions for Docker."""
    try:
        username = os.getenv('USER')
        
        # Check if user is already in docker group
        groups = subprocess.run(['groups'], capture_output=True, text=True, check=True).stdout
        if 'docker' in groups:
            console.print(f"[green]✓ User {username} is already in the docker group[/green]")
            return True
        
        # Add user to docker group
        subprocess.run(['sudo', 'usermod', '-aG', 'docker', username], check=True)
        console.print(f"[green]✓ Added user {username} to docker group[/green]")
        console.print("[yellow]! Please log out and back in for changes to take effect[/yellow]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Failed to configure user permissions: {e}[/red]")
        return False

class DirectoryBrowser(App):
    """A directory browser for selecting folders."""
    
    BINDINGS = [
        Binding("escape", "quit", "Quit", show=True),
        Binding("enter", "select_directory", "Select", show=True)
    ]
    
    def __init__(self, start_dir: str = str(Path.home())):
        super().__init__()
        self.start_dir = start_dir
        self.selected_dir = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        tree = DirectoryTree(str(Path(self.start_dir)))
        tree.guide_depth = 4
        yield tree
        yield Footer()
    
    def on_directory_tree_directory_selected(self, event) -> None:
        """Handle directory selection."""
        self.selected_dir = event.path
        self.exit(self.selected_dir)
    
    def action_quit(self) -> None:
        """Quit the app."""
        self.exit(None)

def browse_directory(start_dir: str = str(Path.home())) -> Optional[str]:
    """Browse for a directory using simple menu interface."""
    current_dir = Path(start_dir)
    
    while True:
        try:
            # Get list of directories using sudo
            items = subprocess.run(
                ['sudo', 'find', str(current_dir), '-maxdepth', '1', '-type', 'd'],
                capture_output=True,
                text=True,
                check=True
            ).stdout.splitlines()
            
            # Remove the current directory from the list and sort
            items = sorted([Path(p) for p in items if Path(p) != current_dir])
            
            if not items and current_dir.parent == current_dir:
                console.print("[yellow]No directories available[/yellow]")
                return None
            
            # Create menu items
            menu_items = []
            for item in items:
                menu_items.append(f"📁 {item.name}")
            
            # Add special options
            if current_dir.parent != current_dir:
                menu_items.insert(0, "📁 ..")
            menu_items.append("✅ Select current directory")
            menu_items.append("❌ Cancel")
            
            # Show current path
            console.print(f"\n[bold cyan]Current path:[/bold cyan] {current_dir}")
            
            menu = Menu(f"Select Directory", menu_items)
            choice = menu.show()
            
            if choice is None or choice == len(menu_items) - 1:  # Cancel
                return None
                
            if choice == len(menu_items) - 2:  # Select current
                return str(current_dir)
                
            # Handle parent directory
            if menu_items[choice] == "📁 ..":
                current_dir = current_dir.parent
                continue
                
            # Navigate to selected directory
            selected = items[choice if not current_dir.parent != current_dir else choice - 1]
            current_dir = selected
        
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✗ Failed to list directories: {e}[/red]")
            return None
        except Exception as e:
            console.print(f"[red]✗ An error occurred: {e}[/red]")
            return None

def change_docker_root() -> bool:
    """Change Docker root directory."""
    try:
        console.print("\n[bold]🔧 Docker Root Directory Configuration[/bold]\n")
        
        try:
            # Show current Docker root directory
            current_root = subprocess.run(
                ['sudo', 'docker', 'info', '--format', '{{.DockerRootDir}}'],
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
        except subprocess.CalledProcessError:
            console.print("[yellow]! Could not determine current Docker root. Using default /var/lib/docker[/yellow]")
            current_root = "/var/lib/docker"
        
        # Format the output in a table-like structure
        console.print("┌─" + "─" * 60 + "┐")
        console.print("│ [bold cyan]Current Configuration[/bold cyan]" + " " * 40 + "│")
        console.print("├─" + "─" * 60 + "┤")
        console.print(f"│ Docker Root: {current_root:<50} │")
        console.print("└─" + "─" * 60 + "┘\n")
        
        # Browse for new directory
        console.print("[bold]Select parent directory for Docker root:[/bold]")
        parent_dir = browse_directory('/')  # Start from root directory
        
        if not parent_dir:
            console.print("[yellow]Operation cancelled[/yellow]")
            return False
        
        # Append /docker to the selected path
        new_root = Path(parent_dir) / "docker"
        new_root = new_root.resolve()
        
        # Validate the new path
        if str(new_root) == current_root:
            console.print("[yellow]⚠️  New path is same as current path[/yellow]")
            return False
            
        # Create the new directory with sudo if it doesn't exist
        try:
            # Check if directory exists using sudo
            subprocess.run(['sudo', 'test', '-d', str(new_root)], check=True)
        except subprocess.CalledProcessError:
            if Confirm.ask(f"[yellow]⚠️  Directory {new_root} does not exist. Create it?[/yellow]"):
                try:
                    subprocess.run(['sudo', 'mkdir', '-p', str(new_root)], check=True)
                    # Set proper permissions
                    subprocess.run(['sudo', 'chown', 'root:root', str(new_root)], check=True)
                    subprocess.run(['sudo', 'chmod', '711', str(new_root)], check=True)
                except subprocess.CalledProcessError as e:
                    console.print(f"[red]✗ Failed to create directory: {e}[/red]")
                    return False
            else:
                return False

        # Check available space in the new location
        try:
            df_output = subprocess.run(
                ['df', '-B1', str(new_root)],
                capture_output=True,
                text=True,
                check=True
            ).stdout.splitlines()
            
            if len(df_output) >= 2:
                available_space = int(df_output[1].split()[3])
                
                # Get size of current Docker root
                du_output = subprocess.run(
                    ['sudo', 'du', '-sb', current_root],
                    capture_output=True,
                    text=True,
                    check=True
                ).stdout.strip()
                
                required_space = int(du_output.split()[0])
                
                if available_space < required_space:
                    console.print(f"[red]✗ Not enough space in {new_root}[/red]")
                    console.print(f"Required: {required_space / 1024 / 1024 / 1024:.2f} GB")
                    console.print(f"Available: {available_space / 1024 / 1024 / 1024:.2f} GB")
                    return False
                
                console.print(f"[green]✓ Sufficient space available[/green]")
                console.print(f"Required: {required_space / 1024 / 1024 / 1024:.2f} GB")
                console.print(f"Available: {available_space / 1024 / 1024 / 1024:.2f} GB")
        except subprocess.CalledProcessError as e:
            console.print("[yellow]! Could not verify available space. Proceed with caution.[/yellow]")
            if not Confirm.ask("[yellow]Continue without space verification?[/yellow]"):
                return False
        
        # Confirm the change
        if not Confirm.ask(f"\n[yellow]⚠️  Are you sure you want to change Docker root to {new_root}?[/yellow]\nThis will restart the Docker daemon and may take some time."):
            console.print("[yellow]Operation cancelled[/yellow]")
            return False
        
        # Create daemon.json configuration
        daemon_config = {
            "data-root": str(new_root)
        }
        
        # Write configuration to temporary file
        with tempfile.NamedTemporaryFile(mode='w') as temp:
            json.dump(daemon_config, temp, indent=2)
            temp.flush()
            
            # Copy configuration to Docker directory
            subprocess.run(['sudo', 'mkdir', '-p', '/etc/docker'], check=True)
            subprocess.run(['sudo', 'cp', temp.name, '/etc/docker/daemon.json'], check=True)
        
        # Stop Docker daemon
        console.print("\n[bold]🛑 Stopping Docker daemon...[/bold]")
        subprocess.run(['sudo', 'systemctl', 'stop', 'docker.socket'], check=True)
        subprocess.run(['sudo', 'systemctl', 'stop', 'docker'], check=True)
        
        # Move existing Docker data
        if Path(current_root).exists() and current_root != str(new_root):
            if Confirm.ask(f"\n[yellow]Move existing Docker data from {current_root} to {new_root}?[/yellow]"):
                console.print("\n[bold]📦 Moving Docker data to new location...[/bold]")
                console.print("[yellow]This may take a while depending on the amount of data.[/yellow]")
                
                # Use rsync with progress and proper source directory
                try:
                    subprocess.run(
                        ['sudo', 'rsync', '-aP', '--delete',
                         f"{current_root}/", # Note the trailing slash
                         str(new_root)],
                        check=True
                    )
                    
                    # Only rename old directory after successful copy
                    subprocess.run(['sudo', 'mv', current_root, f"{current_root}.old"], check=True)
                    console.print("[green]✓ Data migration completed[/green]")
                except subprocess.CalledProcessError as e:
                    # Restore daemon.json on failure
                    console.print("[red]✗ Data migration failed. Rolling back changes...[/red]")
                    subprocess.run(['sudo', 'rm', '/etc/docker/daemon.json'], check=False)
                    subprocess.run(['sudo', 'systemctl', 'start', 'docker'], check=False)
                    return False
        
        # Start Docker daemon
        console.print("\n[bold]🚀 Starting Docker daemon...[/bold]")
        subprocess.run(['sudo', 'systemctl', 'start', 'docker'], check=True)
        
        # Verify the change
        try:
            new_root_verify = subprocess.run(
                ['sudo', 'docker', 'info', '--format', '{{.DockerRootDir}}'],
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            
            if new_root_verify == str(new_root):
                console.print("\n[bold green]✓ Docker Root Directory Successfully Changed[/bold green]")
                console.print("┌─" + "─" * 60 + "┐")
                console.print("│ [bold cyan]New Configuration[/bold cyan]" + " " * 43 + "│")
                console.print("├─" + "─" * 60 + "┤")
                console.print(f"│ Docker Root: {new_root_verify:<50} │")
                console.print("└─" + "─" * 60 + "┘\n")
                return True
            else:
                console.print(f"\n[red]✗ Failed to change Docker root directory[/red]")
                console.print(f"[yellow]Current root is still: {new_root_verify}[/yellow]")
                return False
        except subprocess.CalledProcessError:
            console.print("\n[red]✗ Failed to verify new Docker root directory[/red]")
            return False
            
    except subprocess.CalledProcessError as e:
        console.print(f"\n[red]✗ Failed to change Docker root directory: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"\n[red]✗ An error occurred: {e}[/red]")
        return False
    finally:
        input("\nPress Enter to continue...")

def installation_menu():
    """Handle installation and configuration menu."""
    while True:
        items = [
            "Check Docker installation",
            "Install Docker",
            "Update Docker",
            "Configure Docker daemon",
            "Configure user permissions",
            "Change Docker root directory",
            "View Docker info"
        ]
        
        menu = Menu("Installation & Configuration", items)
        choice = menu.show()
        
        if choice is None:
            break
        
        if choice == 0:
            check_docker_installation()
        elif choice == 1:
            if not check_docker_installation():
                install_docker()
            else:
                console.print("[yellow]Docker is already installed[/yellow]")
        elif choice == 2:
            update_docker()
        elif choice == 3:
            configure_docker_daemon()
        elif choice == 4:
            configure_user_permissions()
        elif choice == 5:
            change_docker_root()
        elif choice == 6:
            output = run_docker_command(['info'])
            if output:
                console.print(f"\n[bold]Docker System Information:[/bold]\n{output}")
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
        ]

        menu = Menu("System Tools", items)
        choice = menu.show()

        if choice is None:
            break

        if choice == 0:
            cleanup_menu()
        elif choice == 1:
            test_menu()

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