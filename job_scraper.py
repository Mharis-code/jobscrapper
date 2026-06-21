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

# Specialist boards: trust their listings without applying a keyword title filter.
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

        print(f"  → {count} jobs\n")
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
