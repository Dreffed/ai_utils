"""
Code Output Analyzer & Project Generator

A tool that analyzes code output files and generates actual project structures.
"""

from .analyzer import CodeAnalyzer
from .core import CodeBlock, ProjectStats, CLIPBOARD_AVAILABLE

__version__ = "1.0.0"
__author__ = "AI Assistant"

__all__ = [
    'CodeAnalyzer',
    'CodeBlock',
    'ProjectStats',
    'CLIPBOARD_AVAILABLE'
]
