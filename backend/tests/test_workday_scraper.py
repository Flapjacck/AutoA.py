"""Tests for Workday Playwright scraper."""

import pytest

from src.posting_scrapers.models import (
    UnsupportedWorkdayUrlError,
    WorkdayNavigationError,
    WorkdayScrapeResult,
)
from src.posting_scrapers.workday_scraper import WorkdayScraper


class FakeLocator:
    """Simple locator stub for Playwright locator API."""

    def __init__(self, count_value: int, text: str):
        self._count_value = count_value
        self._text = text
        self.first = self

    def count(self) -> int:
        return self._count_value

    def inner_text(self) -> str:
        return self._text


class FakePage:
    """Simple page stub with controllable extraction and timeout behavior."""

    def __init__(
        self,
        locator_count: int,
        locator_text: str,
        fallback_text: str,
        timeout_exc: type[Exception],
        raise_timeout: bool,
    ) -> None:
        self.locator_count = locator_count
        self.locator_text = locator_text
        self.fallback_text = fallback_text
        self.timeout_exc = timeout_exc
        self.raise_timeout = raise_timeout
        self.closed = False

    def set_default_timeout(self, timeout_ms: int) -> None:
        self.timeout_ms = timeout_ms

    def goto(self, *_args, **_kwargs) -> None:
        if self.raise_timeout:
            raise self.timeout_exc("timeout")

    def wait_for_load_state(self, *_args, **_kwargs) -> None:
        return None

    def locator(self, _selector: str) -> FakeLocator:
        return FakeLocator(self.locator_count, self.locator_text)

    def evaluate(self, _script: str) -> str:
        return self.fallback_text

    def close(self) -> None:
        self.closed = True


class FakeContext:
    """Simple browser context stub."""

    def __init__(self, page: FakePage) -> None:
        self._page = page
        self.closed = False

    def new_page(self) -> FakePage:
        return self._page

    def close(self) -> None:
        self.closed = True


class FakeBrowser:
    """Simple browser stub."""

    def __init__(self, context: FakeContext) -> None:
        self._context = context
        self.closed = False

    def new_context(self, **_kwargs) -> FakeContext:
        return self._context

    def close(self) -> None:
        self.closed = True


class FakeChromium:
    """Simple chromium launcher stub."""

    def __init__(self, browser: FakeBrowser) -> None:
        self._browser = browser

    def launch(self, **_kwargs) -> FakeBrowser:
        return self._browser


class FakePlaywright:
    """Simple Playwright root object stub."""

    def __init__(self, browser: FakeBrowser) -> None:
        self.chromium = FakeChromium(browser)


class FakePlaywrightContextManager:
    """Context manager wrapper for fake Playwright."""

    def __init__(self, playwright: FakePlaywright) -> None:
        self._playwright = playwright

    def __enter__(self) -> FakePlaywright:
        return self._playwright

    def __exit__(self, _exc_type, _exc, _tb) -> bool:
        return False


def _build_fake_sync_playwright(
    locator_count: int = 1,
    locator_text: str = "Detailed job description",
    fallback_text: str = "",
    timeout_exc: type[Exception] = TimeoutError,
    raise_timeout: bool = False,
) -> tuple[callable, FakePage, FakeContext, FakeBrowser]:
    """Build fake sync_playwright callable and object references."""
    page = FakePage(
        locator_count=locator_count,
        locator_text=locator_text,
        fallback_text=fallback_text,
        timeout_exc=timeout_exc,
        raise_timeout=raise_timeout,
    )
    context = FakeContext(page)
    browser = FakeBrowser(context)
    playwright = FakePlaywright(browser)

    def fake_sync_playwright() -> FakePlaywrightContextManager:
        return FakePlaywrightContextManager(playwright)

    return fake_sync_playwright, page, context, browser


class TestWorkdayUrlValidation:
    """Validate Workday URL matching."""

    def test_is_workday_url_accepts_myworkdayjobs(self):
        """myworkdayjobs URLs are accepted."""
        scraper = WorkdayScraper()
        assert scraper.is_workday_url(
            "https://generalmotors.wd5.myworkdayjobs.com/Careers_GM/job/abc"
        )

    def test_is_workday_url_rejects_non_workday_hosts(self):
        """Non-Workday hosts are rejected."""
        scraper = WorkdayScraper()
        assert not scraper.is_workday_url("https://example.com/job/123")


