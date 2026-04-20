"""Tests for the prompt command."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from src.cli.commands.prompt import cmd_prompt, _generate_prompt_for_job_id, RESUME_TAILOR_SYSTEM_PROMPT
from src.jobs.models import JobPosting


@pytest.fixture
def sample_jobs():
    """Sample job listings for testing."""
    return [
        JobPosting(
            id=1,
            company="TechCorp",
            role="Backend Engineer Intern",
            location="Toronto, ON",
            url="https://techcorp.myworkdayjobs.com/en-US/job/123",
            date_posted="2026-04-05",
            posted_at_raw="Apr 5, 2026",
        ),
        JobPosting(
            id=2,
            company="InnovateLabs",
            role="Frontend Developer Intern",
            location="Vancouver, BC",
            url="https://innovatelabs.com/jobs/456",
            date_posted="2026-04-03",
            posted_at_raw="Apr 3, 2026",
        ),
        JobPosting(
            id=3,
            company="StartupXYZ",
            role="DevOps Engineer Intern",
            location="Montreal, QC",
            url="https://startupxyz.lever.co/apply/789",
            date_posted="2026-03-31",
            posted_at_raw="Mar 31, 2026",
        ),
    ]


class TestCmdPrompt:
    """Test cmd_prompt command parsing."""

    def test_cmd_prompt_missing_args(self):
        """Test prompt command with no job ID."""
        with patch("src.cli.commands.prompt.print_error") as mock_error:
            cmd_prompt([])
            mock_error.assert_called_once_with("Usage: prompt <job_id>")

    def test_cmd_prompt_empty_string_arg(self):
        """Test prompt command with empty string argument."""
        with patch("src.cli.commands.prompt.print_error") as mock_error:
            cmd_prompt([""])
            mock_error.assert_called_once_with("Usage: prompt <job_id>")

    def test_cmd_prompt_invalid_job_id(self):
        """Test prompt command with non-numeric job ID."""
        with patch("src.cli.commands.prompt.print_error") as mock_error:
            cmd_prompt(["abc"])
            mock_error.assert_called_once_with("Usage: prompt <job_id>")

    def test_cmd_prompt_valid_job_id(self, sample_jobs):
        """Test prompt command with valid job ID."""
        with patch("src.cli.commands.prompt._generate_prompt_for_job_id") as mock_generate:
            cmd_prompt(["1"])
            mock_generate.assert_called_once_with(1)

    def test_cmd_prompt_whitespace_job_id(self, sample_jobs):
        """Test prompt command with job ID surrounded by whitespace."""
        with patch("src.cli.commands.prompt._generate_prompt_for_job_id") as mock_generate:
            cmd_prompt(["  2  "])
            mock_generate.assert_called_once_with(2)


class TestGeneratePromptForJobId:
    """Test _generate_prompt_for_job_id function."""

    def test_job_id_out_of_range_too_low(self, sample_jobs):
        """Test job ID less than 1."""
        with patch("src.cli.commands.prompt.JobListingFetcher") as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.get_jobs.return_value = sample_jobs
            mock_fetcher_class.return_value = mock_fetcher

            with patch("src.cli.commands.prompt.print_error") as mock_error:
                _generate_prompt_for_job_id(0)
                mock_error.assert_called_once()
                assert "not found" in mock_error.call_args[0][0]

    def test_job_id_out_of_range_too_high(self, sample_jobs):
        """Test job ID greater than available jobs."""
        with patch("src.cli.commands.prompt.JobListingFetcher") as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.get_jobs.return_value = sample_jobs
            mock_fetcher_class.return_value = mock_fetcher

            with patch("src.cli.commands.prompt.print_error") as mock_error:
                _generate_prompt_for_job_id(100)
                mock_error.assert_called_once()
                assert "not found" in mock_error.call_args[0][0]

    def test_user_aborts_confirmation(self, sample_jobs):
        """Test user saying 'no' at confirmation prompt."""
        with patch("src.cli.commands.prompt.JobListingFetcher") as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.get_jobs.return_value = sample_jobs
            mock_fetcher_class.return_value = mock_fetcher

            with patch("sys.stdin.readline", return_value="n\n"):
                with patch("src.cli.commands.prompt.print_info") as mock_info:
                    _generate_prompt_for_job_id(1)
                    # Check that "Aborted" message was printed
                    assert any("Abort" in str(call) for call in mock_info.call_args_list)

    def test_successful_prompt_generation_with_description(self, sample_jobs):
        """Test successful prompt generation with scraped description."""
        with patch("src.cli.commands.prompt.JobListingFetcher") as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.get_jobs.return_value = sample_jobs
            mock_fetcher_class.return_value = mock_fetcher

            test_description = "Join our team as a Backend Engineer. We use Python, PostgreSQL, and AWS."

            with patch("src.cli.commands.prompt.scrape_description_for_url") as mock_scrape:
                mock_scrape.return_value = ("workday", test_description)

                with patch("sys.stdin.readline", return_value="y\n"):
                    with patch("src.cli.commands.prompt._copy_to_clipboard") as mock_copy:
                        with patch("src.cli.commands.prompt.console.print"):
                            _generate_prompt_for_job_id(1)

                            # Verify scraping was called with correct URL
                            mock_scrape.assert_called_once_with(sample_jobs[0].url)

                            # Verify clipboard copy was called
                            mock_copy.assert_called_once()

                            # Check clipboard contains job data
                            clipboard_text = mock_copy.call_args[0][0]
                            assert "TechCorp" in clipboard_text
                            assert "Backend Engineer Intern" in clipboard_text
                            assert "Toronto, ON" in clipboard_text
                            assert test_description in clipboard_text

    def test_prompt_generation_with_empty_description(self, sample_jobs):
        """Test prompt generation when scraper returns empty description."""
        with patch("src.cli.commands.prompt.JobListingFetcher") as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.get_jobs.return_value = sample_jobs
            mock_fetcher_class.return_value = mock_fetcher

            with patch("src.cli.commands.prompt.scrape_description_for_url") as mock_scrape:
                mock_scrape.return_value = ("unknown", "")

                with patch("sys.stdin.readline", return_value="y\n"):
                    with patch("src.cli.commands.prompt._copy_to_clipboard") as mock_copy:
                        with patch("src.cli.commands.prompt.console.print"):
                            with patch("src.cli.commands.prompt.print_info"):
                                _generate_prompt_for_job_id(2)

                                # Verify clipboard was still called (with fallback message)
                                mock_copy.assert_called_once()
                                clipboard_text = mock_copy.call_args[0][0]
                                assert "InnovateLabs" in clipboard_text
                                assert "Frontend Developer Intern" in clipboard_text

    def test_prompt_template_structure(self, sample_jobs):
        """Test that prompt template includes required sections."""
        with patch("src.cli.commands.prompt.JobListingFetcher") as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.get_jobs.return_value = sample_jobs
            mock_fetcher_class.return_value = mock_fetcher

            test_description = "This is a test job description."

            with patch("src.cli.commands.prompt.scrape_description_for_url") as mock_scrape:
                mock_scrape.return_value = ("lever", test_description)

                with patch("sys.stdin.readline", return_value="y\n"):
                    with patch("src.cli.commands.prompt._copy_to_clipboard") as mock_copy:
                        with patch("src.cli.commands.prompt.console.print"):
                            _generate_prompt_for_job_id(3)

                            clipboard_text = mock_copy.call_args[0][0]

                            # Check required prompt sections exist
                            assert "System Persona & Objective" in clipboard_text
                            assert "Phase 1: Deep Analysis" in clipboard_text
                            assert "Phase 2: Surgical Resume Optimization" in clipboard_text
                            assert "Phase 3: Required Output Format" in clipboard_text
                            assert "TARGET COMPANY & JOB DESCRIPTION:" in clipboard_text
                            assert "MY CURRENT RESUME:" in clipboard_text

    def test_scraper_error_handling(self, sample_jobs):
        """Test handling of scraper exceptions."""
        from src.posting_scrapers import JobScraperError

        with patch("src.cli.commands.prompt.JobListingFetcher") as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.get_jobs.return_value = sample_jobs
            mock_fetcher_class.return_value = mock_fetcher

            with patch("src.cli.commands.prompt.scrape_description_for_url") as mock_scrape:
                mock_scrape.side_effect = JobScraperError("Scraper failed")

                with patch("sys.stdin.readline", return_value="y\n"):
                    with patch("src.cli.commands.prompt.print_error") as mock_error:
                        _generate_prompt_for_job_id(1)
                        # Verify error was handled gracefully
                        mock_error.assert_called()

    def test_clipboard_copy_called_with_full_prompt(self, sample_jobs):
        """Test that clipboard is called with the full formatted prompt."""
        with patch("src.cli.commands.prompt.JobListingFetcher") as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.get_jobs.return_value = sample_jobs
            mock_fetcher_class.return_value = mock_fetcher

            test_description = "Required: 3+ years of Python experience"

            with patch("src.cli.commands.prompt.scrape_description_for_url") as mock_scrape:
                mock_scrape.return_value = ("workday", test_description)

                with patch("sys.stdin.readline", return_value="y\n"):
                    with patch("src.cli.commands.prompt._copy_to_clipboard") as mock_copy:
                        with patch("src.cli.commands.prompt.console.print"):
                            _generate_prompt_for_job_id(1)

                            # Verify _copy_to_clipboard was called
                            mock_copy.assert_called_once()

                            # Extract the prompt text passed to clipboard
                            prompt_text = mock_copy.call_args[0][0]

                            # It should be a string and contain key placeholders filled in
                            assert isinstance(prompt_text, str)
                            assert len(prompt_text) > len(RESUME_TAILOR_SYSTEM_PROMPT)
                            assert "Company: TechCorp" in prompt_text
                            assert "Role: Backend Engineer Intern" in prompt_text


class TestPromptWithResume:
    """Test resume integration with prompt command."""

    def test_prompt_includes_resume_when_available(self, sample_jobs):
        """Test that resume is included in prompt when file exists."""
        sample_resume = "John Doe\nSoftware Engineer\nPython, JavaScript, AWS"

        with patch("src.cli.commands.prompt.JobListingFetcher") as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.get_jobs.return_value = sample_jobs
            mock_fetcher_class.return_value = mock_fetcher

            test_description = "Backend Engineer role"

            with patch("src.cli.commands.prompt.scrape_description_for_url") as mock_scrape:
                mock_scrape.return_value = ("workday", test_description)

                with patch("sys.stdin.readline", return_value="y\n"):
                    with patch("src.cli.commands.prompt._load_resume", return_value=sample_resume):
                        with patch("src.cli.commands.prompt._copy_to_clipboard") as mock_copy:
                            with patch("src.cli.commands.prompt.console.print"):
                                with patch("src.cli.commands.prompt.print_info") as mock_info:
                                    _generate_prompt_for_job_id(1)

                                    # Verify resume included message
                                    assert any(
                                        "Resume included" in str(call)
                                        for call in mock_info.call_args_list
                                    )

                                    # Verify resume is in clipboard
                                    clipboard_text = mock_copy.call_args[0][0]
                                    assert "---\nRESUME:\n" in clipboard_text
                                    assert sample_resume in clipboard_text

    def test_prompt_warns_when_resume_missing(self, sample_jobs):
        """Test warning message when no resume is set."""
        with patch("src.cli.commands.prompt.JobListingFetcher") as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.get_jobs.return_value = sample_jobs
            mock_fetcher_class.return_value = mock_fetcher

            test_description = "Frontend Engineer role"

            with patch("src.cli.commands.prompt.scrape_description_for_url") as mock_scrape:
                mock_scrape.return_value = ("lever", test_description)

                with patch("sys.stdin.readline", return_value="y\n"):
                    with patch("src.cli.commands.prompt._load_resume", return_value=None):
                        with patch("src.cli.commands.prompt._copy_to_clipboard") as mock_copy:
                            with patch("src.cli.commands.prompt.console.print"):
                                with patch("src.cli.commands.prompt.print_info") as mock_info:
                                    _generate_prompt_for_job_id(2)

                                    # Verify warning message about resume
                                    assert any(
                                        "No resume set" in str(call) or "resume -u" in str(call)
                                        for call in mock_info.call_args_list
                                    )

                                    # Verify clipboard was still called (no resume appended)
                                    mock_copy.assert_called_once()
                                    clipboard_text = mock_copy.call_args[0][0]
                                    assert "---\nRESUME:\n" not in clipboard_text

    def test_prompt_separator_format_correct(self, sample_jobs):
        """Test that resume separator is correctly formatted."""
        sample_resume = "Jane Smith\nData Scientist"

        with patch("src.cli.commands.prompt.JobListingFetcher") as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.get_jobs.return_value = sample_jobs
            mock_fetcher_class.return_value = mock_fetcher

            with patch("src.cli.commands.prompt.scrape_description_for_url") as mock_scrape:
                mock_scrape.return_value = ("workday", "Data role")

                with patch("sys.stdin.readline", return_value="y\n"):
                    with patch("src.cli.commands.prompt._load_resume", return_value=sample_resume):
                        with patch("src.cli.commands.prompt._copy_to_clipboard") as mock_copy:
                            with patch("src.cli.commands.prompt.console.print"):
                                _generate_prompt_for_job_id(3)

                                clipboard_text = mock_copy.call_args[0][0]

                                # Check exact separator format
                                assert "\n\n---\nRESUME:\n" in clipboard_text

                                # Check content order: prompt description comes before resume
                                prompt_idx = clipboard_text.find("Description: Data role")
                                resume_idx = clipboard_text.find("---\nRESUME:\n")
                                assert prompt_idx < resume_idx

    def test_prompt_with_multiline_resume(self, sample_jobs):
        """Test prompt correctly handles multiline resume."""
        sample_resume = """John Doe
Software Engineer Intern
john@example.com

SKILLS
Python, JavaScript, React, AWS
Docker, PostgreSQL

EXPERIENCE
Backend Engineer | TechCorp | 2025
- Built REST APIs
- Wrote unit tests"""

        with patch("src.cli.commands.prompt.JobListingFetcher") as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.get_jobs.return_value = sample_jobs
            mock_fetcher_class.return_value = mock_fetcher

            with patch("src.cli.commands.prompt.scrape_description_for_url") as mock_scrape:
                mock_scrape.return_value = ("workday", "Backend role")

                with patch("sys.stdin.readline", return_value="y\n"):
                    with patch("src.cli.commands.prompt._load_resume", return_value=sample_resume):
                        with patch("src.cli.commands.prompt._copy_to_clipboard") as mock_copy:
                            with patch("src.cli.commands.prompt.console.print"):
                                _generate_prompt_for_job_id(1)

                                clipboard_text = mock_copy.call_args[0][0]

                                # Verify all resume content is preserved
                                assert "SKILLS" in clipboard_text
                                assert "EXPERIENCE" in clipboard_text
                                assert "Built REST APIs" in clipboard_text
                                assert "john@example.com" in clipboard_text

