"""Workday command implementation for the interactive CLI."""

from src.cli.theme import console, print_error, print_info, print_section
from src.workday import WorkdayScraper, UnsupportedWorkdayUrlError, WorkdayNavigationError


def cmd_workday(args: list[str]) -> None:
    """Execute the Workday scraper command.

    Args:
        args: Command arguments, expects a single Workday URL.
    """
    if not args:
        print_error("Usage: workday <workday_url>")
        return

    url = args[0].strip()
    if not url:
        print_error("Usage: workday <workday_url>")
        return

    print_section("Workday Scraper")
    print_info(f"Scraping: {url}")

    scraper = WorkdayScraper()
    try:
        description = scraper.scrape_description(url)
        if not description:
            print_info("No description was found for the provided Workday URL.")
            return

        console.print(description)
        print_info("Workday scrape complete.")
    except UnsupportedWorkdayUrlError as exc:
        print_error(str(exc))
    except WorkdayNavigationError as exc:
        print_error(f"Navigation failed: {exc}")
    except Exception as exc:
        print_error(f"Error scraping Workday URL: {exc}")
