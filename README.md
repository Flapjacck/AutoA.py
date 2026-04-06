# AutoA.py

A data pipeline designed to bridge the gap between job listings and a perfectly tailored resume. This tool automates the process of fetching internship postings, extracting job requirements, and generating a tailored resume using AI.

## **The Concept**

As a person seeking employment, I noticed that the most time consuming part of applying for internships is adjusting my resume for every single job description. I wanted to build a tool that handles the boring parts of applying.

The workflow is simple:

1. **Source:** Pull the latest internship listings from the community-driven [Canadian Tech Internships 2026](https://github.com/negarprh/Canadian-Tech-Internships-2026) repository.
2. **Scrape:** Use **Playwright** to navigate to various job portals (Workday, Greenhouse, Lever, etc.) and extract the job title, company, and full description.
3. **Tailor:** Feed that data into the [Rezzy.dev API](https://docs.rezzy.dev/) to generate a resume specifically optimized for that specific job posting.
4. **Output:** A tailored resume that matches the job requirements.

## **Tech Stack**

* **Backend:** Python (Managed with **uv** for fast, reproducible builds).
* **Scraping:** **Playwright** (Chosen for its ability to handle JavaScript-heavy sites like Workday).
* **Resume Generation:** [Rezzy.dev API](https://docs.rezzy.dev/).
* **Data Source:** [Canadian-Tech-Internships-2026](https://github.com/negarprh/Canadian-Tech-Internships-2026).

## **Acknowledgements & Credits**

This project relies heavily on the incredible work done by [negarprh](https://github.com/negarprh) and the contributors of the [Canadian Tech Internships 2026](https://github.com/negarprh/Canadian-Tech-Internships-2026) repo. **All credit for the curated list of internship data goes to them**. this project simply acts as a pipeline to process that information.
