#!/usr/bin/env python3
"""
Main entry point for AI content detection workflow.
"""
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Set

from common.config import config
from common.utils import load_json_file, save_json_file
from .zerogpt_client import ZeroGPTClient
from rich.console import Console

console = Console()


async def check_content(content_path: Path) -> bool:
    """
    Check content for AI detection.
    
    Args:
        content_path: Path to the markdown content file
        
    Returns:
        bool: True if content passes AI detection check
    """
    try:
        # Read the content file
        with open(content_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Initialize ZeroGPT client
        client = ZeroGPTClient()
        if not await client.start():
            console.print("[red]Failed to start ZeroGPT client[/red]")
            return False
        
        try:
            # Check the content
            is_human, ai_percentage = await client.check_text(content)
            
            # Save the results
            results_file = content_path.with_suffix('.json')
            results = {
                'filename': content_path.name,
                'is_human': is_human,
                'ai_percentage': ai_percentage,
                'max_allowed': config.ai_detector.max_ai_percentage
            }
            save_json_file(results, results_file)
            
            if is_human:
                console.print(f"[green]Content passed AI detection ({ai_percentage:.1f}% AI probability)[/green]")
            else:
                console.print(f"[red]Content failed AI detection ({ai_percentage:.1f}% AI probability)[/red]")
            
            return is_human
            
        finally:
            await client.close()
            
    except Exception as e:
        console.print(f"[bold red]Error checking content: {str(e)}[/bold red]")
        return False


def get_completed_content() -> List[Path]:
    """Get list of completed content files that need checking."""
    content_dir = config.content_generator.completed_dir
    return list(content_dir.glob('**/*.md'))


def get_processed_files() -> Set[str]:
    """Get set of already processed filenames."""
    processed_file = Path('content/ai_detection/processed_files.json')
    if processed_file.exists():
        data = load_json_file(processed_file)
        return set(data.get('processed_files', []))
    return set()


def save_processed_files(processed: Set[str]):
    """Save set of processed filenames."""
    processed_file = Path('content/ai_detection/processed_files.json')
    processed_file.parent.mkdir(parents=True, exist_ok=True)
    save_json_file({'processed_files': list(processed)}, processed_file)


async def main():
    """Main entry point for AI detection workflow."""
    try:
        console.print("[yellow]Starting AI detection workflow...[/yellow]")
        
        # Get completed content files
        content_files = get_completed_content()
        if not content_files:
            console.print("[yellow]No content files found to check[/yellow]")
            return
        
        # Get already processed files
        processed_files = get_processed_files()
        
        # Check each unprocessed file
        for content_path in content_files:
            if content_path.name in processed_files:
                continue
                
            console.print(f"[yellow]Checking content file: {content_path.name}[/yellow]")
            
            if await check_content(content_path):
                processed_files.add(content_path.name)
                save_processed_files(processed_files)
            else:
                console.print(f"[red]Content check failed for: {content_path.name}[/red]")
        
        console.print("[green]AI detection workflow completed[/green]")
        
    except Exception as e:
        console.print(f"[bold red]Error in AI detection workflow: {str(e)}[/bold red]")