"""
Configuration management for Claudia
Handles environment variables, config files, and application settings
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ClaudiaConfig:
    """Configuration manager for Claudia application"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or self._find_project_root()
        self.env_file = self.project_root / ".env"
        self.data_dir = self.project_root / "data"
        
        # Load environment variables
        if self.env_file.exists():
            load_dotenv(self.env_file)
    
    def _find_project_root(self) -> Path:
        """Find the project root directory"""
        current = Path(__file__).parent
        while current != current.parent:
            # Look for both claudia executable and bootstrap.sh in same directory
            if (current / "claudia").exists() and (current / "bootstrap.sh").exists():
                return current
            current = current.parent
        return Path.cwd()
    
    @property
    def database_path(self) -> Path:
        """Get database file path"""
        db_path = os.getenv("DATABASE_PATH", "data/jobs.db")
        if not os.path.isabs(db_path):
            return self.project_root / db_path
        return Path(db_path)
    
    @property
    def openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key"""
        return os.getenv("OPENAI_API_KEY")
    
    @property
    def claude_api_key(self) -> Optional[str]:
        """Get Claude API key"""
        return os.getenv("CLAUDE_API_KEY")
    
    @property
    def claude_model(self) -> str:
        """Get Claude model name"""
        return os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    
    @property
    def openai_model(self) -> str:
        """Get OpenAI model name"""
        return os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    @property
    def local_llm_enabled(self) -> bool:
        """Check if local LLM is enabled"""
        return os.getenv("LOCAL_LLM_ENABLED", "false").lower() == "true"
    
    @property
    def local_llm_base_url(self) -> str:
        """Get local LLM base URL"""
        return os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:1234/v1")
    
    @property
    def local_llm_model(self) -> str:
        """Get local LLM model name"""
        return os.getenv("LOCAL_LLM_MODEL", "llama3.1:8b-instruct-q4_K_M")
    
    @property
    def local_llm_api_key(self) -> str:
        """Get local LLM API key (usually just 'lm-studio')"""
        return os.getenv("LOCAL_LLM_API_KEY", "lm-studio")
    
    @property
    def log_level(self) -> str:
        """Get log level"""
        return os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def scraper_delay(self) -> float:
        """Get scraper delay in seconds"""
        return float(os.getenv("SCRAPER_DELAY", "2.0"))
    
    @property
    def scraper_mode(self) -> str:
        """Get scraper mode (headless or headful)"""
        return os.getenv("SCRAPER_MODE", "headless")
    
    @property
    def browser_pool_size(self) -> int:
        """Get browser pool size for concurrent scraping"""
        return int(os.getenv("BROWSER_POOL_SIZE", "3"))
    
    @property
    def user_agent(self) -> str:
        """Get user agent for web scraping"""
        return os.getenv("USER_AGENT", 
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/91.0.4472.124 Safari/537.36")
    
    @property
    def export_dir(self) -> Path:
        """Get export directory path"""
        return self.data_dir / "exports"
    
    @property
    def resume_dir(self) -> Path:
        """Get resume directory path"""
        return self.data_dir / "resumes"
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        self.data_dir.mkdir(exist_ok=True)
        self.export_dir.mkdir(exist_ok=True)
        self.resume_dir.mkdir(exist_ok=True)
    
    def get_scraper_config(self, scraper_name: str) -> Dict[str, Any]:
        """Get configuration for a specific scraper"""
        config = {
            "delay": self.scraper_delay,
            "user_agent": self.user_agent,
            "timeout": float(os.getenv(f"{scraper_name.upper()}_TIMEOUT", "30")),
            "max_retries": int(os.getenv(f"{scraper_name.upper()}_MAX_RETRIES", "3")),
        }
        
        # Add scraper-specific configuration
        if scraper_name == "indeed":
            config.update({
                "base_url": "https://www.indeed.com",
                "results_per_page": int(os.getenv("INDEED_RESULTS_PER_PAGE", "50")),
            })
        elif scraper_name == "linkedin":
            config.update({
                "base_url": "https://www.linkedin.com",
                "login_required": True,
                "linkedin_username": os.getenv("LINKEDIN_USERNAME"),
                "linkedin_password": os.getenv("LINKEDIN_PASSWORD"),
            })
        
        return config
    
    def validate_config(self) -> Dict[str, str]:
        """Validate configuration and return any errors"""
        errors = {}
        
        # Check required directories
        if not self.project_root.exists():
            errors["project_root"] = f"Project root not found: {self.project_root}"
        
        # Check AI API keys - at least one is required (unless local LLM is enabled)
        if not self.openai_api_key and not self.claude_api_key and not self.local_llm_enabled:
            errors["ai_api_keys"] = "At least one AI API key required (OpenAI, Claude, or enable Local LLM)"
        
        # Check database directory is writable
        try:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            errors["database_path"] = f"Cannot create database directory: {self.database_path.parent}"
        
        return errors