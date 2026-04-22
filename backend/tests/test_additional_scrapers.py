"""Tests for Lever, Ashby, iCIMS, and fallback scrapers."""

from src.posting_scrapers.ashby_scraper import AshbyScraper
from src.posting_scrapers.fallback_scraper import FallbackScraper
from src.posting_scrapers.icims_scraper import ICIMSScraper
from src.posting_scrapers.lever_scraper import LeverScraper


class FakeLocator:
    """Simple locator stub for selector-based extraction tests."""

    def __init__(self, count_value: int, text: str):
        self._count_value = count_value
        self._text = text
        self.first = self

    def count(self) -> int:
        return self._count_value

    def inner_text(self) -> str:
        return self._text


class FakePage:
    """Simple page stub with selector text map and fallback evaluate text."""

    def __init__(self, selector_texts: dict[str, str], fallback_text: str = "") -> None:
        self.selector_texts = selector_texts
        self.fallback_text = fallback_text

    def locator(self, selector: str) -> FakeLocator:
        text = self.selector_texts.get(selector, "")
        count = 1 if text else 0
        return FakeLocator(count, text)

    def evaluate(self, _script: str) -> str:
        return self.fallback_text


class TestLeverScraper:
    """Validate Lever scraper URL matching and extraction behavior."""

    def test_supports_url(self):
        """Lever URL host is recognized."""
        assert LeverScraper.supports_url(
            "https://jobs.lever.co/benchsci/bac8e1ed-5a5c-4951-a8d8-8b4ce90701c4/"
        )

    def test_extracts_by_primary_selector(self):
        """Lever selector extraction returns normalized description."""
        page = FakePage(
            {
                ".posting-page .section-wrapper.page-full-width": (
                    " Lever description with responsibilities and qualifications. "
                )
            }
        )
        scraper = LeverScraper()

        result = scraper._extract_description(page)
        assert "Lever description" in result


class TestAshbyScraper:
    """Validate Ashby scraper URL matching and extraction behavior."""

    def test_supports_url(self):
        """Ashby URL host is recognized."""
        assert AshbyScraper.supports_url(
            "https://jobs.ashbyhq.com/tonal/0b7e9f3c-7658-4fef-8273-c7f12957c6cb/"
        )

    def test_fallback_evaluate_when_selector_missing(self):
        """Ashby fallback JS evaluation text is returned when selectors fail."""
        page = FakePage({}, fallback_text=" Ashby fallback description content ")
        scraper = AshbyScraper()

        result = scraper._extract_description(page)
        assert result == "Ashby fallback description content"


class TestICIMSScraper:
    """Validate iCIMS scraper URL matching and extraction behavior."""

    def test_supports_url(self):
        """iCIMS URL host is recognized."""
        assert ICIMSScraper.supports_url(
            "https://careersen-mackenzieinvestments.icims.com/jobs/5735/job"
        )

    def test_extracts_by_description_selector(self):
        """iCIMS selector extraction returns normalized description."""
        page = FakePage({"#job-description": " iCIMS job description block "})
        scraper = ICIMSScraper()

        result = scraper._extract_description(page)
        assert result == "iCIMS job description block"


class TestFallbackScraper:
    """Validate generic fallback scraper behavior."""

    def test_supports_any_http_url(self):
        """Fallback scraper accepts unknown HTTP URLs."""
        assert FallbackScraper.supports_url("https://example.com/jobs/123")

    def test_rejects_non_http_url(self):
        """Fallback scraper rejects non-http(s) URLs."""
        assert not FallbackScraper.supports_url("mailto:test@example.com")

    def test_extracts_using_generic_selectors(self):
        """Fallback uses generic selectors before JS evaluation."""
        page = FakePage({"[class*='job-description']": " Generic job description "})
        scraper = FallbackScraper()

        result = scraper._extract_description(page)
        assert result == "Generic job description"
