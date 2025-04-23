#!/usr/bin/env python3
"""
Common utility functions shared across modules.
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dict containing the parsed JSON data, or None if loading fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file {file_path}: {str(e)}")
        return None


def save_json_file(data: Dict[str, Any], file_path: Path) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        data: Dictionary to save as JSON
        file_path: Path where to save the file
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving JSON file {file_path}: {str(e)}")
        return False


def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
        
    Returns:
        bool: True if directory exists or was created, False on error
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {str(e)}")
        return False


def clean_filename(filename: str) -> str:
    """
    Clean a filename to remove invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Cleaned filename safe for file system use
    """
    # Replace invalid characters with underscores
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()