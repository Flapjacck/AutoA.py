"""Tests for job listing fetcher module."""

import time

import pytest
import requests

from src.jobs.fetcher import CACHE_TTL_SECONDS, JobListingFetcher


class TestJobListingFetcherParsing:
    """Test markdown parsing functionality."""

    def test_parse_markdown_basic(self, reset_singleton, sample_markdown):
        """Parse markdown and return JobPosting list."""
        fetcher = JobListingFetcher()
        jobs = fetcher.parse_markdown(sample_markdown)

        assert len(jobs) == 4  # 5 rows - 1 closed = 4 open
        assert all(hasattr(job, "id") for job in jobs)
        assert all(hasattr(job, "company") for job in jobs)
        assert all(hasattr(job, "role") for job in jobs)
        assert all(hasattr(job, "location") for job in jobs)
        assert all(hasattr(job, "url") for job in jobs)
        assert all(hasattr(job, "date_posted") for job in jobs)

    def test_filter_closed_listings(self, sample_markdown):
        """Closed listings are filtered out."""
        fetcher = JobListingFetcher()
        jobs = fetcher.parse_markdown(sample_markdown)

        # Company C has "Closed" in apply column and should be excluded
        company_names = [job.company for job in jobs]
        assert "Company C" not in company_names
        assert all("Closed" not in job.company for job in jobs)

    def test_extract_fields_correctly(self, sample_markdown):
        """Extract all required fields from row."""
        fetcher = JobListingFetcher()
        jobs = fetcher.parse_markdown(sample_markdown)

        job = next(j for j in jobs if j.company == "Company A")
        assert job.company == "Company A"
        assert job.role == "Role 1"
        assert job.location == "Toronto, ON"
        assert job.url == "https://example.com/job1"
        assert job.date_posted == "2026-04-05"

    def test_sequential_ids_assigned(self, sample_markdown):
        """IDs are sequential starting from 1."""
        fetcher = JobListingFetcher()
        jobs = fetcher.parse_markdown(sample_markdown)

        ids = [job.id for job in jobs]
        assert ids == list(range(1, len(jobs) + 1))

    def test_sorted_by_date_newest_first(self, sample_markdown):
        """Jobs sorted by date posted (newest first)."""
        fetcher = JobListingFetcher()
        jobs = fetcher.parse_markdown(sample_markdown)

        # Expected order (newest first): Apr 5, Apr 3, Mar 31, Mar 28
        dates = [job.posted_at_raw for job in jobs]
        assert dates == ["Apr 5, 2026", "Apr 3, 2026", "Mar 31, 2026", "Mar 28, 2026"]

    def test_parse_date_formats(self):
        """Parse various date formats."""
        fetcher = JobListingFetcher()

        test_cases = [
            ("Apr 1, 2026", "2026-04-01"),
            ("March 31, 2026", "2026-03-31"),
            ("Mar 10, 2026", "2026-03-10"),
            ("February 28, 2026", "2026-02-28"),
        ]

        for date_str, expected in test_cases:
            result = fetcher._parse_date(date_str)
            assert result == expected, f"Failed to parse {date_str}"

    def test_parse_date_without_year_adjusted_when_future(self):
        """Dates without years that parse to future are adjusted to previous year."""
        from datetime import datetime
        
        fetcher = JobListingFetcher()
        # Reference date: April 6, 2026 (today in the test)
        reference_date = datetime(2026, 4, 6)
        
        # "Dec 12" without year would parse to 2026-12-12 (future from Apr 6, 2026)
        # Should be adjusted to 2025-12-12 (previous year)
        result = fetcher._parse_date("Dec 12", reference_date=reference_date)
        assert result == "2025-12-12"
        
        # "Nov 13" without year would parse to 2026-11-13 (future)
        # Should be adjusted to 2025-11-13
        result = fetcher._parse_date("Nov 13", reference_date=reference_date)
        assert result == "2025-11-13"
        
        # "Mar 28" without year would parse to 2026-03-28 (past from Apr 6, 2026)
        # Should NOT be adjusted
        result = fetcher._parse_date("Mar 28", reference_date=reference_date)
        assert result == "2026-03-28"

    def test_parse_markdown_empty_content(self):
        """Handle empty markdown gracefully."""
        fetcher = JobListingFetcher()
        jobs = fetcher.parse_markdown("")

        assert jobs == []

    def test_parse_markdown_no_table(self):
        """Handle markdown without table gracefully."""
        content = "# Some content\nNo table here\nJust text"
        fetcher = JobListingFetcher()
        jobs = fetcher.parse_markdown(content)

        assert jobs == []

    def test_extract_url_from_markdown_link(self):
        """Extract URL from markdown link in apply cell."""
        fetcher = JobListingFetcher()
        markdown = """
| Company | Role | Location | Apply | Date Posted |
|--------|------|----------|:-----:|--------------|
| Test | Dev | Toronto | [![Apply](x)](https://myurl.com/job) | Apr 1, 2026 |
"""
        jobs = fetcher.parse_markdown(markdown)
        assert len(jobs) == 1
        assert jobs[0].url == "https://myurl.com/job"


