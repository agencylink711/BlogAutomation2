#!/usr/bin/env python3
"""
Base browser automation class using Playwright.
Provides common functionality for browser-based automation clients.
"""
import os
import asyncio
import time
from pathlib import Path
from typing import List, Optional, Union
from playwright.async_api import async_playwright, Browser, Page
from rich.console import Console

console = Console()


class BrowserBase:
    """Base class for browser automation clients."""
    
    def __init__(self, 
                 user_data_dir: Union[str, Path],
                 screenshot_dir: Union[str, Path],
                 base_url: str):
        """
        Initialize the browser automation base.
        
        Args:
            user_data_dir: Directory for persistent browser data
            screenshot_dir: Directory for screenshots
            base_url: Base URL for the service
        """
        self.playwright = None
        self.browser = None
        self.page = None
        self.base_url = base_url
        
        # Convert paths to Path objects
        self.user_data_dir = Path(user_data_dir)
        self.screenshot_dir = Path(screenshot_dir)
        
        # Create directories if they don't exist
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Flag to track if we connected to existing browser
        self.using_existing_browser = False
    
    def _is_chrome_available(self) -> bool:
        """Check if Chrome is available on the system."""
        try:
            if os.path.exists("/Applications/Google Chrome.app"):
                return True
            return False
        except:
            return False
    
    async def start(self) -> bool:
        """Start the browser with persistent context."""
        console.print("[yellow]Starting browser with persistent context...[/yellow]")
        
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with persistent context
            self.browser = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=False,
                channel="chrome" if self._is_chrome_available() else None,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            
            # Get or create page
            if len(self.browser.pages) > 0:
                self.page = self.browser.pages[0]
                console.print("[green]Using existing browser page[/green]")
                self.using_existing_browser = True
            else:
                self.page = await self.browser.new_page()
                console.print("[yellow]Created new browser page[/yellow]")
            
            # Add anti-detection scripts
            await self._add_anti_detection_scripts()
            
            return True
            
        except Exception as e:
            console.print(f"[bold red]Failed to start browser: {str(e)}[/bold red]")
            await self.close()
            return False
    
    async def _add_anti_detection_scripts(self):
        """Add scripts to avoid bot detection."""
        if not self.page:
            return
            
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
    
    async def take_screenshot(self, name: str):
        """Take a screenshot and save it with the given name."""
        try:
            screenshot_path = self.screenshot_dir / f"{name}.png"
            await self.page.screenshot(path=str(screenshot_path))
            console.print(f"[green]Saved screenshot to {screenshot_path}[/green]")
        except Exception as e:
            console.print(f"[yellow]Could not save screenshot: {str(e)}[/yellow]")
    
    async def refresh_page(self) -> bool:
        """Refresh the current page and wait for it to load."""
        try:
            console.print("[yellow]Refreshing page...[/yellow]")
            
            current_url = self.page.url
            await self.page.reload()
            await self.page.wait_for_load_state("networkidle")
            
            # Return to original URL if needed
            if current_url and current_url != self.page.url:
                await self.page.goto(current_url)
                await self.page.wait_for_load_state("networkidle")
            
            await self.page.wait_for_timeout(2000)
            console.print("[green]Page refreshed successfully![/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Error refreshing page: {e}[/red]")
            return False
    
    async def wait_for_navigation_or_element(self, 
                                           timeout: int = 60000,
                                           selectors: Optional[List[str]] = None,
                                           url_patterns: Optional[List[str]] = None) -> bool:
        """
        Wait for either navigation to complete or element to appear.
        
        Args:
            timeout: Maximum time to wait in milliseconds
            selectors: List of selectors to wait for
            url_patterns: List of URL patterns to match
        
        Returns:
            bool: True if navigation/element was found, False if timed out
        """
        start_time = time.time()
        check_interval = 3  # seconds
        
        while (time.time() - start_time) * 1000 < timeout:
            if url_patterns:
                current_url = self.page.url
                if any(pattern in current_url for pattern in url_patterns):
                    return True
            
            if selectors:
                for selector in selectors:
                    try:
                        element = await self.page.query_selector(selector)
                        if element:
                            return True
                    except:
                        pass
            
            # Progress update every 30 seconds
            elapsed = int(time.time() - start_time)
            if elapsed % 30 == 0 and elapsed > 0:
                console.print(f"[yellow]Still waiting... ({elapsed} seconds elapsed)[/yellow]")
                await self.take_screenshot(f"waiting_{elapsed}sec")
            
            await asyncio.sleep(check_interval)
        
        return False
    
    async def close(self):
        """Close the browser and clean up resources."""
        try:
            if self.browser:
                try:
                    await self.browser.close()
                except:
                    pass
            
            if self.playwright:
                try:
                    await self.playwright.stop()
                except:
                    pass
                    
            console.print("[yellow]Browser closed.[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Error during cleanup: {str(e)}[/yellow]")