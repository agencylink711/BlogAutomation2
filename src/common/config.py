#!/usr/bin/env python3
"""
Common configuration settings for all modules.
"""
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class BrowserConfig:
    """Browser-related configuration settings."""
    headless: bool = False
    timeout: int = 60000  # Default timeout in milliseconds
    screenshot_dir: Path = Path("screenshots")
    wait_time: int = 3  # Default wait time in seconds


@dataclass
class ContentGeneratorConfig:
    """Configuration for content generation module."""
    claude_url: str = "https://claude.ai/project/434990a3-f303-4f35-85cd-490c991139d4"
    user_data_dir: Path = Path("browser_data/claude")
    completed_dir: Path = Path("content/completed")
    keywords_file: Path = Path("content/keywords/keywords.txt")
    processed_file: Path = Path("content/keywords/processed_keywords.txt")


@dataclass
class AIDetectorConfig:
    """Configuration for AI detection module."""
    zerogpt_url: str = "https://www.zerogpt.com/"
    user_data_dir: Path = Path("browser_data/zerogpt")
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    max_ai_percentage: float = 2.0  # Maximum acceptable AI percentage


class Config:
    """Global configuration container."""
    
    def __init__(self):
        """Initialize configuration with default values."""
        self.browser = BrowserConfig()
        self.content_generator = ContentGeneratorConfig()
        self.ai_detector = AIDetectorConfig()
        
        # Create required directories
        for path in [
            self.browser.screenshot_dir,
            self.content_generator.user_data_dir,
            self.content_generator.completed_dir,
            self.ai_detector.user_data_dir
        ]:
            path.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "browser": self.browser.__dict__,
            "content_generator": self.content_generator.__dict__,
            "ai_detector": self.ai_detector.__dict__
        }


# Global configuration instance
config = Config()