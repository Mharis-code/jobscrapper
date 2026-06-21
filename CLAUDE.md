# Job Scraper — Claude Code Skill

This folder contains a Claude Code skill that scrapes Canadian job listings from multiple job boards using the Firecrawl API.

## Installing the Skill

If the user asks you to install the skill (e.g., "install the skill", "set this up on my machine", "get this working"), do the following:

1. Detect the user's home directory:
   ```
   python -c "import os; print(os.path.expanduser('~/.claude/skills/job-scraper'))"
   ```
2. Create the skill directory and copy SKILL.md there:
   - **Windows:** `mkdir "$env:USERPROFILE\.claude\skills\job-scraper" -Force` then copy SKILL.md
   - **Mac/Linux:** `mkdir -p ~/.claude/skills/job-scraper` then copy SKILL.md
3. Confirm to the user: "The `/job-scraper` skill is installed. Open any project in Claude Code and type `/job-scraper` to start. On first run it will ask for your Firecrawl API key and search settings — just once."

## Skill Command

```
/job-scraper          — run with saved config (or trigger first-time setup)
/job-scraper reset    — reconfigure saved settings
```

## How It Works

1. **SKILL.md** is read by Claude Code when `/job-scraper` is invoked
2. Claude checks for `~/.claude/skills/job-scraper/config.json`
3. If config exists: runs immediately with saved settings
4. If config is missing: asks the user once for all settings, saves them, then runs
5. Claude calls `job_scraper.py` with the config values as CLI arguments
6. The script scrapes all selected sites, filters results, and saves a CSV

## Files

| File | Role |
|------|------|
| `SKILL.md` | Claude Code skill definition — copy to `~/.claude/skills/job-scraper/` |
| `job_scraper.py` | Python CLI scraper — copy to same location |
| `requirements.txt` | `firecrawl-py` (auto-installed by the skill on first run) |
| `.env.example` | Shows the expected env variable format |
| `install.ps1` | Windows one-step installer |
| `install.sh` | Mac/Linux one-step installer |

## Config File (auto-created, not in this repo)

Saved at `~/.claude/skills/job-scraper/config.json`:
```json
{
  "firecrawl_api_key": "fc-...",
  "keywords": "finance manager",
  "location": "Ontario",
  "sites": ["indeed", "glassdoor", "jobbank", "randstad"],
  "output_folder": ""
}
```

## job_scraper.py CLI

```
python job_scraper.py --api-key <key> --keywords <terms> --location <place> --sites <keys> --output <file.csv>
python job_scraper.py --list-sites
```

Available site keys:
`indeed`, `glassdoor`, `workopolis`, `jobbank`, `efinancialcareers`, `cpaontario`, `ziprecruiter`, `eluta`, `roberthalf`, `randstad`, `monster`

## Filtering Logic

- **Location filter**: derived from the user's location string; excludes US states automatically
- **Title filter**: derived from keywords; applied to general boards only (Indeed, Glassdoor, Workopolis, Monster, ZipRecruiter, Eluta)
- **Trusted sources** (no title filter): `jobbank`, `efinancialcareers`, `cpaontario`, `randstad`, `roberthalf`
- **Deduplication**: by `job_url`
- **Exit code 2**: Firecrawl credits exhausted — the skill reports this and stops cleanly

## Output CSV Columns

`Company, Job Title, Location, Job Type, Salary, Job URL, Source`

## Requirements

- Python 3.8+
- Claude Code
- Firecrawl API key (free tier at firecrawl.dev)
