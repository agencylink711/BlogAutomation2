#!/usr/bin/env python3
"""
ZeroGPT client for AI content detection using browser automation.
"""
import asyncio
import time
from pathlib import Path
from typing import Optional, Tuple

from common.browser_base import BrowserBase
from common.config import config
from rich.console import Console

console = Console()


class ZeroGPTClient(BrowserBase):
    """Client for interacting with ZeroGPT via browser automation."""
    
    def __init__(self):
        """Initialize the ZeroGPT client."""
        super().__init__(
            user_data_dir=config.ai_detector.user_data_dir,
            screenshot_dir=config.browser.screenshot_dir,
            base_url=config.ai_detector.zerogpt_url
        )
        
    async def start(self) -> bool:
        """Start browser and navigate to ZeroGPT."""
        if not await super().start():
            return False
            
        try:
            console.print(f"[yellow]Navigating to ZeroGPT: {self.base_url}...[/yellow]")
            await self.page.goto(self.base_url, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            
            await self.take_screenshot("zerogpt_loaded")
            console.print("[green]Successfully connected to ZeroGPT[/green]")
            return True
            
        except Exception as e:
            console.print(f"[bold red]Failed to start ZeroGPT client: {str(e)}[/bold red]")
            await self.close()
            return False
    
    async def check_text(self, text: str, max_retries: int = 3) -> Tuple[bool, float]:
        """
        Check text for AI detection using ZeroGPT.
        
        Args:
            text: The text to check
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tuple[bool, float]: (is_human, ai_percentage)
            - is_human: True if content appears human-written
            - ai_percentage: Estimated AI probability percentage
        """
        try:
            # Find and clear the input field
            input_selector = "textarea"
            input_field = await self.page.query_selector(input_selector)
            
            if not input_field:
                console.print("[red]Could not find input field[/red]")
                return False, 100.0
            
            # Clear any existing text
            await input_field.fill("")
            await asyncio.sleep(1)
            
            # Input the text to check
            await input_field.fill(text)
            await self.take_screenshot("text_entered")
            
            # Find and click the check button
            check_button = await self.page.query_selector('button:has-text("Check")')
            if not check_button:
                console.print("[red]Could not find check button[/red]")
                return False, 100.0
                
            await check_button.click()
            console.print("[yellow]Submitted text for analysis...[/yellow]")
            
            # Wait for results with retry logic
            for attempt in range(max_retries):
                try:
                    # Wait for either success or error indicators
                    result = await self._wait_for_results()
                    if result is not None:
                        is_human, percentage = result
                        console.print(f"[green]Analysis complete: {percentage:.1f}% AI probability[/green]")
                        return is_human, percentage
                    
                    if attempt < max_retries - 1:
                        console.print(f"[yellow]Retry attempt {attempt + 1}/{max_retries}[/yellow]")
                        await asyncio.sleep(config.ai_detector.retry_delay)
                        await check_button.click()
                    
                except Exception as e:
                    console.print(f"[yellow]Error on attempt {attempt + 1}: {str(e)}[/yellow]")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(config.ai_detector.retry_delay)
            
            console.print("[red]Failed to get results after all retries[/red]")
            return False, 100.0
            
        except Exception as e:
            console.print(f"[bold red]Error checking text: {str(e)}[/bold red]")
            return False, 100.0
    
    async def _wait_for_results(self, timeout: int = 30) -> Optional[Tuple[bool, float]]:
        """
        Wait for and extract analysis results.
        
        Returns:
            Optional[Tuple[bool, float]]: (is_human, ai_percentage) or None if failed
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check for result text
                result_text = await self.page.evaluate('''
                    () => {
                        const resultElement = document.querySelector('.result-text, .analysis-result');
                        return resultElement ? resultElement.innerText : '';
                    }
                ''')
                
                if result_text:
                    # Extract percentage from result text
                    import re
                    percentage_match = re.search(r'(\d+\.?\d*)%', result_text)
                    if percentage_match:
                        percentage = float(percentage_match.group(1))
                        is_human = percentage <= config.ai_detector.max_ai_percentage
                        return is_human, percentage
                
                # Check for error messages
                error_text = await self.page.evaluate('''
                    () => {
                        const errorElement = document.querySelector('.error-message, .alert-error');
                        return errorElement ? errorElement.innerText : '';
                    }
                ''')
                
                if error_text:
                    console.print(f"[red]Error from ZeroGPT: {error_text}[/red]")
                    return None
                
                await asyncio.sleep(1)
                
            except Exception as e:
                console.print(f"[yellow]Error while waiting for results: {str(e)}[/yellow]")
                return None
        
        console.print("[red]Timed out waiting for results[/red]")
        return None