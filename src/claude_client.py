#!/usr/bin/env python3
"""
Claude.ai client for browser automation using Playwright.
Uses persistent browser context to maintain login between sessions.
"""
import os
import asyncio
import time
import json
import subprocess
import re
from pathlib import Path
from playwright.async_api import async_playwright
from rich.console import Console

console = Console()

class ClaudeClient:
    """Client for interacting with Claude.ai via browser automation."""
    
    def __init__(self):
        """Initialize the Claude client."""
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        # Specific project URL for Claude's web interface
        self.claude_url = "https://claude.ai/project/434990a3-f303-4f35-85cd-490c991139d4"
        # Path for storing screenshots
        self.screenshot_dir = Path("screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        # Path for storing persistent session data
        self.user_data_dir = Path("browser_data")
        self.user_data_dir.mkdir(exist_ok=True)
        # Flag to track if we connected to existing browser
        self.using_existing_browser = False
        
    async def start(self):
        """Start the browser and navigate to Claude using persistent context."""
        console.print("[yellow]Starting browser with persistent context to maintain login...[/yellow]")
        
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with persistent context to maintain login between sessions
            self.browser = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=False,
                channel="chrome" if self._is_chrome_available() else None,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled"  # Hide automation flags
                ]
            )
            
            # Create page from the persistent context
            if len(self.browser.pages) > 0:
                self.page = self.browser.pages[0]
                console.print("[green]Using existing browser page[/green]")
            else:
                self.page = await self.browser.new_page()
                console.print("[yellow]Created new browser page[/yellow]")
            
            # Set JavaScript flag to appear as normal browser
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });
            """)
            
            # Navigate directly to the project URL
            console.print(f"[yellow]Navigating to project URL: {self.claude_url}...[/yellow]")
            await self.page.goto(self.claude_url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait a moment for the page to load
            await asyncio.sleep(5)
            
            # Take a screenshot
            await self.take_screenshot("project_loaded")
            
            # Check if we're on the project page
            current_url = self.page.url
            console.print(f"[yellow]Current URL after navigation: {current_url}[/yellow]")
            
            if "/project/" in current_url:
                console.print("[green]Successfully navigated to Claude project![/green]")
            else:
                console.print("[yellow]Not on project page. Will check if login is needed.[/yellow]")
                # Handle CAPTCHA if needed
                await self._handle_security_verification()
                # Handle login if needed
                await self._handle_login_if_needed()
                # Try navigating to project again if needed
                if "/project/" not in self.page.url:
                    console.print("[yellow]Trying to navigate to project URL again...[/yellow]")
                    await self.page.goto(self.claude_url, wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(5)
            
            console.print("[green]Successfully connected to Claude[/green]")
            
        except Exception as e:
            console.print(f"[bold red]Failed to start browser: {str(e)}[/bold red]")
            await self.close()
            raise
    
    def _is_chrome_available(self):
        """Check if Chrome is available on the system."""
        try:
            if os.path.exists("/Applications/Google Chrome.app"):
                return True
            return False
        except:
            return False
    
    async def _handle_security_verification(self):
        """Handle security verification challenges like CAPTCHAs."""
        # Take a screenshot to see what's on screen
        await self.take_screenshot("security_check")
        
        # Check for text indicating security verification
        security_texts = [
            "verify you are human", 
            "security verification",
            "complete the action below", 
            "captcha", 
            "security check",
            "cloudflare"
        ]
        
        page_text = await self.page.evaluate('() => document.body.innerText.toLowerCase()')
        has_verification = any(text in page_text.lower() for text in security_texts)
        
        if has_verification:
            console.print("[bold red]Security verification (CAPTCHA) detected![/bold red]")
            console.print("[yellow]Please complete the security verification in the browser window[/yellow]")
            console.print("[yellow]The automation will wait for you to solve it...[/yellow]")
            
            # Wait for the user to solve the CAPTCHA manually
            # Look for longer timeout since CAPTCHAs can be challenging
            await self._wait_for_navigation_or_element(
                timeout=180000,  # 3 minutes
                selectors=["textarea", '.chat-input', '[role="textbox"]'],
                url_patterns=["/chat", "/chats", "/project"]
            )
            
            console.print("[green]Security verification appears to be completed. Continuing...[/green]")
            await self.take_screenshot("after_verification")
            await asyncio.sleep(5)  # Give a moment for everything to load after verification
    
    async def _wait_for_navigation_or_element(self, timeout=60000, selectors=None, url_patterns=None):
        """Wait for either an element to appear or navigation to complete."""
        start_time = time.time()
        check_interval = 3  # seconds
        
        while (time.time() - start_time) * 1000 < timeout:
            # Check URL
            if url_patterns:
                current_url = self.page.url
                if any(pattern in current_url for pattern in url_patterns):
                    return True
            
            # Check for selectors
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
                console.print(f"[yellow]Still waiting for verification ({elapsed} seconds elapsed)...[/yellow]")
                await self.take_screenshot(f"waiting_{elapsed}sec")
            
            await asyncio.sleep(check_interval)
        
        return False
        
    async def take_screenshot(self, name):
        """Take a screenshot and save it with a given name."""
        try:
            screenshot_path = self.screenshot_dir / f"{name}.png"
            await self.page.screenshot(path=str(screenshot_path))
            console.print(f"[green]Saved screenshot to {screenshot_path}[/green]")
        except Exception as e:
            console.print(f"[yellow]Could not save screenshot: {str(e)}[/yellow]")
    
    async def _handle_login_if_needed(self):
        """Check if login is needed and handle it."""
        # Check current URL
        url = self.page.url
        console.print(f"[yellow]Current URL: {url}[/yellow]")
        
        # Take screenshot for debugging
        await self.take_screenshot("login_check")
        
        # Check for login text indicators
        login_texts = ["log in", "sign in", "continue with", "log into"]
        page_text = await self.page.evaluate('() => document.body.innerText.toLowerCase()')
        
        needs_login = ("/chats" not in url and "/project/" not in url) or any(text in page_text.lower() for text in login_texts)
        
        if needs_login:
            console.print("[yellow]Login appears to be required[/yellow]")
            
            # Try to click continue/login button
            try:
                # Check for login options
                login_options = [
                    "button:has-text('Continue')",
                    "button:has-text('Sign in')",
                    "button:has-text('Log in')",
                    "button:has-text('Continue with Google')",
                    "a:has-text('Sign in')",
                    "a:has-text('Log in')"
                ]
                
                for selector in login_options:
                    try:
                        button = await self.page.query_selector(selector)
                        if button:
                            console.print(f"[green]Found login button: {selector}[/green]")
                            await button.click()
                            console.print("[yellow]Clicked login button[/yellow]")
                            await asyncio.sleep(3)  # Give time for click to register
                            break
                    except:
                        continue
                        
            except Exception as e:
                console.print(f"[yellow]Could not click login button: {str(e)}[/yellow]")
            
            # Wait for manual login
            console.print("[bold red]Please complete the login process in the browser window[/bold red]")
            console.print("[yellow]Waiting up to 2 minutes for login to complete...[/yellow]")
            
            # Updated selectors that detect successful login
            login_successful_selectors = [
                "textarea", 
                '.chat-input', 
                '[role="textbox"]',
                '.ProseMirror[contenteditable="true"]',
                'div[contenteditable="true"]',
                '[data-slate-editor="true"]'
            ]
            
            # Wait for redirect to chat page, checking every 5 seconds
            login_successful = await self._wait_for_navigation_or_element(
                timeout=120000,  # 2 minutes
                selectors=login_successful_selectors,
                url_patterns=["/chat", "/chats", "/project"]
            )
            
            if login_successful:
                console.print("[green]Login successful![/green]")
                # Take additional screenshot to validate the successful login state
                await self.take_screenshot("login_successful")
                # Wait a bit longer for the UI to fully load
                await asyncio.sleep(5)
                
                # After successful login, navigate directly to the project URL
                console.print(f"[yellow]Navigating to project URL after login: {self.claude_url}[/yellow]")
                await self.page.goto(self.claude_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(5)  # Wait for project page to load
                await self.take_screenshot("project_after_login")
            else:
                console.print("[bold red]Login may have failed. Taking screenshot for debugging.[/bold red]")
                await self.take_screenshot("login_failed")
        else:
            console.print("[green]Already logged in![/green]")
    
    async def check_login_needed(self):
        """Check if login is needed based on the current page."""
        if not self.page:
            return True
            
        url = self.page.url
        console.print(f"[yellow]Checking if login needed. Current URL: {url}[/yellow]")
        
        # If we're already at a project or chat page, no login needed
        if "/project/" in url or "/chat" in url:
            console.print("[green]Already logged in![/green]")
            return False
            
        # Check for login indicators in page text
        try:
            login_texts = ["log in", "sign in", "continue with", "log into"]
            page_text = await self.page.evaluate('() => document.body.innerText.toLowerCase()')
            
            if any(text in page_text.lower() for text in login_texts):
                console.print("[yellow]Login appears to be required based on page text[/yellow]")
                return True
        except:
            # If we can't evaluate page text, assume login is needed
            return True
            
        return False
    
    async def create_new_chat(self):
        """Navigate to create a new chat."""
        if not self.page:
            raise Exception("Browser not initialized. Call start() first.")

        try:
            # Check if we need to log in
            if await self.check_login_needed():
                await self.login()
                
            # Navigate directly to the specific project URL after successful login
            project_url = "https://claude.ai/project/434990a3-f303-4f35-85cd-490c991139d4"
            console.print(f"[yellow]Navigating to specific project URL: {project_url}[/yellow]")
            
            await self.page.goto(project_url, wait_until="networkidle")
            await asyncio.sleep(2)  # Give the page a moment to stabilize
            
            await self.take_screenshot("project_loaded")
            
            console.print("[green]Project loaded successfully[/green]")
            return True
            
        except Exception as e:
            console.print(f"[bold red]Error creating new chat: {str(e)}[/bold red]")
            await self.take_screenshot("create_chat_error")
            return False
    
    async def submit_prompt(self, prompt: str) -> bool:
        """Submit a prompt to Claude."""
        try:
            console.print("[yellow]Attempting to submit prompt...[/yellow]")
            
            # Common selector patterns for input fields in Claude UI
            input_selectors = [
                "textarea", 
                "div[contenteditable='true']", 
                "//textarea", 
                "//div[@contenteditable='true']",
                "div[role='textbox']",
                "//div[@role='textbox']",
                "[aria-label*='Message']"
            ]
            
            # Find the text input field
            input_field = None
            for selector in input_selectors:
                try:
                    if selector.startswith('//'):
                        input_field = await self.page.query_selector(f"xpath={selector}")
                    else:
                        input_field = await self.page.query_selector(selector)
                    
                    if input_field:
                        break
                except Exception:
                    pass
            
            if not input_field:
                console.print("[bold red]Could not find input field! Refreshing page...[/bold red]")
                await self.take_screenshot("no_text_area")
                
                # Refresh the page to try to find the input field
                if await self.refresh_page():
                    # Try to find the input field again after refresh
                    for selector in input_selectors:
                        try:
                            if selector.startswith('//'):
                                input_field = await self.page.query_selector(f"xpath={selector}")
                            else:
                                input_field = await self.page.query_selector(selector)
                            
                            if input_field:
                                break
                        except Exception:
                            pass
                
                if not input_field:
                    console.print("[bold red]Could not find input field even after refresh[/bold red]")
                    return False
            
            # More robust clearing of the input field
            max_clear_attempts = 3
            for attempt in range(max_clear_attempts):
                try:
                    # Check for existing text - handle both regular and contenteditable inputs
                    existing_text = ""
                    try:
                        # Try to get input value (works for standard inputs)
                        existing_text = await input_field.input_value()
                    except:
                        try:
                            # Try to get inner text (works for contenteditable divs)
                            existing_text = await input_field.evaluate('el => el.innerText')
                        except:
                            # If both fail, check using inner HTML as fallback
                            existing_text = await input_field.evaluate('el => el.innerHTML')
                    
                    if not existing_text or not existing_text.strip():
                        # Field is already clear
                        break
                    
                    console.print(f"[yellow]Input field already contains text (attempt {attempt+1}/{max_clear_attempts}): '{existing_text[:30]}...'[/yellow]")
                    
                    # Try different clearing methods
                    if attempt == 0:
                        # First try: Click + focus + Ctrl+A + Delete
                        await input_field.click()
                        await input_field.focus()
                        await self.page.keyboard.press("Control+A")
                        await self.page.keyboard.press("Delete")
                    elif attempt == 1:
                        # Second try: Clear using JavaScript - handle both input types
                        try:
                            await self.page.evaluate('''
                                (selector) => {
                                    const el = selector.startsWith('//') 
                                        ? document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue
                                        : document.querySelector(selector);
                                    
                                    if (el) {
                                        if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
                                            el.value = '';
                                        } else {
                                            el.innerText = '';
                                        }
                                    }
                                }
                            ''', selector)
                        except Exception as e:
                            console.print(f"[yellow]JS clearing failed: {e}[/yellow]")
                    else:
                        # Last attempt: Refresh page
                        console.print("[yellow]Multiple clearing attempts failed. Refreshing page...[/yellow]")
                        if await self.refresh_page():
                            # Find the input field again after refresh
                            input_field = None
                            for selector in input_selectors:
                                if selector.startswith('//'):
                                    input_field = await self.page.query_selector(f"xpath={selector}")
                                else:
                                    input_field = await self.page.query_selector(selector)
                                
                                if input_field:
                                    break
                        
                        if not input_field:
                            console.print("[bold red]Could not find input field after refresh[/bold red]")
                            return False
                    
                    # Verify if the text was cleared
                    await asyncio.sleep(0.5)  # Short pause to ensure field updates
                    
                    # Check if field is truly cleared now - try both methods
                    existing_text = ""
                    try:
                        # Try input value
                        existing_text = await input_field.input_value()
                    except:
                        try:
                            # Try inner text
                            existing_text = await input_field.evaluate('el => el.innerText')
                        except:
                            # Last resort - innerHTML
                            existing_text = await input_field.evaluate('el => el.innerHTML')
                    
                    if not existing_text or not existing_text.strip():
                        console.print("[green]Successfully cleared input field![/green]")
                        break
                    
                    # If on the last attempt and text still exists, try a last resort approach
                    if attempt == max_clear_attempts - 1:
                        # Force navigate back to project URL as a last resort
                        console.print("[yellow]Text clearing failed. Force navigating to fresh project URL...[/yellow]")
                        # Use the claude_url since project_id might not be available
                        await self.page.goto(self.claude_url)
                        await self.page.wait_for_load_state("networkidle")
                        await self.page.wait_for_timeout(3000)  # Give it time to fully load
                        
                        # Find the input field again
                        input_field = None
                        for selector in input_selectors:
                            if selector.startswith('//'):
                                input_field = await self.page.query_selector(f"xpath={selector}")
                            else:
                                input_field = await self.page.query_selector(selector)
                            
                            if input_field:
                                break
                        
                        if not input_field:
                            console.print("[bold red]Could not find input field after direct navigation[/bold red]")
                            return False
                except Exception as e:
                    console.print(f"[red]Error during text clearing attempt {attempt+1}: {e}[/red]")
                    # Continue to next attempt
            
            # Verify the field is actually empty now
            try:
                existing_text = ""
                try:
                    existing_text = await input_field.input_value()
                except:
                    try:
                        existing_text = await input_field.evaluate('el => el.innerText')
                    except:
                        existing_text = await input_field.evaluate('el => el.innerHTML')
                
                if existing_text and existing_text.strip():
                    console.print(f"[bold red]Failed to clear input field after multiple attempts. Text remains: '{existing_text[:30]}...'[/bold red]")
                    return False
            except Exception as e:
                console.print(f"[red]Error checking if field is cleared: {e}[/red]")
                # Continue anyway and hope for the best
            
            # Click on the input field to focus it
            await input_field.click()
            await input_field.focus()
            
            # Type the prompt
            await input_field.type(prompt)
            
            # Take a screenshot before submission
            await self.take_screenshot("before_submission")
            
            # Submit the prompt (press Enter)
            await self.page.keyboard.press("Enter")
            
            # Take a screenshot after submission
            await self.take_screenshot("prompt_submitted")
            
            # Wait for the response to start generating
            await self.page.wait_for_timeout(2000)
            
            console.print("[green]Prompt submitted successfully![/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Error submitting prompt: {e}[/red]")
            await self.take_screenshot("prompt_submission_error")
            
            # Try refreshing as a last resort if there was an error
            console.print("[yellow]Error occurred. Trying to refresh the page...[/yellow]")
            await self.refresh_page()
            
            return False
    
    async def wait_for_response_completion(self, max_wait_time=900):
        """
        Wait for Claude to complete its response.
        
        Args:
            max_wait_time (int): Maximum time to wait in seconds (default: 15 minutes)
            
        Returns:
            bool: True if response generation completed successfully, False otherwise
        """
        try:
            console.print("[yellow]Waiting for response generation to complete...[/yellow]")
            
            start_time = time.time()
            last_content = ""
            last_change_time = time.time()
            last_spinner_update = time.time()
            completion_check_count = 0
            max_completion_checks = 3
            
            # Spinner animation
            spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            spinner_idx = 0
            
            while time.time() - start_time < max_wait_time:
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Update spinner animation
                if current_time - last_spinner_update >= 0.3:
                    spinner = spinner_chars[spinner_idx % len(spinner_chars)]
                    console.print(f"\r{spinner} Waiting for Claude to generate content... ({int(elapsed)}s elapsed)", end="")
                    spinner_idx += 1
                    last_spinner_update = current_time
                
                # Get current content
                try:
                    current_content = await self.page.evaluate('''
                        () => {
                            const elements = document.querySelectorAll('.prose, .message-content, .claude-response');
                            for (const el of elements) {
                                if (el.innerText && el.innerText.trim().length > 0) {
                                    return el.innerText;
                                }
                            }
                            return '';
                        }
                    ''')
                    
                    # Check if content has changed
                    if current_content != last_content:
                        last_content = current_content
                        last_change_time = current_time
                        completion_check_count = 0  # Reset completion check count when content changes
                    else:
                        # Check for completion indicators if content hasn't changed for 15 seconds
                        # and we've waited at least 2 minutes (typical minimum generation time)
                        if elapsed >= 120 and (current_time - last_change_time) >= 15:
                            try:
                                # Look for signs that generation has stopped
                                still_generating = await self.page.evaluate('''
                                    () => {
                                        // Check for loading indicators
                                        const loadingElements = document.querySelectorAll(
                                            '.loading, .generating, .typing-indicator, [role="progressbar"]'
                                        );
                                        for (const el of loadingElements) {
                                            if (el.offsetParent !== null) return true;
                                        }
                                        
                                        // Check for generation text
                                        const statusTexts = ['generating', 'thinking', 'writing'];
                                        const pageText = document.body.innerText.toLowerCase();
                                        return statusTexts.some(text => pageText.includes(text));
                                    }
                                ''')
                                
                                if not still_generating:
                                    # Check if download button is visible
                                    download_button = await self.page.query_selector(
                                        'xpath=/html/body/div[2]/div[2]/div/div[3]/div/div[2]/div[1]/div[1]/div[2]/div/button[2]'
                                    )
                                    
                                    if download_button and await download_button.is_visible():
                                        console.print("\n[green]Response generation completed![/green]")
                                        console.print(f"[blue]Total generation time: {int(elapsed)} seconds[/blue]")
                                        return True
                                    
                                    # If we can't find the download button but generation seems complete,
                                    # increment the check count
                                    completion_check_count += 1
                                    
                                    # If we've checked multiple times and still no download button,
                                    # assume generation is complete
                                    if completion_check_count >= max_completion_checks:
                                        console.print("\n[yellow]Generation appears complete but download button not found.[/yellow]")
                                        console.print(f"[blue]Total generation time: {int(elapsed)} seconds[/blue]")
                                        return True
                            
                            except Exception as e:
                                console.print(f"\n[yellow]Error checking completion: {str(e)}[/yellow]")
                    
                except Exception as e:
                    console.print(f"\n[yellow]Error getting content: {str(e)}[/yellow]")
                
                await asyncio.sleep(0.2)  # Small delay to prevent excessive CPU usage
            
            # If we get here, we've timed out
            console.print("\n[bold red]Timed out waiting for response[/bold red]")
            return False
            
        except Exception as e:
            console.print(f"\n[bold red]Error in wait_for_response_completion: {str(e)}[/bold red]")
            return False
    
    async def download_content_as_markdown(self, output_path: Path):
        """Download content from Claude as Markdown."""
        try:
            console.print("[yellow]Attempting to download content as markdown...[/yellow]")
            
            # Try direct "Copy" button first since it's more reliable
            try:
                console.print("[yellow]Trying to copy content...[/yellow]")
                copy_button = await self.page.query_selector('button:has-text("Copy")')
                if copy_button:
                    await copy_button.click()
                    await asyncio.sleep(1)
                    
                    # Get content from clipboard via JavaScript
                    content = await self.page.evaluate('''
                        async () => {
                            try {
                                return await navigator.clipboard.readText();
                            } catch (e) {
                                return null;
                            }
                        }
                    ''')
                    
                    if content:
                        # Save content to file
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        console.print(f"[green]Content saved using clipboard method to: {output_path}[/green]")
                        return True
                
                console.print("[yellow]Copy button method failed, trying alternative method...[/yellow]")
            except Exception as copy_error:
                console.print(f"[yellow]Copy method failed: {str(copy_error)}[/yellow]")
            
            # If copy failed, try direct extraction
            try:
                # Extract content directly from the page
                content = await self.extract_response()
                if content:
                    # Save the extracted content
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    console.print(f"[green]Content saved using direct extraction to: {output_path}[/green]")
                    return True
                    
            except Exception as e:
                console.print(f"[red]Content extraction failed: {str(e)}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[bold red]Error saving content: {str(e)}[/bold red]")
            await self.take_screenshot("save_content_error")
            return False
    
    async def refresh_page(self) -> bool:
        """Refresh the Claude AI page and wait for it to load completely."""
        try:
            console.print("[yellow]Refreshing page...[/yellow]")
            
            # Store the current URL before refreshing
            current_url = self.page.url
            
            # Refresh the page
            await self.page.reload()
            
            # Wait for navigation to complete
            await self.page.wait_for_load_state("networkidle")
            
            # Navigate back to the original URL if needed
            if current_url and current_url != self.page.url:
                await self.page.goto(current_url)
                await self.page.wait_for_load_state("networkidle")
            
            # Wait for the page to be fully interactive
            await self.page.wait_for_timeout(2000)
            
            console.print("[green]Page refreshed successfully![/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Error refreshing page: {e}[/red]")
            return False
    
    async def extract_response(self):
        """Extract Claude's response from the page with improved error handling and retry mechanisms."""
        try:
            # Take a screenshot before extraction attempt
            await self.take_screenshot("before_extraction")
            
            # Multiple strategies to identify and extract Claude's response with resilience
            console.print("[yellow]Attempting to extract response text...[/yellow]")
            
            # Various selectors that might contain Claude's response
            response_selectors = [
                '.message.assistant',  # Common Claude response container
                '.claude-response',
                '.message-container.assistant',
                '.message-content.assistant',
                '.prose',  # Often contains the formatted text
                '[data-message-author-role="assistant"]',  # Role-based selector
                '[role="region"][aria-label*="message"]',  # Accessibility-based selector
                '.anthropic-message',  # Anthropic specific class
                '.assistant-message'
            ]
            
            # Try multiple extraction strategies with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # First try to get the latest/last assistant message
                    response_text = None
                    
                    # Strategy 1: Look for specific response selectors
                    for selector in response_selectors:
                        try:
                            elements = await self.page.query_selector_all(selector)
                            if elements and len(elements) > 0:
                                # Get the last/most recent assistant message
                                last_element = elements[-1]
                                response_text = await last_element.inner_text()
                                if response_text and len(response_text.strip()) > 0:
                                    console.print(f"[green]Successfully extracted response using selector: {selector}[/green]")
                                    break
                        except Exception as selector_error:
                            console.print(f"[yellow]Error with selector {selector}: {str(selector_error)}[/yellow]")
                    
                    # Strategy 2: Try JavaScript evaluation if selectors failed
                    if not response_text or len(response_text.strip()) == 0:
                        console.print("[yellow]Trying JavaScript extraction method...[/yellow]")
                        try:
                            # Advanced JS to find and extract the text content
                            js_extraction = """
                            () => {
                                // Look for assistant messages
                                const assistantMessages = Array.from(document.querySelectorAll('.message, [role="region"]'))
                                    .filter(el => {
                                        const text = el.innerText.toLowerCase();
                                        const classList = Array.from(el.classList).join(' ').toLowerCase();
                                        const attributes = Array.from(el.attributes).map(attr => attr.name + '=' + attr.value).join(' ').toLowerCase();
                                        return (classList.includes('assistant') || 
                                                text.includes('claude:') || 
                                                attributes.includes('assistant') ||
                                                attributes.includes('role=region'));
                                    });
                                
                                // Get the last assistant message
                                if (assistantMessages.length > 0) {
                                    return assistantMessages[assistantMessages.length - 1].innerText;
                                }
                                
                                // Fallback: get all text from elements that might contain the response
                                const possibleContainers = document.querySelectorAll('.prose, .content, .message-content, .text-message');
                                if (possibleContainers.length > 0) {
                                    return Array.from(possibleContainers).map(el => el.innerText).join('\\n\\n');
                                }
                                
                                return '';
                            }
                            """
                            js_result = await self.page.evaluate(js_extraction)
                            if js_result and len(js_result.strip()) > 0:
                                response_text = js_result
                                console.print("[green]Successfully extracted response using JavaScript method[/green]")
                        except Exception as js_error:
                            console.print(f"[yellow]JavaScript extraction failed: {str(js_error)}[/yellow]")
                    
                    # Strategy 3: Try using page content if all else fails
                    if not response_text or len(response_text.strip()) == 0:
                        console.print("[yellow]Attempting to extract from page content...[/yellow]")
                        try:
                            # Take another screenshot to verify page state
                            await self.take_screenshot("extraction_fallback")
                            
                            # Get entire page content and try to identify Claude's response
                            page_content = await self.page.content()
                            
                            # Parse HTML content to find response
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(page_content, 'html.parser')
                            
                            # Look for common response container patterns
                            assistant_elements = soup.select('.message.assistant, .claude-response, .prose')
                            if assistant_elements and len(assistant_elements) > 0:
                                response_text = assistant_elements[-1].get_text(strip=True)
                                console.print("[green]Successfully extracted response using HTML parsing[/green]")
                        except Exception as content_error:
                            console.print(f"[yellow]Page content extraction failed: {str(content_error)}[/yellow]")
                    
                    # If we found a response, process and return it
                    if response_text and len(response_text.strip()) > 0:
                        # Clean up the response text
                        response_text = response_text.strip()
                        
                        # Additional cleaning if needed
                        # Remove common prefixes like "Claude:" or "Assistant:"
                        common_prefixes = ["Claude:", "Assistant:", "AI:", "Claude's Response:"]
                        for prefix in common_prefixes:
                            if response_text.startswith(prefix):
                                response_text = response_text[len(prefix):].strip()
                        
                        console.print("[green]Response extraction successful[/green]")
                        return response_text
                    
                    # If we get here, no response text was extracted in this attempt
                    console.print(f"[yellow]Attempt {attempt+1}/{max_retries} failed to extract response text.[/yellow]")
                    
                    # Take an additional screenshot to diagnose issues
                    await self.take_screenshot(f"extraction_attempt_{attempt+1}_failed")
                    
                    if attempt < max_retries - 1:
                        # Wait and try again if not last attempt
                        console.print("[yellow]Waiting a moment before trying again...[/yellow]")
                        await asyncio.sleep(5)  # Wait 5 seconds before retrying
                        
                        # Try refreshing the page for the next attempt if we're still not seeing content
                        if attempt == 1:  # Only try refreshing once
                            console.print("[yellow]Refreshing page for next extraction attempt...[/yellow]")
                            await self.refresh_page()
                            await asyncio.sleep(3)
                
                except Exception as attempt_error:
                    console.print(f"[bold red]Error during extraction attempt {attempt+1}: {str(attempt_error)}[/bold red]")
                    await self.take_screenshot(f"extraction_error_{attempt+1}")
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)  # Wait before retry
            
            # If we got here, all extraction attempts failed
            console.print("[bold red]Could not extract response text[/bold red]")
            await self.take_screenshot("empty_response")
            return None
            
        except Exception as e:
            console.print(f"[bold red]Failed to get response from Claude: {str(e)}[/bold red]")
            await self.take_screenshot("extraction_critical_error")
            return None
    
    async def close(self):
        """Close the browser and clean up resources."""
        try:
            # Special handling for persistent context
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