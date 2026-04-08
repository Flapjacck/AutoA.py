"""Models and exceptions for job board scraping."""

from dataclasses import dataclass


@dataclass
class ScrapeResult:
    """Represents extracted content from any supported job board URL."""

    source: str
    url: str
    description: str


@dataclass
class WorkdayScrapeResult:
    """Represents the extracted content from a Workday job posting."""

    url: str
    description: str


class JobScraperError(Exception):
    """Base exception for all job board scraper failures."""


class UnsupportedJobUrlError(JobScraperError, ValueError):
    """Raised when a URL does not match any supported scraper type."""


class JobNavigationError(JobScraperError):
    """Raised when page navigation fails or times out."""


class WorkdayScraperError(JobScraperError):
    """Base exception for Workday scraper failures."""


class UnsupportedWorkdayUrlError(
    WorkdayScraperError,
    UnsupportedJobUrlError,
):
    """Raised when a URL is not a supported Workday jobs URL."""


class WorkdayNavigationError(WorkdayScraperError, JobNavigationError):
    """Raised when page navigation fails or times out."""