class TestJobListingFetcherCache:
    """Test caching functionality."""

    def test_cache_stores_jobs(self, reset_singleton, mock_requests_get):
        """Jobs are cached after fetch."""
        fetcher = JobListingFetcher()
        url = "https://example.com/test"

        jobs = fetcher.get_jobs(url=url)

        assert url in fetcher.cache
        cached_jobs, _ = fetcher.cache[url]
        assert len(cached_jobs) == len(jobs)

    def test_cache_hit_returns_cached_data(self, reset_singleton, mock_requests_get):
        """Second call returns cached data without fetching."""
        fetcher = JobListingFetcher()
        url = "https://example.com/test"

        # First call
        jobs1 = fetcher.get_jobs(url=url)
        cached_jobs, timestamp1 = fetcher.cache[url]

        # Second call (should return cache)
        jobs2 = fetcher.get_jobs(url=url)
        _, timestamp2 = fetcher.cache[url]

        assert timestamp1 == timestamp2  # Cache timestamp unchanged
        assert jobs1 == jobs2
        assert len(jobs2) == 4

    def test_cache_expires_after_ttl(self, reset_singleton, mock_requests_get, monkeypatch):
        """Cache is refreshed after TTL expires."""
        fetcher = JobListingFetcher()
        url = "https://example.com/test"

        # First call
        fetcher.get_jobs(url=url)
        timestamp1 = fetcher.cache[url][1]

        # Mock time to advance past TTL
        monkeypatch.setattr(
            "src.jobs.fetcher.time.time",
            lambda: timestamp1 + CACHE_TTL_SECONDS + 1,
        )

        # Second call (cache expired, should refetch)
        fetcher.get_jobs(url=url)
        timestamp2 = fetcher.cache[url][1]

        assert timestamp2 > timestamp1

    def test_force_refresh_bypasses_cache(self, reset_singleton, mock_requests_get):
        """force_refresh=True bypasses cache."""
        fetcher = JobListingFetcher()
        url = "https://example.com/test"

        # First call
        fetcher.get_jobs(url=url)
        timestamp1 = fetcher.cache[url][1]

        # Second call with force_refresh
        fetcher.get_jobs(url=url, force_refresh=True)
        timestamp2 = fetcher.cache[url][1]

        assert timestamp2 > timestamp1

    def test_returns_expired_cache_on_fetch_error(self, reset_singleton, monkeypatch):
        """Returns expired cached data if fetch fails."""
        fetcher = JobListingFetcher()
        
        # Manually set cache with old timestamp
        old_jobs = [type('Job', (), {'id': 1, 'company': 'OldCo'})()]
        fetcher.cache["https://example.com"] = (old_jobs, 0)

        # Mock fetch to fail
        import requests
        monkeypatch.setattr(
            requests,
            "get",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                requests.Timeout("timeout")
            ),
        )

        # Should return cached data despite expiration
        result = fetcher.get_jobs(url="https://example.com")
        assert len(result) == 1

    def test_returns_empty_on_fetch_error_no_cache(self, reset_singleton, monkeypatch):
        """Returns empty list if fetch fails and no cache available."""
        fetcher = JobListingFetcher()

        # Mock fetch to fail
        import requests
        monkeypatch.setattr(
            requests,
            "get",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                requests.Timeout("timeout")
            ),
        )

        result = fetcher.get_jobs(url="https://example.com")
        assert result == []


class TestJobListingFetcherFetch:
    """Test GitHub fetching functionality."""

    def test_fetch_from_github_success(self, reset_singleton, mock_requests_get):
        """Successfully fetch markdown from GitHub."""
        fetcher = JobListingFetcher()
        content = fetcher.fetch_from_github("https://example.com")

        assert isinstance(content, str)
        assert len(content) > 0
        assert "Company A" in content

    def test_fetch_from_github_timeout_raises(self, reset_singleton, mock_requests_timeout):
        """Timeout during fetch raises exception."""
        fetcher = JobListingFetcher()

        with pytest.raises(requests.Timeout):
            fetcher.fetch_from_github("https://example.com")

    def test_fetch_http_error_raises(self, reset_singleton, monkeypatch):
        """HTTP errors raise exception."""
        import requests

        class MockResponse:
            status_code = 404

            def raise_for_status(self):
                raise requests.HTTPError("404 Not Found")

        monkeypatch.setattr(
            requests, "get", lambda *args, **kwargs: MockResponse()
        )

        fetcher = JobListingFetcher()
        with pytest.raises(requests.HTTPError):
            fetcher.fetch_from_github("https://example.com")


class TestIntegration:
    """Integration tests."""

    def test_get_jobs_end_to_end(self, reset_singleton, mock_requests_get):
        """Full pipeline: fetch -> parse -> cache -> return."""
        fetcher = JobListingFetcher()
        jobs = fetcher.get_jobs()

        # Verify count
        assert len(jobs) == 4

        # Verify sorting (newest first)
        assert jobs[0].posted_at_raw == "Apr 5, 2026"
        assert jobs[1].posted_at_raw == "Apr 3, 2026"
        assert jobs[-1].posted_at_raw == "Mar 28, 2026"

        # Verify IDs
        assert jobs[0].id == 1
        assert jobs[-1].id == 4

        # Verify all required fields present
        for job in jobs:
            assert job.id > 0
            assert job.company
            assert job.role
            assert job.location
            assert job.url.startswith("http")
            assert job.date_posted

    def test_no_closed_listings_in_result(self, reset_singleton, mock_requests_get):
        """Result never includes closed listings."""
        fetcher = JobListingFetcher()
        jobs = fetcher.get_jobs()

        for job in jobs:
            assert "Closed" not in job.role
            assert "Closed" not in job.company
            assert "closed" not in job.url.lower()
