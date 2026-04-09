"""Playwright-based scraper for Ashby job posting pages."""

from __future__ import annotations

from urllib.parse import urlparse

from src.posting_scrapers.base_scraper import BaseJobScraper

ASHBY_HOSTS = {"jobs.ashbyhq.com", "ashbyhq.com", "www.ashbyhq.com"}
ASHBY_SELECTORS = [
    "main",
    "article",
    "[data-testid='job-posting']",
    "[data-testid='jobDescription']",
    "[class*='job-posting']",
]


class AshbyScraper(BaseJobScraper):
    """Scrape full job descriptions from Ashby URLs."""

    SOURCE_NAME = "ashby"

    @staticmethod
    def is_ashby_url(url: str) -> bool:
        """Return True when URL host belongs to Ashby."""
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and parsed.netloc in ASHBY_HOSTS

    @classmethod
    def supports_url(cls, url: str) -> bool:
        """Return True for Ashby-compatible URL hosts."""
        return cls.is_ashby_url(url)

    def _extract_description(self, page: object) -> str:
        """Extract Ashby description from primary content sections."""
        by_selector = self._extract_by_selectors(page, ASHBY_SELECTORS)
        if by_selector:
            return by_selector

        fallback_script = r"""
            (() => {
                const normalize = (value) => (value || '').replace(/\s+/g, ' ').trim();
                const sectionTitles = [
                    'About the role',
                    'Overview',
                    'Responsibilities',
                    'Qualifications',
                    'About',
                    'In this role you will'
                ];

                const blocks = [];
                for (const title of sectionTitles) {
                    const heading = Array.from(document.querySelectorAll('h1,h2,h3,h4'))
                        .find((el) => normalize(el.textContent) === title);
                    if (!heading) continue;

                    const content = heading.nextElementSibling;
                    if (!content) continue;

                    const text = normalize(content.innerText || content.textContent);
                    if (text.length > 80) {
                        blocks.push(`${title}: ${text}`);
                    }
                }

                if (blocks.length > 0) {
                    return blocks.join(' ');
                }

                const main = document.querySelector('main') || document.body;
                if (!main) return '';

                const clone = main.cloneNode(true);
                clone.querySelectorAll('button, nav, footer, form').forEach((el) => el.remove());
                return normalize(clone.innerText || clone.textContent);
            })();
        """
        return self._evaluate_text(page, fallback_script)
