#!/usr/bin/env python3
"""
File manager for handling file operations in the BlogAutomation2 project.
"""
import os
import shutil
from pathlib import Path
import pdfkit
from rich.console import Console

console = Console()

class FileManager:
    """Manages file operations for blog automation."""
    
    def __init__(self, output_dir: Path):
        """Initialize the file manager with the path to the output directory."""
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_completed_content_structure(self, index: int, keyword: str) -> Path:
        """
        Create directory structure for completed content.
        
        Args:
            index (int): Index number for the folder prefix (e.g., 1)
            keyword (str): The keyword for the content
            
        Returns:
            Path: Path to the created directory
        """
        # Sanitize keyword for use in directory name
        safe_keyword = "".join(c if c.isalnum() or c in [' ', '-'] else '_' for c in keyword)
        safe_keyword = safe_keyword.replace(' ', '_').lower()
        
        # Create directory path with format: {index}_{keyword}
        dir_name = f"{index}_{safe_keyword}"
        dir_path = self.output_dir / dir_name
        
        # Create directory if it doesn't exist
        dir_path.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]Created directory structure: {dir_path}[/green]")
        
        return dir_path
    
    def get_next_index(self) -> int:
        """Get the next available index number for content folders."""
        try:
            # List all directories in the output directory
            existing_dirs = [d for d in self.output_dir.iterdir() if d.is_dir()]
            
            # Extract indices from directory names
            indices = []
            for dir_path in existing_dirs:
                try:
                    # Try to get the index from the directory name (format: {index}_{keyword})
                    index_str = dir_path.name.split('_')[0]
                    if index_str.isdigit():
                        indices.append(int(index_str))
                except (IndexError, ValueError):
                    continue
            
            # Return next available index (max + 1), or 1 if no directories exist
            return max(indices, default=0) + 1
            
        except Exception as e:
            console.print(f"[yellow]Error getting next index: {str(e)}. Using 1.[/yellow]")
            return 1
    
    def create_output_dir(self, keyword: str) -> Path:
        """Create a directory for the output files based on the keyword."""
        # Sanitize keyword for use in directory name
        safe_keyword = "".join(c if c.isalnum() or c in [' ', '-'] else '_' for c in keyword)
        safe_keyword = safe_keyword.replace(' ', '_').lower()
        
        # Create directory path
        dir_path = self.output_dir / f"01_{safe_keyword}"
        
        # Create directory if it doesn't exist
        dir_path.mkdir(parents=True, exist_ok=True)
        
        return dir_path
    
    def save_as_markdown(self, content: str, output_dir: Path, keyword: str) -> Path:
        """Save content as markdown file."""
        # Sanitize keyword for use in filename
        safe_keyword = "".join(c if c.isalnum() or c in [' ', '-'] else '_' for c in keyword)
        safe_keyword = safe_keyword.replace(' ', '_').lower()
        
        # Create file path
        file_path = output_dir / f"{safe_keyword}.md"
        
        # Save content to file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            console.print(f"[green]Content saved as markdown: {file_path}[/green]")
            return file_path
        except Exception as e:
            console.print(f"[bold red]Error saving markdown file: {str(e)}[/bold red]")
            return None
    
    def save_as_pdf(self, markdown_path: Path, output_dir: Path, keyword: str) -> Path:
        """Convert markdown to PDF and save."""
        if not markdown_path or not markdown_path.exists():
            console.print("[bold red]Markdown file not found.[/bold red]")
            return None
        
        # Sanitize keyword for use in filename
        safe_keyword = "".join(c if c.isalnum() or c in [' ', '-'] else '_' for c in keyword)
        safe_keyword = safe_keyword.replace(' ', '_').lower()
        
        # Create file path
        pdf_path = output_dir / f"{safe_keyword}.pdf"
        
        try:
            # Read markdown content
            with open(markdown_path, "r", encoding="utf-8") as f:
                markdown_content = f.read()
            
            # Convert markdown to HTML
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{keyword}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1 {{ font-size: 24px; margin-top: 24px; }}
                    h2 {{ font-size: 20px; margin-top: 20px; }}
                    h3 {{ font-size: 16px; margin-top: 16px; }}
                    p {{ margin: 16px 0; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; }}
                    th {{ padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                {markdown_content}
            </body>
            </html>
            """
            
            # Save HTML to temporary file
            html_path = output_dir / f"{safe_keyword}_temp.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # Convert HTML to PDF
            options = {
                'page-size': 'A4',
                'margin-top': '20mm',
                'margin-right': '20mm',
                'margin-bottom': '20mm',
                'margin-left': '20mm',
                'encoding': 'UTF-8',
            }
            
            pdfkit.from_file(str(html_path), str(pdf_path), options=options)
            
            # Remove temporary HTML file
            html_path.unlink()
            
            console.print(f"[green]Content saved as PDF: {pdf_path}[/green]")
            return pdf_path
            
        except Exception as e:
            console.print(f"[bold red]Error saving PDF file: {str(e)}[/bold red]")
            console.print("[yellow]Note: PDF conversion requires wkhtmltopdf to be installed.[/yellow]")
            return None