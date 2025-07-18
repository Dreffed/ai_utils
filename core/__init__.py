"""
Core module for code analyzer.
"""

from .models import CodeBlock, ProjectStats
from .utils import (
    is_likely_filepath,
    read_from_clipboard,
    read_from_file,
    normalize_content,
    CLIPBOARD_AVAILABLE
)

__all__ = [
    'CodeBlock',
    'ProjectStats',
    'is_likely_filepath',
    'read_from_clipboard',
    'read_from_file',
    'normalize_content',
    'CLIPBOARD_AVAILABLE'
]
