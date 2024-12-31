"""Core Docker operations manager."""
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.prompt import Confirm
from ..utils.docker_utils import run_docker_command
import tempfile

console = Console()

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

    def install_yacht(self, port: int = 8000) -> bool:
        """Install Yacht - Docker Web UI."""
        try:
            # Check if Yacht is already running
            existing = run_docker_command(['ps', '-a', '--filter', 'name=yacht', '--format', '{{.Names}}'])
            if existing and 'yacht' in existing:
                console.print("[yellow]Yacht is already installed[/yellow]")
                return False

            # Create required volumes
            console.print("Creating Yacht volumes...")
            run_docker_command(['volume', 'create', 'yacht'])

            # Pull and run Yacht container
            console.print("Pulling Yacht image...")
            run_docker_command(['pull', 'selfhostedpro/yacht'])

            console.print("Starting Yacht container...")
            run_docker_command([
                'run', '-d',
                '--name', 'yacht',
                '--restart', 'unless-stopped',
                '-v', '/var/run/docker.sock:/var/run/docker.sock',
                '-v', 'yacht:/config',
                '-p', f'{port}:8000',
                '--label', 'docker-mgmt=true',
                'selfhostedpro/yacht'
            ])

            console.print(f"[green]✓ Yacht installed successfully![/green]")
            console.print(f"[green]Access Yacht at http://localhost:{port}[/green]")
            console.print("[yellow]Default credentials:[/yellow]")
            console.print("Email: [cyan]admin@yacht.local[/cyan]")
            console.print("Password: [cyan]pass[/cyan]")
            return True

        except Exception as e:
            console.print(f"[red]✗ Failed to install Yacht: {e}[/red]")
            return False 

    def backup_container(self, container_name: str) -> bool:
        """Backup a container and its data."""
        try:
            # Check if container exists
            output = run_docker_command(['inspect', container_name])
            if not output:
                console.print(f"[red]Container {container_name} not found[/red]")
                return False

            # Create backup timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{container_name}_{timestamp}.tar"

            # Create temporary directory for backup
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Save container configuration
                config_file = temp_path / "config.json"
                config_file.write_text(output)

                # Get container volumes
                container_info = json.loads(output)[0]
                volumes = container_info.get('Mounts', [])
                
                if volumes:
                    volumes_dir = temp_path / "volumes"
                    volumes_dir.mkdir()
                    
                    # Stop container temporarily for consistent backup
                    console.print("[yellow]Stopping container for backup...[/yellow]")
                    run_docker_command(['stop', container_name])
                    
                    try:
                        for volume in volumes:
                            if volume.get('Type') == 'volume':
                                volume_name = volume.get('Name')
                                if volume_name:
                                    volume_dir = volumes_dir / volume_name
                                    volume_dir.mkdir()
                                    
                                    # Use a temporary container to copy volume data
                                    console.print(f"Backing up volume: {volume_name}")
                                    run_docker_command([
                                        'run', '--rm',
                                        '-v', f"{volume_name}:/source",
                                        '-v', f"{volume_dir}:/backup",
                                        'alpine',
                                        'cp', '-a', '/source/.', '/backup/'
                                    ])
                    finally:
                        # Restart container
                        console.print("[yellow]Restarting container...[/yellow]")
                        run_docker_command(['start', container_name])

                # Create tar archive
                console.print("Creating backup archive...")
                subprocess.run(
                    ['tar', '-czf', str(backup_path), '-C', str(temp_path), '.'],
                    check=True
                )

            console.print(f"[green]✓ Backup created: {backup_path.name}[/green]")
            return True

        except Exception as e:
            console.print(f"[red]✗ Backup failed: {e}[/red]")
            return False

    def restore_container(self, backup_path: str) -> bool:
        """Restore a container from backup."""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                console.print(f"[red]Backup file not found: {backup_path}[/red]")
                return False

            # Create temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Extract backup
                console.print("Extracting backup...")
                subprocess.run(
                    ['tar', '-xzf', str(backup_file), '-C', str(temp_path)],
                    check=True
                )

                # Read container configuration
                config_file = temp_path / "config.json"
                if not config_file.exists():
                    console.print("[red]Invalid backup: missing configuration[/red]")
                    return False

                container_info = json.loads(config_file.read_text())[0]
                container_name = container_info['Name'].lstrip('/')
                image = container_info['Config']['Image']

                # Check if container already exists
                existing = run_docker_command(['ps', '-a', '--format', '{{.Names}}'])
                if container_name in existing.splitlines():
                    if not Confirm.ask(f"[yellow]Container {container_name} already exists. Remove it?[/yellow]"):
                        return False
                    run_docker_command(['rm', '-f', container_name])

                # Restore volumes if they exist
                volumes_dir = temp_path / "volumes"
                if volumes_dir.exists():
                    for volume_dir in volumes_dir.iterdir():
                        if volume_dir.is_dir():
                            volume_name = volume_dir.name
                            console.print(f"Restoring volume: {volume_name}")
                            
                            # Create volume if it doesn't exist
                            run_docker_command(['volume', 'create', volume_name])
                            
                            # Copy data to volume
                            run_docker_command([
                                'run', '--rm',
                                '-v', f"{volume_name}:/target",
                                '-v', f"{volume_dir}:/source",
                                'alpine',
                                'cp', '-a', '/source/.', '/target/'
                            ])

                # Pull the image
                console.print(f"Pulling image: {image}")
                run_docker_command(['pull', image])

                # Create container with original configuration
                ports = []
                if 'PortBindings' in container_info.get('HostConfig', {}):
                    for container_port, host_bindings in container_info['HostConfig']['PortBindings'].items():
                        for binding in host_bindings:
                            ports.extend(['-p', f"{binding.get('HostPort', '')}:{container_port.split('/')[0]}"])

                volumes = []
                if 'Mounts' in container_info:
                    for mount in container_info['Mounts']:
                        if mount['Type'] == 'volume':
                            volumes.extend(['-v', f"{mount['Name']}:{mount['Destination']}"])

                # Create and start the container
                run_cmd = ['run', '-d', '--name', container_name]
                if ports:
                    run_cmd.extend(ports)
                if volumes:
                    run_cmd.extend(volumes)
                run_cmd.append(image)

                console.print("Creating container...")
                run_docker_command(run_cmd)
                console.print(f"[green]✓ Container {container_name} restored successfully[/green]")
                return True

        except Exception as e:
            console.print(f"[red]✗ Restore failed: {e}[/red]")
            return False 