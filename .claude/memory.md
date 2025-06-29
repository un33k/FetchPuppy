# Claude Memory for JobSite Project

## Project Context
JobSite is a job scraping and AI-powered analysis platform that helps users find optimal job matches based on their resume, salary requirements, location preferences, and skills. The project uses a modular architecture with a CLI called `claudia`.

## Key Architecture Decisions
- **Modular Design**: Inspired by the Ansible Cloudy project structure
- **CLI Framework**: Professional command-line interface with rich help and colored output
- **Storage Strategy**: SQLite for structured job data, file system for resumes and exports
- **AI Integration**: OpenAI API for intelligent job-resume matching and analysis
- **Scraping Approach**: Respectful, rate-limited scraping with pluggable scraper architecture

## Current Implementation Status
- ✅ Project structure and bootstrap script
- ✅ Development environment configuration (.vscode, .claude)
- ✅ Comprehensive CLAUDE.md documentation
- 🔄 CLI implementation in progress
- ⏳ Scraper modules pending
- ⏳ Database schema pending
- ⏳ AI analysis modules pending

## Important Technical Details
- Python 3.11.9 via pyenv (with system Python fallback)
- Virtual environment in `.venv/`
- SQLite database at `data/jobs.db`
- OpenAI API key required for AI features
- CLI executable at `./claudia` (bash wrapper)

## Development Patterns
- All scrapers inherit from `BaseJobScraper`
- Database operations go through `database/operations.py`
- AI analysis uses consistent scoring and weighting
- CLI commands follow the pattern: `./claudia <service> <command> [options]`

## User Requirements
- Scrape job sites (Indeed, LinkedIn, generic)
- Store jobs in SQLite or simple files
- AI-powered analysis for job-resume matching
- Search by salary, location, remote options
- Export capabilities (CSV, JSON, HTML)
- Professional CLI with comprehensive help