"""Resume management command - store and retrieve user resume."""

import sys
from pathlib import Path

from src.cli.theme import console, print_error, print_info, print_section, print_success
from src.logger import get_logger

logger = get_logger(__name__)

# Resume storage path (project root)
RESUME_FILE_PATH = Path("./resume.txt")

# Size limits
MIN_RESUME_LENGTH = 10
MAX_RESUME_LENGTH = 50000


def cmd_resume(args: list[str]) -> None:
    """Handle resume command (show, update, or help).

    Args:
        args: Command arguments. Empty for view, ['-u'] for update.

    Examples:
        resume          # Show stored resume
        resume -u       # Enter update mode (paste resume)
    """
    if not args:
        # No arguments: show resume
        _show_resume()
    elif args[0].lower() == "-u":
        # Update flag: enter paste mode
        _update_resume()
    else:
        print_error(f"Invalid argument: {args[0]}")
        print_info("Usage: resume [options]")
        print_info("  resume    - Display stored resume")
        print_info("  resume -u - Update/set your resume")


def _load_resume() -> str | None:
    """Load resume from disk.

    Returns:
        Resume content as string, or None if file doesn't exist.
    """
    if RESUME_FILE_PATH.exists():
        try:
            content = RESUME_FILE_PATH.read_text(encoding="utf-8")
            logger.info(f"Loaded resume from {RESUME_FILE_PATH}")
            return content
        except Exception as e:
            logger.error(f"Failed to read resume file: {e}", exc_info=True)
            print_error(f"Could not read resume: {e}")
            return None
    return None


def _save_resume(content: str) -> bool:
    """Save resume to disk with validation.

    Args:
        content: Resume text to save.

    Returns:
        True if successful, False otherwise.
    """
    # Validate content
    if not content or len(content.strip()) < MIN_RESUME_LENGTH:
        print_error(f"Resume is too short (minimum {MIN_RESUME_LENGTH} characters).")
        return False

    if len(content) > MAX_RESUME_LENGTH:
        print_error(f"Resume is too long (maximum {MAX_RESUME_LENGTH} characters).")
        return False

    try:
        RESUME_FILE_PATH.write_text(content, encoding="utf-8")
        logger.info(f"Saved resume to {RESUME_FILE_PATH}")
        return True
    except Exception as e:
        logger.error(f"Failed to write resume file: {e}", exc_info=True)
        print_error(f"Could not save resume: {e}")
        return False


def _show_resume() -> None:
    """Display stored resume to user, or error if none exists."""
    print_section("Your Resume")

    resume = _load_resume()
    if resume is None:
        print_error("No resume set yet.")
        print_info("Run 'resume -u' to add your resume.")
        return

    # Display resume in a panel for clarity
    from rich.panel import Panel

    panel = Panel(resume, border_style="cyan", title="[bold magenta]Resume[/bold magenta]")
    console.print(panel)
    print_success("Resume displayed above.")


def _update_resume() -> None:
    """Interactive update mode: prompt user to paste resume, preview, and confirm save."""
    print_section("Resume Update")
    print_info("Paste your resume below. On Unix/Linux/Mac, press Ctrl+D when done.")
    print_info("On Windows, press Ctrl+Z then Enter when done.\n")

    # Capture multiline input
    print("> ", end="", flush=True)
    try:
        resume_input = sys.stdin.read()
    except KeyboardInterrupt:
        print_info("\nAborted.")
        return
    except EOFError:
        # Normal end of input on Unix systems
        resume_input = ""

    if not resume_input:
        print_error("No input received. Resume not saved.")
        return

    # Validate
    if len(resume_input.strip()) < MIN_RESUME_LENGTH:
        print_error(f"Resume is too short (minimum {MIN_RESUME_LENGTH} characters).")
        return

    if len(resume_input) > MAX_RESUME_LENGTH:
        print_error(f"Resume is too large (maximum {MAX_RESUME_LENGTH} characters).")
        return

    # Show preview
    print_section("Preview")
    from rich.panel import Panel

    panel = Panel(
        resume_input[:500] + ("..." if len(resume_input) > 500 else ""),
        border_style="yellow",
        title="[bold magenta]Resume Preview (first 500 chars)[/bold magenta]",
    )
    console.print(panel)

    # Ask confirmation
    console.print()
    console.print("[bold cyan]Save this resume?[/bold cyan] (y/n): ", end="")
    try:
        confirmation = sys.stdin.readline().strip().lower()
    except KeyboardInterrupt:
        print_info("\nAborted.")
        return

    if confirmation not in ["y", "yes"]:
        print_info("Aborted. Resume not saved.")
        return

    # Save
    if _save_resume(resume_input):
        print_success("Resume saved successfully!")
        logger.info("Resume updated successfully")
    else:
        logger.warning("Resume save validation failed")
