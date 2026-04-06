"""Interactive CLI shell for the AutoA.py backend."""

import sys

import click

from src.jobs.fetcher import JobListingFetcher
from src.logger import get_logger

logger = get_logger(__name__)

# Force UTF-8 encoding for output
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def show_job(job: "JobPosting") -> None:
    """Display a single job listing."""
    try:
        click.echo(f"[{job.id}] {job.company}")
        click.echo(f"    Role: {job.role}")
        click.echo(f"    Location: {job.location}")
        click.echo(f"    Posted: {job.posted_at_raw}")
        # Create a clickable hyperlink (OSC 8 format)
        hyperlink = f"\x1b]8;;{job.url}\x1b\\View Posting\x1b]8;;\x1b\\"
        click.echo(f"    Link: {hyperlink}")
    except UnicodeEncodeError:
        # Fallback for encoding issues
        click.echo(f"[{job.id}] Job listing")


def cmd_show_jobs(page: int = 1, refresh: bool = False) -> None:
    """Display cached jobs with pagination.
    
    Args:
        page: Page number to display (1-based).
        refresh: If True, fetch fresh data from GitHub before displaying.
    """
    fetcher = JobListingFetcher()
    
    # Refresh if requested
    if refresh:
        logger.info("Fetching latest jobs from GitHub...")
        click.echo("[*] Updating job listings...\n")
    
    jobs = fetcher.get_jobs(force_refresh=refresh)

    if not jobs:
        click.echo("[!] No jobs cached. Run 'jobs -u' to fetch from GitHub.\n")
        return

    # Pagination
    jobs_per_page = 10
    total_pages = (len(jobs) + jobs_per_page - 1) // jobs_per_page

    if page < 1 or page > total_pages:
        click.echo(f"[!] Page {page} out of range (1-{total_pages})\n")
        return

    start_idx = (page - 1) * jobs_per_page
    end_idx = min(start_idx + jobs_per_page, len(jobs))
    page_jobs = jobs[start_idx:end_idx]

    click.echo(f"\n[*] Jobs ({start_idx + 1}-{end_idx} of {len(jobs)})\n")
    click.echo("=" * 100)

    for job in page_jobs:
        show_job(job)
        click.echo("-" * 100)

    click.echo(f"\nPage {page}/{total_pages}")
    if total_pages > 1:
        click.echo(f"Type 'jobs <page>' to view another page\n")
    else:
        click.echo()


def cmd_help() -> None:
    """Display help message."""
    click.echo("\nAvailable Commands:")
    click.echo("  jobs [page] [-u|--update]  Display cached jobs (10 per page)")
    click.echo("                              -u or --update: Refresh jobs from GitHub")
    click.echo("  help                       Show this message")
    click.echo("  exit, quit, q              Exit the CLI\n")


def main_cli() -> None:
    """Interactive CLI shell for job listing management."""
    click.clear()
    click.echo("========================================")
    click.echo("  AutoA.py - Resume Tailoring Tool")
    click.echo("========================================\n")
    cmd_help()

    while True:
        try:
            # Use sys.stdin directly for better compatibility
            sys.stdout.write("autoa> ")
            sys.stdout.flush()
            user_input = sys.stdin.readline().strip()

            if not user_input:
                continue

            parts = user_input.split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            if cmd in ["exit", "quit", "q"]:
                click.echo("\n[*] Goodbye!\n")
                break
            elif cmd == "help":
                cmd_help()
            elif cmd == "jobs":
                page = 1
                refresh = False
                
                # Parse page number and flags
                for arg in args:
                    if arg in ["-u", "--update"]:
                        refresh = True
                    elif arg.isdigit():
                        page = int(arg)
                
                click.echo()
                cmd_show_jobs(page=page, refresh=refresh)
            else:
                click.echo(f"[!] Unknown command: {cmd}. Type 'help' for available commands.\n")

        except KeyboardInterrupt:
            click.echo("\n\n[*] Interrupted. Type 'quit' to exit.\n")
        except EOFError:
            # Handle when input stream ends (e.g., piped input)
            click.echo("\n[*] Goodbye!\n")
            break
        except Exception as e:
            logger.error(f"CLI Error: {e}")
            click.echo(f"[!] Error: {e}\n")


if __name__ == "__main__":
    main_cli()
