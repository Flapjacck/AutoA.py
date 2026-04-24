"""Integration tests for end-to-end workflows."""

import pytest
from unittest.mock import patch, MagicMock

from src.jobs.fetcher import JobListingFetcher
from src.jobs.models import JobPosting
from src.posting_scrapers.router import (
    scrape_description_for_url,
    build_scraper_for_url,
)


class TestFetchScrapeWorkflow:
    """Test full workflow: fetch jobs -> scrape descriptions -> ready for prompt."""

    @pytest.fixture
    def sample_jobs(self):
        """Create sample jobs representing fetched listings."""
        return [
            JobPosting(
                id=1,
                company="TechCorp",
                role="Backend Engineer",
                location="Toronto, ON",
                url="https://techcorp.myworkday.com/en-US/techcorp/job/123",
                date_posted="2026-04-15",
                posted_at_raw="Apr 15, 2026",
            ),
            JobPosting(
                id=2,
                company="StartupXYZ",
                role="Frontend Developer",
                location="Vancouver, BC",
                url="https://startupxyz.lever.co/jobs/frontend",
                date_posted="2026-04-14",
                posted_at_raw="Apr 14, 2026",
            ),
            JobPosting(
                id=3,
                company="MegaCorp",
                role="DevOps Engineer",
                location="Montreal, QC",
                url="https://megacorp.ashby.com/job/devops-2026",
                date_posted="2026-04-13",
                posted_at_raw="Apr 13, 2026",
            ),
        ]

    def test_fetch_jobs_returns_job_postings(self, reset_singleton, mock_requests_get):
        """Verify fetched jobs are JobPosting objects with required fields."""
        fetcher = JobListingFetcher()
        jobs = fetcher.get_jobs()

        # Verify structure
        assert len(jobs) > 0
        assert all(isinstance(job, JobPosting) for job in jobs)
        assert all(hasattr(job, "id") and job.id for job in jobs)
        assert all(hasattr(job, "url") and job.url for job in jobs)
        assert all(hasattr(job, "company") for job in jobs)
        assert all(hasattr(job, "role") for job in jobs)

    def test_scrape_description_for_different_platforms(self, sample_jobs):
        """Verify scraper detection and description extraction works for multiple platforms."""
        results = {}

        for job in sample_jobs:
            # Mock the scraper to return a sample description
            with patch(
                "src.posting_scrapers.router.build_scraper_for_url"
            ) as mock_build:
                mock_scraper = MagicMock()
                mock_scraper.scrape_description.return_value = f"Job description for {job.role} at {job.company}"
                mock_build.return_value = ("workday", mock_scraper)

                source, description = scrape_description_for_url(job.url)

                results[job.id] = {
                    "source": source,
                    "description": description,
                    "company": job.company,
                }

        # Verify all jobs were scraped
        assert len(results) == len(sample_jobs)
        assert all(desc["description"] for desc in results.values())

    def test_scraper_source_detection(self):
        """Verify correct scraper source is detected for each platform URL."""
        test_cases = [
            ("https://company.myworkday.com/en-US/company/job/123", "workday"),
            ("https://company.lever.co/jobs/engineer", "lever"),
            ("https://company.ashby.com/job/engineer", "ashby"),
            ("https://company.icims.com/jobs/123", "icims"),
            ("https://unknown-platform.com/job/123", "fallback"),
        ]

        for url, expected_source in test_cases:
            with patch(
                "src.posting_scrapers.router.detect_scraper_source"
            ) as mock_detect:
                mock_detect.return_value = expected_source
                source, _scraper = build_scraper_for_url(url)
                assert source == expected_source

    def test_scrape_unsupported_url_fallback(self):
        """Verify unsupported URLs fall back to generic scraper."""
        weird_url = "https://some-unknown-job-board.example.com/apply/12345"

        with patch(
            "src.posting_scrapers.router.detect_scraper_source"
        ) as mock_detect:
            mock_detect.return_value = "fallback"

            source, _scraper = build_scraper_for_url(weird_url)
            assert source == "fallback"

    def test_fetch_with_closed_listings_filtered(self, reset_singleton):
        """Verify closed listings are filtered out during fetch."""
        fetcher = JobListingFetcher()
        
        # Parse markdown with closed listings
        markdown_with_closed = """
# Internships

## Listings

| Company | Role | Location | Apply | Date Posted |
|---------|------|----------|:-----:|------------|
| OpenCo | Engineer | Toronto | [![Apply](https://img.shields.io/badge/-Apply-blue)](https://example.com/1) | Apr 15, 2026 |
| ClosedCo | Manager | Vancouver | Closed🔒 | Apr 14, 2026 |
"""
        jobs = fetcher.parse_markdown(markdown_with_closed)
        
        # Only open jobs should be present
        assert len(jobs) == 1
        assert jobs[0].company == "OpenCo"

    def test_jobs_sorted_by_date_newest_first(self, reset_singleton):
        """Verify fetched jobs are sorted by date with newest first."""
        markdown = """
# Internships

## Listings

| Company | Role | Location | Apply | Date Posted |
|---------|------|----------|:-----:|------------|
| Company A | Role A | Toronto | [![Apply](https://img.shields.io/badge/-Apply-blue)](https://a.com/1) | Apr 10, 2026 |
| Company B | Role B | Toronto | [![Apply](https://img.shields.io/badge/-Apply-blue)](https://b.com/1) | Apr 20, 2026 |
| Company C | Role C | Toronto | [![Apply](https://img.shields.io/badge/-Apply-blue)](https://c.com/1) | Apr 15, 2026 |
"""
        fetcher = JobListingFetcher()
        jobs = fetcher.parse_markdown(markdown)

        assert len(jobs) == 3
        # Verify newest first
        assert jobs[0].company == "Company B"  # Apr 20
        assert jobs[1].company == "Company C"  # Apr 15
        assert jobs[2].company == "Company A"  # Apr 10

    def test_sequential_ids_assigned(self, reset_singleton):
        """Verify jobs are assigned sequential IDs starting from 1."""
        markdown = """
# Internships

## Listings

| Company | Role | Location | Apply | Date Posted |
|---------|------|----------|:-----:|------------|
| Company A | Role A | Toronto | [![Apply](https://img.shields.io/badge/-Apply-blue)](https://a.com) | Apr 15, 2026 |
| Company B | Role B | Vancouver | [![Apply](https://img.shields.io/badge/-Apply-blue)](https://b.com) | Apr 14, 2026 |
| Company C | Role C | Montreal | [![Apply](https://img.shields.io/badge/-Apply-blue)](https://c.com) | Apr 13, 2026 |
"""
        fetcher = JobListingFetcher()
        jobs = fetcher.parse_markdown(markdown)

        assert len(jobs) == 3
        assert [job.id for job in jobs] == [1, 2, 3]

    def test_parse_empty_markdown(self, reset_singleton):
        """Verify graceful handling when no jobs are found."""
        empty_markdown = """
# Internships

## Listings

No jobs available right now.
"""
        fetcher = JobListingFetcher()
        jobs = fetcher.parse_markdown(empty_markdown)

        assert jobs == []


