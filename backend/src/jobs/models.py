from dataclasses import dataclass
from typing import Optional


@dataclass
class JobPosting:
    """Represents a job posting from the internship listings."""

    id: int
    company: str
    role: str
    location: str
    url: str
    date_posted: str
    posted_at_raw: Optional[str] = None
