"""Job board scraping package with multi-site auto-detection."""

from src.posting_scrapers.ashby_scraper import AshbyScraper
from src.posting_scrapers.detector import detect_scraper_source
from src.posting_scrapers.fallback_scraper import FallbackScraper
from src.posting_scrapers.icims_scraper import ICIMSScraper
from src.posting_scrapers.lever_scraper import LeverScraper
from src.posting_scrapers.models import (
    JobNavigationError,
    JobScraperError,
    ScrapeResult,
    UnsupportedJobUrlError,
    UnsupportedWorkdayUrlError,
    WorkdayNavigationError,
    WorkdayScrapeResult,
    WorkdayScraperError,
)
from src.posting_scrapers.router import build_scraper_for_url, scrape_description_for_url
from src.posting_scrapers.workday_scraper import WorkdayScraper

__all__ = [
    "AshbyScraper",
    "build_scraper_for_url",
    "detect_scraper_source",
    "FallbackScraper",
    "ICIMSScraper",
    "JobNavigationError",
    "JobScraperError",
    "LeverScraper",
    "ScrapeResult",
    "scrape_description_for_url",
    "UnsupportedJobUrlError",
    "UnsupportedWorkdayUrlError",
    "WorkdayNavigationError",
    "WorkdayScrapeResult",
    "WorkdayScraper",
    "WorkdayScraperError",
]