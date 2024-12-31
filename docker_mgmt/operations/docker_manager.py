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

    def delete_container(self, container_name: str) -> bool:
        """Delete a container."""
        try:
            # Get container info before deletion to check for volumes
            output = run_docker_command(['inspect', container_name])
            if not output:
                console.print(f"[red]Container {container_name} not found[/red]")
                return False

            container_info = json.loads(output)[0]
            volumes = container_info.get('Mounts', [])
            
            if not Confirm.ask(f"[yellow]Are you sure you want to delete container {container_name}?[/yellow]"):
                return False

            # Remove the container
            run_docker_command(['rm', '-f', container_name])
            console.print(f"[green]✓ Container {container_name} deleted[/green]")

            # After container deletion, ask about cleaning up volumes
            volume_names = [v['Name'] for v in volumes if v.get('Type') == 'volume']
            if volume_names:
                console.print("\n[yellow]The following volumes were associated with this container:[/yellow]")
                for name in volume_names:
                    console.print(f"  - {name}")
                console.print("[yellow]These volumes still contain data that might be needed later.[/yellow]")
                
                if Confirm.ask("[yellow]Would you like to clean up these volumes?[/yellow]"):
                    for volume in volumes:
                        if volume.get('Type') == 'volume':
                            volume_name = volume.get('Name')
                            if volume_name:
                                try:
                                    run_docker_command(['volume', 'rm', volume_name])
                                    console.print(f"[green]✓ Volume {volume_name} removed[/green]")
                                except Exception as e:
                                    console.print(f"[red]✗ Failed to remove volume {volume_name}: {e}[/red]")
                else:
                    console.print("[green]Volumes have been kept for future use[/green]")

            return True
        except Exception as e:
            console.print(f"[red]✗ Failed to delete container: {e}[/red]")
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
            temp_dir = "/tmp/docker_backup_temp"
            subprocess.run(['sudo', 'rm', '-rf', temp_dir], check=True)
            subprocess.run(['sudo', 'mkdir', '-p', temp_dir], check=True)
            temp_path = Path(temp_dir)

            try:
                # Save container configuration
                config_file = temp_path / "config.json"
                subprocess.run(['sudo', 'bash', '-c', f'echo \'{output}\' > {config_file}'], check=True)

                # Get container volumes
                container_info = json.loads(output)[0]
                volumes = container_info.get('Mounts', [])
                
                if volumes:
                    volumes_dir = temp_path / "volumes"
                    subprocess.run(['sudo', 'mkdir', '-p', str(volumes_dir)], check=True)
                    
                    # Stop container temporarily for consistent backup
                    console.print("[yellow]Stopping container for backup...[/yellow]")
                    run_docker_command(['stop', container_name])
                    
                    try:
                        for volume in volumes:
                            if volume.get('Type') == 'volume':
                                volume_name = volume.get('Name')
                                if volume_name:
                                    volume_dir = volumes_dir / volume_name
                                    subprocess.run(['sudo', 'mkdir', '-p', str(volume_dir)], check=True)
                                    
                                    # Use a temporary container to copy volume data
                                    console.print(f"Backing up volume: {volume_name}")
                                    run_docker_command([
                                        'run', '--rm',
                                        '-v', f"{volume_name}:/source:ro",  # Read-only source
                                        '-v', f"{str(volume_dir)}:/backup",
                                        'alpine',
                                        'sh', '-c', 'cp -a /source/. /backup/ && chown -R root:root /backup/'
                                    ])
                    finally:
                        # Restart container
                        console.print("[yellow]Restarting container...[/yellow]")
                        run_docker_command(['start', container_name])

                # Create tar archive with sudo
                console.print("Creating backup archive...")
                subprocess.run(
                    ['sudo', 'tar', '-czf', str(backup_path), '-C', str(temp_path), '.'],
                    check=True
                )

                # Set proper ownership of backup file
                subprocess.run(['sudo', 'chown', f"{os.getuid()}:{os.getgid()}", str(backup_path)], check=True)

            finally:
                # Cleanup
                subprocess.run(['sudo', 'rm', '-rf', temp_dir], check=True)

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
                    console.print(f"\n[yellow]Container '{container_name}' already exists. You can:[/yellow]")
                    console.print("1. Remove the existing container")
                    console.print("2. Restore with a different name")
                    console.print("3. Cancel restore")
                    
                    choice = console.input("\n[cyan]Choose an option (1-3):[/cyan] ")
                    if choice == "1":
                        run_docker_command(['rm', '-f', container_name])
                    elif choice == "2":
                        new_name = console.input("[cyan]Enter new container name:[/cyan] ")
                        if not new_name:
                            console.print("[red]Invalid name[/red]")
                            return False
                        container_name = new_name
                    else:
                        return False

                # Restore volumes if they exist
                volumes_dir = temp_path / "volumes"
                if volumes_dir.exists():
                    for volume_dir in volumes_dir.iterdir():
                        if volume_dir.is_dir():
                            original_volume_name = volume_dir.name
                            # If restoring with a different name, use that name for the volume
                            volume_name = container_name if container_name != container_info['Name'].lstrip('/') else original_volume_name
                            console.print(f"Restoring volume: {volume_name}")
                            
                            # Create volume if it doesn't exist
                            run_docker_command(['volume', 'create', volume_name])
                            
                            # Copy data to volume using sudo for permissions
                            run_docker_command([
                                'run', '--rm',
                                '-v', f"{volume_name}:/target",
                                '-v', f"{volume_dir}:/source",
                                'alpine',
                                'sh', '-c', 'cp -a /source/. /target/ && chown -R root:root /target/'
                            ])

                            # Update volume name in mounts for the container configuration
                            for mount in container_info.get('Mounts', []):
                                if mount.get('Type') == 'volume' and mount.get('Name') == original_volume_name:
                                    mount['Name'] = volume_name

                # Pull the image
                console.print(f"Pulling image: {image}")
                run_docker_command(['pull', image])

                # Build run command with original configuration
                run_cmd = ['run', '-d', '--name', container_name]

                # Add restart policy if it exists
                if 'RestartPolicy' in container_info.get('HostConfig', {}):
                    policy = container_info['HostConfig']['RestartPolicy']
                    if policy.get('Name'):
                        run_cmd.extend(['--restart', policy['Name']])

                # Handle port bindings and potential conflicts
                if 'PortBindings' in container_info.get('HostConfig', {}):
                    port_bindings = container_info['HostConfig']['PortBindings']
                    if port_bindings:
                        console.print("\n[yellow]Container port mappings:[/yellow]")
                        for container_port, host_bindings in port_bindings.items():
                            for binding in host_bindings:
                                host_port = binding.get('HostPort', '')
                                console.print(f"  {host_port}:{container_port}")
                        
                        console.print("\n[yellow]How would you like to handle port mappings?[/yellow]")
                        console.print("1. Use original ports (might fail if ports are in use)")
                        console.print("2. Map to different ports")
                        console.print("3. Skip port mapping")
                        
                        port_choice = console.input("\n[cyan]Choose an option (1-3):[/cyan] ")
                        
                        if port_choice == "1":
                            # Use original ports
                            for container_port, host_bindings in port_bindings.items():
                                for binding in host_bindings:
                                    host_port = binding.get('HostPort', '')
                                    run_cmd.extend(['-p', f"{host_port}:{container_port}"])
                        elif port_choice == "2":
                            # Map to different ports
                            for container_port, host_bindings in port_bindings.items():
                                for binding in host_bindings:
                                    original_port = binding.get('HostPort', '')
                                    while True:
                                        new_port = console.input(f"[cyan]Enter new port for {container_port} (original: {original_port}):[/cyan] ")
                                        if new_port.isdigit() and 1 <= int(new_port) <= 65535:
                                            run_cmd.extend(['-p', f"{new_port}:{container_port}"])
                                            break
                                        console.print("[red]Invalid port number. Must be between 1 and 65535.[/red]")
                        # Option 3: Skip port mapping (do nothing)

                # Add volume mounts
                if 'Mounts' in container_info:
                    for mount in container_info['Mounts']:
                        if mount['Type'] == 'volume':
                            run_cmd.extend(['-v', f"{mount['Name']}:{mount['Destination']}"])
                        elif mount['Type'] == 'bind':
                            run_cmd.extend(['-v', f"{mount['Source']}:{mount['Destination']}"])

                # Add environment variables
                if 'Env' in container_info.get('Config', {}):
                    for env in container_info['Config']['Env']:
                        run_cmd.extend(['-e', env])

                # Add network mode if specified
                if 'NetworkMode' in container_info.get('HostConfig', {}):
                    network_mode = container_info['HostConfig']['NetworkMode']
                    if network_mode != 'default':
                        run_cmd.extend(['--network', network_mode])

                # Add labels
                if 'Labels' in container_info.get('Config', {}):
                    for label, value in container_info['Config']['Labels'].items():
                        run_cmd.extend(['--label', f"{label}={value}"])

                # Add the image
                run_cmd.append(image)

                # Add command and args if specified
                if 'Cmd' in container_info.get('Config', {}) and container_info['Config']['Cmd']:
                    run_cmd.extend(container_info['Config']['Cmd'])

                # Create and start the container
                console.print("Creating container with original configuration...")
                run_docker_command(run_cmd)

                console.print(f"[green]✓ Container {container_name} restored successfully[/green]")
                return True

        except Exception as e:
            console.print(f"[red]✗ Restore failed: {e}[/red]")
            return False 