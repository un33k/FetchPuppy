"""
Claudia CLI Argument Parser
Handles command line argument parsing and configuration
"""

import argparse
from pathlib import Path
import sys

# Add parent directory to path for imports
claudia_dir = Path(__file__).parent.parent
sys.path.insert(0, str(claudia_dir))

from utils.colors import Colors  # noqa: E402
from cli.help_system import ColoredHelpFormatter  # noqa: E402


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description=f"{Colors.CYAN}Claudia (Claude-inspired Job Site Assistant){Colors.NC}\n{Colors.YELLOW}AI-Powered Job Scraping and Analysis{Colors.NC}",
        formatter_class=ColoredHelpFormatter,
        epilog=f"""
{Colors.YELLOW}Examples:{Colors.NC}
  {Colors.GREEN}./claudia scrape universal "python developer" --site indeed.com --location remote{Colors.NC}
  {Colors.GREEN}./claudia scrape universal "data scientist" --site linkedin.com/jobs --location "San Francisco"{Colors.NC}
  {Colors.GREEN}./claudia discover jobsite.com --analyze-structure{Colors.NC}
  {Colors.GREEN}./claudia analyze resume ~/Documents/resume.pdf{Colors.NC}
  {Colors.GREEN}./claudia match --salary 100k --location remote --skills python,ai{Colors.NC}
  {Colors.GREEN}./claudia export --format csv --filter remote{Colors.NC}
  {Colors.GREEN}./claudia database --init{Colors.NC}
  {Colors.GREEN}./claudia llm --ping --all --hello{Colors.NC}

{Colors.YELLOW}Universal Scraper:{Colors.NC}
  • Works with any job site using AI navigation
  • Adapts to site changes automatically
  • No site-specific configuration needed

{Colors.YELLOW}Analysis Features:{Colors.NC}
  • Resume parsing and skill extraction
  • AI-powered job matching and scoring
  • Salary comparison and market analysis
  • Company culture fit assessment

{Colors.BLUE}Setup:{Colors.NC}
  1. Run {Colors.CYAN}./bootstrap.sh{Colors.NC} to setup environment
  2. Copy {Colors.CYAN}.env.example{Colors.NC} to {Colors.CYAN}.env{Colors.NC} and add OpenAI API key
  3. Initialize database with {Colors.CYAN}./claudia database --init{Colors.NC}
        """,
    )

    # Main command
    parser.add_argument(
        "command",
        nargs="?",
        choices=["scrape", "analyze", "match", "export", "database", "llm", "discover", "dev"],
        help="Main command to execute"
    )
    
    # Subcommand for specific operations
    parser.add_argument(
        "subcommand",
        nargs="?",
        help="Subcommand (e.g., scraper name, analysis type, export format)"
    )
    
    # Additional positional arguments
    parser.add_argument(
        "args",
        nargs="*",
        help="Additional arguments (e.g., search query, file path)"
    )

    # Global options
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information"
    )
    
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Show usage examples"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )

    # Scraping options
    scrape_group = parser.add_argument_group("scraping options")
    scrape_group.add_argument(
        "--site",
        type=str,
        help="Job site URL (e.g., indeed.com, linkedin.com/jobs)"
    )
    
    scrape_group.add_argument(
        "--location", "-l",
        type=str,
        help="Job location (city, state, or 'remote')"
    )
    
    scrape_group.add_argument(
        "--salary-min",
        type=str,
        help="Minimum salary (e.g., '80k', '100000')"
    )
    
    scrape_group.add_argument(
        "--salary-max",
        type=str,
        help="Maximum salary (e.g., '120k', '150000')"
    )
    
    scrape_group.add_argument(
        "--job-type",
        choices=["full-time", "part-time", "contract", "internship"],
        help="Type of employment"
    )
    
    scrape_group.add_argument(
        "--remote",
        action="store_true",
        help="Include remote jobs"
    )
    
    scrape_group.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Maximum number of jobs to scrape (default: 100)"
    )

    # Analysis options
    analysis_group = parser.add_argument_group("analysis options")
    analysis_group.add_argument(
        "--skills",
        type=str,
        help="Comma-separated list of skills to match"
    )
    
    analysis_group.add_argument(
        "--experience",
        type=str,
        help="Years of experience (e.g., '3-5', '5+', 'entry')"
    )
    
    analysis_group.add_argument(
        "--company-size",
        choices=["startup", "small", "medium", "large", "enterprise"],
        help="Preferred company size"
    )
    
    analysis_group.add_argument(
        "--industry",
        type=str,
        help="Preferred industry"
    )

    # Export options
    export_group = parser.add_argument_group("export options")
    export_group.add_argument(
        "--format",
        choices=["csv", "json", "html", "xlsx"],
        default="csv",
        help="Export format (default: csv)"
    )
    
    export_group.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path"
    )
    
    export_group.add_argument(
        "--filter",
        type=str,
        help="Filter jobs by criteria"
    )
    
    export_group.add_argument(
        "--top",
        type=int,
        help="Export only top N results"
    )

    # Database options
    db_group = parser.add_argument_group("database options")
    db_group.add_argument(
        "--init",
        action="store_true",
        help="Initialize database schema"
    )
    
    db_group.add_argument(
        "--stats",
        action="store_true",
        help="Show database statistics"
    )
    
    db_group.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old database entries"
    )
    
    db_group.add_argument(
        "--older-than",
        type=str,
        help="Clean up entries older than specified time (e.g., '30d', '1w')"
    )

    # Generic scraper options
    generic_group = parser.add_argument_group("generic scraper options")
    generic_group.add_argument(
        "--url",
        type=str,
        help="Base URL for generic scraper"
    )
    
    generic_group.add_argument(
        "--search",
        type=str,
        help="Search query for generic scraper"
    )
    
    generic_group.add_argument(
        "--selectors",
        type=str,
        help="JSON file with CSS selectors for generic scraper"
    )

    # LLM options
    llm_group = parser.add_argument_group("LLM testing options")
    llm_group.add_argument(
        "--ping",
        action="store_true",
        help="Test connectivity to AI providers"
    )
    
    llm_group.add_argument(
        "--local",
        action="store_true",
        help="Test local LLM (LM Studio)"
    )
    
    llm_group.add_argument(
        "--claude",
        action="store_true",
        help="Test Claude API"
    )
    
    llm_group.add_argument(
        "--openai",
        action="store_true",
        help="Test OpenAI API"
    )
    
    llm_group.add_argument(
        "--all",
        action="store_true",
        help="Test all configured AI providers"
    )
    
    llm_group.add_argument(
        "--hello",
        action="store_true",
        help="Send a friendly hello message to test conversation"
    )

    return parser


def split_arguments():
    """Split command line arguments"""
    # For now, no special splitting needed like in Ansible version
    return sys.argv[1:], []


def parse_arguments(claudia_args):
    """Parse command line arguments"""
    parser = create_parser()
    args, remaining_args = parser.parse_known_args(claudia_args)
    return args, remaining_args