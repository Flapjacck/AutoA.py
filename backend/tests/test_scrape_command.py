"""Tests for the auto-detected scrape CLI command."""

from src.cli.commands.scrape import cmd_scrape
from src.jobs.models import JobPosting
from src.posting_scrapers.models import JobNavigationError, UnsupportedJobUrlError


class TestScrapeCommand:
    """Validate scrape command argument and output behavior."""

    def test_usage_when_no_args(self, capsys):
        """Command prints usage when no argument is provided."""
        cmd_scrape([])

        output = capsys.readouterr().out
        assert "Usage: scrape" in output

    def test_scrape_by_job_id_valid(self, reset_singleton, monkeypatch, capsys):
        """Command scrapes by job ID from cached job listings."""
        import src.cli.commands.scrape as scrape_module

        # Mock JobListingFetcher.get_jobs
        def fake_get_jobs(force_refresh=False):
            return [
                JobPosting(
                    id=1,
                    company="TechCorp",
                    role="Software Engineer",
                    location="Toronto, ON",
                    url="https://example.com/job1",
                    date_posted="2026-04-05",
                ),
                JobPosting(
                    id=2,
                    company="DataCo",
                    role="Data Analyst",
                    location="Vancouver, BC",
                    url="https://example.com/job2",
                    date_posted="2026-04-03",
                ),
            ]

        def fake_scrape_description_for_url(_url: str):
            return "lever", "A complete job description for this role."

        # Patch the fetcher
        from src.jobs.fetcher import JobListingFetcher
        from unittest.mock import MagicMock

        mock_fetcher = MagicMock()
        mock_fetcher.get_jobs = fake_get_jobs
        monkeypatch.setattr(JobListingFetcher, "__new__", lambda cls: mock_fetcher)

        # Patch the scraper
        monkeypatch.setattr(
            scrape_module,
            "scrape_description_for_url",
            fake_scrape_description_for_url,
        )

        cmd_scrape(["1"])

        output = capsys.readouterr().out
        assert "TechCorp" in output
        assert "Software Engineer" in output
        assert "Toronto, ON" in output
        assert "A complete job description for this role." in output
        assert "Job ID:" in output
        assert "1" in output

    def test_scrape_by_job_id_invalid_number_too_high(
        self, reset_singleton, monkeypatch, capsys
    ):
        """Command shows error with total job count when job ID is out of range."""
        import src.cli.commands.scrape as scrape_module

        def fake_get_jobs(force_refresh=False):
            return [
                JobPosting(
                    id=1,
                    company="TechCorp",
                    role="Software Engineer",
                    location="Toronto, ON",
                    url="https://example.com/job1",
                    date_posted="2026-04-05",
                ),
                JobPosting(
                    id=2,
                    company="DataCo",
                    role="Data Analyst",
                    location="Vancouver, BC",
                    url="https://example.com/job2",
                    date_posted="2026-04-03",
                ),
            ]

        from src.jobs.fetcher import JobListingFetcher
        from unittest.mock import MagicMock

        mock_fetcher = MagicMock()
        mock_fetcher.get_jobs = fake_get_jobs
        monkeypatch.setattr(JobListingFetcher, "__new__", lambda cls: mock_fetcher)

        cmd_scrape(["999"])

        output = capsys.readouterr().out
        assert "999" in output
        assert "not found" in output
        assert "Only" in output
        assert "jobs available" in output

    def test_scrape_by_url_valid(self, capsys, monkeypatch):
        """Command scrapes by URL (existing functionality preserved)."""
        import src.cli.commands.scrape as scrape_module

        def fake_scrape_description_for_url(_url: str):
            return "lever", "A complete job description"

        monkeypatch.setattr(
            scrape_module,
            "scrape_description_for_url",
            fake_scrape_description_for_url,
        )

        cmd_scrape(["https://jobs.lever.co/example/job-id"])

        output = capsys.readouterr().out
        assert "Detected source: lever" in output
        assert "A complete job description" in output
        assert "Scrape complete" in output

    def test_scrape_by_url_empty_description(self, capsys, monkeypatch):
        """Command prints no-description message when scraper returns None."""
        import src.cli.commands.scrape as scrape_module

        monkeypatch.setattr(
            scrape_module,
            "scrape_description_for_url",
            lambda _url: ("fallback", None),
        )

        cmd_scrape(["https://example.com/jobs/123"])

        output = capsys.readouterr().out
        assert "Detected source: fallback" in output
        assert "No description was found" in output

    def test_scrape_handles_unsupported_url_error(self, capsys, monkeypatch):
        """Command prints friendly message for unsupported URL errors."""
        import src.cli.commands.scrape as scrape_module

        def fake_scrape_description_for_url(_url: str):
            raise UnsupportedJobUrlError("Unsupported URL format")

        monkeypatch.setattr(
            scrape_module,
            "scrape_description_for_url",
            fake_scrape_description_for_url,
        )

        cmd_scrape(["invalid-url"])

        output = capsys.readouterr().out
        assert "Unsupported URL format" in output

    def test_scrape_handles_navigation_error(self, capsys, monkeypatch):
        """Command prints navigation failure details for transient page failures."""
        import src.cli.commands.scrape as scrape_module

        def fake_scrape_description_for_url(_url: str):
            raise JobNavigationError("Timed out loading page")

        monkeypatch.setattr(
            scrape_module,
            "scrape_description_for_url",
            fake_scrape_description_for_url,
        )

        cmd_scrape(["https://jobs.ashbyhq.com/tonal/job-id"])

        output = capsys.readouterr().out
        assert "Navigation failed" in output

    def test_scrape_by_job_id_zero_or_negative(
        self, reset_singleton, monkeypatch, capsys
    ):
        """Command shows error for invalid job ID (zero or negative)."""
        def fake_get_jobs(force_refresh=False):
            return [
                JobPosting(
                    id=1,
                    company="TechCorp",
                    role="Software Engineer",
                    location="Toronto, ON",
                    url="https://example.com/job1",
                    date_posted="2026-04-05",
                ),
            ]

        from src.jobs.fetcher import JobListingFetcher
        from unittest.mock import MagicMock

        mock_fetcher = MagicMock()
        mock_fetcher.get_jobs = fake_get_jobs
        monkeypatch.setattr(JobListingFetcher, "__new__", lambda cls: mock_fetcher)

        # Note: isdigit() returns False for negative numbers, so this will be treated as URL
        # But let's test the actual scenario if someone tries job ID 0 via a malformed argument
        # The current implementation won't hit negative paths due to isdigit() behavior
        # So we test the valid range validation instead
        cmd_scrape(["0"])

        output = capsys.readouterr().out
        # "0" is numeric but invalid, will be treated as URL (isdigit returns True for "0")
        # which will fail, so we expect either a scraper error or job not found
        # Actually, let me reconsider: isdigit("0") is True, so 0 is numeric
        # and will be treated as job ID. The _scrape_by_job_id will check if 0 < 1
        assert "not found" in output or "Job #0 not found" in output
