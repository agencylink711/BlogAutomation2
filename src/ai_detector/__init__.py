"""AI detection module for checking generated content."""
from .zerogpt_client import ZeroGPTClient
from .main import main

__all__ = ['ZeroGPTClient', 'main']