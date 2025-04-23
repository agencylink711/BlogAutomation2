#!/usr/bin/env python3
"""
Entry point script for blog content generation using Claude AI.
"""
import sys
import asyncio
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from content_generator.main import main as generate_content

if __name__ == "__main__":
    asyncio.run(generate_content())