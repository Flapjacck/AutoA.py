"""Base Playwright scraper for job board pages."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from src.logger import get_logger
from src.posting_scrapers.models import (
    JobNavigationError,
    JobScraperError,
    ScrapeResult,
    UnsupportedJobUrlError,
)

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - handled by runtime checks.
    PlaywrightTimeoutError = TimeoutError
    sync_playwright = None


logger = get_logger(__name__)

DEFAULT_TIMEOUT_MS = 30000
DEFAULT_MAX_ATTEMPTS = 2
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class BaseJobScraper(ABC):
    """Shared Playwright flow for site-specific job scrapers."""

    SOURCE_NAME = "unknown"

    def __init__(
        self,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        headless: bool = True,
    ) -> None:
        """Initialize common scraping settings.

        Args:
            timeout_ms: Navigation and selector timeout in milliseconds.
            max_attempts: Maximum attempts for transient navigation failures.
            headless: Launch Chromium in headless mode when True.
        """
        self.timeout_ms = timeout_ms
        self.max_attempts = max_attempts
        self.headless = headless

    @classmethod
    @abstractmethod
    def supports_url(cls, url: str) -> bool:
        """Return True when the URL matches this scraper's board type."""

    def scrape(self, url: str) -> ScrapeResult | None:
        """Scrape a URL and return source + description payload when found."""
        self._validate_url(url)

        last_error: JobNavigationError | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return self._scrape_once(url)
            except JobNavigationError as exc:
                last_error = exc
                logger.warning(
                    "Navigation attempt %s/%s failed for %s (%s): %s",
                    attempt,
                    self.max_attempts,
                    url,
                    self.SOURCE_NAME,
                    exc,
                )

        if last_error is not None:
            raise last_error

        return None

    def scrape_description(self, url: str) -> str | None:
        """Scrape and return only description text for compatibility."""
        result = self.scrape(url)
        if result is None:
            return None
        return result.description

    def _validate_url(self, url: str) -> None:
        """Raise a typed error when URL is unsupported for this scraper."""
        if not self.supports_url(url):
            raise self._unsupported_url_error(url)

    def _scrape_once(self, url: str) -> ScrapeResult | None:
        """Execute one Playwright scrape attempt."""
        if sync_playwright is None:
            raise JobScraperError(
                "Playwright is not installed. Install dependencies with uv first."
            )

        browser = None
        context = None
        page = None

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self.headless)
                context = browser.new_context(user_agent=DEFAULT_USER_AGENT)
                page = context.new_page()
                page.set_default_timeout(self.timeout_ms)

                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_load_state("networkidle", timeout=self.timeout_ms)

                description = self._extract_description(page)
                if not description:
                    logger.warning("No description text found at URL: %s", url)
                    return None

                return ScrapeResult(
                    source=self.SOURCE_NAME,
                    url=url,
                    description=description,
                )

        except PlaywrightTimeoutError as exc:
            raise self._navigation_error(
                f"Timed out loading {self.SOURCE_NAME} page within {self.timeout_ms}ms"
            ) from exc
        except JobScraperError:
            raise
        except Exception as exc:
            raise self._scraper_error(
                f"Unexpected {self.SOURCE_NAME} scrape failure: {exc}"
            ) from exc
        finally:
            self._safe_close(page)
            self._safe_close(context)
            self._safe_close(browser)

    @abstractmethod
    def _extract_description(self, page: object) -> str:
        """Extract job description text from the loaded page."""

    def _unsupported_url_error(self, url: str) -> JobScraperError:
        """Create unsupported URL error for this scraper type."""
        return UnsupportedJobUrlError(
            f"Unsupported URL for {self.SOURCE_NAME} scraper: {url}"
        )

    def _navigation_error(self, message: str) -> JobNavigationError:
        """Create navigation error for this scraper type."""
        return JobNavigationError(message)

    def _scraper_error(self, message: str) -> JobScraperError:
        """Create general scraper error for this scraper type."""
        return JobScraperError(message)

    @staticmethod
    def _extract_by_selectors(
        page: object,
        selectors: list[str],
        min_length: int = 120,
    ) -> str:
        """Return normalized text from first viable selector match."""
        best_text = ""

        for selector in selectors:
            locator = page.locator(selector).first
            if locator.count() == 0:
                continue

            candidate = BaseJobScraper._normalize_text(locator.inner_text())
            if not candidate:
                continue

            if len(candidate) >= min_length:
                return candidate

            if len(candidate) > len(best_text):
                best_text = candidate

        return best_text

    @staticmethod
    def _evaluate_text(page: object, script: str) -> str:
        """Execute a JS extraction script and normalize returned text."""
        return BaseJobScraper._normalize_text(page.evaluate(script))

    @staticmethod
    def _normalize_text(text: str | None) -> str:
        """Normalize whitespace and return a clean text block."""
        if not text:
            return ""

        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _safe_close(obj: object | None) -> None:
        """Close Playwright object without raising cleanup errors."""
        if obj is None:
            return

        close_method = getattr(obj, "close", None)
        if callable(close_method):
            try:
                close_method()
            except Exception as exc:  # pragma: no cover - defensive cleanup.
                logger.debug("Cleanup close failed: %s", exc)
