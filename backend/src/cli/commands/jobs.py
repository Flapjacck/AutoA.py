"""Jobs command implementation."""

from rich.table import Table
from rich.text import Text

from src.jobs.fetcher import JobListingFetcher
from src.logger import get_logger
from src.cli.theme import console, print_info, print_warning, print_section, print_success

logger = get_logger(__name__)


def show_job_detailed(job: "JobPosting") -> None:
    """Display a single job listing with styling."""
    row = Table.grid(padding=(0, 2))
    row.add_row(
        f"[bold cyan]#{job.id}[/bold cyan]",
        f"[bold bright_magenta]{job.company}[/bold bright_magenta]"
    )
    row.add_row(
        "[muted]Role[/muted]",
        f"{job.role}"
    )
    row.add_row(
        "[muted]Location[/muted]",
        f"{job.location}"
    )
    row.add_row(
        "[muted]Posted[/muted]",
        f"{job.posted_at_raw}"
    )
    row.add_row(
        "[muted]Link[/muted]",
        f"[underline blue]{job.url}[/underline blue]"
    )
    
    console.print(row)
    console.print("[subtle]" + "─" * 80 + "[/subtle]")


def cmd_jobs(page: int = 1, refresh: bool = False) -> None:
    """Display job listings with pagination.
    
    Args:
        page: Page number to display (1-based).
        refresh: If True, fetch fresh data from GitHub before displaying.
    """
    fetcher = JobListingFetcher()
    
    # Refresh if requested
    if refresh:
        print_info("Updating job listings from GitHub...")
        console.print()
    
    jobs = fetcher.get_jobs(force_refresh=refresh)

    if not jobs:
        print_warning("No jobs cached. Run 'jobs -u' to fetch from GitHub.")
        console.print()
        return

    # Pagination
    jobs_per_page = 10
    total_pages = (len(jobs) + jobs_per_page - 1) // jobs_per_page

    if page < 1 or page > total_pages:
        print_warning(f"Page {page} out of range (1-{total_pages})")
        console.print()
        return

    start_idx = (page - 1) * jobs_per_page
    end_idx = min(start_idx + jobs_per_page, len(jobs))
    page_jobs = jobs[start_idx:end_idx]

    # Print section header with pagination info
    print_section(f"Job Listings ({start_idx + 1}-{end_idx} of {len(jobs)})")
    console.print()

    for job in page_jobs:
        show_job_detailed(job)

    # Footer with pagination info
    console.print()
    pagination_text = Text()
    pagination_text.append(f"Page ", style="muted")
    pagination_text.append(f"{page}/{total_pages}", style="bold cyan")
    console.print(pagination_text)
    
    if total_pages > 1:
        hint = Text()
        hint.append("Type ", style="muted")
        hint.append("'jobs <number>'", style="bold cyan")
        hint.append(" to view another page", style="muted")
        console.print(hint)
    
    console.print()


def jobs_command_handler(args: list[str]) -> None:
    """Parse jobs command arguments and execute.
    
    Args:
        args: Command arguments (page number and/or flags).
    """
    page = 1
    refresh = False
    
    # Parse arguments
    for arg in args:
        if arg in ["-u", "--update"]:
            refresh = True
        elif arg.isdigit():
            page = int(arg)
    
    cmd_jobs(page=page, refresh=refresh)
