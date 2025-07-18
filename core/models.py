"""
Data models for the code analyzer.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class CodeBlock:
    """Represents a code block with language, path, and content."""
    language: str
    path: Optional[str]
    content: str
    line_count: int
    is_artifact: bool = False


@dataclass
class ProjectStats:
    """Statistics about the analyzed project."""
    total_files: int
    total_lines: int
    languages: Dict[str, int]
    folders: List[str]
    artifacts: List[str]
