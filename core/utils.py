"""
Utility functions for the code analyzer.
"""

import re
import platform
from typing import Optional

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False


def is_likely_filepath(text: str) -> bool:
    """Determine if text looks like a file path."""
    if not text:
        return False

    # Check for common file path indicators
    file_indicators = [
        '/' in text,  # Unix path separator
        '\\' in text,  # Windows path separator
        '.' in text and not text.startswith('.') and not text.endswith('.'),  # Has extension
        text.endswith(('.py', '.js', '.html', '.css', '.txt', '.md', '.yaml', '.yml', '.json', '.xml')),
        text.startswith(('src/', 'lib/', 'app/', 'components/', 'utils/', 'config/')),
        re.match(r'^[a-zA-Z_][a-zA-Z0-9_.-]*\.[a-zA-Z0-9]+$', text) is not None  # filename.ext pattern
    ]

    return any(file_indicators)


def read_from_clipboard() -> str:
    """Read content from clipboard."""
    if not CLIPBOARD_AVAILABLE:
        raise RuntimeError("pyperclip not installed")
    return pyperclip.paste()


def read_from_file(file_path: str) -> str:
    """Read content from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Error reading file: {e}")


def normalize_content(content: str) -> str:
    """Normalize line endings in content."""
    return content.replace('\r\n', '\n').replace('\r', '\n')


def is_duplicate_content(content: str, existing_blocks: list) -> bool:
    """Check if content is already in existing blocks."""
    content_hash = hash(content.strip())
    for block in existing_blocks:
        if hash(block.content.strip()) == content_hash:
            return True
    return False


def get_file_extension_for_language(language: str) -> str:
    """Get appropriate file extension for a programming language."""
    extension_map = {
        'python': 'py',
        'javascript': 'js',
        'html': 'html',
        'css': 'css',
        'yaml': 'yaml',
        'json': 'json',
        'bash': 'sh',
        'shell': 'sh',
        'markdown': 'md',
        'xml': 'xml',
        'sql': 'sql',
        'dockerfile': 'dockerfile',
        'text': 'txt'
    }
    return extension_map.get(language.lower(), 'txt')


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"