class TestWorkdayScrapeDescription:
    """Validate high-level scrape retry and validation behavior."""

    def test_scrape_description_rejects_unsupported_url(self):
        """Unsupported URL raises a typed error."""
        scraper = WorkdayScraper()
        with pytest.raises(UnsupportedWorkdayUrlError):
            scraper.scrape_description("https://example.com/job/123")

    def test_scrape_description_retries_then_succeeds(self, monkeypatch):
        """Navigation failure retries and returns description on next attempt."""
        scraper = WorkdayScraper(max_attempts=2)
        attempts = {"count": 0}

        def fake_scrape_once(_url: str):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise WorkdayNavigationError("first attempt failed")
            return WorkdayScrapeResult(
                url="https://rakuten.wd1.myworkdayjobs.com/Kobo/job/abc",
                description="This is a complete description.",
            )

        monkeypatch.setattr(scraper, "_scrape_once", fake_scrape_once)

        result = scraper.scrape_description(
            "https://rakuten.wd1.myworkdayjobs.com/Kobo/job/abc"
        )
        assert result == "This is a complete description."
        assert attempts["count"] == 2

    def test_scrape_description_raises_when_all_attempts_fail(self, monkeypatch):
        """Persistent navigation failure raises after max attempts."""
        scraper = WorkdayScraper(max_attempts=2)

        def fake_scrape_once(_url: str):
            raise WorkdayNavigationError("still failing")

        monkeypatch.setattr(scraper, "_scrape_once", fake_scrape_once)

        with pytest.raises(WorkdayNavigationError):
            scraper.scrape_description(
                "https://generalmotors.wd5.myworkdayjobs.com/Careers_GM/job/abc"
            )


class TestWorkdayScrapeOnce:
    """Validate Playwright handling and extraction at single-attempt level."""

    def test_scrape_once_extracts_primary_description_and_cleans_up(self, monkeypatch):
        """Primary selector extraction succeeds and resources are closed."""
        import src.posting_scrapers.base_scraper as base_module

        fake_sync_playwright, page, context, browser = _build_fake_sync_playwright(
            locator_count=1,
            locator_text="Role details and responsibilities",
            fallback_text="",
        )
        monkeypatch.setattr(base_module, "sync_playwright", fake_sync_playwright)

        scraper = WorkdayScraper()
        result = scraper._scrape_once(
            "https://generalmotors.wd5.myworkdayjobs.com/Careers_GM/job/abc"
        )

        assert result is not None
        assert result.description == "Role details and responsibilities"
        assert page.closed
        assert context.closed
        assert browser.closed

    def test_scrape_once_uses_fallback_extraction_when_primary_missing(self, monkeypatch):
        """Fallback extraction path is used when primary selector is absent."""
        import src.posting_scrapers.base_scraper as base_module

        fake_sync_playwright, _page, _context, _browser = _build_fake_sync_playwright(
            locator_count=0,
            locator_text="",
            fallback_text="  Long fallback description text from page body.  ",
        )
        monkeypatch.setattr(base_module, "sync_playwright", fake_sync_playwright)

        scraper = WorkdayScraper()
        result = scraper._scrape_once(
            "https://rakuten.wd1.myworkdayjobs.com/Kobo/job/abc"
        )

        assert result is not None
        assert result.description == "Long fallback description text from page body."

    def test_scrape_once_returns_none_when_no_description_found(self, monkeypatch):
        """No primary or fallback description returns None."""
        import src.posting_scrapers.base_scraper as base_module

        fake_sync_playwright, _page, _context, _browser = _build_fake_sync_playwright(
            locator_count=0,
            locator_text="",
            fallback_text="",
        )
        monkeypatch.setattr(base_module, "sync_playwright", fake_sync_playwright)

        scraper = WorkdayScraper()
        result = scraper._scrape_once(
            "https://rakuten.wd1.myworkdayjobs.com/Kobo/job/abc"
        )

        assert result is None

    def test_scrape_once_timeout_maps_to_navigation_error(self, monkeypatch):
        """Playwright timeout is mapped to WorkdayNavigationError."""
        import src.posting_scrapers.base_scraper as base_module

        class FakeTimeoutError(Exception):
            """Fake timeout used to map to WorkdayNavigationError."""

        fake_sync_playwright, page, context, browser = _build_fake_sync_playwright(
            locator_count=1,
            locator_text="unused",
            fallback_text="",
            timeout_exc=FakeTimeoutError,
            raise_timeout=True,
        )
        monkeypatch.setattr(base_module, "sync_playwright", fake_sync_playwright)
        monkeypatch.setattr(base_module, "PlaywrightTimeoutError", FakeTimeoutError)

        scraper = WorkdayScraper(timeout_ms=50)

        with pytest.raises(WorkdayNavigationError):
            scraper._scrape_once(
                "https://generalmotors.wd5.myworkdayjobs.com/Careers_GM/job/abc"
            )

        assert page.closed
        assert context.closed
        assert browser.closed