# AutoA Backend

Resume tailoring automation for internship applications. Fetches job listings, scrapes job descriptions with auto-detection, and generates tailored resumes.

## Setup

### Prerequisites

- Python 3.11+
- `uv` package manager

### Installation

1. Create and activate virtual environment:

```bash
uv venv
```

1. Install dependencies:

```bash
uv pip install -e ".[dev]"
```

1. Install Playwright browser binaries:

```bash
playwright install chromium
```

## CLI Commands

The backend provides an interactive CLI shell with the following commands:

### Job Listings

#### `jobs [page]`

Display cached job listings (10 per page).

```bash
jobs       # Show page 1
jobs 2     # Show page 2
```

**Use Case:** Browse the job listings fetched from the Canadian Tech Internships 2026 GitHub repository.

#### `jobs -u [page]`

Refresh job listings from GitHub and display them (optionally on a specific page).

```bash
jobs -u      # Refresh and show page 1
jobs -u 2    # Refresh and show page 2
```

**Use Case:** Pull the latest job postings before you start scraping.

---

### Job Scraping

#### `scrape <id|url>`

Scrape full job description from either a job listing ID or a direct URL. Auto-detects the job board platform and selects the appropriate scraper.

```bash
scrape 1                                                    # Scrape job #1 from cached listings
scrape 5                                                    # Scrape job #5 from cached listings
scrape https://jobs.lever.co/company/abc123/                # Scrape from Lever
scrape https://company.myworkdayjobs.com/en-US/job/12345   # Scrape from Workday
scrape https://company.ashbyhq.com/opening/job-id           # Scrape from Ashby
```

**Output:** Displays the extracted job description with detected platform name.

**Supported Platforms:** Workday, Lever, Ashby, iCIMS, plus fallback for generic sites.

---

### Resume Management

#### `resume`

Display your currently stored resume.

```bash
resume
```

**Use Case:** Verify what resume is loaded before generating tailored versions.

#### `resume -u`

Update/set your base resume. Enters paste mode where you can copy-paste your full resume text.

```bash
resume -u
```

**Use Case:** Store your master resume that will be tailored for each application.

---

### AI-Powered Resume Tailoring

#### `prompt <id>`

Generate an AI prompt for resume tailoring and copy it to your clipboard. Use the job ID from the listings.

```bash
prompt 1   # Generate prompt for job #1
prompt 3   # Generate prompt for job #3
```

**Output:** A detailed system prompt optimized for resume tailoring is copied to clipboard. This prompt:

- Analyzes the job description for key skills and keywords
- Identifies gaps in your resume
- Provides specific instructions for surgical resume editing
- Ensures no hallucination of skills or metrics
- Maintains formatting and length constraints

**Use Case:** Copy the prompt to Claude, ChatGPT, or your preferred LLM to get tailored resumes that match the job posting.

---

### Help & Navigation

#### `help`

Display a quick reference of all available commands.

```bash
help
```

#### `exit`, `quit`, `q`

Exit the CLI application.

```bash
exit
```

---

## Job Posting Scrapers

The backend includes a modular scraper system that auto-detects job board platforms and extracts full job descriptions.

### Architecture

**Router** → Platform detection → **Source-specific scraper** → Job description

### Supported Platforms

#### **Workday**

Handles URLs from `*.myworkdayjobs.com` domain.

- **URL Pattern:** `https://company.myworkdayjobs.com/en-US/job/[JOB_ID]`
- **Selector:** `[data-automation-id='jobPostingDescription']`
- **Features:** Robust handling of Workday's dynamic job description container

#### **Lever**

Handles URLs from `jobs.lever.co` and `lever.co` domains.

- **URL Pattern:** `https://jobs.lever.co/[COMPANY]/[JOB_ID]/`
- **Selectors:** Content containers like `.posting-page`, `.section-wrapper`, `.content`
- **Features:** Flexible selector fallbacks for various Lever page layouts

#### **Ashby**

Handles URLs from Ashby career portals.

- **URL Pattern:** `https://company.ashbyhq.com/opening/[JOB_ID]`
- **Features:** Auto-detection and robust content extraction

#### **iCIMS**

Handles URLs from iCIMS-hosted job boards.

- **URL Pattern:** Various iCIMS domain patterns
- **Features:** Platform-specific selectors for iCIMS layouts

#### **Fallback**

Generic scraper for any other HTTP(S) job posting URL not matched by specific scrapers.

- **URL Pattern:** Any valid HTTP(S) URL
- **Strategy:** Attempts common selectors and generic article/main content blocks
- **Features:** Best-effort extraction for unsupported platforms

### Scraper Features

- **Auto-detection:** `detect_scraper_source(url)` automatically determines the platform
- **Playwright-based:** Uses headless Chromium for JavaScript-heavy sites
- **Retry logic:** 2 attempts by default with transient failure handling
- **Timeout handling:** 30-second default timeout (configurable)
- **Error types:**
  - `JobScraperError` - General scraping failure
  - `JobNavigationError` - Page navigation timeout or failure
  - `UnsupportedJobUrlError` - URL doesn't match any supported platform
  - Platform-specific errors (e.g., `UnsupportedWorkdayUrlError`)

### Library Usage

Use the scraper module directly in Python code:

```python
from src.posting_scrapers import scrape_description_for_url

# Auto-detects platform and scrapes description
source, description = scrape_description_for_url(
    "https://jobs.lever.co/company/abc123/"
)

if description:
    print(f"Detected platform: {source}")
    print(f"Description:\n{description}")
else:
    print("Failed to scrape!")
```

### Scraper Configuration

When building a scraper programmatically:

```python
from src.posting_scrapers import build_scraper_for_url

source, scraper = build_scraper_for_url(
    url="https://company.myworkdayjobs.com/en-US/job/12345",
    timeout_ms=30000,      # 30-second timeout
    max_attempts=2,        # Retry twice on transient failures
    headless=True,         # Launch in headless mode
)

description = scraper.scrape_description(url)
```

---

## Running the Application

### Interactive Shell

```bash
python main.py
```

Launches the interactive CLI shell. Type commands at the prompt.

### Single Command Execution

```bash
python main.py jobs -u
python main.py scrape 1
python main.py prompt 3
```

Executes a single command and exits.

---

## Configuration

- **Resume file:** Stored in `./resume.txt` (project root)
- **Timeout:** Default 30 seconds per scrape (configurable)
- **Retry logic:** 2 attempts for transient failures
- **Browser:** Headless Chromium

---

## Error Handling

The CLI provides clear error messages for common issues:

- **Unknown command:** Type `help` for available commands
- **Invalid job ID:** Use `jobs` to see available job numbers
- **Unsupported URL:** Check that the job board is in the supported list
- **Scrape timeout:** The site may be slow or blocking scrapers; try again
- **Resume not found:** Use `resume -u` to set your resume first

---

## Performance

- **Job listings:** Cached in memory (fetched once per session or on `jobs -u`)
- **Scraping:** Uses headless Chromium with configurable timeouts
- **Prompt generation:** Runs locally, no API calls (uses your stored resume + scraped description)
