"""URL-based detector for selecting a job board scraper."""

from __future__ import annotations

from src.posting_scrapers.ashby_scraper import AshbyScraper
from src.posting_scrapers.fallback_scraper import FallbackScraper
from src.posting_scrapers.icims_scraper import ICIMSScraper
from src.posting_scrapers.lever_scraper import LeverScraper
from src.posting_scrapers.models import UnsupportedJobUrlError
from src.posting_scrapers.workday_scraper import WorkdayScraper

SCRAPER_SOURCE_ORDER = [
    ("workday", WorkdayScraper),
    ("lever", LeverScraper),
    ("ashby", AshbyScraper),
    ("icims", ICIMSScraper),
]


def detect_scraper_source(url: str) -> str:
    """Detect scraper source key from URL.

    Args:
        url: Job posting URL.

    Returns:
        Source key: workday, lever, ashby, icims, fallback.

    Raises:
        UnsupportedJobUrlError: If URL is not a valid HTTP(S) URL.
    """
    for source, scraper_cls in SCRAPER_SOURCE_ORDER:
        if scraper_cls.supports_url(url):
            return source

    if FallbackScraper.supports_url(url):
        return "fallback"

    raise UnsupportedJobUrlError(f"Unsupported URL format: {url}")
