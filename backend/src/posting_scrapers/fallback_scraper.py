"""Generic fallback scraper for misc job posting pages."""

from __future__ import annotations

from urllib.parse import urlparse

from src.posting_scrapers.base_scraper import BaseJobScraper

FALLBACK_SELECTORS = [
    "[data-testid='jobDescription']",
    "[data-automation-id='jobPostingDescription']",
    "[class*='job-description']",
    "[class*='jobDescription']",
    "[id*='job-description']",
    "[id*='description']",
    "article",
    "main",
    "[role='main']",
]


class FallbackScraper(BaseJobScraper):
    """Scrape description text from unknown boards using generic heuristics."""

    SOURCE_NAME = "fallback"

    @staticmethod
    def is_supported_http_url(url: str) -> bool:
        """Return True when URL is a supported HTTP(S) address."""
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    @classmethod
    def supports_url(cls, url: str) -> bool:
        """Fallback supports any valid HTTP(S) URL."""
        return cls.is_supported_http_url(url)

    def _extract_description(self, page: object) -> str:
        """Extract description from generic job content selectors."""
        by_selector = self._extract_by_selectors(page, FALLBACK_SELECTORS)
        if by_selector:
            return by_selector

        fallback_script = r"""
            (() => {
                const normalize = (value) => (value || '').replace(/\s+/g, ' ').trim();
                const selectors = [
                    'main',
                    'article',
                    '[role="main"]',
                    'section',
                    'body'
                ];

                let best = '';

                for (const selector of selectors) {
                    const nodes = Array.from(document.querySelectorAll(selector));
                    for (const node of nodes) {
                        const clone = node.cloneNode(true);
                        clone.querySelectorAll('script,style,noscript,nav,header,footer,button,form').forEach(
                            (el) => el.remove()
                        );

                        const text = normalize(clone.innerText || clone.textContent);
                        if (text.length > best.length) {
                            best = text;
                        }
                    }
                }

                return best;
            })();
        """
        return self._evaluate_text(page, fallback_script)
