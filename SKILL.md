---
name: job-scraper
description: Use when someone wants to scrape, find, search for, or collect job listings from the web. Triggers on "scrape jobs", "find job listings", "search for jobs", "collect job postings", "job research", "find me jobs". On first run, installs itself and asks for config once — subsequent runs use saved config automatically.
argument-hint: Pass "reset" to reconfigure saved settings — /job-scraper reset
allowed-tools: Read, Write, Bash(python *)
disable-model-invocation: true
---

# Job Scraper Skill

Scrapes job listings from up to 11 Canadian job boards using Firecrawl API and saves results to CSV.

This skill is **self-installing** — it writes its own Python script and installs its own dependencies on first run. The client only needs this one SKILL.md file.

---

## STEP 0 — Auto-Install (runs silently every time; no-ops if already installed)

**0a. Detect skill directory**

Run:
```
python -c "import os; print(os.path.expanduser('~/.claude/skills/job-scraper'))"
```
Store the output as `SKILL_DIR`. Use it as the base path for all file operations below.

**0b. Write job_scraper.py if missing**

Check if `{SKILL_DIR}/job_scraper.py` exists.

If it does NOT exist: use the Write tool to create that file with the **exact content** from the `## EMBEDDED SCRIPT` section at the bottom of this SKILL.md.

**0c. Install Python package if missing**

Run silently:
```
python -c "import firecrawl"
```
If it exits with an error: run `pip install firecrawl-py --quiet`

---

## STEP 1 — Load or Create Config

Read `{SKILL_DIR}/config.json`.

**If it exists AND the user did NOT pass "reset":** load all values silently and skip to STEP 3.

**If it is missing OR the user passed "reset":** proceed to STEP 2.

---

## STEP 2 — First-Time Setup (runs once, saved forever)

Tell the user:
> "Let's set up your job scraper. You'll only need to do this once — all settings will be saved and reused automatically. Use `/job-scraper reset` any time to change them."

Ask ONE combined message covering all 5 items:

> **Job Scraper Setup**
>
> **1. Firecrawl API key**
> Get a free key at https://firecrawl.dev — paste it here.
>
> **2. Job keywords**
> What type of jobs to search for?
> Examples: "finance manager", "software engineer", "registered nurse"
>
> **3. Location**
> Province or city?
> Examples: "Ontario", "Toronto, ON", "British Columbia", "Calgary, AB"
>
> **4. Job boards**
> Which sites to include? Type numbers (e.g. "1,2,4") or "all":
> ```
>  1.  Indeed.ca           — large Canadian board
>  2.  Glassdoor.ca        — includes salary data
>  3.  Workopolis          — Canadian-focused
>  4.  Job Bank            — Government of Canada (free, open)
>  5.  eFinancialCareers   — finance & banking specialist
>  6.  CPA Ontario         — accounting / CPA roles
>  7.  ZipRecruiter        — salary transparency
>  8.  Eluta.ca            — Canadian aggregator
>  9.  Robert Half Canada  — finance/admin staffing
> 10.  Randstad Canada     — temp & permanent roles
> 11.  Monster.ca          — general board
> ```
>
> **5. Output folder** (optional — leave blank for current directory)

Map number selections to site keys:
```
1→indeed  2→glassdoor  3→workopolis  4→jobbank  5→efinancialcareers
6→cpaontario  7→ziprecruiter  8→eluta  9→roberthalf  10→randstad  11→monster
```
"all" → all 11 keys.

Write `{SKILL_DIR}/config.json`:
```json
{
  "firecrawl_api_key": "<pasted key>",
  "keywords": "<job keywords>",
  "location": "<location>",
  "sites": ["<key1>", "<key2>"],
  "output_folder": "<path or empty string>"
}
```

Confirm: _"Config saved. Running your first job search now..."_ then proceed immediately to STEP 3.

---

## STEP 3 — Run Scraper

