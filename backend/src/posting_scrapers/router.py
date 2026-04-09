"""Factory and execution helpers for job board scraping."""

from __future__ import annotations

from src.posting_scrapers.ashby_scraper import AshbyScraper
from src.posting_scrapers.base_scraper import BaseJobScraper
from src.posting_scrapers.detector import detect_scraper_source
from src.posting_scrapers.fallback_scraper import FallbackScraper
from src.posting_scrapers.icims_scraper import ICIMSScraper
from src.posting_scrapers.lever_scraper import LeverScraper
from src.posting_scrapers.workday_scraper import WorkdayScraper

SCRAPER_CLASS_MAP: dict[str, type[BaseJobScraper]] = {
    "workday": WorkdayScraper,
    "lever": LeverScraper,
    "ashby": AshbyScraper,
    "icims": ICIMSScraper,
    "fallback": FallbackScraper,
}


def build_scraper_for_url(
    url: str,
    timeout_ms: int = 30000,
    max_attempts: int = 2,
    headless: bool = True,
) -> tuple[str, BaseJobScraper]:
    """Create a configured scraper for the given URL.

    Args:
        url: Job posting URL.
        timeout_ms: Navigation and selector timeout in milliseconds.
        max_attempts: Maximum attempts for transient navigation failures.
        headless: Launch browser headless when True.

    Returns:
        Tuple of detected source key and configured scraper instance.
    """
    source = detect_scraper_source(url)
    scraper_cls = SCRAPER_CLASS_MAP[source]
    scraper = scraper_cls(
        timeout_ms=timeout_ms,
        max_attempts=max_attempts,
        headless=headless,
    )
    return source, scraper


def scrape_description_for_url(
    url: str,
    timeout_ms: int = 30000,
    max_attempts: int = 2,
    headless: bool = True,
) -> tuple[str, str | None]:
    """Detect source, scrape URL, and return source + description text."""
    source, scraper = build_scraper_for_url(
        url=url,
        timeout_ms=timeout_ms,
        max_attempts=max_attempts,
        headless=headless,
    )
    return source, scraper.scrape_description(url)
