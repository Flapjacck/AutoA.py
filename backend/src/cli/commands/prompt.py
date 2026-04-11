"""AI-powered resume tailoring prompt generator command."""

import sys
import pyperclip

from src.cli.theme import console, print_error, print_info, print_section, print_success
from src.jobs.fetcher import JobListingFetcher
from src.posting_scrapers import (
    JobNavigationError,
    JobScraperError,
    UnsupportedJobUrlError,
    scrape_description_for_url,
)


# System prompt template for resume tailoring
RESUME_TAILOR_SYSTEM_PROMPT = """System Persona & Objective
Act as the Senior Technical Recruiter and Lead Engineering Hiring Manager for the company listed in the input section below. You have screened thousands of software engineering resumes and know exactly what the ATS and the engineering team at this specific company value.

Your task is to surgically tailor my provided resume to perfectly align with the provided job description for this role. You will maximize ATS compatibility and recruiter appeal while strictly adhering to formatting and length constraints.

Phase 1: Deep Analysis (Internal Review)

Extract & Categorize: Identify the most heavily weighted Hard Skills, Soft Skills, Tools, Frameworks, and specific phrasing from the Job Description (JD).

Gap Analysis: Compare my resume to the JD. Identify which high-priority keywords and skills are missing or underrepresented in my current bullet points.

Phase 2: Surgical Resume Optimization (Output Requirements)
You must revise my technical skills and bullet points based on the following strict constraints:

Strict Rules for Bullet Points:

Surgical Edits Only: Do NOT completely rewrite my bullet points. Keep my original voice, intent, and base structure. Your goal is to insert missing keywords into the existing sentences naturally.

Technical Accuracy: All additions must make complete technical sense. Do not arbitrarily string buzzwords together.

Format & Length (NO Hanging Lines): The new bullet points must be roughly the exact same character count as the original. You must prevent "hanging lines" (where 1 or 2 words spill over onto a new line, wasting vertical space).

Concise XYZ Framework: Incorporate Google's "Accomplished [X] as measured by [Y] by doing [Z]" format only where it naturally fits without increasing the length of the bullet point.

No Hallucinations: Do not fabricate metrics, experiences, or tools I did not list.

No Keyword Stuffing/Over-Bolding: Make the text flow professionally. Do not bold text within the bullet points; it creates visual clutter.

Strict Rules for Technical Skills Section:

Keep exactly 4 sections/categories (matching my original layout).

The physical width/length of each line must match the longest line in my current resume so it takes up the exact same amount of space.

Integrate the missing technical keywords from the JD into these 4 sections.

Format Rule: You must bold only the newly added skills in this section.

Phase 3: Required Output Format
Please output your response exactly in this structure:

1. Target Company Keyword Analysis:

A concise list of the must-have Hard & Soft skills from the JD.

A brief list of the gaps in my current resume.

2. Optimized Technical Skills Section:

(Provide the newly formatted 4-category block, ensuring length constraints and bolding only new skills).

3. Revised Bullet Points (Only the Changed Ones):

(Provide ONLY the bullet points you modified. Present them clearly so I can swap them out. Remember: ensure exact length matching to prevent hanging lines, and include every JD keyword at least once across the resume).

4. High-Impact Suggestions (Optional):

1-2 brief bullet points on structural or overall improvements (do not suggest adding new lines).

TARGET COMPANY & JOB DESCRIPTION:
Company: {company}
Role: {role}
Location: {location}
Description: {description}

MY CURRENT RESUME:
[resume here]"""


def cmd_prompt(args: list[str]) -> None:
    """Execute resume tailoring prompt generator.

    Args:
        args: Command arguments, expects a numeric job listing ID (e.g., 1, 2, 3)

    Examples:
        prompt 1          # Generate prompt for first job from cached listings
        prompt 5          # Generate prompt for fifth job from cached listings
    """
    if not args:
        print_error("Usage: prompt <job_id>")
        return

    argument = args[0].strip()
    if not argument or not argument.isdigit():
        print_error("Usage: prompt <job_id>")
        return

    _generate_prompt_for_job_id(int(argument))


def _generate_prompt_for_job_id(job_id: int) -> None:
    """Generate and copy AI prompt for resume tailoring.

    Args:
        job_id: 1-indexed job ID from the job listings.
    """
    try:
        # Fetch cached job list
        fetcher = JobListingFetcher()
        jobs = fetcher.get_jobs(force_refresh=False)

        # Validate job ID is in range
        if job_id < 1 or job_id > len(jobs):
            total = len(jobs)
            print_error(f"Job #{job_id} not found. Only {total} jobs available.")
            return

        # Get the job (convert 1-indexed to 0-indexed)
        job = jobs[job_id - 1]

        print_section("Resume Tailoring Prompt Generator")
        console.print()

        # Display job details for confirmation
        _display_job_details(job)
        console.print()

        # Ask for confirmation
        console.print("[accent]autoa[/accent]> Proceed with scraping and generating prompt? (y/n): ", end="")
        try:
            confirmation = sys.stdin.readline().strip().lower()
        except EOFError:
            print_info("Aborted.")
            return

        if confirmation not in ["y", "yes"]:
            print_info("Aborted.")
            return

        console.print()
        print_info(f"Scraping job description from: {job.url}")

        # Scrape the job description
        source, description = scrape_description_for_url(job.url)
        if not description:
            print_info("Warning: No description found. Using empty description in prompt.")
            description = "[No description was scraped. Please manually paste the job description here.]"

        print_success(f"Successfully scraped from: {source}")

        # Generate the prompt
        prompt_text = RESUME_TAILOR_SYSTEM_PROMPT.format(
            company=job.company,
            role=job.role,
            location=job.location,
            description=description,
        )

        # Copy to clipboard
        _copy_to_clipboard(prompt_text)

    except UnsupportedJobUrlError as exc:
        print_error(str(exc))
    except JobNavigationError as exc:
        print_error(f"Navigation failed: {exc}")
    except JobScraperError as exc:
        print_error(f"Scraper error: {exc}")
    except Exception as exc:
        print_error(f"Error generating prompt: {exc}")


def _display_job_details(job) -> None:
    """Display job details for user confirmation.

    Args:
        job: JobPosting object to display.
    """
    from rich.table import Table

    row = Table.grid(padding=(0, 2))
    row.add_row("[bold cyan]Job ID[/bold cyan]", f"{job.id}")
    row.add_row("[bold cyan]Company[/bold cyan]", f"[bold bright_magenta]{job.company}[/bold bright_magenta]")
    row.add_row("[bold cyan]Role[/bold cyan]", f"{job.role}")
    row.add_row("[bold cyan]Location[/bold cyan]", f"{job.location}")
    row.add_row("[bold cyan]Posted[/bold cyan]", f"{job.posted_at_raw}")
    row.add_row("[bold cyan]URL[/bold cyan]", f"[underline blue]{job.url}[/underline blue]")
    
    console.print(row)


def _copy_to_clipboard(text: str) -> None:
    """Copy text to clipboard and display confirmation.

    Args:
        text: Text to copy to clipboard.
    """
    try:
        pyperclip.copy(text)
        print_success("Prompt copied to clipboard!")
        print_info("Paste into ChatGPT, Claude, or your preferred AI platform.")
    except Exception as e:
        print_error(f"Failed to copy to clipboard: {e}")
        print_info("You can manually select and copy the prompt above.")
