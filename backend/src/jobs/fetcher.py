"""Fetch and parse job listings from GitHub's Canadian Tech Internships repo."""

import re
import time
from datetime import datetime, timedelta
from typing import Optional

import requests
from dateutil import parser as date_parser

from src.jobs.models import JobPosting
from src.logger import get_logger

logger = get_logger(__name__)

# Cache TTL in seconds (1 hour)
CACHE_TTL_SECONDS = 3600
# GitHub raw markdown URL
DEFAULT_GITHUB_URL = (
    "https://raw.githubusercontent.com/negarprh/Canadian-Tech-Internships-2026/"
    "main/README.md"
)


class JobListingFetcher:
    """Fetches and parses job listings from GitHub markdown.
    
    Singleton pattern ensures cache persists across multiple calls.
    """

    _instance = None

    def __new__(cls):
        """Ensure only one instance exists (singleton)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.cache = {}
        return cls._instance

    def fetch_from_github(self, url: str = DEFAULT_GITHUB_URL) -> str:
        """Fetch raw markdown from GitHub URL.

        Args:
            url: GitHub raw markdown URL.

        Returns:
            Raw markdown content.

        Raises:
            requests.RequestException: If fetch fails.
        """
        logger.info(f"Fetching job listings from GitHub: {url}")
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            logger.info(f"Successfully fetched {len(response.text)} bytes")
            return response.text
        except requests.Timeout:
            logger.error(f"Timeout fetching from GitHub after 10s")
            raise
        except requests.RequestException as e:
            logger.error(f"Failed to fetch from GitHub: {e}")
            raise

    def parse_markdown(self, content: str) -> list[JobPosting]:
        """Parse markdown table into JobPosting objects.

        Filters out closed listings and assigns sequential IDs.
        Sorts by date posted (newest first).

        Args:
            content: Raw markdown content.

        Returns:
            List of JobPosting objects, sorted by date (newest first).
        """
        logger.info("Parsing markdown content")
        jobs = []
        lines = content.split("\n")

        # Find the table start
        table_start = None
        for i, line in enumerate(lines):
            if "Company" in line and "Role" in line and "Apply" in line:
                table_start = i
                break

        if table_start is None:
            logger.warning("Could not find internship listings table in markdown")
            return []

        # Skip header and separator rows
        for i in range(table_start + 2, len(lines)):
            line = lines[i].strip()

            # Stop at end of table
            if not line or line.startswith("###"):
                break

            # Skip separator rows (all dashes)
            if all(c in "-|: " for c in line):
                continue

            # Parse row
            try:
                job = self._parse_row(line)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.warning(f"Failed to parse row: {line[:80]}... Error: {e}")
                continue

        # Sort by date (newest first)
        jobs.sort(key=lambda j: j.date_posted, reverse=True)

        # Assign sequential IDs after sorting
        for idx, job in enumerate(jobs, start=1):
            job.id = idx

        logger.info(f"Parsed {len(jobs)} open job listings")
        return jobs

    def _parse_row(self, row: str) -> Optional[JobPosting]:
        """Parse a single markdown table row into JobPosting.

        Args:
            row: Markdown table row string.

        Returns:
            JobPosting object or None if row is closed/invalid.
        """
        # Split by pipe, accounting for leading/trailing pipes
        parts = [p.strip() for p in row.split("|")]
        # Filter empty parts (from leading/trailing pipes)
        parts = [p for p in parts if p]

        if len(parts) < 5:
            logger.debug(f"Row has fewer than 5 columns: {row[:60]}...")
            return None

        company = parts[0]
        role = parts[1]
        location = parts[2]
        apply_cell = parts[3]
        date_posted_str = parts[4]

        # Filter out closed listings
        if "Closed" in apply_cell or "closed" in apply_cell:
            return None

        # Extract URL from markdown link format: [text](url) or [![Apply](...)](url)
        url_match = re.search(r"\]\(([^\)]+)\)$", apply_cell)
        if not url_match:
            logger.debug(f"Could not extract URL from apply cell: {apply_cell[:60]}...")
            return None

        url = url_match.group(1)

        # Parse date (pass current time as reference for future-date detection)
        try:
            reference_date = datetime.now()
            date_posted = self._parse_date(date_posted_str, reference_date)
        except Exception as e:
            logger.debug(f"Failed to parse date '{date_posted_str}': {e}")
            return None

        return JobPosting(
            id=0,  # Will be reassigned after sorting
            company=company,
            role=role,
            location=location,
            url=url,
            date_posted=date_posted,
            posted_at_raw=date_posted_str,
        )

    @staticmethod
    def _parse_date(date_str: str, reference_date: Optional[datetime] = None) -> str:
        """Parse date string and return ISO format string.
        
        Handles dates without explicit years that parse to the future by
        subtracting 1 year (assumes they are from the previous year).
        For example, "Dec 12" parsed on Apr 6, 2026 would become 2026-12-12,
        which is in the future. This method detects that and adjusts to 2025-12-12.

        Args:
            date_str: Date string (e.g., "Apr 1, 2026" or "Dec 12").
            reference_date: Date to use as "today" for future-date detection.
                           Defaults to datetime.now() if not provided.

        Returns:
            ISO format date string (YYYY-MM-DD).

        Raises:
            ValueError: If date cannot be parsed.
        """
        if reference_date is None:
            reference_date = datetime.now()
        
        parsed = date_parser.parse(date_str, fuzzy=True)
        
        # If parsed date is in the future relative to reference_date,
        # assume it's from the previous year (common for year-less dates)
        if parsed > reference_date:
            parsed = parsed.replace(year=parsed.year - 1)
            logger.debug(
                f"Adjusted future date '{date_str}' to previous year: "
                f"{parsed.strftime('%Y-%m-%d')}"
            )
        
        return parsed.strftime("%Y-%m-%d")

    def get_jobs(
        self, url: str = DEFAULT_GITHUB_URL, force_refresh: bool = False
    ) -> list[JobPosting]:
        """Fetch and parse jobs with caching.

        Returns cached jobs if available and not expired.
        Fetches fresh data if cache is empty, expired, or force_refresh=True.

        Args:
            url: GitHub raw markdown URL.
            force_refresh: Force fetch fresh data, bypassing cache.

        Returns:
            List of JobPosting objects, sorted by date (newest first).
        """
        # Check cache
        if not force_refresh and url in self.cache:
            data, timestamp = self.cache[url]
            age_seconds = time.time() - timestamp
            if age_seconds < CACHE_TTL_SECONDS:
                logger.info(
                    f"Returning cached jobs (age: {age_seconds:.0f}s, "
                    f"TTL: {CACHE_TTL_SECONDS}s)"
                )
                return data

        # Fetch fresh data
        try:
            markdown = self.fetch_from_github(url)
            jobs = self.parse_markdown(markdown)
            self.cache[url] = (jobs, time.time())
            return jobs
        except requests.RequestException:
            logger.warning("Failed to fetch fresh data from GitHub")
            # Return cached data if available, even if expired
            if url in self.cache:
                data, _ = self.cache[url]
                logger.info(f"Returning expired cached data ({len(data)} jobs)")
                return data
            # No cache available, return empty list
            return []