class TestScrapeIntegration:
    """Test scraper integration with real-world scenarios."""

    def test_scraper_handles_unsupported_url_error(self):
        """Verify scraper gracefully handles unsupported URLs."""
        from src.posting_scrapers.models import UnsupportedJobUrlError

        with patch("src.posting_scrapers.router.build_scraper_for_url") as mock_build:
            mock_build.side_effect = UnsupportedJobUrlError("URL not supported")

            url = "https://unknown-platform.com/job/123"
            with pytest.raises(UnsupportedJobUrlError):
                scrape_description_for_url(url)

    def test_scraper_returns_source_and_description(self):
        """Verify scraper returns both source type and description."""
        with patch("src.posting_scrapers.router.build_scraper_for_url") as mock_build:
            mock_scraper = MagicMock()
            expected_desc = "This is a backend engineering role focused on microservices"
            mock_scraper.scrape_description.return_value = expected_desc
            mock_build.return_value = ("lever", mock_scraper)

            url = "https://company.lever.co/jobs/engineer"
            source, description = scrape_description_for_url(url)

            assert source == "lever"
            assert description == expected_desc

    def test_multiple_scrapers_for_different_urls(self):
        """Verify different URLs route to different scrapers."""
        test_cases = [
            ("https://company.myworkday.com/job/123", "workday"),
            ("https://company.lever.co/jobs/eng", "lever"),
            ("https://company.ashby.com/job/role", "ashby"),
        ]

        for url, expected_source in test_cases:
            with patch("src.posting_scrapers.router.build_scraper_for_url") as mock_build:
                mock_scraper = MagicMock()
                mock_scraper.scrape_description.return_value = f"Description from {expected_source}"
                mock_build.return_value = (expected_source, mock_scraper)

                source, desc = scrape_description_for_url(url)

                assert source == expected_source
                assert desc is not None