Construct the output path:
- `output_folder` set → `{output_folder}/{keywords-slug}-jobs.csv`
- blank → `{keywords-slug}-jobs.csv` (current directory)
- slug = keywords lowercased, spaces → hyphens ("finance manager" → "finance-manager")

Run:
```
python "{SKILL_DIR}/job_scraper.py" --api-key "<firecrawl_api_key>" --keywords "<keywords>" --location "<location>" --sites "<sites joined by commas>" --output "<output_path>"
```

Wait for completion. The script prints per-site counts, a total, and a top-5 preview.

If the script exits with **code 2** (credits exhausted): report which sites finished and link to https://firecrawl.dev/pricing.

---

## STEP 4 — Report Results

Present:
1. Total unique jobs found
2. Per-site breakdown table
3. Top 5 preview — Company | Job Title | Location | Salary
4. Full path to the saved CSV

Note any sites that returned 0 jobs (e.g., "Robert Half: 0 — blocked extraction").

---

## RULES

- Never run the scraper without a valid config (STEP 1/2).
- If config.json is corrupt or missing required keys, treat as missing and run STEP 2.
- Never ask for API key, keywords, location, or sites more than once — they are saved.
- `/job-scraper reset` is the only way to reconfigure.
- On any Python error (not credits), show the full error and suggest checking the API key.

---

## EMBEDDED SCRIPT

> This section contains the exact content of `job_scraper.py`.
> In STEP 0b, if `{SKILL_DIR}/job_scraper.py` is missing, use the Write tool
> to create it with the content below — copy it verbatim, preserving all
> indentation and line breaks.

