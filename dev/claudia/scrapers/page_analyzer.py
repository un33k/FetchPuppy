"""
Page Analyzer for Universal Scraper
Analyzes page structure and identifies common patterns without AI assistance
"""

import logging
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

from playwright.async_api import Page


class PageAnalyzer:
    """Analyzes page structure using pattern matching and heuristics"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def analyze_page_structure(self, page: Page) -> Dict[str, Any]:
        """Analyze page structure and identify key elements"""
        
        url = page.url
        title = await page.title()
        html = await page.content()
        
        analysis = {
            "url": url,
            "title": title,
            "page_type": self._identify_page_type(html, url, title),
            "forms": await self._find_forms(page),
            "links": await self._analyze_links(page),
            "inputs": await self._find_inputs(page),
            "buttons": await self._find_buttons(page),
            "lists": await self._find_lists(page),
            "navigation": await self._find_navigation(page),
            "content_areas": await self._find_content_areas(page),
            "meta_info": await self._extract_meta_info(page)
        }
        
        return analysis
    
    def _identify_page_type(self, html: str, url: str, title: str) -> str:
        """Identify the type of page based on content and URL patterns"""
        
        html_lower = html.lower()
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Job search page indicators
        if any(keyword in html_lower for keyword in ['job search', 'find jobs', 'search jobs']):
            return "job_search"
        
        # Job listings page indicators
        if any(keyword in html_lower for keyword in ['job listings', 'search results', 'jobs found']):
            return "job_listings"
        
        # Individual job page indicators
        if any(keyword in url_lower for keyword in ['/job/', '/jobs/', '/position/']):
            if any(keyword in html_lower for keyword in ['apply now', 'job description', 'requirements']):
                return "job_detail"
        
        # Company page
        if any(keyword in html_lower for keyword in ['about company', 'company profile', 'our company']):
            return "company_page"
        
        # Home page indicators
        if any(keyword in url_lower for keyword in ['/', '/home', '/index']):
            if len(url_lower.split('/')) <= 4:  # Root or shallow URL
                return "homepage"
        
        return "unknown"
    
    async def _find_forms(self, page: Page) -> List[Dict[str, Any]]:
        """Find and analyze forms on the page"""
        
        forms = []
        form_elements = await page.query_selector_all("form")
        
        for i, form in enumerate(form_elements):
            form_data = {
                "index": i,
                "action": await form.get_attribute("action"),
                "method": await form.get_attribute("method") or "get",
                "id": await form.get_attribute("id"),
                "class": await form.get_attribute("class"),
                "inputs": []
            }
            
            # Find inputs within this form
            inputs = await form.query_selector_all("input, select, textarea")
            for input_elem in inputs:
                input_data = {
                    "type": await input_elem.get_attribute("type"),
                    "name": await input_elem.get_attribute("name"),
                    "id": await input_elem.get_attribute("id"),
                    "placeholder": await input_elem.get_attribute("placeholder"),
                    "value": await input_elem.get_attribute("value"),
                    "required": await input_elem.get_attribute("required") is not None
                }
                form_data["inputs"].append(input_data)
            
            forms.append(form_data)
        
        return forms
    
    async def _analyze_links(self, page: Page) -> Dict[str, Any]:
        """Analyze links on the page"""
        
        links = await page.query_selector_all("a[href]")
        link_data = {
            "total_links": len(links),
            "job_links": [],
            "pagination_links": [],
            "navigation_links": [],
            "external_links": []
        }
        
        current_domain = urlparse(page.url).netloc
        
        for link in links:
            href = await link.get_attribute("href")
            text = (await link.text_content() or "").strip()
            title = await link.get_attribute("title")
            
            if not href:
                continue
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(page.url, href)
            link_domain = urlparse(absolute_url).netloc
            
            link_info = {
                "href": href,
                "text": text,
                "title": title,
                "absolute_url": absolute_url
            }
            
            # Categorize links
            if self._is_job_link(href, text, title):
                link_data["job_links"].append(link_info)
            elif self._is_pagination_link(href, text, title):
                link_data["pagination_links"].append(link_info)
            elif link_domain != current_domain:
                link_data["external_links"].append(link_info)
            else:
                link_data["navigation_links"].append(link_info)
        
        return link_data
    
    def _is_job_link(self, href: str, text: str, title: str) -> bool:
        """Determine if a link is likely a job posting"""
        
        job_indicators = ['job', 'position', 'career', 'opening', 'vacancy']
        
        # Check URL
        href_lower = href.lower()
        if any(indicator in href_lower for indicator in job_indicators):
            return True
        
        # Check link text
        text_lower = text.lower()
        if any(indicator in text_lower for indicator in job_indicators):
            return True
        
        # Check title attribute
        if title:
            title_lower = title.lower()
            if any(indicator in title_lower for indicator in job_indicators):
                return True
        
        return False
    
    def _is_pagination_link(self, href: str, text: str, title: str) -> bool:
        """Determine if a link is pagination"""
        
        pagination_indicators = ['next', 'previous', 'prev', 'page', 'more']
        
        text_lower = text.lower()
        if any(indicator in text_lower for indicator in pagination_indicators):
            return True
        
        # Check for numeric pagination
        if text.strip().isdigit():
            return True
        
        return False
    
    async def _find_inputs(self, page: Page) -> List[Dict[str, Any]]:
        """Find and categorize input elements"""
        
        inputs = []
        input_elements = await page.query_selector_all("input, select, textarea")
        
        for input_elem in input_elements:
            input_data = {
                "tag": await input_elem.evaluate("el => el.tagName.toLowerCase()"),
                "type": await input_elem.get_attribute("type"),
                "name": await input_elem.get_attribute("name"),
                "id": await input_elem.get_attribute("id"),
                "class": await input_elem.get_attribute("class"),
                "placeholder": await input_elem.get_attribute("placeholder"),
                "value": await input_elem.get_attribute("value"),
                "required": await input_elem.get_attribute("required") is not None,
                "category": self._categorize_input(input_elem)
            }
            inputs.append(input_data)
        
        return inputs
    
    def _categorize_input(self, input_elem) -> str:
        """Categorize input based on attributes"""
        # This would need to be implemented with actual element inspection
        # For now, return a placeholder
        return "unknown"
    
    async def _find_buttons(self, page: Page) -> List[Dict[str, Any]]:
        """Find and categorize buttons"""
        
        buttons = []
        button_elements = await page.query_selector_all("button, input[type='submit'], input[type='button']")
        
        for button in button_elements:
            button_data = {
                "tag": await button.evaluate("el => el.tagName.toLowerCase()"),
                "type": await button.get_attribute("type"),
                "text": await button.text_content(),
                "value": await button.get_attribute("value"),
                "id": await button.get_attribute("id"),
                "class": await button.get_attribute("class"),
                "category": self._categorize_button(await button.text_content(), 
                                                  await button.get_attribute("class") or "")
            }
            buttons.append(button_data)
        
        return buttons
    
    def _categorize_button(self, text: str, class_attr: str) -> str:
        """Categorize button based on text and class"""
        
        if not text:
            text = ""
        
        text_lower = text.lower()
        class_lower = class_attr.lower()
        
        if any(keyword in text_lower for keyword in ['search', 'find', 'go']):
            return "search"
        elif any(keyword in text_lower for keyword in ['apply', 'submit']):
            return "submit"
        elif any(keyword in text_lower for keyword in ['next', 'more', 'load']):
            return "pagination"
        elif any(keyword in text_lower for keyword in ['filter', 'sort']):
            return "filter"
        else:
            return "unknown"
    
    async def _find_lists(self, page: Page) -> List[Dict[str, Any]]:
        """Find list structures that might contain jobs"""
        
        lists = []
        list_elements = await page.query_selector_all("ul, ol, div[class*='list'], div[class*='grid']")
        
        for i, list_elem in enumerate(list_elements):
            # Count items in the list
            items = await list_elem.query_selector_all("li, div[class*='item'], div[class*='card']")
            
            if len(items) > 2:  # Only consider lists with multiple items
                list_data = {
                    "index": i,
                    "tag": await list_elem.evaluate("el => el.tagName.toLowerCase()"),
                    "class": await list_elem.get_attribute("class"),
                    "id": await list_elem.get_attribute("id"),
                    "item_count": len(items),
                    "likely_job_list": self._is_likely_job_list(await list_elem.get_attribute("class") or "",
                                                              len(items))
                }
                lists.append(list_data)
        
        return lists
    
    def _is_likely_job_list(self, class_attr: str, item_count: int) -> bool:
        """Determine if a list likely contains job postings"""
        
        job_indicators = ['job', 'position', 'listing', 'result', 'card']
        class_lower = class_attr.lower()
        
        # Check class name for job indicators
        if any(indicator in class_lower for indicator in job_indicators):
            return True
        
        # Lists with many items are more likely to be job lists
        if item_count > 10:
            return True
        
        return False
    
    async def _find_navigation(self, page: Page) -> Dict[str, Any]:
        """Find navigation elements"""
        
        nav_data = {
            "nav_elements": [],
            "breadcrumbs": [],
            "menus": []
        }
        
        # Find navigation elements
        nav_elements = await page.query_selector_all("nav, div[class*='nav'], div[role='navigation']")
        for nav in nav_elements:
            nav_info = {
                "tag": await nav.evaluate("el => el.tagName.toLowerCase()"),
                "class": await nav.get_attribute("class"),
                "id": await nav.get_attribute("id"),
                "role": await nav.get_attribute("role")
            }
            nav_data["nav_elements"].append(nav_info)
        
        # Find breadcrumbs
        breadcrumb_elements = await page.query_selector_all("[class*='breadcrumb'], [aria-label*='breadcrumb']")
        for breadcrumb in breadcrumb_elements:
            breadcrumb_info = {
                "class": await breadcrumb.get_attribute("class"),
                "text": await breadcrumb.text_content()
            }
            nav_data["breadcrumbs"].append(breadcrumb_info)
        
        return nav_data
    
    async def _find_content_areas(self, page: Page) -> Dict[str, Any]:
        """Find main content areas"""
        
        content_areas = {
            "main_content": [],
            "sidebars": [],
            "headers": [],
            "footers": []
        }
        
        # Find main content areas
        main_elements = await page.query_selector_all("main, [role='main'], .main, .content")
        for main in main_elements:
            content_info = {
                "tag": await main.evaluate("el => el.tagName.toLowerCase()"),
                "class": await main.get_attribute("class"),
                "id": await main.get_attribute("id")
            }
            content_areas["main_content"].append(content_info)
        
        # Find sidebars
        sidebar_elements = await page.query_selector_all("[class*='sidebar'], [class*='aside'], aside")
        for sidebar in sidebar_elements:
            sidebar_info = {
                "tag": await sidebar.evaluate("el => el.tagName.toLowerCase()"),
                "class": await sidebar.get_attribute("class")
            }
            content_areas["sidebars"].append(sidebar_info)
        
        return content_areas
    
    async def _extract_meta_info(self, page: Page) -> Dict[str, Any]:
        """Extract meta information from the page"""
        
        meta_info = {
            "charset": await page.query_selector("meta[charset]"),
            "viewport": await page.query_selector("meta[name='viewport']"),
            "description": await page.query_selector("meta[name='description']"),
            "keywords": await page.query_selector("meta[name='keywords']"),
            "robots": await page.query_selector("meta[name='robots']"),
            "canonical": await page.query_selector("link[rel='canonical']")
        }
        
        # Extract actual content from meta tags
        for key, element in meta_info.items():
            if element:
                content = await element.get_attribute("content")
                href = await element.get_attribute("href")
                meta_info[key] = content or href
            else:
                meta_info[key] = None
        
        return meta_info