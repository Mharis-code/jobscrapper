# Job Scraper — Claude Code Skill

A Claude Code skill that scrapes Canadian job listings from up to 11 job boards simultaneously using the [Firecrawl](https://firecrawl.dev) API. Results are exported to a clean CSV file with job title, company, location, salary, and a direct application link.

**Works with any job type and any Canadian province or city.**

---

## Features

- Scrapes 11 Canadian job boards in one run
- **One-time setup** — API key and search preferences saved automatically; never asked again
- Filters out US job listings automatically
- Removes off-topic results using keyword matching
- Deduplicates listings that appear on multiple boards
- Exports CSV: `Company, Job Title, Location, Job Type, Salary, Job URL, Source`
- `/job-scraper reset` to update your saved settings any time

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| [Claude Code](https://claude.ai/code) | The CLI or VS Code extension |
| Python 3.8+ | Must be on your system PATH |
| `firecrawl-py` | Installed automatically on first run |
| Firecrawl API key | Free tier available — [sign up here](https://firecrawl.dev) |

---

## Installation

There are two ways to install this skill. **Option A is recommended** — it requires no manual commands.

---

### Option A — Open in Claude Code (Recommended)

1. **Download or clone this repository**

   ```bash
   git clone https://github.com/your-repo/job-scraper.git
   ```
   Or click **Download ZIP** on GitHub and extract it.

2. **Open the folder in Claude Code**

   - **VS Code extension:** Open VS Code, then open the `job-scraper` folder (`File → Open Folder`)
   - **Claude Code CLI:** `cd job-scraper && claude`

3. **Ask Claude to install the skill**

   Once Claude Code is open with this project, simply type:
   ```
   Can you install the job-scraper skill on my machine?
   ```
   Claude will read the `CLAUDE.md` file, copy `SKILL.md` to the correct location, and confirm when done.

4. **You're ready** — type `/job-scraper` in any Claude Code session to start

---

### Option B — Manual (One Command)

Copy `SKILL.md` to your Claude Code skills directory:

**Windows (PowerShell):**
```powershell
mkdir "$env:USERPROFILE\.claude\skills\job-scraper" -Force
copy SKILL.md "$env:USERPROFILE\.claude\skills\job-scraper\SKILL.md"
```

**Mac / Linux:**
```bash
mkdir -p ~/.claude/skills/job-scraper
cp SKILL.md ~/.claude/skills/job-scraper/
```

---

### What happens on first run

When you type `/job-scraper` for the first time, the skill automatically:
- Writes `job_scraper.py` to the skill directory (the Python script is embedded inside `SKILL.md` — no separate download needed)
- Installs the `firecrawl-py` Python package via pip
- Asks for your Firecrawl API key and search settings — **once only**
- Saves everything and starts scraping immediately

### Get a Firecrawl API key

1. Go to [firecrawl.dev](https://firecrawl.dev) and create a free account
2. Copy your API key (starts with `fc-`) — Claude will ask for it on first run

---

## Usage

Open Claude Code (any project) and type:

```
/job-scraper
```

**First run:** Claude will ask you five questions (all at once) — API key, keywords, location, which boards to search, and where to save the output. Answers are saved. You'll never be asked again.

**All future runs:**
```
/job-scraper
```
Uses your saved settings and runs immediately.

**To update your search settings:**
```
/job-scraper reset
```

---

## Supported Job Boards

| # | Site | Best for |
|---|------|---------|
| 1 | Indeed.ca | High volume, all job types |
| 2 | Glassdoor.ca | Salary data, company reviews |
| 3 | Workopolis | Canadian-specific listings |
| 4 | Job Bank (govt) | Official government board — very open |
| 5 | eFinancialCareers | Finance and banking roles |
| 6 | CPA Ontario | Accounting and CPA roles |
| 7 | ZipRecruiter | Salary transparency |
| 8 | Eluta.ca | Canadian job aggregator |
| 9 | Robert Half Canada | Finance and admin staffing |
| 10 | Randstad Canada | Temp and permanent roles |
| 11 | Monster.ca | General job board |

> **Note:** LinkedIn is not included — it actively blocks scraping and violates their Terms of Service.

---

## Output

Results are saved as a `.csv` file:

| Column | Example |
|--------|---------|
| Company | TD Bank |
| Job Title | Financial Analyst |
| Location | Toronto, ON |
| Job Type | Full-time |
| Salary | $75,000–$95,000 a year |
| Job URL | https://ca.indeed.com/... |
| Source | Indeed |

---

## Firecrawl Credit Usage

Each run uses Firecrawl API credits. The extract endpoint costs vary — see [firecrawl.dev/pricing](https://firecrawl.dev/pricing).

- Per site: ~1–5 credits depending on page complexity
- Typical full run (11 sites): ~30–55 credits
- If credits run out mid-run, the skill reports which sites completed and stops cleanly

---

## Project Structure

```
job-scraper/
├── SKILL.md          Claude Code skill definition
├── job_scraper.py    Python scraper (CLI interface)
├── requirements.txt  Python dependencies
├── .env.example      API key template (never commit your real .env)
├── install.ps1       Windows installer
├── install.sh        Mac/Linux installer
├── CLAUDE.md         Claude Code project context
└── .gitignore        Excludes secrets and output files
```

---

## Running the Script Directly

You can also run the scraper without Claude Code:

```bash
python job_scraper.py \
  --api-key "fc-your-key-here" \
  --keywords "software engineer" \
  --location "British Columbia" \
  --sites "indeed,glassdoor,jobbank" \
  --output "software-engineer-jobs.csv"
```

List all available site keys:
```bash
python job_scraper.py --list-sites
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: firecrawl` | Run `pip install firecrawl-py` |
| `Payment Required` error | Top up Firecrawl credits at firecrawl.dev/pricing |
| Site returned 0 jobs | Site may have blocked scraping; try a different site |
| US jobs appearing in results | Only affects general boards (Indeed, Glassdoor) — re-run or filter manually |
| Wrong settings saved | Run `/job-scraper reset` to reconfigure |

---

## License

MIT — free to use, modify, and distribute.