```python
#!/usr/bin/env python3
"""
job_scraper.py — Flexible job listing scraper via Firecrawl API.
Called by the Claude Code /job-scraper skill.

Usage:
  python job_scraper.py \
    --api-key "fc-..." \
    --keywords "finance manager" \
    --location "Ontario" \
    --sites "indeed,glassdoor,jobbank" \
    --output "finance-manager-jobs.csv"

  python job_scraper.py --list-sites
"""

import argparse
import csv
import re
import sys
import time
from collections import Counter
from typing import Optional, List
from urllib.parse import quote_plus

from pydantic import BaseModel
from firecrawl import FirecrawlApp


# ─── Site Registry ────────────────────────────────────────────────────────────

SITE_NAMES = {
    "indeed":            "Indeed",
    "glassdoor":         "Glassdoor",
    "workopolis":        "Workopolis",
    "jobbank":           "Job Bank",
    "efinancialcareers": "eFinancialCareers",
    "cpaontario":        "CPA Ontario",
    "ziprecruiter":      "ZipRecruiter",
    "eluta":             "Eluta",
    "roberthalf":        "Robert Half",
    "randstad":          "Randstad",
    "monster":           "Monster",
}

ALL_SITES = list(SITE_NAMES.keys())

# Specialist boards: trust their listings without a keyword title filter.
TRUSTED_SOURCES = {"efinancialcareers", "cpaontario", "randstad", "jobbank", "roberthalf"}


def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def build_url(site_key: str, keywords: str, location: str) -> str:
    kw       = quote_plus(keywords)
    loc      = quote_plus(location)
    kw_slug  = slugify(keywords)
    loc_slug = slugify(location)

    templates = {
        "indeed":            f"https://ca.indeed.com/jobs?q={kw}&l={loc}",
        "glassdoor":         f"https://www.glassdoor.ca/Job/{loc_slug}-{kw_slug}-jobs-SRCH_KO0,{len(kw_slug)}.htm",
        "workopolis":        f"https://www.workopolis.com/jobsearch/find-jobs?q={kw}&l={loc}",
        "jobbank":           f"https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={kw}&locationstring={loc}",
        "efinancialcareers": f"https://www.efinancialcareers.com/jobs/{kw_slug}/in-canada",
        "cpaontario":        "https://mycareer.cpaontario.ca/jobs/ontario/",
        "ziprecruiter":      f"https://www.ziprecruiter.com/Jobs/{kw_slug}-Jobs-In-Canada",
        "eluta":             f"https://www.eluta.ca/jobs-search.php?q={kw}&p={loc}",
        "roberthalf":        f"https://www.roberthalf.com/ca/en/jobs/ontario/{kw_slug}",
        "randstad":          f"https://www.randstad.ca/jobs/q-{kw_slug}-/ontario/",
        "monster":           f"https://www.monster.ca/jobs/search?q={kw}&where={loc}",
    }
    return templates.get(site_key, "")


# ─── Pydantic Models ──────────────────────────────────────────────────────────

class Job(BaseModel):
    company: str
    job_title: str
    location: str
    job_type: Optional[str] = ""
    salary: Optional[str] = ""
    job_url: str


class JobListings(BaseModel):
    jobs: List[Job]


# ─── Filters ─────────────────────────────────────────────────────────────────

US_STATES_RE = re.compile(
    r',\s*(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|'
    r'MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|'
    r'SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)\b', re.IGNORECASE
)

CANADIAN_PROVINCES = {
    "ontario":          r'(,\s*ON\b|ontario)',
    "british columbia": r'(,\s*BC\b|british\s+columbia)',
    "alberta":          r'(,\s*AB\b|alberta)',
    "quebec":           r'(,\s*QC\b|qu[eé]bec)',
    "nova scotia":      r'(,\s*NS\b|nova\s+scotia)',
    "new brunswick":    r'(,\s*NB\b|new\s+brunswick)',
    "manitoba":         r'(,\s*MB\b|manitoba)',
    "saskatchewan":     r'(,\s*SK\b|saskatchewan)',
    "pei":              r'(,\s*PE\b|prince\s+edward)',
    "newfoundland":     r'(,\s*NL\b|newfoundland)',
}


def build_location_filter(location: str):
    loc_lower = location.lower().strip()
    for province, pattern in CANADIAN_PROVINCES.items():
        if province in loc_lower:
            return re.compile(pattern, re.IGNORECASE)
    terms = [re.escape(t) for t in re.split(r'[\s,]+', location) if len(t) > 3]
    if terms:
        return re.compile('|'.join(terms), re.IGNORECASE)
    return re.compile(r'.*', re.IGNORECASE)


def is_target_location(loc: str, loc_filter) -> bool:
    if not loc:
        return False
    if US_STATES_RE.search(loc):
        return False
    return bool(loc_filter.search(loc))


def build_title_filter(keywords: str):
    terms = [t for t in re.split(r'[\s,]+', keywords.lower()) if len(t) > 3]
    if not terms:
        return None
    return re.compile('|'.join(re.escape(t) for t in terms), re.IGNORECASE)


def is_relevant_title(title: str, title_filter) -> bool:
    if title_filter is None:
        return True
    return bool(title_filter.search(title))


def is_valid_url(url: str) -> bool:
    return bool(url and url.startswith("http"))


# ─── Scraper ─────────────────────────────────────────────────────────────────

EXTRACT_PROMPT = (
    "Extract all job listings visible on this page. "
    "For each listing found, extract: company name, job title, "
    "location (city and province/state), job type "
    "(Full-time / Part-time / Contract / Temporary), "
    "salary or pay range if shown, and the direct URL to that specific job posting. "
    "Do not omit any listing — include all jobs shown on the page."
)


def scrape_site(app: FirecrawlApp, url: str) -> list:
    try:
        result = app.extract(
            urls=[url],
            prompt=EXTRACT_PROMPT,
            schema=JobListings.model_json_schema(),
        )
        data     = result.data if hasattr(result, "data") else (result or {})
        jobs_raw = data.get("jobs", []) if isinstance(data, dict) else []
        jobs = []
        for j in jobs_raw:
            if isinstance(j, dict):
                jobs.append(j)
            elif hasattr(j, "model_dump"):
                jobs.append(j.model_dump())
        return jobs
    except Exception as e:
        err = str(e)
        if "Payment Required" in err or "credits" in err.lower():
            print("  [CREDITS] Firecrawl credits exhausted — stopping.")
            print("  Top up at: https://firecrawl.dev/pricing")
            sys.exit(2)
        print(f"  [ERROR] {err}")
        return []


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Job scraper via Firecrawl API")
    parser.add_argument("--api-key",    default="",    help="Firecrawl API key")
    parser.add_argument("--keywords",   default="",    help="Job search keywords")
    parser.add_argument("--location",   default="",    help="Target location (province/city)")
    parser.add_argument("--sites",      default="all", help="Comma-separated site keys or 'all'")
    parser.add_argument("--output",     default="",    help="Output CSV file path")
    parser.add_argument("--list-sites", action="store_true", help="List available sites and exit")
    args = parser.parse_args()

    if args.list_sites:
        print("Available sites:")
        for key, name in SITE_NAMES.items():
            print(f"  {key:20s}  {name}")
        return

    if not args.api_key or not args.keywords or not args.location:
        parser.error("--api-key, --keywords, and --location are required")

    if not args.output:
        args.output = f"{slugify(args.keywords)}-jobs.csv"

    if args.sites.strip().lower() == "all":
        selected = ALL_SITES
    else:
        selected = [s.strip().lower() for s in args.sites.split(",") if s.strip()]
        unknown  = [s for s in selected if s not in SITE_NAMES]
        if unknown:
            print(f"[WARN] Unknown site(s) ignored: {', '.join(unknown)}")
        selected = [s for s in selected if s in SITE_NAMES]

    if not selected:
        print("[ERROR] No valid sites selected.")
        sys.exit(1)

    loc_filter   = build_location_filter(args.location)
    title_filter = build_title_filter(args.keywords)
    app          = FirecrawlApp(api_key=args.api_key)

    print(f"\nJob Scraper")
    print(f"  Keywords : {args.keywords}")
    print(f"  Location : {args.location}")
    print(f"  Sites    : {', '.join(SITE_NAMES[s] for s in selected)}")
    print(f"  Output   : {args.output}\n")

    all_rows  = []
    seen_urls = set()

    for site_key in selected:
        url       = build_url(site_key, args.keywords, args.location)
        site_name = SITE_NAMES[site_key]
        print(f"[{site_name}] {url}")

        jobs  = scrape_site(app, url)
        count = 0

        for j in jobs:
            job_url  = (j.get("job_url")   or "").strip()
            location = (j.get("location")  or "").strip()
            title    = (j.get("job_title") or "").strip()

            if not is_valid_url(job_url) or job_url in seen_urls:
                continue

            if site_key not in TRUSTED_SOURCES:
                if not is_target_location(location, loc_filter):
                    continue
                if not is_relevant_title(title, title_filter):
                    continue

            seen_urls.add(job_url)
            all_rows.append({
                "Company":   (j.get("company")  or "").strip(),
                "Job Title": title,
                "Location":  location,
                "Job Type":  (j.get("job_type") or "").strip(),
                "Salary":    (j.get("salary")   or "").strip(),
                "Job URL":   job_url,
                "Source":    site_name,
            })
            count += 1

        print(f"  -> {count} jobs\n")
        time.sleep(3)

    fieldnames = ["Company", "Job Title", "Location", "Job Type", "Salary", "Job URL", "Source"]
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print("=" * 50)
    print(f"Total unique jobs saved : {len(all_rows)}")
    print(f"Output file             : {args.output}")
    print("=" * 50)

    sources = Counter(r["Source"] for r in all_rows)
    for src, c in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {src}: {c}")

    if all_rows:
        print("\n--- TOP 5 PREVIEW ---")
        for row in all_rows[:5]:
            print(f"  {row['Company']} | {row['Job Title']} | {row['Location']} | {row['Salary'] or 'N/A'}")


if __name__ == "__main__":
    main()
```
