"""Docker utility functions."""
import subprocess
from rich.console import Console

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