"""
Data Extractor for Universal Scraper
AI-powered extraction of structured job data from web pages
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import anthropic
from playwright.async_api import Page

from ai_navigator import PageAnalysis
from database.models import Job


class DataExtractor:
    """Extracts structured job data using AI and pattern matching"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI clients in order of preference
        self.claude_client = None
        self.openai_client = None
        self.local_llm_client = None
        
        # 1. Claude client (highest quality)
        if config.claude_api_key:
            self.claude_client = anthropic.Anthropic(api_key=config.claude_api_key)
        
        # 2. Local LLM client (private, no cost)
        elif config.local_llm_enabled:
            try:
                import openai
                self.local_llm_client = openai.OpenAI(
                    base_url=config.local_llm_base_url,
                    api_key=config.local_llm_api_key
                )
                self.local_llm_model = config.local_llm_model
            except Exception as e:
                self.logger.error(f"Failed to initialize local LLM: {e}")
        
        # 3. OpenAI client (fallback)
        elif config.openai_api_key:
            import openai
            self.openai_client = openai.OpenAI(api_key=config.openai_api_key)
    
    async def extract_jobs_from_page(self, page: Page, analysis: PageAnalysis) -> List[Job]:
        """Extract structured job data from a page"""
        
        try:
            # Get page content
            html_content = await page.content()
            page_url = page.url
            
            # Extract jobs using AI if available
            if self.claude_client or self.local_llm_client or self.openai_client:
                jobs = await self._extract_with_ai(html_content, page_url, analysis)
            else:
                # Fallback to pattern-based extraction
                jobs = await self._extract_with_patterns(page, analysis)
            
            # Clean and validate job data
            cleaned_jobs = []
            for job in jobs:
                cleaned_job = self._clean_job_data(job, page_url)
                if self._is_valid_job(cleaned_job):
                    cleaned_jobs.append(cleaned_job)
            
            self.logger.info(f"Extracted {len(cleaned_jobs)} valid jobs from page")
            return cleaned_jobs
            
        except Exception as e:
            self.logger.error(f"Error extracting jobs: {e}")
            return []
    
    async def _extract_with_ai(self, html: str, url: str, analysis: PageAnalysis) -> List[Job]:
        """Extract job data using AI"""
        
        # Truncate HTML for API limits
        html_excerpt = self._truncate_html_for_extraction(html)
        
        prompt = f"""Extract all job listings from this HTML page and return them as a JSON array.

URL: {url}
Page Analysis: {analysis.page_type}

HTML Content:
{html_excerpt}

For each job found, extract the following information if available:
- title: Job title
- company: Company name  
- location: Job location
- remote: true/false if remote work is mentioned
- job_type: full-time, part-time, contract, internship, etc.
- salary_min: Minimum salary (number only)
- salary_max: Maximum salary (number only)
- salary_currency: Currency code (USD, EUR, etc.)
- salary_period: annual, hourly, monthly, etc.
- description: Job description text
- requirements: Job requirements
- benefits: Job benefits
- url: Direct link to job posting
- posted_date: When job was posted (ISO format)
- external_id: Any job ID from the source site

Return ONLY a JSON array of job objects. Example:
[
  {{
    "title": "Software Engineer",
    "company": "Tech Corp",
    "location": "San Francisco, CA",
    "remote": false,
    "job_type": "full-time",
    "salary_min": 100000,
    "salary_max": 150000,
    "salary_currency": "USD",
    "salary_period": "annual",
    "description": "We are looking for...",
    "requirements": "Bachelor's degree...",
    "benefits": "Health insurance...",
    "url": "https://example.com/job/123",
    "external_id": "job_123"
  }}
]

If no jobs are found, return an empty array []."""

        try:
            if self.claude_client:
                response = self.claude_client.messages.create(
                    model=self.config.claude_model,
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
            elif self.local_llm_client:
                # Use local LLM with simpler, shorter prompt
                local_prompt = f"""Extract job listings from this HTML. Return JSON array only.

HTML: {self._truncate_html_for_extraction(html, 6000)}

Return JSON like:
[{{"title":"Software Engineer","company":"Tech Corp","location":"SF","salary_min":100000}}]

If no jobs found, return []"""

                response = self.local_llm_client.chat.completions.create(
                    model=self.local_llm_model,
                    messages=[{"role": "user", "content": local_prompt}],
                    temperature=0.1,
                    max_tokens=2000
                )
                response_text = response.choices[0].message.content
            elif self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=self.config.openai_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=3000
                )
                response_text = response.choices[0].message.content
            else:
                return []
            
            # Parse JSON response
            jobs_data = self._extract_json_from_response(response_text)
            
            # Convert to Job objects
            jobs = []
            for job_data in jobs_data:
                job = Job()
                
                # Map fields
                job.title = job_data.get('title')
                job.company = job_data.get('company')
                job.location = job_data.get('location')
                job.remote = job_data.get('remote', False)
                job.job_type = job_data.get('job_type')
                job.salary_min = job_data.get('salary_min')
                job.salary_max = job_data.get('salary_max')
                job.salary_currency = job_data.get('salary_currency', 'USD')
                job.salary_period = job_data.get('salary_period')
                job.description = job_data.get('description')
                job.requirements = job_data.get('requirements')
                job.benefits = job_data.get('benefits')
                job.url = job_data.get('url')
                job.external_id = job_data.get('external_id')
                
                # Parse posted date
                if job_data.get('posted_date'):
                    try:
                        job.posted_date = datetime.fromisoformat(job_data['posted_date'].replace('Z', '+00:00'))
                    except:
                        pass
                
                jobs.append(job)
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"AI extraction error: {e}")
            return []
    
    async def _extract_with_patterns(self, page: Page, analysis: PageAnalysis) -> List[Job]:
        """Fallback extraction using pattern matching"""
        
        jobs = []
        
        try:
            # Look for job containers based on analysis
            job_selectors = analysis.elements_found.get("job_cards", [])
            if not job_selectors:
                # Try common job card selectors
                job_selectors = [
                    ".job", ".job-card", ".job-item", ".job-listing",
                    "[data-job]", "[data-testid*='job']", ".result",
                    ".search-result", ".listing-item"
                ]
            
            # Extract jobs from each selector
            for selector in job_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        job = await self._extract_job_from_element(page, element)
                        if job and job.title:  # Only add if we got at least a title
                            jobs.append(job)
                            
                except Exception as e:
                    self.logger.debug(f"Failed with selector {selector}: {e}")
                    continue
            
            # If no jobs found with structured selectors, try link-based extraction
            if not jobs:
                jobs = await self._extract_jobs_from_links(page)
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Pattern extraction error: {e}")
            return []
    
    async def _extract_job_from_element(self, page: Page, element) -> Optional[Job]:
        """Extract job data from a single DOM element"""
        
        try:
            job = Job()
            
            # Extract title
            title_selectors = ["h1", "h2", "h3", ".title", ".job-title", "a"]
            job.title = await self._extract_text_from_selectors(element, title_selectors)
            
            # Extract company
            company_selectors = [".company", ".employer", ".org", ".company-name"]
            job.company = await self._extract_text_from_selectors(element, company_selectors)
            
            # Extract location
            location_selectors = [".location", ".job-location", ".place", ".city"]
            job.location = await self._extract_text_from_selectors(element, location_selectors)
            
            # Check for remote indicators
            element_text = await element.text_content() or ""
            job.remote = any(keyword in element_text.lower() for keyword in ['remote', 'work from home', 'telecommute'])
            
            # Extract salary
            salary_selectors = [".salary", ".pay", ".wage", ".compensation"]
            salary_text = await self._extract_text_from_selectors(element, salary_selectors)
            if salary_text:
                job.salary_min, job.salary_max = self._parse_salary(salary_text)
            
            # Extract job URL
            link_element = await element.query_selector("a[href]")
            if link_element:
                href = await link_element.get_attribute("href")
                if href:
                    job.url = urljoin(page.url, href)
            
            # Extract external ID from URL or data attributes
            if job.url:
                job.external_id = self._extract_job_id_from_url(job.url)
            
            # Extract description (limited)
            description_selectors = [".description", ".summary", ".snippet"]
            job.description = await self._extract_text_from_selectors(element, description_selectors)
            
            return job
            
        except Exception as e:
            self.logger.debug(f"Error extracting job from element: {e}")
            return None
    
    async def _extract_text_from_selectors(self, element, selectors: List[str]) -> Optional[str]:
        """Try multiple selectors to extract text"""
        
        for selector in selectors:
            try:
                sub_element = await element.query_selector(selector)
                if sub_element:
                    text = await sub_element.text_content()
                    if text and text.strip():
                        return text.strip()
            except:
                continue
        
        return None
    
    async def _extract_jobs_from_links(self, page: Page) -> List[Job]:
        """Extract basic job info from job links"""
        
        jobs = []
        
        # Find job-related links
        job_link_selectors = [
            "a[href*='job']",
            "a[href*='position']", 
            "a[href*='career']",
            "a[title*='job' i]",
            "a[title*='position' i]"
        ]
        
        for selector in job_link_selectors:
            try:
                links = await page.query_selector_all(selector)
                
                for link in links:
                    href = await link.get_attribute("href")
                    text = await link.text_content()
                    
                    if href and text and len(text.strip()) > 5:
                        job = Job()
                        job.title = text.strip()
                        job.url = urljoin(page.url, href)
                        job.external_id = self._extract_job_id_from_url(job.url)
                        
                        # Try to extract company from nearby elements
                        parent = await link.query_selector("..")
                        if parent:
                            company_text = await parent.text_content()
                            # Simple company extraction logic
                            lines = [line.strip() for line in company_text.split('\n') if line.strip()]
                            if len(lines) > 1:
                                job.company = lines[1]  # Often second line after title
                        
                        jobs.append(job)
                        
            except Exception as e:
                self.logger.debug(f"Error extracting from links {selector}: {e}")
                continue
        
        return jobs[:20]  # Limit to prevent too many low-quality jobs
    
    def _parse_salary(self, salary_text: str) -> tuple[Optional[int], Optional[int]]:
        """Parse salary range from text"""
        
        if not salary_text:
            return None, None
        
        # Remove common currency symbols and normalize
        normalized = re.sub(r'[,$]', '', salary_text)
        normalized = normalized.lower()
        
        # Look for salary ranges (e.g., "80k - 120k", "100,000-150,000")
        range_patterns = [
            r'(\d+)k?\s*-\s*(\d+)k?',
            r'(\d{3,})\s*-\s*(\d{3,})',
            r'(\d+),?(\d{3})\s*-\s*(\d+),?(\d{3})'
        ]
        
        for pattern in range_patterns:
            match = re.search(pattern, normalized)
            if match:
                groups = match.groups()
                
                if len(groups) == 2:
                    # Simple range like "80k - 120k"
                    min_val = int(groups[0])
                    max_val = int(groups[1])
                    
                    # Convert k to thousands
                    if 'k' in salary_text.lower():
                        min_val *= 1000
                        max_val *= 1000
                    
                    return min_val, max_val
                
                elif len(groups) == 4:
                    # Range with commas like "100,000 - 150,000"
                    min_val = int(groups[0] + groups[1])
                    max_val = int(groups[2] + groups[3])
                    return min_val, max_val
        
        # Look for single salary values
        single_patterns = [
            r'(\d+)k',
            r'(\d{3,})',
            r'(\d+),(\d{3})'
        ]
        
        for pattern in single_patterns:
            match = re.search(pattern, normalized)
            if match:
                if len(match.groups()) == 1:
                    value = int(match.group(1))
                    if 'k' in salary_text.lower():
                        value *= 1000
                    return value, value
                elif len(match.groups()) == 2:
                    value = int(match.group(1) + match.group(2))
                    return value, value
        
        return None, None
    
    def _extract_job_id_from_url(self, url: str) -> Optional[str]:
        """Extract job ID from URL"""
        
        # Common patterns for job IDs in URLs
        patterns = [
            r'/job[s]?/([a-zA-Z0-9-_]+)',
            r'/position[s]?/([a-zA-Z0-9-_]+)',
            r'jobId=([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
            r'/([a-zA-Z0-9-_]+)/?$'  # Last segment of URL
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                job_id = match.group(1)
                if len(job_id) > 2:  # Ignore very short IDs
                    return job_id
        
        return None
    
    def _extract_json_from_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Extract JSON array from AI response text"""
        
        try:
            # First try to parse as direct JSON
            return json.loads(response_text)
        except:
            pass
        
        # Look for JSON array within the response
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') + 1
        
        if json_start >= 0 and json_end > json_start:
            try:
                json_text = response_text[json_start:json_end]
                return json.loads(json_text)
            except:
                pass
        
        # Look for JSON object array pattern
        object_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(object_pattern, response_text)
        
        jobs = []
        for match in matches:
            try:
                job_data = json.loads(match)
                jobs.append(job_data)
            except:
                continue
        
        return jobs
    
    def _truncate_html_for_extraction(self, html: str, max_length: int = 20000) -> str:
        """Truncate HTML for AI processing while preserving job content"""
        
        if len(html) <= max_length:
            return html
        
        # Try to keep the main content area
        main_patterns = [
            r'<main[^>]*>.*?</main>',
            r'<div[^>]*class="[^"]*main[^"]*"[^>]*>.*?</div>',
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>.*?</div>',
            r'<div[^>]*class="[^"]*results[^"]*"[^>]*>.*?</div>'
        ]
        
        for pattern in main_patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match and len(match.group(0)) <= max_length:
                return match.group(0)
        
        # Fallback to simple truncation
        return html[:max_length] + "\n<!-- HTML truncated for AI processing -->"
    
    def _clean_job_data(self, job: Job, page_url: str) -> Job:
        """Clean and normalize job data"""
        
        # Clean title
        if job.title:
            job.title = re.sub(r'\s+', ' ', job.title.strip())
            job.title = job.title[:200]  # Limit length
        
        # Clean company
        if job.company:
            job.company = re.sub(r'\s+', ' ', job.company.strip())
            job.company = job.company[:100]
        
        # Clean location
        if job.location:
            job.location = re.sub(r'\s+', ' ', job.location.strip())
            job.location = job.location[:100]
        
        # Ensure URL is absolute
        if job.url and not job.url.startswith('http'):
            job.url = urljoin(page_url, job.url)
        
        # Set scraped date
        job.scraped_date = datetime.now()
        
        return job
    
    def _is_valid_job(self, job: Job) -> bool:
        """Validate job data quality"""
        
        # Must have at least a title
        if not job.title or len(job.title.strip()) < 3:
            return False
        
        # Filter out obvious non-jobs
        invalid_titles = [
            'cookie', 'privacy', 'terms', 'about', 'contact',
            'home', 'search', 'filter', 'sort', 'page'
        ]
        
        title_lower = job.title.lower()
        if any(invalid in title_lower for invalid in invalid_titles):
            return False
        
        # Title should not be too long (likely extracted wrong)
        if len(job.title) > 200:
            return False
        
        return True