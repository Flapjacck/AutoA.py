"""Pytest configuration and shared fixtures."""

import pytest

from src.jobs.models import JobPosting


# Sample markdown table data for testing
SAMPLE_MARKDOWN = """
# 🍁 Canadian Tech Internships - 2026

Some intro text here...

## 💼 Internship Listings

| Company | Role | Location | Apply | Date Posted |
|--------|------|----------|:-----:|--------------|
| Company A | Role 1 | Toronto, ON | [![Apply](https://img.shields.io/badge/-Apply-blue?style=for-the-badge)](https://example.com/job1) | Apr 5, 2026 |
| Company B | Role 2 | Vancouver, BC | [![Apply](https://img.shields.io/badge/-Apply-blue?style=for-the-badge)](https://example.com/job2) | Apr 3, 2026 |
| Company C | Role 3 | Montreal, QC | Closed🔒 | Apr 2, 2026 |
| Company D | Role 4 | Calgary, AB | [![Apply](https://img.shields.io/badge/-Apply-blue?style=for-the-badge)](https://example.com/job4) | Mar 31, 2026 |
| Company E | Role 5 | Ottawa, ON | [![Apply](https://img.shields.io/badge/-Apply-blue?style=for-the-badge)](https://example.com/job5) | Mar 28, 2026 |

Some footer text...
"""

SAMPLE_MARKDOWN_NO_CLOSED = """
# Internships

## Listings

| Company | Role | Location | Apply | Date Posted |
|--------|------|----------|:-----:|--------------|
| TestCo | Backend Engineer | Toronto, ON | [![Apply](https://img.shields.io/badge/-Apply-blue?style=for-the-badge)](https://test.com/1) | Feb 15, 2026 |
"""


@pytest.fixture
def reset_singleton():
    """Reset JobListingFetcher singleton cache before each test."""
    from src.jobs.fetcher import JobListingFetcher

    # Reset the singleton
    JobListingFetcher._instance = None
    yield
    # Cleanup after test
    JobListingFetcher._instance = None


@pytest.fixture
def sample_markdown():
    """Markdown content with mixed open/closed listings."""
    return SAMPLE_MARKDOWN


@pytest.fixture
def sample_markdown_minimal():
    """Minimal markdown with one open listing."""
    return SAMPLE_MARKDOWN_NO_CLOSED


@pytest.fixture
def mock_requests_get(monkeypatch):
    """Mock requests.get to return sample markdown."""
    import requests

    class MockResponse:
        def __init__(self, text, status_code=200):
            self.text = text
            self.status_code = status_code

        def raise_for_status(self):
            if self.status_code != 200:
                raise requests.HTTPError(f"Status {self.status_code}")

    def mock_get(url, timeout=None):
        return MockResponse(SAMPLE_MARKDOWN)

    monkeypatch.setattr(requests, "get", mock_get)
    return mock_get


@pytest.fixture
def mock_requests_timeout(monkeypatch):
    """Mock requests.get to raise timeout."""
    import requests

    def mock_get(url, timeout=None):
        raise requests.Timeout("Connection timeout")

    monkeypatch.setattr(requests, "get", mock_get)


@pytest.fixture
def sample_job_posting() -> JobPosting:
    """Sample job posting for CLI tests."""
    return JobPosting(
        id=3,
        company="Example Co",
        role="Software Engineer Intern",
        location="Toronto, ON",
        url="https://example.com/jobs/3",
        date_posted="2026-04-06",
        posted_at_raw="Apr 6, 2026",
    )





# Sample resume text for testing
SAMPLE_RESUME = """John Doe
Software Engineer
(613) 555-0123 | john@example.com | github.com/johndoe

SKILLS
Languages: Python, JavaScript, SQL, C++
Tools & Frameworks: Git, Docker, AWS, Flask, React, PostgreSQL
Soft Skills: Communication, Problem-solving, Leadership

EXPERIENCE
Backend Engineer Intern | TechCorp | Apr 2025 - Aug 2025
- Developed REST APIs using Flask and PostgreSQL, serving 10k+ daily requests
- Wrote unit tests with 85% code coverage using pytest
- Collaborated with 5 engineers on microservices migration reducing latency by 40%
- Deployed infrastructure as code using Terraform and AWS CloudFormation

Full Stack Developer Intern | InnovateLabs | Sep 2024 - Dec 2024
- Built React components with Redux state management for internal dashboards
- Integrated GitHub API for automated CI/CD pipeline monitoring
- Mentored 2 junior developers on best practices and code reviews

EDUCATION
B.Sc. Computer Science | University of Toronto | 2026
GPA: 3.8/4.0 | Relevant Coursework: Data Structures, Algorithms, Systems Design
Dean's Honor List (2022-2026)
"""


@pytest.fixture
def sample_resume_text() -> str:
    """Sample resume text for testing."""
    return SAMPLE_RESUME


@pytest.fixture
def temp_resume_file():
    """Create a temporary resume file for testing cleanup."""
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        resume_file = Path(tmpdir) / "resume.txt"
        yield resume_file
        # Cleanup happens automatically when context exits

