"""Main CLI entry point with interactive shell."""

import sys

from src.cli.theme import console, print_banner, print_error
from src.cli.commands import cmd_help, cmd_scrape
from src.cli.commands.jobs import jobs_command_handler
from src.cli.commands.prompt import cmd_prompt
from src.cli.commands.resume import cmd_resume
from src.logger import get_logger

logger = get_logger(__name__)


def main_cli(argv: list[str] | None = None) -> None:
    """Interactive CLI shell or direct command entry point."""
    if argv is None:
        argv = sys.argv[1:]

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

    if argv:
        cmd = argv[0].lower()
        args = argv[1:]
        if cmd in ["exit", "quit", "q"]:
            console.print("\n[success]✓ Goodbye![/success]\n")
            return
        elif cmd == "help":
            cmd_help()
            return
        elif cmd == "jobs":
            jobs_command_handler(args)
            return
        elif cmd == "scrape":
            cmd_scrape(args)
            return
        elif cmd == "prompt":
            cmd_prompt(args)
            return
        elif cmd == "resume":
            cmd_resume(args)
            return
        else:
            print_error(f"Unknown command: {cmd}")
            console.print("[muted]Type 'help' for available commands[/muted]\n")
            return

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
            elif cmd == "scrape":
                cmd_scrape(args)
            elif cmd == "prompt":
                cmd_prompt(args)
            elif cmd == "resume":
                cmd_resume(args)
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
