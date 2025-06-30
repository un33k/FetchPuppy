"""
Site Manager for JobSite
Manages tracked career sites and their configurations
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from urllib.parse import urlparse


@dataclass
class TrackedSite:
    """Represents a tracked career site"""
    url: str
    name: str
    added_date: str
    last_scraped: Optional[str] = None
    active: bool = True
    jobs_found: int = 0
    success_rate: float = 0.0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrackedSite':
        return cls(**data)


class SiteManager:
    """Manages tracked career sites for automated job searching"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.sites_file = config.data_dir / "tracked_sites.json"
        self.sites_file.parent.mkdir(exist_ok=True)
        
    def add_site(self, url: str, name: Optional[str] = None) -> bool:
        """Add a new site to track"""
        try:
            # Normalize URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Generate name if not provided
            if not name:
                parsed = urlparse(url)
                name = parsed.netloc.replace('www.', '').title()
            
            # Load existing sites
            sites = self.load_sites()
            
            # Check if site already exists
            for site in sites:
                if site.url == url:
                    self.logger.warning(f"Site already tracked: {url}")
                    return False
            
            # Create new site
            new_site = TrackedSite(
                url=url,
                name=name,
                added_date=datetime.now().isoformat()
            )
            
            sites.append(new_site)
            self.save_sites(sites)
            
            self.logger.info(f"Added site: {name} ({url})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding site: {e}")
            return False
    
    def remove_site(self, url: str) -> bool:
        """Remove a site from tracking"""
        try:
            sites = self.load_sites()
            original_count = len(sites)
            
            sites = [site for site in sites if site.url != url]
            
            if len(sites) < original_count:
                self.save_sites(sites)
                self.logger.info(f"Removed site: {url}")
                return True
            else:
                self.logger.warning(f"Site not found: {url}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error removing site: {e}")
            return False
    
    def list_sites(self) -> List[TrackedSite]:
        """List all tracked sites"""
        return self.load_sites()
    
    def get_active_sites(self) -> List[TrackedSite]:
        """Get only active sites"""
        return [site for site in self.load_sites() if site.active]
    
    def update_site_stats(self, url: str, jobs_found: int, success: bool) -> None:
        """Update site statistics after scraping"""
        try:
            sites = self.load_sites()
            
            for site in sites:
                if site.url == url:
                    site.last_scraped = datetime.now().isoformat()
                    site.jobs_found += jobs_found
                    
                    # Update success rate (simple moving average)
                    if hasattr(site, '_scrape_attempts'):
                        site._scrape_attempts += 1
                    else:
                        site._scrape_attempts = 1
                    
                    if hasattr(site, '_successful_scrapes'):
                        if success:
                            site._successful_scrapes += 1
                    else:
                        site._successful_scrapes = 1 if success else 0
                    
                    site.success_rate = site._successful_scrapes / site._scrape_attempts
                    break
            
            self.save_sites(sites)
            
        except Exception as e:
            self.logger.error(f"Error updating site stats: {e}")
    
    def load_sites(self) -> List[TrackedSite]:
        """Load sites from file"""
        try:
            if not self.sites_file.exists():
                return []
            
            with open(self.sites_file, 'r') as f:
                data = json.load(f)
            
            return [TrackedSite.from_dict(site_data) for site_data in data]
            
        except Exception as e:
            self.logger.error(f"Error loading sites: {e}")
            return []
    
    def save_sites(self, sites: List[TrackedSite]) -> None:
        """Save sites to file"""
        try:
            data = [site.to_dict() for site in sites]
            
            with open(self.sites_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving sites: {e}")
    
    def get_site_info(self, url: str) -> Optional[TrackedSite]:
        """Get information about a specific site"""
        sites = self.load_sites()
        for site in sites:
            if site.url == url:
                return site
        return None
    
    def toggle_site_active(self, url: str, active: bool) -> bool:
        """Activate or deactivate a site"""
        try:
            sites = self.load_sites()
            
            for site in sites:
                if site.url == url:
                    site.active = active
                    self.save_sites(sites)
                    status = "activated" if active else "deactivated"
                    self.logger.info(f"Site {status}: {url}")
                    return True
            
            self.logger.warning(f"Site not found: {url}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error toggling site: {e}")
            return False