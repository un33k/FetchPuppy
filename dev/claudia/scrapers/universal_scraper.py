"""
Universal Job Scraper
AI-powered scraper that can adapt to any job site using Claude/OpenAI for navigation and data extraction
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from browser_controller import BrowserController
from ai_navigator import AINavigator, NavigationInstruction, PageAnalysis
from page_analyzer import PageAnalyzer
from data_extractor import DataExtractor
from database.models import Job


class UniversalScraper:
    """AI-powered universal job scraper that adapts to any job site"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.browser_controller = BrowserController(config)
        self.ai_navigator = AINavigator(config)
        self.page_analyzer = PageAnalyzer(config)
        self.data_extractor = DataExtractor(config)
        
        # Scraping state
        self.jobs_found = []
        self.visited_urls = set()
        self.current_site = None
    
    async def scrape_jobs(self, 
                         site_url: str,
                         search_query: str,
                         location: Optional[str] = None,
                         max_results: int = 100,
                         **filters) -> List[Job]:
        """Main entry point for universal job scraping"""
        
        self.logger.info(f"Starting universal scrape: {search_query} on {site_url}")
        self.current_site = urlparse(site_url).netloc
        self.jobs_found = []
        self.visited_urls = set()
        
        try:
            async with self.browser_controller as browser:
                async with browser.get_page() as page:
                    
                    # Step 1: Navigate to the site and analyze
                    success = await self._navigate_and_analyze(page, site_url, search_query, location)
                    if not success:
                        self.logger.error("Failed to navigate and analyze site")
                        return []
                    
                    # Step 2: Perform job search
                    search_success = await self._perform_search(page, search_query, location, **filters)
                    if not search_success:
                        self.logger.error("Failed to perform job search")
                        return []
                    
                    # Step 3: Extract job listings with pagination
                    await self._extract_all_jobs(page, max_results)
                    
                    self.logger.info(f"Scraping complete: {len(self.jobs_found)} jobs found")
                    return self.jobs_found
                    
        except Exception as e:
            self.logger.error(f"Universal scraper error: {e}")
            return []
    
    async def discover_site_structure(self, site_url: str) -> Dict[str, Any]:
        """Analyze a new job site and return its structure information"""
        
        self.logger.info(f"Discovering site structure for: {site_url}")
        
        try:
            async with self.browser_controller as browser:
                async with browser.get_page() as page:
                    
                    # Navigate to site
                    if not await browser.navigate_to(page, site_url):
                        return {"error": "Failed to load site"}
                    
                    # Analyze page structure
                    analysis = await self.ai_navigator.analyze_page(
                        page, 
                        "analyze site structure and identify job search capabilities",
                        screenshot=True
                    )
                    
                    # Get additional page info
                    page_info = await self.page_analyzer.analyze_page_structure(page)
                    
                    return {
                        "site_url": site_url,
                        "page_type": analysis.page_type,
                        "elements_found": analysis.elements_found,
                        "confidence": analysis.confidence,
                        "reasoning": analysis.reasoning,
                        "page_info": page_info,
                        "discovery_date": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            self.logger.error(f"Site discovery error: {e}")
            return {"error": str(e)}
    
    async def _navigate_and_analyze(self, page, site_url: str, search_query: str, location: Optional[str]) -> bool:
        """Navigate to site and perform initial analysis"""
        
        # Navigate to the main site
        if not await self.browser_controller.navigate_to(page, site_url):
            return False
        
        # Analyze the landing page
        task = f"find job search functionality for query '{search_query}'"
        if location:
            task += f" in location '{location}'"
        
        analysis = await self.ai_navigator.analyze_page(page, task, screenshot=True)
        
        if analysis.confidence < 0.3:
            self.logger.warning(f"Low confidence in page analysis: {analysis.confidence}")
        
        self.logger.info(f"Page analysis: {analysis.page_type} - {analysis.reasoning}")
        return True
    
    async def _perform_search(self, page, search_query: str, location: Optional[str], **filters) -> bool:
        """Execute job search based on AI analysis"""
        
        # Get search strategy from AI
        task = f"search for '{search_query}'"
        if location:
            task += f" in '{location}'"
        
        analysis = await self.ai_navigator.analyze_page(page, task)
        
        # Execute navigation instructions
        for instruction in analysis.navigation_instructions:
            success = await self._execute_instruction(page, instruction, search_query, location)
            if not success:
                self.logger.warning(f"Failed to execute: {instruction.description}")
        
        # Wait for results to load
        await self.browser_controller.wait_for_page_load(page)
        await asyncio.sleep(2)  # Additional wait for dynamic content
        
        # Verify we're on a results page
        results_analysis = await self.ai_navigator.analyze_page(
            page, "identify job listings and pagination"
        )
        
        if results_analysis.page_type == "job_listings":
            self.logger.info("Successfully reached job listings page")
            return True
        else:
            self.logger.warning("May not have reached job listings page")
            return True  # Continue anyway, might still find jobs
    
    async def _execute_instruction(self, page, instruction: NavigationInstruction, 
                                 search_query: str, location: Optional[str]) -> bool:
        """Execute a single navigation instruction"""
        
        try:
            if instruction.action == "navigate":
                return await self.browser_controller.navigate_to(page, instruction.url)
            
            elif instruction.action == "click":
                return await self.browser_controller.click_element(page, instruction.selector)
            
            elif instruction.action == "type":
                text = instruction.text
                # Replace placeholders with actual values
                if text and "{search_query}" in text:
                    text = text.replace("{search_query}", search_query)
                if text and "{location}" in text and location:
                    text = text.replace("{location}", location)
                
                return await self.browser_controller.type_text(page, instruction.selector, text)
            
            elif instruction.action == "wait":
                if instruction.selector:
                    return await self.browser_controller.wait_for_element(page, instruction.selector)
                else:
                    await asyncio.sleep(2)
                    return True
            
            elif instruction.action == "scroll":
                await self.browser_controller.scroll_page(page)
                return True
            
            else:
                self.logger.warning(f"Unknown instruction action: {instruction.action}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing instruction {instruction.action}: {e}")
            return False
    
    async def _extract_all_jobs(self, page, max_results: int) -> None:
        """Extract jobs from all pages with pagination"""
        
        jobs_extracted = 0
        page_num = 1
        
        while jobs_extracted < max_results:
            self.logger.info(f"Extracting jobs from page {page_num}")
            
            # Extract jobs from current page
            page_jobs = await self._extract_jobs_from_page(page)
            
            if not page_jobs:
                self.logger.info("No more jobs found, stopping pagination")
                break
            
            self.jobs_found.extend(page_jobs)
            jobs_extracted += len(page_jobs)
            
            # Check if we have enough jobs
            if jobs_extracted >= max_results:
                self.logger.info(f"Reached max results limit: {max_results}")
                break
            
            # Try to go to next page
            next_page_success = await self._go_to_next_page(page)
            if not next_page_success:
                self.logger.info("No more pages available")
                break
            
            page_num += 1
            
            # Safety limit
            if page_num > 20:
                self.logger.warning("Reached maximum page limit (20)")
                break
    
    async def _extract_jobs_from_page(self, page) -> List[Job]:
        """Extract job data from the current page"""
        
        try:
            # Analyze page for job listings
            analysis = await self.ai_navigator.analyze_page(
                page, "extract all job listings from this page"
            )
            
            if not analysis.elements_found.get("job_cards") and not analysis.elements_found.get("job_links"):
                self.logger.warning("No job elements found on page")
                return []
            
            # Use data extractor to get structured job data
            jobs = await self.data_extractor.extract_jobs_from_page(page, analysis)
            
            # Add metadata to jobs
            for job in jobs:
                job.source = self.current_site
                job.scraped_date = datetime.now()
                if page.url not in self.visited_urls:
                    self.visited_urls.add(page.url)
            
            self.logger.info(f"Extracted {len(jobs)} jobs from current page")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error extracting jobs from page: {e}")
            return []
    
    async def _go_to_next_page(self, page) -> bool:
        """Navigate to next page of results"""
        
        try:
            # Analyze page for pagination
            analysis = await self.ai_navigator.analyze_page(
                page, "find next page or pagination controls"
            )
            
            pagination_selectors = analysis.elements_found.get("pagination", [])
            if not pagination_selectors:
                return False
            
            # Try different pagination approaches
            next_selectors = [
                "a[aria-label*='next' i]",
                "a[title*='next' i]", 
                "button[aria-label*='next' i]",
                ".next",
                ".pagination-next",
                "[data-testid*='next']",
                "a:contains('Next')",
                "button:contains('Next')"
            ] + pagination_selectors
            
            for selector in next_selectors:
                try:
                    # Check if element exists and is clickable
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        # Get current URL to detect if navigation happened
                        current_url = page.url
                        
                        # Click next page
                        await self.browser_controller.click_element(page, selector)
                        await self.browser_controller.wait_for_page_load(page)
                        
                        # Check if URL changed or new content loaded
                        if page.url != current_url:
                            self.logger.info(f"Successfully navigated to next page: {page.url}")
                            return True
                        
                        # Wait a bit more for dynamic content
                        await asyncio.sleep(3)
                        return True
                        
                except Exception as e:
                    self.logger.debug(f"Failed with selector {selector}: {e}")
                    continue
            
            self.logger.info("No working pagination found")
            return False
            
        except Exception as e:
            self.logger.error(f"Error navigating to next page: {e}")
            return False
    
    def get_scraping_stats(self) -> Dict[str, Any]:
        """Get statistics about the current scraping session"""
        return {
            "jobs_found": len(self.jobs_found),
            "pages_visited": len(self.visited_urls),
            "current_site": self.current_site,
            "unique_companies": len(set(job.company for job in self.jobs_found if job.company)),
            "unique_locations": len(set(job.location for job in self.jobs_found if job.location)),
        }