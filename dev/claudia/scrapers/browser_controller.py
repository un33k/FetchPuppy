"""
Browser Controller for Universal Scraper
Manages Playwright browser instances with stealth configuration and anti-detection measures
"""

import asyncio
import logging
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError


class BrowserController:
    """Manages browser instances with stealth and anti-detection features"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.playwright = None
        self.browser = None
        self.contexts: List[BrowserContext] = []
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def start(self):
        """Start Playwright and browser"""
        self.playwright = await async_playwright().start()
        
        # Browser launch arguments for stealth
        browser_args = [
            '--no-first-run',
            '--disable-blink-features=AutomationControlled',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
        ]
        
        # Launch browser based on configuration
        headless = self.config.scraper_mode == "headless"
        
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=browser_args,
            slow_mo=50 if not headless else 0,  # Slow down for debugging
        )
        
        self.logger.info(f"Browser started in {'headless' if headless else 'headful'} mode")
    
    async def close(self):
        """Close all browser resources"""
        if self.contexts:
            for context in self.contexts:
                await context.close()
            self.contexts.clear()
        
        if self.browser:
            await self.browser.close()
        
        if self.playwright:
            await self.playwright.stop()
        
        self.logger.info("Browser resources closed")
    
    async def create_context(self, **kwargs) -> BrowserContext:
        """Create a new browser context with stealth settings"""
        if not self.browser:
            await self.start()
        
        # Default context options for stealth
        context_options = {
            'user_agent': self.config.user_agent,
            'viewport': {'width': 1366, 'height': 768},
            'extra_http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            'java_script_enabled': True,
            'ignore_https_errors': True,
        }
        
        # Override with user-provided options
        context_options.update(kwargs)
        
        context = await self.browser.new_context(**context_options)
        
        # Add stealth scripts
        await self._add_stealth_scripts(context)
        
        self.contexts.append(context)
        return context
    
    async def _add_stealth_scripts(self, context: BrowserContext):
        """Add JavaScript to make browser appear more human-like"""
        stealth_scripts = [
            # Remove webdriver property
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            """,
            
            # Mock plugins
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            """,
            
            # Mock languages
            """
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            """,
            
            # Override permissions
            """
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            """,
        ]
        
        for script in stealth_scripts:
            await context.add_init_script(script)
    
    @asynccontextmanager
    async def get_page(self, url: Optional[str] = None, **context_kwargs):
        """Get a new page with automatic cleanup"""
        context = await self.create_context(**context_kwargs)
        page = await context.new_page()
        
        try:
            # Configure page with human-like behavior
            await self._configure_page(page)
            
            if url:
                await self.navigate_to(page, url)
            
            yield page
            
        finally:
            await page.close()
            await context.close()
            if context in self.contexts:
                self.contexts.remove(context)
    
    async def _configure_page(self, page: Page):
        """Configure page with human-like settings"""
        # Set random viewport size
        viewports = [
            {'width': 1366, 'height': 768},
            {'width': 1920, 'height': 1080},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864},
        ]
        viewport = random.choice(viewports)
        await page.set_viewport_size(viewport)
        
        # Set timeout
        page.set_default_timeout(30000)
        
        # Block unnecessary resources for faster loading
        await page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", 
                        lambda route: route.abort())
    
    async def navigate_to(self, page: Page, url: str, wait_for: str = 'networkidle') -> bool:
        """Navigate to URL with human-like timing"""
        try:
            # Add random delay before navigation
            await self._human_delay()
            
            self.logger.info(f"Navigating to: {url}")
            
            # Navigate to URL
            response = await page.goto(url, wait_until=wait_for, timeout=30000)
            
            if response and response.status >= 400:
                self.logger.warning(f"HTTP {response.status} for {url}")
                return False
            
            # Add delay after navigation
            await self._human_delay(min_delay=1.0, max_delay=3.0)
            
            return True
            
        except PlaywrightTimeoutError:
            self.logger.error(f"Timeout navigating to {url}")
            return False
        except Exception as e:
            self.logger.error(f"Error navigating to {url}: {e}")
            return False
    
    async def click_element(self, page: Page, selector: str, **kwargs) -> bool:
        """Click element with human-like behavior"""
        try:
            # Wait for element to be visible
            await page.wait_for_selector(selector, state='visible', timeout=10000)
            
            # Add random delay before clicking
            await self._human_delay(0.5, 2.0)
            
            # Hover before clicking (more human-like)
            await page.hover(selector)
            await self._human_delay(0.2, 0.8)
            
            # Click the element
            await page.click(selector, **kwargs)
            
            # Add delay after clicking
            await self._human_delay(0.5, 1.5)
            
            self.logger.debug(f"Clicked element: {selector}")
            return True
            
        except PlaywrightTimeoutError:
            self.logger.warning(f"Timeout waiting for element: {selector}")
            return False
        except Exception as e:
            self.logger.error(f"Error clicking element {selector}: {e}")
            return False
    
    async def type_text(self, page: Page, selector: str, text: str, clear: bool = True) -> bool:
        """Type text with human-like timing"""
        try:
            # Wait for element
            await page.wait_for_selector(selector, state='visible', timeout=10000)
            
            # Focus on element
            await page.focus(selector)
            await self._human_delay(0.3, 0.8)
            
            # Clear existing text if requested
            if clear:
                await page.fill(selector, "")
                await self._human_delay(0.2, 0.5)
            
            # Type text with human-like speed
            for char in text:
                await page.type(selector, char, delay=random.uniform(50, 150))
                if random.random() < 0.1:  # 10% chance of longer pause
                    await self._human_delay(0.1, 0.3)
            
            self.logger.debug(f"Typed text in {selector}: {text[:20]}...")
            return True
            
        except PlaywrightTimeoutError:
            self.logger.warning(f"Timeout waiting for element: {selector}")
            return False
        except Exception as e:
            self.logger.error(f"Error typing in element {selector}: {e}")
            return False
    
    async def wait_for_element(self, page: Page, selector: str, timeout: int = 10000) -> bool:
        """Wait for element to appear"""
        try:
            await page.wait_for_selector(selector, state='visible', timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False
    
    async def get_page_content(self, page: Page) -> str:
        """Get full page HTML content"""
        return await page.content()
    
    async def take_screenshot(self, page: Page, path: Optional[str] = None) -> bytes:
        """Take page screenshot"""
        if path:
            await page.screenshot(path=path, full_page=True)
            return Path(path).read_bytes()
        else:
            return await page.screenshot(full_page=True)
    
    async def scroll_page(self, page: Page, direction: str = 'down', amount: int = 3) -> None:
        """Scroll page with human-like behavior"""
        scroll_amounts = {
            'down': amount * 300,
            'up': -amount * 300,
        }
        
        scroll_distance = scroll_amounts.get(direction, 900)
        
        # Scroll in smaller chunks for more human-like behavior
        chunks = 5
        chunk_size = scroll_distance // chunks
        
        for _ in range(chunks):
            await page.evaluate(f"window.scrollBy(0, {chunk_size})")
            await self._human_delay(0.2, 0.6)
    
    async def wait_for_page_load(self, page: Page, timeout: int = 30000) -> bool:
        """Wait for page to fully load"""
        try:
            await page.wait_for_load_state('networkidle', timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            self.logger.warning("Timeout waiting for page load")
            return False
    
    async def _human_delay(self, min_delay: float = None, max_delay: float = None) -> None:
        """Add human-like random delay"""
        if min_delay is None:
            min_delay = self.config.scraper_delay * 0.5
        if max_delay is None:
            max_delay = self.config.scraper_delay * 1.5
        
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def extract_elements(self, page: Page, selector: str) -> List[Dict[str, Any]]:
        """Extract multiple elements with their properties"""
        try:
            elements = await page.query_selector_all(selector)
            results = []
            
            for element in elements:
                element_data = {
                    'text': await element.text_content(),
                    'html': await element.inner_html(),
                    'href': await element.get_attribute('href'),
                    'class': await element.get_attribute('class'),
                    'id': await element.get_attribute('id'),
                }
                results.append(element_data)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error extracting elements {selector}: {e}")
            return []
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get browser debug information"""
        return {
            'browser_active': self.browser is not None,
            'contexts_count': len(self.contexts),
            'scraper_mode': self.config.scraper_mode,
            'user_agent': self.config.user_agent[:50] + '...',
        }