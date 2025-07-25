import os
import re
from enum import Enum
from pathlib import Path
from typing import List, Tuple, Optional, Dict

class ParseState(Enum):
    SCANNING = "scanning"          # Looking for start of structure
    IN_STRUCTURE = "in_structure"  # Parsing structure lines
    IN_CODE_BLOCK = "in_code_block" # Inside markdown code block
    COMPLETE = "complete"          # Finished parsing

class FolderStructureParser:
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.state = ParseState.SCANNING
        self.structure_lines = []
        self.current_depth = 0
        self.root_folder = None
        self.in_markdown_block = False
        self.markdown_fence = None

        # Patterns for different structure elements
        self.tree_patterns = {
            'tree_line': re.compile(r'^[\s│]*[├└]──\s*(.+)$'),
            'continuation': re.compile(r'^[\s│]*│\s*$'),
            'root_folder': re.compile(r'^([^/\s]+)/$'),
            'markdown_start': re.compile(r'^```\s*(\w+)?'),
            'markdown_end': re.compile(r'^```\s*$'),
            'comment': re.compile(r'\s*#.*$'),
            'spaces_and_pipes': re.compile(r'^[\s│]*'),
        }

    def reset(self):
        """Reset parser state for new structure"""
        self.state = ParseState.SCANNING
        self.structure_lines = []
        self.current_depth = 0
        self.root_folder = None
        self.in_markdown_block = False
        self.markdown_fence = None

    def detect_structure_start(self, line: str) -> bool:
        """Detect if line indicates start of folder structure"""
        line = line.strip()

        # Check for markdown code block start
        markdown_match = self.tree_patterns['markdown_start'].match(line)
        if markdown_match:
            self.in_markdown_block = True
            self.markdown_fence = line
            return False

        # Check for root folder (ends with /)
        root_match = self.tree_patterns['root_folder'].match(line)
        if root_match:
            self.root_folder = root_match.group(1)
            return True

        # Check for tree structure line
        if self.tree_patterns['tree_line'].match(line):
            return True

        return False

    def detect_structure_end(self, line: str) -> bool:
        """Detect if line indicates end of folder structure"""
        line_stripped = line.strip()

        # End of markdown block
        if self.in_markdown_block and self.tree_patterns['markdown_end'].match(line_stripped):
            return True

        # Empty line or line that doesn't match structure patterns
        if not line_stripped:
            return True

        # Line that doesn't start with tree characters, spaces, or folder name
        if not (self.tree_patterns['tree_line'].match(line) or
                self.tree_patterns['continuation'].match(line) or
                self.tree_patterns['root_folder'].match(line_stripped)):
            return True

        return False

    def parse_line(self, line: str) -> Optional[Tuple[str, int, bool]]:
        """
        Parse a single line to extract file/folder info
        Returns: (name, depth, is_folder) or None if not a structure line
        """
        original_line = line
        line = line.rstrip()

        # Skip empty lines and continuation lines
        if not line.strip() or self.tree_patterns['continuation'].match(line):
            return None

        # Handle root folder
        root_match = self.tree_patterns['root_folder'].match(line.strip())
        if root_match:
            folder_name = root_match.group(1)
            return (folder_name, 0, True)

        # Handle tree structure lines
        tree_match = self.tree_patterns['tree_line'].match(line)
        if tree_match:
            # Calculate depth based on leading characters
            prefix = self.tree_patterns['spaces_and_pipes'].match(line).group(0)
            # Each level of nesting typically adds 4 characters (│   or ├── )
            depth = len(prefix) // 4 + 1

            # Extract name and remove comments
            name_with_comment = tree_match.group(1)
            name = self.tree_patterns['comment'].sub('', name_with_comment).strip()

            # Determine if it's a folder (ends with /)
            is_folder = name.endswith('/')
            if is_folder:
                name = name[:-1]  # Remove trailing slash

            return (name, depth, is_folder)

        return None

    def process_line(self, line: str) -> bool:
        """
        Process a single line through the state machine
        Returns: True if structure is complete, False if more lines needed
        """
        if self.state == ParseState.SCANNING:
            if self.detect_structure_start(line):
                self.state = ParseState.IN_CODE_BLOCK if self.in_markdown_block else ParseState.IN_STRUCTURE
                self.structure_lines.append(line)
            return False

        elif self.state in [ParseState.IN_STRUCTURE, ParseState.IN_CODE_BLOCK]:
            if self.detect_structure_end(line):
                self.state = ParseState.COMPLETE
                return True
            else:
                self.structure_lines.append(line)
                return False

        return True

    def parse_structure(self, lines: List[str]) -> List[Tuple[str, int, bool]]:
        """Parse collected structure lines into file/folder info"""
        parsed_items = []

        for line in self.structure_lines:
            parsed = self.parse_line(line)
            if parsed:
                parsed_items.append(parsed)

        return parsed_items

    def create_structure(self, structure_items: List[Tuple[str, int, bool]],
                        base_path: Optional[str] = None) -> List[str]:
        """
        Create the actual files and folders
        Returns: List of created paths
        """
        if base_path:
            self.base_path = Path(base_path)

        created_paths = []
        path_stack = [self.base_path]

        for name, depth, is_folder in structure_items:
            # Adjust path stack to current depth
            while len(path_stack) > depth + 1:
                path_stack.pop()

            # Create current path
            current_path = path_stack[-1] / name

            try:
                if is_folder:
                    current_path.mkdir(parents=True, exist_ok=True)
                    path_stack.append(current_path)
                    created_paths.append(f"📁 {current_path}")
                else:
                    # Ensure parent directory exists
                    current_path.parent.mkdir(parents=True, exist_ok=True)
                    # Create empty file
                    current_path.touch()
                    created_paths.append(f"📄 {current_path}")

            except Exception as e:
                created_paths.append(f"❌ Error creating {current_path}: {e}")

        return created_paths

    def parse_and_create(self, text: str, base_path: Optional[str] = None) -> Dict:
        """
        Complete workflow: parse text and create structure
        Returns: Dictionary with results and status
        """
        self.reset()
        lines = text.split('\n')

        # Process lines through state machine
        for i, line in enumerate(lines):
            if self.process_line(line):
                break

        if self.state != ParseState.COMPLETE and self.structure_lines:
            # Force completion if we have structure lines
            self.state = ParseState.COMPLETE

        if self.state != ParseState.COMPLETE:
            return {
                'success': False,
                'message': 'No valid folder structure found',
                'created_paths': []
            }

        # Parse the structure
        structure_items = self.parse_structure(self.structure_lines)

        if not structure_items:
            return {
                'success': False,
                'message': 'No valid structure items found',
                'created_paths': []
            }

        # Create the structure
        created_paths = self.create_structure(structure_items, base_path)

        return {
            'success': True,
            'message': f'Successfully created {len(structure_items)} items',
            'structure_items': structure_items,
            'created_paths': created_paths,
            'root_folder': self.root_folder
        }

