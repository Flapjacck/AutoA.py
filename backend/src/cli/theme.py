"""Theme and styling utilities for modern CLI output."""

from rich.console import Console
from rich.theme import Theme
from rich.style import Style


# Define custom theme with modern color palette
THEME = Theme({
    "header": "bold bright_magenta",
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "info": "bold cyan",
    "muted": "dim white",
    "accent": "bright_magenta",
    "subtle": "bright_black",
})

# Global console instance with theme
console = Console(theme=THEME, force_terminal=True)


def print_header(title: str) -> None:
    """Display a stylized header."""
    console.print(f"\n[header]{'═' * 50}[/header]")
    console.print(f"[header]  {title}[/header]")
    console.print(f"[header]{'═' * 50}[/header]\n")


def print_banner() -> None:
    """Display app banner on startup."""
    console.print("\n[header]╔════════════════════════════════════════════════════╗[/header]")
    console.print("[header]║                                                    ║[/header]")
    console.print("[header]║     AutoA.py - Resume Tailoring Tool              ║[/header]")
    console.print("[header]║                                                    ║[/header]")
    console.print("[header]╚════════════════════════════════════════════════════╝[/header]\n")


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[success]✓ {message}[/success]")


def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[error]✗ {message}[/error]")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[warning]⚠ {message}[/warning]")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[info]ℹ {message}[/info]")


def print_section(title: str) -> None:
    """Print a section header."""
    console.print(f"\n[accent]{title}[/accent]")
    console.print(f"[subtle]{'─' * len(title)}[/subtle]")
