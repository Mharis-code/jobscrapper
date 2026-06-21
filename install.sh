#!/usr/bin/env bash
# install.sh — Mac/Linux installer for the /job-scraper Claude Code skill
# Run from the folder containing this script:  ./install.sh

set -e

SKILL_DIR="$HOME/.claude/skills/job-scraper"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "Installing /job-scraper skill..."

# Create skill directory
mkdir -p "$SKILL_DIR"
echo "  Directory: $SKILL_DIR"

# Copy skill files
cp "$SCRIPT_DIR/SKILL.md"       "$SKILL_DIR/SKILL.md"
cp "$SCRIPT_DIR/job_scraper.py" "$SKILL_DIR/job_scraper.py"
echo "  Copied SKILL.md and job_scraper.py"

# Install Python dependency
echo "  Installing firecrawl-py..."
pip install firecrawl-py --quiet && echo "  firecrawl-py installed" || echo "  Warning: pip install failed. Run 'pip install firecrawl-py' manually."

echo ""
echo "Done! Open Claude Code and type:"
echo "  /job-scraper"
echo ""
echo "On first run, Claude will ask for your Firecrawl API key and search settings."
echo "Get a free key at: https://firecrawl.dev"
echo ""
