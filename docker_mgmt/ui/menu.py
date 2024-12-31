"""Menu system for Docker Management Tool."""
from typing import Optional, List
import typer
from rich.console import Console

console = Console()

class Menu:
    """Simple menu system."""
    def __init__(self, title: str, items: List[str]):
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