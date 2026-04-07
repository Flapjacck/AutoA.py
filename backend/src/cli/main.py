"""Main CLI entry point with interactive shell."""

import sys

from src.cli.theme import console, print_banner, print_error
from src.cli.commands import cmd_help
from src.cli.commands.jobs import jobs_command_handler
from src.logger import get_logger

logger = get_logger(__name__)


def main_cli() -> None:
    """Interactive CLI shell for job listing management."""
    # Force UTF-8 encoding for better output
    if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    
    # Clear and show banner
    console.clear()
    print_banner()
    cmd_help()

    while True:
        try:
            # Prompt with modern styling
            console.print("[accent]autoa[/accent]", end="> ")
            user_input = sys.stdin.readline().strip()

            if not user_input:
                continue

            parts = user_input.split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            # Command routing
            if cmd in ["exit", "quit", "q"]:
                console.print("\n[success]✓ Goodbye![/success]\n")
                break
            elif cmd == "help":
                cmd_help()
            elif cmd == "jobs":
                jobs_command_handler(args)
            else:
                print_error(f"Unknown command: {cmd}")
                console.print("[muted]Type 'help' for available commands[/muted]\n")

        except KeyboardInterrupt:
            console.print("\n[warning]⚠ Interrupted[/warning]")
            console.print("[muted]Type 'quit' to exit[/muted]\n")
        except EOFError:
            # Handle when input stream ends (e.g., piped input)
            console.print("\n[success]✓ Goodbye![/success]\n")
            break
        except Exception as e:
            logger.error(f"CLI Error: {e}", exc_info=True)
            print_error(f"An error occurred: {e}")
            console.print()


if __name__ == "__main__":
    main_cli()
