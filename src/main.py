#!/usr/bin/env python3
"""
Main script for BlogAutomation2 project.
Automates blog writing using Claude.ai and Playwright.
"""
import os
import asyncio
import sys
import traceback
from pathlib import Path
from claude_client import ClaudeClient
from keyword_manager import KeywordManager
from file_manager import FileManager
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

async def main():
    """Main automation process for blog writing."""
    console.print("[bold blue]Starting Blog Automation with Claude AI[/bold blue]")
    
    # Initialize components
    keyword_manager = KeywordManager(Path("content/keywords/keywords.txt"))
    file_manager = FileManager(Path("content/completed"))
    
    # Get next keyword to process
    keyword = keyword_manager.get_next_keyword()
    if not keyword:
        console.print("[bold red]No keywords found in the keywords file.[/bold red]")
        return
    
    console.print(f"[green]Processing keyword:[/green] [bold]{keyword}[/bold]")
    
    # Create directory structure before starting content generation
    next_index = file_manager.get_next_index()
    output_dir = file_manager.create_completed_content_structure(next_index, keyword)
    
    # Initialize Claude client
    claude = ClaudeClient()
    
    try:
        # Start Playwright browser and navigate to Claude
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("[yellow]Starting browser and connecting to Claude...", total=None)
            await claude.start()
            progress.update(task, completed=True)
        
        # Load prompt template and replace keyword
        prompt_template_path = Path("content/prompts/prompt_template.txt")
        if not prompt_template_path.exists():
            console.print(f"[bold red]Error: Prompt template not found at {prompt_template_path}[/bold red]")
            return
            
        try:
            with open(prompt_template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except Exception as e:
            console.print(f"[bold red]Error reading prompt template: {str(e)}[/bold red]")
            return
        
        # Replace keyword placeholder in prompt
        prompt = prompt_template.replace("replace_with_keyword", keyword)
        
        # Submit prompt to Claude and get response
        console.print("[yellow]Submitting prompt to Claude...[/yellow]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=False,
        ) as progress:
            task = progress.add_task("[yellow]Waiting for Claude to generate content...", total=None)
            
            # Submit the prompt (returns True/False for success)
            submission_successful = await claude.submit_prompt(prompt)
            
            if not submission_successful:
                progress.update(task, description="[red]Failed to submit prompt to Claude[/red]")
                console.print("[bold red]Failed to submit prompt to Claude[/bold red]")
                return
                
            # Wait for response completion
            completion_successful = await claude.wait_for_response_completion()
            
            if not completion_successful:
                progress.update(task, description="[red]Failed to complete response generation[/red]")
                console.print("[bold red]Failed to complete response generation[/bold red]")
                return
            
            # Download the content using the download button
            markdown_path = output_dir / f"{keyword.replace(' ', '_').lower()}.md"
            download_successful = await claude.download_content_as_markdown(markdown_path)
            
            if download_successful:
                progress.update(task, completed=True)
                console.print(f"[bold green]✓[/bold green] Content downloaded and saved to: {markdown_path}")
                
                # Try to generate PDF from the downloaded markdown
                try:
                    pdf_path = file_manager.save_as_pdf(markdown_path, output_dir, keyword)
                    if pdf_path:
                        console.print(f"[bold green]✓[/bold green] PDF saved as: {pdf_path}")
                    else:
                        console.print("[yellow]PDF generation failed, but markdown was saved successfully.[/yellow]")
                except Exception as e:
                    console.print(f"[yellow]PDF generation error: {str(e)}. Markdown still saved successfully.[/yellow]")
                
                # Mark keyword as processed
                keyword_manager.mark_processed(keyword)
                console.print(f"[green]Marked keyword '[bold]{keyword}[/bold]' as processed.[/green]")
            else:
                progress.update(task, description="[red]Failed to download content[/red]")
                console.print("[bold red]Failed to download content from Claude[/bold red]")
                
                # Fallback to extracting content if download fails
                console.print("[yellow]Attempting to extract content as fallback...[/yellow]")
                response = await claude.extract_response()
                
                if response and len(response) > 0:
                    # Save the extracted content
                    markdown_path = file_manager.save_as_markdown(response, output_dir, keyword)
                    
                    if markdown_path:
                        console.print(f"[bold green]✓[/bold green] Content extracted and saved as: {markdown_path}")
                        
                        # Try to generate PDF from the extracted content
                        try:
                            pdf_path = file_manager.save_as_pdf(markdown_path, output_dir, keyword)
                            if pdf_path:
                                console.print(f"[bold green]✓[/bold green] PDF saved as: {pdf_path}")
                            else:
                                console.print("[yellow]PDF generation failed, but markdown was saved successfully.[/yellow]")
                        except Exception as e:
                            console.print(f"[yellow]PDF generation error: {str(e)}. Markdown still saved successfully.[/yellow]")
                        
                        # Mark keyword as processed
                        keyword_manager.mark_processed(keyword)
                        console.print(f"[green]Marked keyword '[bold]{keyword}[/bold]' as processed.[/green]")
                    else:
                        console.print("[bold red]Failed to save extracted content.[/bold red]")
                else:
                    console.print("[bold red]Failed to extract content as fallback[/bold red]")
                    console.print("[yellow]Check screenshots for details on what happened.[/yellow]")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Process interrupted by user.[/yellow]")
    
    except Exception as e:
        console.print(f"[bold red]Error occurred:[/bold red] {str(e)}")
        console.print("[red]Stack trace:[/red]")
        traceback.print_exc(file=sys.stderr)
    
    finally:
        # Close browser
        console.print("[yellow]Cleaning up and closing browser...[/yellow]")
        try:
            await claude.close()
            console.print("[blue]Blog automation completed.[/blue]")
        except Exception as e:
            console.print(f"[yellow]Error during cleanup: {str(e)}[/yellow]")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Process terminated by user.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Fatal error: {str(e)}[/bold red]")
        traceback.print_exc(file=sys.stderr)