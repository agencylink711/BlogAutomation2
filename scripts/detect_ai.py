#!/usr/bin/env python3
"""
Entry point script for AI content detection and refinement using ZeroGPT.
"""
import sys
import asyncio
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from ai_detector.main import main as detect_ai

if __name__ == "__main__":
    asyncio.run(detect_ai())