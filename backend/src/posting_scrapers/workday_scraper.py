"""Playwright-based scraper for Workday job posting pages."""

from __future__ import annotations

from urllib.parse import urlparse

from src.posting_scrapers.base_scraper import BaseJobScraper
from src.posting_scrapers.models import (
    WorkdayNavigationError,
    WorkdayScrapeResult,
    WorkdayScraperError,
    UnsupportedWorkdayUrlError,
)

WORKDAY_HOST_SUFFIX = ".myworkdayjobs.com"
PRIMARY_DESCRIPTION_SELECTOR = "[data-automation-id='jobPostingDescription']"


class WorkdayScraper(BaseJobScraper):
    """Scrape full job descriptions from Workday-hosted job posting URLs."""

    SOURCE_NAME = "workday"

    @staticmethod
    def is_workday_url(url: str) -> bool:
        """Return True when URL host belongs to myworkdayjobs.com."""
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and parsed.netloc.endswith(
            WORKDAY_HOST_SUFFIX
        )

    @classmethod
    def supports_url(cls, url: str) -> bool:
        """Return True for Workday-compatible URL hosts."""
        return cls.is_workday_url(url)

    def scrape_description(self, url: str) -> str | None:
        """Scrape only the description text for Workday URLs."""
        if not self.is_workday_url(url):
            raise UnsupportedWorkdayUrlError(f"Unsupported Workday URL: {url}")

        return super().scrape_description(url)

    def _scrape_once(self, url: str) -> WorkdayScrapeResult | None:
        """Execute one Workday scrape attempt and return Workday result type."""
        if not self.is_workday_url(url):
            raise UnsupportedWorkdayUrlError(f"Unsupported Workday URL: {url}")

        result = super()._scrape_once(url)
        if result is None:
            return None

        return WorkdayScrapeResult(url=result.url, description=result.description)

    def _extract_description(self, page: object) -> str:
        """Extract the most likely Workday job description text."""
        primary_text = self._extract_by_selectors(page, [PRIMARY_DESCRIPTION_SELECTOR])
        if primary_text:
            return primary_text

        fallback_script = r"""
            (() => {
                const norm = (v) => (v || '').replace(/\s+/g, ' ').trim();
                const headingNames = ['Job Description', 'Description'];

                for (const name of headingNames) {
                    const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,div,span'))
                      .filter((el) => norm(el.textContent) === name);
                    for (const heading of headings) {
                        const sibling = heading.nextElementSibling;
                        if (!sibling) continue;
                        const text = norm(sibling.innerText || sibling.textContent);
                        if (text && text.length > 120) {
                            return text;
                        }
                    }
                }

                const containers = [
                    'main',
                    'article',
                    '[data-automation-id="jobPostingDescription"]',
                    '[data-automation-id="jobDetails"]'
                ];

                for (const selector of containers) {
                    const node = document.querySelector(selector);
                    if (!node) continue;
                    const text = norm(node.innerText || node.textContent);
                    if (text && text.length > 180) {
                        return text;
                    }
                }

                return '';
            })();
        """
        return self._evaluate_text(page, fallback_script)

    def _validate_url(self, url: str) -> None:
        """Raise Workday-specific unsupported URL errors."""
        if not self.is_workday_url(url):
            raise UnsupportedWorkdayUrlError(f"Unsupported Workday URL: {url}")

    def _unsupported_url_error(self, url: str) -> WorkdayScraperError:
        """Create Workday-specific unsupported URL error."""
        return UnsupportedWorkdayUrlError(f"Unsupported Workday URL: {url}")

    def _scraper_error(self, message: str) -> WorkdayScraperError:
        """Create Workday-specific scraper error."""
        return WorkdayScraperError(message)

    def _navigation_error(self, message: str) -> WorkdayNavigationError:
        """Create Workday-specific navigation error."""
        return WorkdayNavigationError(message)
