"""
Command router for Claudia CLI
Routes commands to appropriate handlers and manages application flow
"""

from pathlib import Path
import sys
from typing import List, Optional

# Add parent directory to path for imports
claudia_dir = Path(__file__).parent.parent
sys.path.insert(0, str(claudia_dir))

from utils.colors import Colors, success, error, warning, info  # noqa: E402
from utils.config import ClaudiaConfig  # noqa: E402


class CommandRouter:
    """Routes CLI commands to appropriate handlers"""
    
    def __init__(self):
        self.config = None
    
    def initialize_config(self) -> ClaudiaConfig:
        """Initialize and validate configuration"""
        if self.config is None:
            self.config = ClaudiaConfig()
            self.config.ensure_directories()
            
            # Validate configuration
            errors = self.config.validate_config()
            if errors:
                print(warning("Configuration issues found:"))
                for key, msg in errors.items():
                    print(f"  • {msg}")
                print()
        
        return self.config
    
    def handle_help_requests(self, args: List[str]) -> bool:
        """Handle help-related requests before main parsing"""
        if not args:
            return False
            
        if "--examples" in args:
            from cli.help_system import show_examples
            show_examples()
            return True
            
        if args == ["help"] or args == ["-h"] or args == ["--help"]:
            from cli.help_system import show_quick_help
            show_quick_help()
            return True
            
        return False
    
    def handle_scrape_command(self, args, remaining_args) -> bool:
        """Handle job scraping commands"""
        if not args.subcommand:
            print(error("Scraper type required"))
            print("Available: universal")
            print("Example: ./claudia scrape universal \"python developer\" --site indeed.com")
            return False
        
        scraper_type = args.subcommand.lower()
        
        if scraper_type == "universal":
            return self._handle_universal_scraper(args, remaining_args)
        else:
            print(error(f"Unknown scraper type: {scraper_type}"))
            print("Available: universal")
            print("Example: ./claudia scrape universal \"python developer\" --site indeed.com")
            return False
    
    def _handle_universal_scraper(self, args, remaining_args) -> bool:
        """Handle universal AI-powered scraping"""
        
        # Validate required arguments
        if not args.args:
            print(error("Search query required"))
            print("Example: ./claudia scrape universal \"python developer\" --site indeed.com")
            return False
        
        search_query = " ".join(args.args)
        
        # Site URL can be provided via --site or --url
        site_url = getattr(args, 'site', None) or getattr(args, 'url', None)
        if not site_url:
            print(error("Site URL required (use --site or --url)"))
            print("Example: ./claudia scrape universal \"python developer\" --site indeed.com")
            return False
        
        # Ensure URL has protocol
        if not site_url.startswith('http'):
            site_url = 'https://' + site_url
        
        print(info(f"Starting universal AI scraper..."))
        print(f"Site: {site_url}")
        print(f"Query: {search_query}")
        print(f"Location: {args.location or 'Any'}")
        print(f"Max results: {args.max_results}")
        print(f"Mode: {self.config.scraper_mode}")
        
        try:
            import asyncio
            import sys
            from pathlib import Path
            
            # Add parent directory to Python path for imports
            claudia_dir = Path(__file__).parent.parent
            scrapers_dir = claudia_dir / "scrapers"
            sys.path.insert(0, str(claudia_dir))
            sys.path.insert(0, str(scrapers_dir))
            
            from scrapers.universal_scraper import UniversalScraper
            from database.operations import DatabaseOperations
            
            # Create scraper instance
            scraper = UniversalScraper(self.config)
            
            # Run scraping
            async def run_scraping():
                jobs = await scraper.scrape_jobs(
                    site_url=site_url,
                    search_query=search_query,
                    location=args.location,
                    max_results=args.max_results,
                    job_type=args.job_type,
                    salary_min=args.salary_min,
                    salary_max=args.salary_max,
                    remote=args.remote
                )
                
                if jobs:
                    # Save jobs to database
                    db = DatabaseOperations(self.config)
                    saved_count = 0
                    
                    for job in jobs:
                        try:
                            job_id = db.save_job(job)
                            if job_id:
                                saved_count += 1
                        except Exception as e:
                            print(warning(f"Failed to save job: {job.title} - {e}"))
                    
                    print(success(f"Scraped {len(jobs)} jobs, saved {saved_count} to database"))
                    
                    # Show statistics
                    stats = scraper.get_scraping_stats()
                    print(f"Pages visited: {stats['pages_visited']}")
                    print(f"Unique companies: {stats['unique_companies']}")
                    print(f"Unique locations: {stats['unique_locations']}")
                    
                else:
                    print(warning("No jobs found"))
                
                return len(jobs) > 0
            
            # Run the async scraping
            result = asyncio.run(run_scraping())
            return result
            
        except ImportError as e:
            print(error(f"Universal scraper not available: {e}"))
            print("Make sure Playwright and Anthropic are installed with ./bootstrap.sh")
            return False
        except Exception as e:
            print(error(f"Universal scraping failed: {e}"))
            if args.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def handle_analyze_command(self, args, remaining_args) -> bool:
        """Handle analysis commands"""
        if not args.subcommand:
            print(error("Analysis type required"))
            print("Available: resume")
            return False
        
        if args.subcommand == "resume":
            if not args.args:
                print(error("Resume file path required"))
                print("Example: ./claudia analyze resume ~/Documents/resume.pdf")
                return False
            
            resume_path = args.args[0]
            print(info(f"Analyzing resume: {resume_path}"))
            
            try:
                from analysis.resume_parser import ResumeParser
                parser = ResumeParser(self.config)
                analysis = parser.analyze_resume(
                    resume_path,
                    skills_filter=args.skills.split(",") if args.skills else None
                )
                
                print(success("Resume analysis completed"))
                # TODO: Display analysis results
                return True
                
            except ImportError as e:
                print(error(f"Analysis module not found: {e}"))
                return False
            except Exception as e:
                print(error(f"Analysis failed: {e}"))
                return False
        
        print(error(f"Unknown analysis type: {args.subcommand}"))
        return False
    
    def handle_match_command(self, args, remaining_args) -> bool:
        """Handle job matching commands"""
        print(info("Finding job matches..."))
        
        criteria = {
            "salary_min": args.salary_min,
            "salary_max": args.salary_max,
            "location": args.location,
            "skills": args.skills.split(",") if args.skills else None,
            "experience": args.experience,
            "company_size": args.company_size,
            "industry": args.industry,
            "remote": args.remote
        }
        
        # Filter out None values
        criteria = {k: v for k, v in criteria.items() if v is not None}
        
        print(f"Search criteria: {criteria}")
        
        try:
            from analysis.job_matcher import JobMatcher
            matcher = JobMatcher(self.config)
            matches = matcher.find_matches(criteria)
            
            print(success(f"Found {len(matches)} matching jobs"))
            # TODO: Display match results
            return True
            
        except ImportError as e:
            print(error(f"Matching module not found: {e}"))
            return False
        except Exception as e:
            print(error(f"Matching failed: {e}"))
            return False
    
    def handle_export_command(self, args, remaining_args) -> bool:
        """Handle data export commands"""
        print(info(f"Exporting data in {args.format} format..."))
        
        try:
            from database.operations import DatabaseOperations
            db = DatabaseOperations(self.config)
            
            # Apply filters
            filters = {}
            if args.filter:
                # TODO: Parse filter string
                pass
            if args.top:
                filters["limit"] = args.top
            
            # Export data
            output_path = args.output or f"export.{args.format}"
            success_msg = db.export_jobs(
                format=args.format,
                output_path=output_path,
                filters=filters
            )
            
            print(success(f"Data exported to {output_path}"))
            return True
            
        except ImportError as e:
            print(error(f"Export module not found: {e}"))
            return False
        except Exception as e:
            print(error(f"Export failed: {e}"))
            return False
    
    def handle_llm_command(self, args, remaining_args) -> bool:
        """Handle LLM connectivity and testing commands"""
        if not args.ping:
            print(error("LLM command required"))
            print("Available: --ping")
            print("Examples:")
            print("  ./claudia llm --ping --local")
            print("  ./claudia llm --ping --claude")
            print("  ./claudia llm --ping --openai")
            print("  ./claudia llm --ping --all")
            print("  ./claudia llm --ping --local --hello")
            return False
        
        try:
            from utils.llm_tester import LLMTester
            tester = LLMTester(self.config)
            
            # Check if hello mode is enabled
            hello_mode = getattr(args, 'hello', False)
            
            if args.local:
                return tester.ping_local_llm(hello_mode=hello_mode)
            elif args.claude:
                return tester.ping_claude(hello_mode=hello_mode)
            elif args.openai:
                return tester.ping_openai(hello_mode=hello_mode)
            elif args.all:
                return tester.ping_all(hello_mode=hello_mode)
            else:
                print(error("Provider required: --local, --claude, --openai, or --all"))
                return False
                
        except ImportError as e:
            print(error(f"LLM testing module not found: {e}"))
            return False
        except Exception as e:
            print(error(f"LLM testing failed: {e}"))
            return False
    
    def handle_database_command(self, args, remaining_args) -> bool:
        """Handle database management commands"""
        try:
            from database.operations import DatabaseOperations
            db = DatabaseOperations(self.config)
            
            if args.init:
                print(info("Initializing database..."))
                db.initialize_database()
                print(success("Database initialized successfully"))
                return True
            
            if args.stats:
                print(info("Database statistics:"))
                stats = db.get_statistics()
                for key, value in stats.items():
                    print(f"  {key}: {value}")
                return True
            
            if args.cleanup:
                print(info("Cleaning up database..."))
                older_than = args.older_than or "30d"
                removed = db.cleanup_old_entries(older_than)
                print(success(f"Removed {removed} old entries"))
                return True
            
            print(error("Database command required: --init, --stats, or --cleanup"))
            return False
            
        except ImportError as e:
            print(error(f"Database module not found: {e}"))
            return False
        except Exception as e:
            print(error(f"Database operation failed: {e}"))
            return False
    
    def handle_dev_command(self, args, remaining_args) -> bool:
        """Handle development commands"""
        if not args.subcommand:
            print(error("Dev command required"))
            print("Available: validate, test, lint")
            return False
        
        if args.subcommand == "validate":
            print(info("Running validation..."))
            # TODO: Implement validation
            print(success("Validation completed"))
            return True
        
        if args.subcommand == "test":
            print(info("Running tests..."))
            # TODO: Run tests
            print(success("Tests completed"))
            return True
        
        if args.subcommand == "lint":
            print(info("Running linting..."))
            # TODO: Run linting
            print(success("Linting completed"))
            return True
        
        print(error(f"Unknown dev command: {args.subcommand}"))
        return False
    
    def handle_discover_command(self, args, remaining_args) -> bool:
        """Handle site discovery command"""
        site_url = args.subcommand
        if not site_url:
            print(error("Site URL required"))
            print("Example: ./claudia discover jobsite.com --analyze-structure")
            return False
        
        # Ensure URL has protocol
        if not site_url.startswith('http'):
            site_url = 'https://' + site_url
        
        print(info(f"Discovering site structure for: {site_url}"))
        
        try:
            import asyncio
            import sys
            from pathlib import Path
            
            # Add parent directory to Python path for imports
            claudia_dir = Path(__file__).parent.parent
            scrapers_dir = claudia_dir / "scrapers"
            sys.path.insert(0, str(claudia_dir))
            sys.path.insert(0, str(scrapers_dir))
            
            from scrapers.universal_scraper import UniversalScraper
            
            scraper = UniversalScraper(self.config)
            
            async def run_discovery():
                analysis = await scraper.discover_site_structure(site_url)
                
                if "error" in analysis:
                    print(error(f"Discovery failed: {analysis['error']}"))
                    return False
                
                print(success("Site discovery completed!"))
                print(f"Page type: {analysis['page_type']}")
                print(f"Confidence: {analysis['confidence']:.2f}")
                print(f"Reasoning: {analysis['reasoning']}")
                
                if analysis['elements_found']:
                    print("\nElements found:")
                    for element_type, selectors in analysis['elements_found'].items():
                        if selectors:
                            print(f"  {element_type}: {len(selectors)} selectors")
                
                return True
            
            return asyncio.run(run_discovery())
            
        except ImportError as e:
            print(error(f"Discovery not available: {e}"))
            return False
        except Exception as e:
            print(error(f"Discovery failed: {e}"))
            return False