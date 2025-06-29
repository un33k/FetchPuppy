"""
AI Navigator for Universal Scraper
Uses Claude API to analyze pages and provide navigation instructions
"""

import base64
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

import anthropic
from playwright.async_api import Page


@dataclass
class NavigationInstruction:
    """Represents an instruction for browser automation"""
    action: str  # 'click', 'type', 'navigate', 'scroll', 'wait'
    selector: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None
    wait_for: Optional[str] = None
    description: str = ""


@dataclass
class PageAnalysis:
    """Results of AI page analysis"""
    page_type: str  # 'job_search', 'job_listings', 'job_detail', 'pagination', 'unknown'
    elements_found: Dict[str, List[str]]  # element_type -> list of selectors
    navigation_instructions: List[NavigationInstruction]
    data_extraction_hints: Dict[str, str]  # field_name -> selector_hint
    confidence: float  # 0.0 to 1.0
    reasoning: str


class AINavigator:
    """AI-powered page analysis and navigation instruction generator"""
    
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
                self.logger.info(f"Local LLM client initialized: {config.local_llm_base_url}")
            except Exception as e:
                self.logger.error(f"Failed to initialize local LLM: {e}")
        
        # 3. OpenAI client (fallback)
        elif config.openai_api_key:
            import openai
            self.openai_client = openai.OpenAI(api_key=config.openai_api_key)
    
    async def analyze_page(self, page: Page, task: str, screenshot: bool = True) -> PageAnalysis:
        """Analyze page structure and provide navigation instructions"""
        try:
            # Get page content
            html_content = await page.content()
            page_url = page.url
            
            # Take screenshot if requested and AI supports it
            screenshot_data = None
            if screenshot and self.claude_client:
                screenshot_bytes = await page.screenshot(full_page=False)  # Viewport only for faster processing
                screenshot_data = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Analyze with AI (in order of preference)
            if self.claude_client:
                analysis = await self._analyze_with_claude(html_content, page_url, task, screenshot_data)
            elif self.local_llm_client:
                analysis = await self._analyze_with_local_llm(html_content, page_url, task)
            elif self.openai_client:
                analysis = await self._analyze_with_openai(html_content, page_url, task)
            else:
                # Fallback to basic pattern matching
                analysis = self._analyze_with_patterns(html_content, page_url, task)
            
            self.logger.info(f"Page analysis complete: {analysis.page_type} (confidence: {analysis.confidence:.2f})")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing page: {e}")
            return self._create_fallback_analysis(task)
    
    async def _analyze_with_claude(self, html: str, url: str, task: str, screenshot: Optional[str] = None) -> PageAnalysis:
        """Analyze page using Claude API"""
        
        # Truncate HTML for API limits
        html_excerpt = self._truncate_html(html, max_length=15000)
        
        prompt = f"""Analyze this job website page and provide navigation instructions.

URL: {url}
Task: {task}

Page HTML (excerpt):
{html_excerpt}

Please analyze this page and return a JSON response with the following structure:
{{
    "page_type": "job_search|job_listings|job_detail|pagination|unknown",
    "elements_found": {{
        "search_forms": ["selector1", "selector2"],
        "job_cards": ["selector1", "selector2"],
        "pagination": ["selector1", "selector2"],
        "job_links": ["selector1", "selector2"]
    }},
    "navigation_instructions": [
        {{
            "action": "click|type|navigate|scroll|wait",
            "selector": "css_selector_or_null",
            "text": "text_to_type_or_null",
            "url": "url_to_navigate_or_null",
            "wait_for": "selector_to_wait_for_or_null",
            "description": "Human readable description"
        }}
    ],
    "data_extraction_hints": {{
        "job_title": "selector_hint",
        "company": "selector_hint",
        "location": "selector_hint",
        "salary": "selector_hint"
    }},
    "confidence": 0.0-1.0,
    "reasoning": "Explanation of analysis"
}}

Focus on finding:
1. Search forms and input fields
2. Job listing cards or items
3. Pagination controls
4. Navigation elements
5. Data fields for extraction

Provide practical CSS selectors that can be used with Playwright."""

        try:
            # Prepare messages for Claude
            messages = [{"role": "user", "content": prompt}]
            
            # Add screenshot if available
            if screenshot:
                messages[0]["content"] = [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": screenshot
                        }
                    }
                ]
            
            response = self.claude_client.messages.create(
                model=self.config.claude_model,
                max_tokens=4000,
                messages=messages
            )
            
            # Parse JSON response
            response_text = response.content[0].text
            analysis_data = json.loads(response_text)
            
            return self._parse_analysis_data(analysis_data)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Claude JSON response: {e}")
            return self._create_fallback_analysis(task)
        except Exception as e:
            self.logger.error(f"Claude API error: {e}")
            return self._create_fallback_analysis(task)
    
    async def _analyze_with_local_llm(self, html: str, url: str, task: str) -> PageAnalysis:
        """Analyze page using local LLM via LM Studio"""
        
        # Truncate HTML for local model (smaller context)
        html_excerpt = self._truncate_html(html, max_length=8000)
        
        # Simpler prompt optimized for local models
        prompt = f"""Analyze this job website page. Return only JSON.

URL: {url}
Task: {task}

HTML:
{html_excerpt}

Return JSON with this exact structure:
{{
    "page_type": "job_search|job_listings|job_detail|unknown",
    "elements_found": {{
        "search_forms": ["selector1", "selector2"],
        "job_cards": ["selector1", "selector2"],
        "pagination": ["selector1"],
        "job_links": ["selector1"]
    }},
    "navigation_instructions": [
        {{
            "action": "type",
            "selector": "input[name='q']",
            "text": "{task.split(' ', 1)[1] if ' ' in task else 'jobs'}",
            "description": "Enter search term"
        }}
    ],
    "data_extraction_hints": {{
        "job_title": ".job-title",
        "company": ".company",
        "location": ".location",
        "salary": ".salary"
    }},
    "confidence": 0.7,
    "reasoning": "Local LLM analysis"
}}

Return only the JSON, no other text."""

        try:
            response = self.local_llm_client.chat.completions.create(
                model=self.local_llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            analysis_data = json.loads(response_text)
            return self._parse_analysis_data(analysis_data)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse local LLM JSON response: {e}")
            return self._create_fallback_analysis(task)
        except Exception as e:
            self.logger.error(f"Local LLM API error: {e}")
            return self._create_fallback_analysis(task)
    
    async def _analyze_with_openai(self, html: str, url: str, task: str) -> PageAnalysis:
        """Analyze page using OpenAI API (fallback)"""
        
        html_excerpt = self._truncate_html(html, max_length=10000)
        
        prompt = f"""Analyze this job website page and provide navigation instructions for the task: {task}

URL: {url}
HTML excerpt: {html_excerpt}

Return a JSON response with page analysis including:
- page_type (job_search, job_listings, job_detail, etc.)
- elements_found (search forms, job cards, pagination)
- navigation_instructions (actions to take)
- data_extraction_hints (selectors for job data)
- confidence (0.0-1.0)
- reasoning

Focus on practical CSS selectors for Playwright automation."""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content
            
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                analysis_data = json.loads(json_text)
                return self._parse_analysis_data(analysis_data)
            else:
                raise ValueError("No JSON found in OpenAI response")
                
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            return self._create_fallback_analysis(task)
    
    def _analyze_with_patterns(self, html: str, url: str, task: str) -> PageAnalysis:
        """Fallback analysis using pattern matching"""
        
        # Basic pattern matching for common job site elements
        elements_found = {
            "search_forms": [],
            "job_cards": [],
            "pagination": [],
            "job_links": []
        }
        
        # Look for search forms
        if 'search' in html.lower() or 'input' in html.lower():
            elements_found["search_forms"] = ['form', 'input[type="search"]', '.search-form']
        
        # Look for job listings
        if 'job' in html.lower():
            elements_found["job_cards"] = ['.job', '.job-card', '.job-item', '[data-job]']
            elements_found["job_links"] = ['a[href*="job"]', '.job-link', '.job-title a']
        
        # Look for pagination
        if 'next' in html.lower() or 'page' in html.lower():
            elements_found["pagination"] = ['.pagination', '.next', '[aria-label*="next"]']
        
        # Determine page type
        page_type = "unknown"
        if "search" in task.lower():
            page_type = "job_search"
        elif any(elements_found["job_cards"]):
            page_type = "job_listings"
        
        # Create basic navigation instructions
        instructions = []
        if task.lower().startswith("search"):
            instructions.append(NavigationInstruction(
                action="type",
                selector="input[type='search'], input[name*='search'], input[placeholder*='search']",
                text=task.split(" ", 1)[1] if " " in task else "jobs",
                description="Enter search term"
            ))
            instructions.append(NavigationInstruction(
                action="click",
                selector="button[type='submit'], .search-button, input[type='submit']",
                description="Submit search"
            ))
        
        return PageAnalysis(
            page_type=page_type,
            elements_found=elements_found,
            navigation_instructions=instructions,
            data_extraction_hints={
                "job_title": ".job-title, h2, h3",
                "company": ".company, .employer",
                "location": ".location, .job-location",
                "salary": ".salary, .pay, .wage"
            },
            confidence=0.3,  # Low confidence for pattern matching
            reasoning="Pattern-based analysis (fallback method)"
        )
    
    def _parse_analysis_data(self, data: Dict[str, Any]) -> PageAnalysis:
        """Parse analysis data into PageAnalysis object"""
        
        # Parse navigation instructions
        instructions = []
        for inst_data in data.get("navigation_instructions", []):
            instructions.append(NavigationInstruction(
                action=inst_data.get("action", ""),
                selector=inst_data.get("selector"),
                text=inst_data.get("text"),
                url=inst_data.get("url"),
                wait_for=inst_data.get("wait_for"),
                description=inst_data.get("description", "")
            ))
        
        return PageAnalysis(
            page_type=data.get("page_type", "unknown"),
            elements_found=data.get("elements_found", {}),
            navigation_instructions=instructions,
            data_extraction_hints=data.get("data_extraction_hints", {}),
            confidence=float(data.get("confidence", 0.5)),
            reasoning=data.get("reasoning", "AI analysis completed")
        )
    
    def _create_fallback_analysis(self, task: str) -> PageAnalysis:
        """Create a basic fallback analysis"""
        return PageAnalysis(
            page_type="unknown",
            elements_found={},
            navigation_instructions=[],
            data_extraction_hints={},
            confidence=0.1,
            reasoning="Fallback analysis due to AI failure"
        )
    
    def _truncate_html(self, html: str, max_length: int = 15000) -> str:
        """Truncate HTML to fit API limits while preserving structure"""
        if len(html) <= max_length:
            return html
        
        # Try to find a good break point
        truncated = html[:max_length]
        
        # Find last complete tag
        last_tag_end = truncated.rfind('>')
        if last_tag_end > max_length * 0.8:  # If we're close to the limit
            truncated = truncated[:last_tag_end + 1]
        
        return truncated + "\n<!-- HTML truncated for API limits -->"
    
    async def get_job_search_strategy(self, site_url: str, search_query: str) -> List[NavigationInstruction]:
        """Get AI-powered strategy for searching jobs on a specific site"""
        
        prompt = f"""You are an expert at web automation. Provide a step-by-step strategy to search for jobs on this website.

Website: {site_url}
Search Query: {search_query}

Provide a JSON array of navigation instructions to:
1. Navigate to the job search page
2. Find and fill search forms
3. Execute the search
4. Handle any additional filters or options

Each instruction should have:
- action: "navigate", "click", "type", "wait", "scroll"
- selector: CSS selector (if applicable)
- text: text to type (if applicable)
- url: URL to navigate to (if applicable)
- description: human-readable description

Example format:
[
    {{
        "action": "navigate",
        "url": "{site_url}",
        "description": "Go to the website"
    }},
    {{
        "action": "click",
        "selector": ".jobs-link",
        "description": "Click on jobs section"
    }}
]"""

        try:
            if self.claude_client:
                response = self.claude_client.messages.create(
                    model=self.config.claude_model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
            else:
                return []  # No AI available
            
            # Parse JSON response
            instructions_data = json.loads(response_text)
            
            instructions = []
            for inst_data in instructions_data:
                instructions.append(NavigationInstruction(
                    action=inst_data.get("action", ""),
                    selector=inst_data.get("selector"),
                    text=inst_data.get("text"),
                    url=inst_data.get("url"),
                    description=inst_data.get("description", "")
                ))
            
            return instructions
            
        except Exception as e:
            self.logger.error(f"Error getting job search strategy: {e}")
            return []