# Example usage and testing
def demo():
    """Demonstrate the parser with example structures"""

    # Example 1: Tree structure format
    structure1 = """
rag-system/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI main application
│   ├── config.py              # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py        # Document models
│   │   └── chat.py           # Chat models
│   └── static/
│       ├── index.html        # Simple UI
│       ├── style.css
│       └── script.js
├── data/
│   ├── uploads/              # Uploaded documents
│   └── vector_db/            # Chroma database
├── requirements.txt
├── docker-compose.yml
└── README.md
    """

    # Example 2: Markdown code block format
    structure2 = """
## Project Structure
```
conversation_analyzer/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── base_classes.py
│   │   └── config.py
│   └── web/
│       ├── __init__.py
│       └── app.py
├── requirements.txt
└── main.py
```
    """

    parser = FolderStructureParser()

    print("=== Demo 1: Tree Structure ===")
    result1 = parser.parse_and_create(structure1, "./demo1")
    print(f"Success: {result1['success']}")
    print(f"Message: {result1['message']}")
    if len(result1['created_paths']) > 5:
        print(f"  ... and {len(result1['created_paths']) - 5} more")

    print("\n=== Demo 2: Markdown Block ===")
    result2 = parser.parse_and_create(structure2, "./demo2")
    print(f"Success: {result2['success']}")
    print(f"Message: {result2['message']}")


if __name__ == "__main__":
    demo()
