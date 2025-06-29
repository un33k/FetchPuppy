"""
Help system and formatting for Claudia CLI
Provides rich help output with colors and examples
"""

import argparse
from pathlib import Path
import sys

# Add parent directory to path for imports
claudia_dir = Path(__file__).parent.parent
sys.path.insert(0, str(claudia_dir))

from utils.colors import Colors  # noqa: E402


class ColoredHelpFormatter(argparse.HelpFormatter):
    """Custom help formatter with color support"""
    
    def _format_usage(self, usage, actions, groups, prefix):
        if prefix is None:
            prefix = f"{Colors.YELLOW}usage: {Colors.NC}"
        return super()._format_usage(usage, actions, groups, prefix)
    
    def _format_action_invocation(self, action):
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            metavar, = self._metavar_formatter(action, default)(1)
            return f"{Colors.GREEN}{metavar}{Colors.NC}"
        else:
            parts = []
            if action.nargs == 0:
                parts.extend([f"{Colors.CYAN}{s}{Colors.NC}" for s in action.option_strings])
            else:
                default = self._get_default_metavar_for_optional(action)
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    parts.append(f"{Colors.CYAN}{option_string}{Colors.NC} {args_string}")
            return ', '.join(parts)


def show_version():
    """Display version information"""
    print(f"{Colors.CYAN}Claudia (Claude-inspired Job Site Assistant){Colors.NC}")
    print(f"{Colors.YELLOW}Version: 1.0.0{Colors.NC}")
    print(f"{Colors.BLUE}Intelligent Job Scraping and AI-Powered Analysis{Colors.NC}")
    print()
    print("Components:")
    print(f"  • Job Scrapers: Indeed, LinkedIn, Generic")
    print(f"  • AI Analysis: OpenAI-powered job matching")
    print(f"  • Data Storage: SQLite database")
    print(f"  • Export Formats: CSV, JSON, HTML")


def show_examples():
    """Display usage examples"""
    print(f"{Colors.YELLOW}Claudia Usage Examples:{Colors.NC}")
    print()
    
    print(f"{Colors.CYAN}Job Scraping:{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia scrape indeed \"python developer\" --location remote{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia scrape linkedin \"data scientist\" --location \"San Francisco\"{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia scrape generic --url jobsite.com --search \"ML engineer\"{Colors.NC}")
    print()
    
    print(f"{Colors.CYAN}Resume Analysis:{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia analyze resume ~/Documents/resume.pdf{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia analyze resume resume.docx --skills python,javascript{Colors.NC}")
    print()
    
    print(f"{Colors.CYAN}Job Matching:{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia match --salary 100k --location remote{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia match --skills python,ai --experience \"5+ years\"{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia match --company-size startup --industry tech{Colors.NC}")
    print()
    
    print(f"{Colors.CYAN}Data Export:{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia export --format csv --filter remote{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia export --format json --salary 80k+{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia export --html --top 20{Colors.NC}")
    print()
    
    print(f"{Colors.CYAN}Database Management:{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia database --init{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia database --stats{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia database --cleanup --older-than 30d{Colors.NC}")
    print()
    
    print(f"{Colors.CYAN}LLM Testing:{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia llm --ping --all{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia llm --ping --local{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia llm --ping --claude{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia llm --ping --openai{Colors.NC}")
    print()
    
    print(f"{Colors.CYAN}Development:{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia dev validate{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia dev test{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia dev lint{Colors.NC}")


def show_quick_help():
    """Display quick help information"""
    print(f"{Colors.CYAN}Claudia - AI-Powered Job Search Assistant{Colors.NC}")
    print()
    print(f"{Colors.YELLOW}Quick Commands:{Colors.NC}")
    print(f"  {Colors.GREEN}./claudia scrape [site] [query]{Colors.NC}     - Scrape jobs")
    print(f"  {Colors.GREEN}./claudia match [criteria]{Colors.NC}          - Find matching jobs") 
    print(f"  {Colors.GREEN}./claudia analyze resume [file]{Colors.NC}     - Analyze resume")
    print(f"  {Colors.GREEN}./claudia export [format]{Colors.NC}           - Export data")
    print(f"  {Colors.GREEN}./claudia --help{Colors.NC}                    - Full help")
    print(f"  {Colors.GREEN}./claudia --examples{Colors.NC}                - Usage examples")