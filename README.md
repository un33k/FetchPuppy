# JobSite - AI-Powered Job Scraping & Analysis Platform

JobSite is an intelligent job search platform that scrapes job postings from multiple sources and uses AI to match them with your resume, preferences, and requirements. Find your perfect job based on salary, location, remote options, and skill alignment.

## Features

- 🔍 **Multi-Source Scraping**: Extract jobs from Indeed, LinkedIn, and other job sites
- 🤖 **AI-Powered Matching**: OpenAI integration for intelligent job-resume analysis
- 💰 **Smart Filtering**: Filter by salary, location, remote options, and more
- 📊 **Data Export**: Export results to CSV, JSON, or HTML reports
- 🗄️ **Local Storage**: SQLite database with optional file-based storage
- 🖥️ **Professional CLI**: Intuitive command-line interface with rich help system

## Quick Start

**🚀 New to JobSite? See [QUICK_START.md](QUICK_START.md) for the fastest setup!**

### 1. Environment Setup
```bash
# Setup and activate environment
./bootstrap.sh
source .venv/bin/activate
```

### 2. AI Configuration
```bash
# Copy and configure environment
cp .env.example .env

# Test AI connectivity (IMPORTANT!)
./claudia llm --ping --all
```

### 3. Initialize Database
```bash
./claudia database --init
```

### 4. Start Scraping
```bash
# Universal AI-powered scraping (works with any site!)
./claudia scrape universal "python developer" --site indeed.com --location "remote"
./claudia scrape universal "data scientist" --site linkedin.com/jobs --location "San Francisco"
```

### 5. Analyze & Export
```bash
# Export results
./claudia export --format csv --filter remote
./claudia export --format json
```

## CLI Commands

### Job Scraping
```bash
./claudia scrape indeed "job title" --location "city/remote"
./claudia scrape linkedin "job title" --location "city/remote"
./claudia scrape generic --url "job-site.com" --search "job title"
```

### Resume Analysis
```bash
./claudia analyze resume path/to/resume.pdf
./claudia analyze resume path/to/resume.docx --skills python,javascript
```

### Job Matching
```bash
./claudia match --salary 80k-120k --location remote
./claudia match --skills python,ai --experience "5+ years"
./claudia match --company-size startup --industry tech
```

### Data Management
```bash
./claudia database --init          # Initialize database
./claudia database --stats         # Show statistics
./claudia database --cleanup       # Remove old entries

./claudia export --format csv      # Export to CSV
./claudia export --format json     # Export to JSON
./claudia export --html            # Generate HTML report
```

### LLM Testing
```bash
./claudia llm --ping --all         # Test all AI providers
./claudia llm --ping --local       # Test local LLM (LM Studio)
./claudia llm --ping --claude      # Test Claude API
./claudia llm --ping --openai      # Test OpenAI API
```

### Development
```bash
./claudia dev validate             # Validate scrapers and database
./claudia dev test                 # Run unit tests
./claudia dev lint                 # Code linting and formatting
```

## Project Structure

```
JobSite/
├── claudia                        # Main CLI executable
├── bootstrap.sh                   # Environment setup
├── dev/claudia/                   # Application modules
│   ├── cli/                       # Command-line interface
│   ├── scrapers/                  # Job scraping modules
│   ├── database/                  # Database operations
│   ├── analysis/                  # AI analysis modules
│   └── utils/                     # Utility functions
├── data/                          # Data storage
│   ├── jobs.db                    # SQLite database
│   ├── resumes/                   # Resume storage
│   └── exports/                   # Export files
└── .vscode/                       # VS Code configuration
```

## Scrapers

### Indeed Scraper
- Search by job title and location
- Extract job details, salary, company info
- Respectful rate limiting

### LinkedIn Scraper
- Requires LinkedIn authentication
- Advanced job filtering options
- Company and recruiter information

### Generic Scraper
- Configurable for any job site
- CSS selector-based extraction
- Custom field mapping

## AI Analysis

The AI analysis engine uses OpenAI's API to:

- **Resume Parsing**: Extract skills, experience, and preferences
- **Job Matching**: Score jobs against resume criteria
- **Salary Analysis**: Compare offers against market data
- **Culture Fit**: Analyze company culture vs. preferences
- **Skill Gap Analysis**: Identify missing skills for dream jobs

## Configuration

### Environment Variables (.env)
```bash
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_PATH=data/jobs.db
LOG_LEVEL=INFO
SCRAPER_DELAY=2  # Seconds between requests
```

### Scraper Settings
Each scraper supports configuration for:
- Rate limiting and delays
- User agent rotation
- Proxy support
- Custom headers and authentication

## Development

### Adding New Scrapers
1. Create a new scraper class inheriting from `BaseJobScraper`
2. Implement required methods: `search_jobs()`, `parse_job_details()`
3. Add scraper to the CLI command router
4. Write unit tests with mock data

### Database Schema
Jobs are stored with comprehensive metadata:
- Basic info (title, company, location, salary)
- Job content (description, requirements, benefits)
- Scraping metadata (source, date, URL)
- Analysis results (AI scores, match percentages)

### Testing
```bash
# Run all tests
./claudia dev test

# Test specific scraper
python -m pytest tests/test_indeed_scraper.py

# Test with coverage
python -m pytest --cov=dev/claudia tests/
```

## Documentation

- **[QUICK_START.md](QUICK_START.md)** - ⚡ Fastest way to get JobSite running in 5 minutes
- **[LLM_TESTING.md](LLM_TESTING.md)** - 🔍 Test AI provider connectivity and diagnose issues
- **[LM_STUDIO_SETUP.md](LM_STUDIO_SETUP.md)** - 🏠 Complete guide to setting up local LLM with LM Studio
- **[CLAUDE.md](CLAUDE.md)** - 🛠️ Technical implementation details and architecture
- **[progress.md](progress.md)** - 📈 Development progress and feature status

## AI Provider Options

JobSite supports three AI options (in order of preference):

1. **🏆 Claude API** - Highest quality, supports screenshots
2. **🏠 Local LLM** - Privacy-first, zero cost via LM Studio
3. **🔄 OpenAI API** - Reliable fallback option

**Quick AI Setup:**
```bash
# Test all providers
./claudia llm --ping --all

# Setup local LLM (private, free)
# Follow LM_STUDIO_SETUP.md

# Or configure cloud APIs in .env:
CLAUDE_API_KEY=your_claude_key_here
OPENAI_API_KEY=your_openai_key_here
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the existing code style and patterns
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details