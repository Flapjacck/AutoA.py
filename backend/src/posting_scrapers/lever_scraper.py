"""Playwright-based scraper for Lever job posting pages."""

from __future__ import annotations

from urllib.parse import urlparse

from src.posting_scrapers.base_scraper import BaseJobScraper

LEVER_HOSTS = {"jobs.lever.co", "lever.co"}
LEVER_SELECTORS = [
    ".posting-page .section-wrapper.page-full-width",
    ".posting-page .section-wrapper",
    ".posting .content",
    ".posting-page",
    "main",
    "article",
]


class LeverScraper(BaseJobScraper):
    """Scrape full job descriptions from Lever URLs."""

    SOURCE_NAME = "lever"

    @staticmethod
    def is_lever_url(url: str) -> bool:
        """Return True when URL host belongs to Lever."""
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and parsed.netloc in LEVER_HOSTS

    @classmethod
    def supports_url(cls, url: str) -> bool:
        """Return True for Lever-compatible URL hosts."""
        return cls.is_lever_url(url)

    def _extract_description(self, page: object) -> str:
        """Extract Lever description from known content containers."""
        by_selector = self._extract_by_selectors(page, LEVER_SELECTORS)
        if by_selector:
            return by_selector

        fallback_script = r"""
            (() => {
                const normalize = (value) => (value || '').replace(/\s+/g, ' ').trim();
                const candidates = [
                    '.posting-page',
                    '.posting',
                    'main',
                    'article'
                ];

                let best = '';
                for (const selector of candidates) {
                    const node = document.querySelector(selector);
                    if (!node) continue;

                    const clone = node.cloneNode(true);
                    clone.querySelectorAll('button, nav, footer, form').forEach((el) => el.remove());
                    const text = normalize(clone.innerText || clone.textContent);
                    if (text.length > best.length) {
                        best = text;
                    }
                }

                return best;
            })();
        """
        return self._evaluate_text(page, fallback_script)
