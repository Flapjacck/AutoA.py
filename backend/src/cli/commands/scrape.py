"""Auto-detected job URL scraper command implementation."""

from src.cli.theme import console, print_error, print_info, print_section
from src.posting_scrapers import (
    JobNavigationError,
    JobScraperError,
    UnsupportedJobUrlError,
    scrape_description_for_url,
)


def cmd_scrape(args: list[str]) -> None:
    """Execute scraper command for any supported job URL.

    Args:
        args: Command arguments, expects a single job posting URL.
    """
    if not args:
        print_error("Usage: scrape <job_url>")
        return

    url = args[0].strip()
    if not url:
        print_error("Usage: scrape <job_url>")
        return

    print_section("Job Scraper")
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
