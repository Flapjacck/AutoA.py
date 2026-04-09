"""Playwright-based scraper for iCIMS job posting pages."""

from __future__ import annotations

from urllib.parse import urlparse

from src.posting_scrapers.base_scraper import BaseJobScraper

ICIMS_HOST_TOKEN = "icims.com"
ICIMS_SELECTORS = [
    "#job-description",
    "[class*='iCIMS_JobContent']",
    "[class*='jobDescription']",
    "main",
    "article",
]


class ICIMSScraper(BaseJobScraper):
    """Scrape full job descriptions from iCIMS URLs."""

    SOURCE_NAME = "icims"

    @staticmethod
    def is_icims_url(url: str) -> bool:
        """Return True when URL host belongs to iCIMS."""
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and ICIMS_HOST_TOKEN in parsed.netloc

    @classmethod
    def supports_url(cls, url: str) -> bool:
        """Return True for iCIMS-compatible URL hosts."""
        return cls.is_icims_url(url)

    def _extract_description(self, page: object) -> str:
        """Extract iCIMS description from common description containers."""
        by_selector = self._extract_by_selectors(page, ICIMS_SELECTORS)
        if by_selector:
            return by_selector

        fallback_script = r"""
            (() => {
                const normalize = (value) => (value || '').replace(/\s+/g, ' ').trim();
                const heading = Array.from(document.querySelectorAll('h1,h2,h3,h4,div,span'))
                    .find((el) => normalize(el.textContent) === 'Job Description');

                if (heading) {
                    const chunks = [];
                    let node = heading.nextElementSibling;

                    while (node && chunks.length < 16) {
                        const text = normalize(node.innerText || node.textContent);
                        if (text.length > 30) {
                            chunks.push(text);
                        }

                        if (/^Options$|^Share on your newsfeed$/i.test(text)) {
                            break;
                        }

                        node = node.nextElementSibling;
                    }

                    if (chunks.length > 0) {
                        return chunks.join(' ');
                    }
                }

                const main = document.querySelector('main') || document.body;
                if (!main) return '';

                const clone = main.cloneNode(true);
                clone.querySelectorAll('button, nav, footer, form').forEach((el) => el.remove());
                return normalize(clone.innerText || clone.textContent);
            })();
        """
        return self._evaluate_text(page, fallback_script)
