"""
Claudia (Claude-inspired Job Site Assistant)
AI-Powered Job Scraping and Analysis Platform

Main CLI entry point that coordinates between modular components.
"""

from pathlib import Path
import sys

# Add parent directory to path for imports
claudia_dir = Path(__file__).parent.parent
cli_dir = Path(__file__).parent
sys.path.insert(0, str(claudia_dir))
sys.path.insert(0, str(cli_dir))

from argument_parser import split_arguments, parse_arguments, create_parser  # noqa: E402
from command_router import CommandRouter  # noqa: E402
from help_system import show_version, show_examples  # noqa: E402
from utils.colors import Colors, error  # noqa: E402


def main() -> None:
    """Main entry point for Claudia CLI"""
    
    # Split arguments
    claudia_args, remaining_args = split_arguments()
    
    # Initialize command router
    router = CommandRouter()
    
    # Handle help requests before main parsing
    if router.handle_help_requests(claudia_args):
        return
    
    # Parse arguments
    args, extra_args = parse_arguments(claudia_args)
    remaining_args.extend(extra_args)
    
    # Handle version command
    if args.version:
        show_version()
        return
    
    # Handle examples command
    if args.examples:
        show_examples()
        return
    
    # Initialize configuration
    router.initialize_config()
    
    # Route commands
    try:
        if not args.command:
            parser = create_parser()
            parser.print_help()
            return
        
        success = False
        
        if args.command == "scrape":
            success = router.handle_scrape_command(args, remaining_args)
        elif args.command == "analyze":
            success = router.handle_analyze_command(args, remaining_args)
        elif args.command == "match":
            success = router.handle_match_command(args, remaining_args)
        elif args.command == "search":
            success = router.handle_search_command(args, remaining_args)
        elif args.command == "export":
            success = router.handle_export_command(args, remaining_args)
        elif args.command == "database":
            success = router.handle_database_command(args, remaining_args)
        elif args.command == "sites":
            success = router.handle_sites_command(args, remaining_args)
        elif args.command == "resume":
            success = router.handle_resume_command(args, remaining_args)
        elif args.command == "llm":
            success = router.handle_llm_command(args, remaining_args)
        elif args.command == "discover":
            success = router.handle_discover_command(args, remaining_args)
        elif args.command == "dev":
            success = router.handle_dev_command(args, remaining_args)
        else:
            print(error(f"Unknown command: {args.command}"))
            parser = create_parser()
            parser.print_help()
            return
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation cancelled by user{Colors.NC}")
        sys.exit(130)
    except Exception as e:
        print(error(f"Unexpected error: {e}"))
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()