# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JobSite is a job scraping and AI-powered analysis platform that helps users find the best job matches based on their resume, salary requirements, location preferences, and other criteria. The project follows a modular architecture with a professional CLI interface called `claudia`.

## Common Development Commands

### Environment Setup
- `./bootstrap.sh` - Set up Python virtual environment and install dependencies
- `source .venv/bin/activate` - Activate virtual environment
- `deactivate` - Deactivate virtual environment

### CLI Usage
- `./claudia scrape universal "python developer" --site indeed.com --location "remote"` - Universal AI-powered scraping
- `./claudia discover jobs.apple.com` - Analyze site structure with AI
- `./claudia analyze resume path/to/resume.pdf` - Analyze resume against job database
- `./claudia match --salary 100k --location remote --skills python,ai` - Find matching jobs
- `./claudia export --format csv --filter remote` - Export job data
- `./claudia database --init` - Initialize SQLite database
- `./claudia database --stats` - Show database statistics and job counts
- `./claudia llm --ping --all` - Test all AI provider connections

### Development Commands
- `./claudia dev validate` - Run comprehensive validation of scrapers and database
- `./claudia dev test` - Run unit tests for all modules
- `./claudia dev lint` - Run code linting and formatting checks

### LLM Testing Commands
- `./claudia llm --ping --all` - Test all configured AI providers
- `./claudia llm --ping --local` - Test LM Studio local LLM connection
- `./claudia llm --ping --claude` - Test Claude API connection and response
- `./claudia llm --ping --openai` - Test OpenAI API connection and response

## Architecture Overview

### Modular Structure
The codebase follows a clean modular architecture inspired by the Ansible Cloudy project:

- **CLI Layer** (`dev/claudia/cli/`): Command parsing, routing, and user interface
- **Scrapers** (`dev/claudia/scrapers/`): Job site scraping with pluggable architecture
- **Database** (`dev/claudia/database/`): SQLite operations and data models
- **Analysis** (`dev/claudia/analysis/`): AI-powered job matching and resume parsing
- **Utils** (`dev/claudia/utils/`): Shared utilities and configuration management

### Key Components

#### Universal AI Scraper
- `universal_scraper.py`: Main orchestrator for AI-powered universal scraping
- `ai_navigator.py`: AI-powered page analysis and navigation instruction generator
- `browser_controller.py`: Playwright-based browser automation with stealth features
- `data_extractor.py`: AI-powered extraction of structured job data from web pages

**AI Provider Priority:**
1. Claude API (highest quality, supports screenshots)
2. Local LLM via LM Studio (privacy-first, zero cost)
3. OpenAI API (reliable fallback)
4. Pattern matching (graceful degradation)

#### Database Schema
Jobs are stored in SQLite with the following key fields:
- Job metadata (title, company, location, salary, remote options)
- Job content (description, requirements, benefits)
- Scraping metadata (source, scraped_date, job_url)

#### AI Analysis
- Uses OpenAI API for intelligent job-resume matching
- Analyzes job descriptions against resume content
- Provides scoring and recommendations based on multiple criteria
- Supports custom weighting for salary, location, skills, etc.

## Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:

**AI Provider Configuration:**
- `CLAUDE_API_KEY`: Claude API key (highest quality, supports screenshots)
- `OPENAI_API_KEY`: OpenAI API key (reliable fallback)
- `LOCAL_LLM_ENABLED`: Enable local LLM via LM Studio (privacy + zero cost)
- `LOCAL_LLM_BASE_URL`: Local LLM endpoint (default: http://localhost:1234/v1)
- `LOCAL_LLM_MODEL`: Model name for local LLM

**Database & System:**
- `DATABASE_PATH`: SQLite database location (default: `data/jobs.db`)
- `SCRAPER_MODE`: Browser mode (headless/headful)
- `LOG_LEVEL`: Logging verbosity

### Scraper Configuration
Each scraper can be configured for:
- Rate limiting and politeness delays
- User agent rotation
- Proxy support for large-scale scraping
- Custom search parameters and filters

## Data Flow

1. **Scraping**: Jobs are collected from various sources and stored in SQLite
2. **Analysis**: Resumes are parsed and analyzed against job database
3. **Matching**: AI-powered matching considers multiple factors (salary, location, skills, culture fit)
4. **Export**: Results can be exported in multiple formats (CSV, JSON, HTML reports)

## Development Guidelines

### Adding New Scrapers
1. Inherit from `BaseJobScraper` in `scrapers/base_scraper.py`
2. Implement required methods: `search_jobs()`, `parse_job_details()`
3. Handle rate limiting and respectful scraping practices
4. Add scraper to CLI command router

### Database Changes
- Use the `database/models.py` for schema definitions
- Database migrations are handled through versioned SQL files
- Always test database operations with sample data

### AI Analysis Extensions
- New analysis features should extend the `analysis/job_matcher.py` module
- Consider adding configurable scoring weights for different criteria
- Test AI analysis with various resume and job combinations

## Testing Strategy

- Unit tests for each scraper with mock data
- Database operations tested with temporary SQLite files
- AI analysis tested with sample resumes and job descriptions
- Integration tests for complete scrape-to-analysis workflows