"""Tests for scraper URL detection and router behavior."""

import pytest

from src.posting_scrapers import build_scraper_for_url, detect_scraper_source
from src.posting_scrapers.ashby_scraper import AshbyScraper
from src.posting_scrapers.fallback_scraper import FallbackScraper
from src.posting_scrapers.icims_scraper import ICIMSScraper
from src.posting_scrapers.lever_scraper import LeverScraper
from src.posting_scrapers.models import UnsupportedJobUrlError
from src.posting_scrapers.workday_scraper import WorkdayScraper


class TestScraperDetection:
    """Validate URL source detection logic."""

    def test_detects_workday_url(self):
        """Workday hosts map to workday source."""
        source = detect_scraper_source(
            "https://generalmotors.wd5.myworkdayjobs.com/Careers_GM/job/abc"
        )
        assert source == "workday"

    def test_detects_lever_url(self):
        """Lever hosts map to lever source."""
        source = detect_scraper_source(
            "https://jobs.lever.co/benchsci/bac8e1ed-5a5c-4951-a8d8-8b4ce90701c4/"
        )
        assert source == "lever"

    def test_detects_ashby_url(self):
        """Ashby hosts map to ashby source."""
        source = detect_scraper_source(
            "https://jobs.ashbyhq.com/tonal/0b7e9f3c-7658-4fef-8273-c7f12957c6cb/"
        )
        assert source == "ashby"

    def test_detects_icims_url(self):
        """iCIMS hosts map to icims source."""
        source = detect_scraper_source(
            "https://careersen-mackenzieinvestments.icims.com/jobs/5735/job"
        )
        assert source == "icims"

    def test_detects_fallback_for_unknown_http_url(self):
        """Unknown valid job URLs map to fallback source."""
        source = detect_scraper_source("https://example.com/jobs/123")
        assert source == "fallback"

    def test_rejects_non_http_url(self):
        """Non-http(s) URLs are rejected with typed error."""
        with pytest.raises(UnsupportedJobUrlError):
            detect_scraper_source("mailto:test@example.com")


class TestScraperFactory:
    """Validate source-to-scraper factory mapping."""

    def test_builds_workday_scraper(self):
        """Factory returns Workday scraper for Workday URLs."""
        source, scraper = build_scraper_for_url(
            "https://generalmotors.wd5.myworkdayjobs.com/Careers_GM/job/abc"
        )

        assert source == "workday"
        assert isinstance(scraper, WorkdayScraper)

    def test_builds_lever_scraper(self):
        """Factory returns Lever scraper for Lever URLs."""
        source, scraper = build_scraper_for_url(
            "https://jobs.lever.co/benchsci/bac8e1ed-5a5c-4951-a8d8-8b4ce90701c4/"
        )

        assert source == "lever"
        assert isinstance(scraper, LeverScraper)

    def test_builds_ashby_scraper(self):
        """Factory returns Ashby scraper for Ashby URLs."""
        source, scraper = build_scraper_for_url(
            "https://jobs.ashbyhq.com/sentry/d2e3391f-9401-410a-b8a6-de3bf5f762b7/"
        )

        assert source == "ashby"
        assert isinstance(scraper, AshbyScraper)

    def test_builds_icims_scraper(self):
        """Factory returns iCIMS scraper for iCIMS URLs."""
        source, scraper = build_scraper_for_url(
            "https://careersen-mackenzieinvestments.icims.com/jobs/5735/job"
        )

        assert source == "icims"
        assert isinstance(scraper, ICIMSScraper)

    def test_builds_fallback_scraper(self):
        """Factory returns fallback scraper for unknown job URLs."""
        source, scraper = build_scraper_for_url("https://example.com/careers/job/123")

        assert source == "fallback"
        assert isinstance(scraper, FallbackScraper)
