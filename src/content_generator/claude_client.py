#!/usr/bin/env python3
"""
Claude.ai client for browser automation using Playwright.
Uses persistent browser context to maintain login between sessions.
"""
import os
import asyncio
import time
import json
import re
from pathlib import Path
from typing import Optional

from common.browser_base import BrowserBase
from common.config import config
from rich.console import Console

console = Console()


class ClaudeClient(BrowserBase):
    """Client for interacting with Claude.ai via browser automation."""
    
    def __init__(self):
        """Initialize the Claude client."""
        super().__init__(
            user_data_dir=config.content_generator.user_data_dir,
            screenshot_dir=config.browser.screenshot_dir,
            base_url=config.content_generator.claude_url
        )
    
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
            
            await self.wait_for_navigation_or_element(
                timeout=180000,  # 3 minutes
                selectors=["textarea", '.chat-input', '[role="textbox"]'],
                url_patterns=["/chat", "/chats", "/project"]
            )
            
            console.print("[green]Security verification appears to be completed. Continuing...[/green]")
            await self.take_screenshot("after_verification")
            await asyncio.sleep(5)
    
    async def check_login_needed(self) -> bool:
        """Check if login is needed based on the current page."""
        if not self.page:
            return True
            
        url = self.page.url
        console.print(f"[yellow]Checking if login needed. Current URL: {url}[/yellow]")
        
        if "/project/" in url or "/chat" in url:
            console.print("[green]Already logged in![/green]")
            return False
            
        try:
            login_texts = ["log in", "sign in", "continue with", "log into"]
            page_text = await self.page.evaluate('() => document.body.innerText.toLowerCase()')
            
            if any(text in page_text.lower() for text in login_texts):
                console.print("[yellow]Login appears to be required based on page text[/yellow]")
                return True
        except:
            return True
            
        return False
    
    async def _handle_login_if_needed(self):
        """Check if login is needed and handle it."""
        await self.take_screenshot("login_check")
        
        if not await self.check_login_needed():
            return True
            
        console.print("[yellow]Login appears to be required[/yellow]")
        
        # Try to click continue/login button
        try:
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
                        await asyncio.sleep(3)
                        break
                except:
                    continue
                    
        except Exception as e:
            console.print(f"[yellow]Could not click login button: {str(e)}[/yellow]")
        
        console.print("[bold red]Please complete the login process in the browser window[/bold red]")
        console.print("[yellow]Waiting up to 2 minutes for login to complete...[/yellow]")
        
        login_successful = await self.wait_for_navigation_or_element(
            timeout=120000,  # 2 minutes
            selectors=[
                "textarea", 
                '.chat-input', 
                '[role="textbox"]',
                '.ProseMirror[contenteditable="true"]',
                'div[contenteditable="true"]',
                '[data-slate-editor="true"]'
            ],
            url_patterns=["/chat", "/chats", "/project"]
        )
        
        if login_successful:
            console.print("[green]Login successful![/green]")
            await self.take_screenshot("login_successful")
            await asyncio.sleep(5)
            
            await self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)
            await self.take_screenshot("project_after_login")
            return True
        else:
            console.print("[bold red]Login may have failed. Taking screenshot for debugging.[/bold red]")
            await self.take_screenshot("login_failed")
            return False
    
    async def start(self):
        """Start the browser and navigate to Claude using persistent context."""
        if not await super().start():
            return False
            
        try:
            console.print(f"[yellow]Navigating to project URL: {self.base_url}...[/yellow]")
            await self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)
            
            await self.take_screenshot("project_loaded")
            
            current_url = self.page.url
            console.print(f"[yellow]Current URL after navigation: {current_url}[/yellow]")
            
            if "/project/" in current_url:
                console.print("[green]Successfully navigated to Claude project![/green]")
            else:
                console.print("[yellow]Not on project page. Will check if login is needed.[/yellow]")
                await self._handle_security_verification()
                await self._handle_login_if_needed()
                
                if "/project/" not in self.page.url:
                    console.print("[yellow]Trying to navigate to project URL again...[/yellow]")
                    await self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(5)
            
            console.print("[green]Successfully connected to Claude[/green]")
            return True
            
        except Exception as e:
            console.print(f"[bold red]Failed to start browser: {str(e)}[/bold red]")
            await self.close()
            return False
            
    async def submit_prompt(self, prompt: str) -> bool:
        """Submit a prompt to Claude."""
        try:
            console.print("[yellow]Attempting to submit prompt...[/yellow]")
            
            input_selectors = [
                "textarea", 
                "div[contenteditable='true']", 
                "//textarea", 
                "//div[@contenteditable='true']",
                "div[role='textbox']",
                "//div[@role='textbox']",
                "[aria-label*='Message']"
            ]
            
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
                
                if await self.refresh_page():
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
                    # Check for existing text
                    existing_text = ""
                    try:
                        existing_text = await input_field.input_value()
                    except:
                        try:
                            existing_text = await input_field.evaluate('el => el.innerText')
                        except:
                            existing_text = await input_field.evaluate('el => el.innerHTML')
                    
                    if not existing_text or not existing_text.strip():
                        break
                    
                    console.print(f"[yellow]Input field already contains text (attempt {attempt+1}/{max_clear_attempts}): '{existing_text[:30]}...'[/yellow]")
                    
                    if attempt == 0:
                        await input_field.click()
                        await input_field.focus()
                        await self.page.keyboard.press("Control+A")
                        await self.page.keyboard.press("Delete")
                    elif attempt == 1:
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
                        console.print("[yellow]Multiple clearing attempts failed. Refreshing page...[/yellow]")
                        if await self.refresh_page():
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
                    
                    await asyncio.sleep(0.5)
                    
                    existing_text = ""
                    try:
                        existing_text = await input_field.input_value()
                    except:
                        try:
                            existing_text = await input_field.evaluate('el => el.innerText')
                        except:
                            existing_text = await input_field.evaluate('el => el.innerHTML')
                    
                    if not existing_text or not existing_text.strip():
                        console.print("[green]Successfully cleared input field![/green]")
                        break
                    
                    if attempt == max_clear_attempts - 1:
                        console.print("[yellow]Text clearing failed. Force navigating to fresh project URL...[/yellow]")
                        await self.page.goto(self.base_url)
                        await self.page.wait_for_load_state("networkidle")
                        await self.page.wait_for_timeout(3000)
                        
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
            
            await input_field.click()
            await input_field.focus()
            await input_field.type(prompt)
            
            await self.take_screenshot("before_submission")
            await self.page.keyboard.press("Enter")
            await self.take_screenshot("prompt_submitted")
            await self.page.wait_for_timeout(2000)
            
            console.print("[green]Prompt submitted successfully![/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Error submitting prompt: {e}[/red]")
            await self.take_screenshot("prompt_submission_error")
            
            console.print("[yellow]Error occurred. Trying to refresh the page...[/yellow]")
            await self.refresh_page()
            
            return False
    
    async def wait_for_response_completion(self, max_wait_time: int = 900) -> bool:
        """Wait for Claude to complete its response."""
        try:
            console.print("[yellow]Waiting for response generation to complete...[/yellow]")
            
            start_time = time.time()
            last_content = ""
            last_change_time = time.time()
            completion_check_count = 0
            max_completion_checks = 3
            
            while time.time() - start_time < max_wait_time:
                current_time = time.time()
                elapsed = current_time - start_time
                
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
                    
                    if current_content != last_content:
                        last_content = current_content
                        last_change_time = current_time
                        completion_check_count = 0
                    else:
                        if elapsed >= 120 and (current_time - last_change_time) >= 15:
                            try:
                                still_generating = await self.page.evaluate('''
                                    () => {
                                        const loadingElements = document.querySelectorAll(
                                            '.loading, .generating, .typing-indicator, [role="progressbar"]'
                                        );
                                        for (const el of loadingElements) {
                                            if (el.offsetParent !== null) return true;
                                        }
                                        
                                        const statusTexts = ['generating', 'thinking', 'writing'];
                                        const pageText = document.body.innerText.toLowerCase();
                                        return statusTexts.some(text => pageText.includes(text));
                                    }
                                ''')
                                
                                if not still_generating:
                                    download_button = await self.page.query_selector(
                                        'xpath=/html/body/div[2]/div[2]/div/div[3]/div/div[2]/div[1]/div[1]/div[2]/div/button[2]'
                                    )
                                    
                                    if download_button and await download_button.is_visible():
                                        console.print("\n[green]Response generation completed![/green]")
                                        console.print(f"[blue]Total generation time: {int(elapsed)} seconds[/blue]")
                                        return True
                                    
                                    completion_check_count += 1
                                    
                                    if completion_check_count >= max_completion_checks:
                                        console.print("\n[yellow]Generation appears complete but download button not found.[/yellow]")
                                        console.print(f"[blue]Total generation time: {int(elapsed)} seconds[/blue]")
                                        return True
                            
                            except Exception as e:
                                console.print(f"\n[yellow]Error checking completion: {str(e)}[/yellow]")
                    
                except Exception as e:
                    console.print(f"\n[yellow]Error getting content: {str(e)}[/yellow]")
                
                await asyncio.sleep(0.2)
            
            console.print("\n[bold red]Timed out waiting for response[/bold red]")
            return False
            
        except Exception as e:
            console.print(f"\n[bold red]Error in wait_for_response_completion: {str(e)}[/bold red]")
            return False
    
    async def download_content_as_markdown(self, output_path: Path) -> bool:
        """Download content from Claude as Markdown."""
        try:
            console.print("[yellow]Attempting to download content as markdown...[/yellow]")
            
            try:
                console.print("[yellow]Trying to copy content...[/yellow]")
                copy_button = await self.page.query_selector('button:has-text("Copy")')
                if copy_button:
                    await copy_button.click()
                    await asyncio.sleep(1)
                    
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
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        console.print(f"[green]Content saved using clipboard method to: {output_path}[/green]")
                        return True
                
                console.print("[yellow]Copy button method failed, trying alternative method...[/yellow]")
            except Exception as copy_error:
                console.print(f"[yellow]Copy method failed: {str(copy_error)}[/yellow]")
            
            try:
                content = await self.extract_response()
                if content:
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
    
    async def extract_response(self) -> Optional[str]:
        """Extract Claude's response from the page."""
        try:
            await self.take_screenshot("before_extraction")
            
            console.print("[yellow]Attempting to extract response text...[/yellow]")
            
            response_selectors = [
                '.message.assistant',
                '.claude-response',
                '.message-container.assistant',
                '.message-content.assistant',
                '.prose',
                '[data-message-author-role="assistant"]',
                '[role="region"][aria-label*="message"]',
                '.anthropic-message',
                '.assistant-message'
            ]
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response_text = None
                    
                    for selector in response_selectors:
                        try:
                            elements = await self.page.query_selector_all(selector)
                            if elements and len(elements) > 0:
                                last_element = elements[-1]
                                response_text = await last_element.inner_text()
                                if response_text and len(response_text.strip()) > 0:
                                    console.print(f"[green]Successfully extracted response using selector: {selector}[/green]")
                                    break
                        except Exception as selector_error:
                            console.print(f"[yellow]Error with selector {selector}: {str(selector_error)}[/yellow]")
                    
                    if not response_text or len(response_text.strip()) == 0:
                        console.print("[yellow]Trying JavaScript extraction method...[/yellow]")
                        try:
                            js_extraction = """
                            () => {
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
                                
                                if (assistantMessages.length > 0) {
                                    return assistantMessages[assistantMessages.length - 1].innerText;
                                }
                                
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
                    
                    if not response_text or len(response_text.strip()) == 0:
                        console.print("[yellow]Attempting to extract from page content...[/yellow]")
                        try:
                            await self.take_screenshot("extraction_fallback")
                            
                            page_content = await self.page.content()
                            
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(page_content, 'html.parser')
                            
                            assistant_elements = soup.select('.message.assistant, .claude-response, .prose')
                            if assistant_elements and len(assistant_elements) > 0:
                                response_text = assistant_elements[-1].get_text(strip=True)
                                console.print("[green]Successfully extracted response using HTML parsing[/green]")
                        except Exception as content_error:
                            console.print(f"[yellow]Page content extraction failed: {str(content_error)}[/yellow]")
                    
                    if response_text and len(response_text.strip()) > 0:
                        response_text = response_text.strip()
                        
                        common_prefixes = ["Claude:", "Assistant:", "AI:", "Claude's Response:"]
                        for prefix in common_prefixes:
                            if response_text.startswith(prefix):
                                response_text = response_text[len(prefix):].strip()
                        
                        console.print("[green]Response extraction successful[/green]")
                        return response_text
                    
                    console.print(f"[yellow]Attempt {attempt+1}/{max_retries} failed to extract response text.[/yellow]")
                    await self.take_screenshot(f"extraction_attempt_{attempt+1}_failed")
                    
                    if attempt < max_retries - 1:
                        console.print("[yellow]Waiting a moment before trying again...[/yellow]")
                        await asyncio.sleep(5)
                        
                        if attempt == 1:
                            console.print("[yellow]Refreshing page for next extraction attempt...[/yellow]")
                            await self.refresh_page()
                            await asyncio.sleep(3)
                
                except Exception as attempt_error:
                    console.print(f"[bold red]Error during extraction attempt {attempt+1}: {str(attempt_error)}[/bold red]")
                    await self.take_screenshot(f"extraction_error_{attempt+1}")
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
            
            console.print("[bold red]Could not extract response text[/bold red]")
            await self.take_screenshot("empty_response")
            return None
            
        except Exception as e:
            console.print(f"[bold red]Failed to get response from Claude: {str(e)}[/bold red]")
            await self.take_screenshot("extraction_critical_error")
            return None