"""Auto-detected job URL scraper command implementation."""

from src.cli.theme import console, print_error, print_info, print_section
from src.jobs.fetcher import JobListingFetcher
from src.posting_scrapers import (
    JobNavigationError,
    JobScraperError,
    UnsupportedJobUrlError,
    scrape_description_for_url,
)


def cmd_scrape(args: list[str]) -> None:
    """Execute scraper command for job ID or URL.

    Args:
        args: Command arguments, expects either:
            - A numeric job listing ID (e.g., 1, 2, 3)
            - A job posting URL

    Examples:
        scrape 1          # Scrape first job from cached listings
        scrape 5          # Scrape fifth job from cached listings
        scrape https://...  # Scrape any supported job board URL
    """
    if not args:
        print_error("Usage: scrape <job_id> or scrape <job_url>")
        return

    argument = args[0].strip()
    if not argument:
        print_error("Usage: scrape <job_id> or scrape <job_url>")
        return

    # Detect if argument is a job ID (numeric) or URL
    is_job_id = argument.isdigit()

    print_section("Job Scraper")

    if is_job_id:
        _scrape_by_job_id(int(argument))
    else:
        _scrape_by_url(argument)


def _scrape_by_job_id(job_id: int) -> None:
    """Scrape a job by its listing ID from cached jobs.

    Args:
        job_id: 1-indexed job ID from the job listings.
    """
    try:
        # Fetch cached job list
        fetcher = JobListingFetcher()
        jobs = fetcher.get_jobs(force_refresh=False)

        # Validate job ID is in range
        if job_id < 1 or job_id > len(jobs):
            total = len(jobs)
            print_error(f"Job #{job_id} not found. Only {total} jobs available.")
            return

        # Get the job (convert 1-indexed to 0-indexed)
        job = jobs[job_id - 1]

        print_info(f"Scraping: {job.url}")
        print_info(f"Job ID: {job_id}")

        # Scrape the job URL
        source, description = scrape_description_for_url(job.url)
        print_info(f"Detected source: {source}")

        if not description:
            print_info("No description was found for this job posting.")
            return

        # Display job metadata
        print_section(f"📋 {job.company} | {job.role} | {job.location}")
        console.print(description)
        print_info("Scrape complete.")

    except UnsupportedJobUrlError as exc:
        print_error(str(exc))
    except JobNavigationError as exc:
        print_error(f"Navigation failed: {exc}")
    except JobScraperError as exc:
        print_error(f"Scraper error: {exc}")
    except Exception as exc:
        print_error(f"Error scraping job: {exc}")


def _scrape_by_url(url: str) -> None:
    """Scrape a job by its direct URL.

    Args:
        url: Job posting URL.
    """
    print_info(f"Scraping: {url}")

    try:
        source, description = scrape_description_for_url(url)
        print_info(f"Detected source: {source}")

        if not description:
            print_info("No description was found for the provided URL.")
            return

        console.print(description)
        print_info("Scrape complete.")
    except UnsupportedJobUrlError as exc:
        print_error(str(exc))
    except JobNavigationError as exc:
        print_error(f"Navigation failed: {exc}")
    except JobScraperError as exc:
        print_error(f"Scraper error: {exc}")
    except Exception as exc:
        print_error(f"Error scraping URL: {exc}")
