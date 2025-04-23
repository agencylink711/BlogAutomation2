#!/usr/bin/env python3
"""
Keyword manager for handling keywords in the BlogAutomation2 project.
"""
import os
from pathlib import Path
from typing import Optional, List
from rich.console import Console

console = Console()

class KeywordManager:
    """Manages keywords for blog automation."""
    
    def __init__(self, keywords_file: Path):
        """Initialize the keyword manager with the path to the keywords file."""
        self.keywords_file = keywords_file
        self.processed_file = keywords_file.parent / "processed_keywords.txt"
        
        # Create the processed keywords file if it doesn't exist
        if not self.processed_file.exists():
            self.processed_file.touch()
    
    def get_keywords(self) -> List[str]:
        """Get all keywords from the keywords file."""
        if not self.keywords_file.exists():
            console.print(f"[bold red]Keywords file not found: {self.keywords_file}[/bold red]")
            return []
        
        try:
            with open(self.keywords_file, "r", encoding="utf-8") as f:
                keywords = [line.strip() for line in f.readlines() if line.strip()]
            return keywords
        except Exception as e:
            console.print(f"[bold red]Error reading keywords file: {str(e)}[/bold red]")
            return []
    
    def get_processed_keywords(self) -> List[str]:
        """Get list of already processed keywords."""
        try:
            with open(self.processed_file, "r", encoding="utf-8") as f:
                processed = [line.strip() for line in f.readlines() if line.strip()]
            return processed
        except Exception:
            return []
    
    def get_next_keyword(self) -> Optional[str]:
        """Get the next unprocessed keyword."""
        all_keywords = self.get_keywords()
        if not all_keywords:
            return None
            
        processed_keywords = self.get_processed_keywords()
        
        # Find first keyword that hasn't been processed yet
        for keyword in all_keywords:
            if keyword not in processed_keywords:
                return keyword
                
        console.print("[yellow]All keywords have been processed![/yellow]")
        return None
    
    def mark_processed(self, keyword: str):
        """Mark a keyword as processed."""
        if not keyword or keyword in self.get_processed_keywords():
            return
            
        try:
            with open(self.processed_file, "a", encoding="utf-8") as f:
                f.write(f"{keyword}\n")
        except Exception as e:
            console.print(f"[bold red]Error marking keyword as processed: {str(e)}[/bold red]")