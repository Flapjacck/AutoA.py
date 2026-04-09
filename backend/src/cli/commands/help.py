"""Help command implementation."""

from rich.table import Table

from src.cli.theme import console, print_section


def cmd_help() -> None:
    """Display available commands and usage guide."""
    print_section("Commands")
    
    # Create command table
    table = Table(show_header=True, header_style="bold bright_magenta", padding=(0, 1))
    table.add_column("Command", style="bold cyan", width=20)
    table.add_column("Description", style="white")
    table.add_column("Examples", style="dim")
    
    table.add_row(
        "jobs [page]",
        "Display cached job listings (10 per page)",
        "jobs  |  jobs 2"
    )
    table.add_row(
        "jobs -u",
        "Refresh job listings from GitHub",
        "jobs -u  |  jobs -u 1"
    )
    table.add_row(
        "scrape <url>",
        "Auto-detect and scrape Workday, Lever, Ashby, iCIMS, or fallback",
        "scrape https://jobs.lever.co/..."
    )
    table.add_row(
        "help",
        "Show this help message",
        "help"
    )
    table.add_row(
        "exit, quit, q",
        "Exit the CLI",
        "exit  |  quit"
    )
    
    console.print(table)
    console.print()


def cmd_hint() -> None:
    """Display quick command hint."""
    console.print("[muted]Type 'help' for available commands[/muted]")
