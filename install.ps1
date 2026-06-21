# install.ps1 — Windows installer for the /job-scraper Claude Code skill
# Run from the folder containing this script:  .\install.ps1

$skillDir = "$env:USERPROFILE\.claude\skills\job-scraper"

Write-Host ""
Write-Host "Installing /job-scraper skill..." -ForegroundColor Cyan

# Create skill directory
if (-not (Test-Path $skillDir)) {
    New-Item -ItemType Directory -Force $skillDir | Out-Null
    Write-Host "  Created: $skillDir" -ForegroundColor Green
} else {
    Write-Host "  Directory exists: $skillDir" -ForegroundColor Yellow
}

# Copy skill files
Copy-Item -Force "$PSScriptRoot\SKILL.md"        "$skillDir\SKILL.md"
Copy-Item -Force "$PSScriptRoot\job_scraper.py"  "$skillDir\job_scraper.py"
Write-Host "  Copied SKILL.md and job_scraper.py" -ForegroundColor Green

# Install Python dependency
Write-Host "  Installing firecrawl-py..." -ForegroundColor Cyan
pip install firecrawl-py --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "  firecrawl-py installed" -ForegroundColor Green
} else {
    Write-Host "  Warning: pip install failed. Run 'pip install firecrawl-py' manually." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Done! Open Claude Code and type:" -ForegroundColor Green
Write-Host "  /job-scraper" -ForegroundColor White
Write-Host ""
Write-Host "On first run, Claude will ask for your Firecrawl API key and search settings."
Write-Host "Get a free key at: https://firecrawl.dev"
Write-Host ""
