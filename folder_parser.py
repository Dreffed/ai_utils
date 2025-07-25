# Example: Integrating the FolderStructureParser into an existing linear parser

import logging
from pathlib import Path
from folder_structure_parser import FolderStructureParser, ParseState

# Import from the main parser module

class DocumentParser:
    """Example of how to integrate the folder structure parser into your existing app"""

    def __init__(self):
        self.folder_parser = FolderStructureParser()
        self.current_section = None
        self.structures_found = []
        self.logger = None

    def parse_document(self, text: str, create_structures: bool = True, base_path: str = "./output", logger=None):
        """
        Main parser that processes text line by line and detects folder structures
        """
        self.logger = logger or self._get_default_logger()

        lines = text.split('\n')
        current_line = 0

        self.logger.info(f"Starting to parse {len(lines)} lines")

        while current_line < len(lines):
            line = lines[current_line]

            # Your existing parsing logic here...
            if self.is_header(line):
                self.current_section = self.extract_header(line)
                self.logger.info(f"Found section: {self.current_section}")

            # Check for folder structure
            elif self.folder_parser.state == ParseState.SCANNING:
                # Try to start parsing a folder structure
                if self.folder_parser.process_line(line):
                    # Structure complete immediately (single line case)
                    self.handle_completed_structure(create_structures, base_path)

            elif self.folder_parser.state in [ParseState.IN_STRUCTURE, ParseState.IN_CODE_BLOCK]:
                # Continue parsing the structure
                if self.folder_parser.process_line(line):
                    # Structure parsing complete
                    self.handle_completed_structure(create_structures, base_path)

            current_line += 1

        # Handle case where structure was at end of document
        if (self.folder_parser.state in [ParseState.IN_STRUCTURE, ParseState.IN_CODE_BLOCK]
            and self.folder_parser.structure_lines):
            self.folder_parser.state = ParseState.COMPLETE
            self.handle_completed_structure(create_structures, base_path)

        self.logger.info(f"Parsing complete. Found {len(self.structures_found)} structures")
        return self.structures_found

    def handle_completed_structure(self, create_structures: bool, base_path: str):
        """Handle when a folder structure parsing is complete"""
        structure_items = self.folder_parser.parse_structure(self.folder_parser.structure_lines)

        if structure_items:
            self.logger.info(f"Parsed structure with {len(structure_items)} items")

            structure_info = {
                'section': self.current_section,
                'root_folder': self.folder_parser.root_folder,
                'items': structure_items,
                'created': False,
                'created_paths': []
            }

            if create_structures:
                # Determine output path
                if self.folder_parser.root_folder:
                    output_path = f"{base_path}/{self.folder_parser.root_folder}"
                else:
                    output_path = f"{base_path}/structure_{len(self.structures_found) + 1}"

                self.logger.info(f"Creating structure at: {output_path}")

                try:
                    # Create the structure
                    created_paths = self.folder_parser.create_structure(structure_items, output_path)
                    structure_info['created'] = True
                    structure_info['created_paths'] = created_paths
                    structure_info['output_path'] = output_path

                    self.logger.info(f"✅ Successfully created structure: {self.folder_parser.root_folder or 'unnamed'}")
                    self.logger.info(f"   Location: {output_path}")
                    self.logger.info(f"   Items created: {len(structure_items)}")

                except Exception as e:
                    self.logger.error(f"❌ Failed to create structure: {e}")
                    structure_info['error'] = str(e)
            else:
                self.logger.info(f"🧪 Test mode - structure '{self.folder_parser.root_folder or 'unnamed'}' parsed but not created")

            self.structures_found.append(structure_info)
        else:
            self.logger.warning("No valid structure items found in parsed lines")

        # Reset for next structure
        self.folder_parser.reset()

    def _get_default_logger(self):
        """Create a default logger if none provided"""
        import logging
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def is_header(self, line: str) -> bool:
        """Example method to detect document headers"""
        return line.strip().startswith('#') or line.strip().startswith('##')

    def extract_header(self, line: str) -> str:
        """Example method to extract header text"""
        return line.strip().lstrip('#').strip()

# Enhanced command-line interface with logging
def main():
    import argparse
    import sys
    import logging
    import urllib.request
    import urllib.parse
    from datetime import datetime

    parser = argparse.ArgumentParser(description='Parse documents and create folder structures')
    parser.add_argument('--file', '-f', required=True, help='File path or URL to parse')
    parser.add_argument('--output', '-o', default='./output', help='Base path to create structure under')
    parser.add_argument('--log', '-l', help='Log file to write to')
    parser.add_argument('--test', '-t', action='store_true', default=False,
                       help='Test mode: output to log and console only, don\'t create files')

    args = parser.parse_args()

    # Setup logging
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    log_level = logging.INFO

    # Configure logging handlers
    handlers = [logging.StreamHandler(sys.stdout)]  # Always log to console

    if args.log:
        try:
            # Ensure log directory exists
            log_path = Path(args.log)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(args.log, mode='a'))
        except Exception as e:
            print(f"Warning: Could not setup log file '{args.log}': {e}")

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers,
        force=True
    )

    logger = logging.getLogger(__name__)

    # Log startup information
    logger.info("="*60)
    logger.info("Folder Structure Parser - Starting")
    logger.info(f"File: {args.file}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Test mode: {args.test}")
    logger.info(f"Log file: {args.log or 'None'}")
    logger.info("="*60)

    # Read the input file/URL
    try:
        content = read_file_or_url(args.file, logger)
    except Exception as e:
        logger.error(f"Failed to read input: {e}")
        sys.exit(1)

    logger.info(f"Successfully read input ({len(content)} characters)")

    # Parse the document
    doc_parser = DocumentParser()
    try:
        structures = doc_parser.parse_document(content,
                                             create_structures=not args.test,
                                             base_path=args.output,
                                             logger=logger)
    except Exception as e:
        logger.error(f"Parsing failed: {e}")
        sys.exit(1)

    # Report results
    logger.info("="*40)
    logger.info("PARSING RESULTS")
    logger.info("="*40)
    logger.info(f"Found {len(structures)} folder structure(s)")

    for i, struct in enumerate(structures, 1):
        logger.info(f"\n📁 Structure {i}:")
        logger.info(f"   Section: {struct['section'] or 'None'}")
        logger.info(f"   Root: {struct['root_folder'] or 'unnamed'}")
        logger.info(f"   Items: {len(struct['items'])}")

        # Log detailed structure items in test mode
        if args.test:
            logger.info("   Structure items:")
            for name, depth, is_folder in struct['items']:
                indent = "  " * (depth + 2)
                icon = "📁" if is_folder else "📄"
                logger.info(f"   {indent}{icon} {name}")

        if struct['created']:
            logger.info(f"   ✅ Created at: {struct['output_path']}")
            logger.info(f"   📄 Files/folders created: {len(struct['created_paths'])}")

            # Log first few created paths
            for path in struct['created_paths'][:5]:
                logger.info(f"     {path}")
            if len(struct['created_paths']) > 5:
                logger.info(f"     ... and {len(struct['created_paths']) - 5} more")

        elif args.test:
            logger.info(f"   🧪 Test mode - structure not created")
        else:
            logger.info(f"   ❌ Creation failed or skipped")

    if not structures:
        logger.warning("No folder structures found in the input")

    logger.info("="*40)
    logger.info("Processing complete")
    logger.info("="*40)

def read_file_or_url(file_path: str, logger: logging.Logger) -> str:
    """Read content from file path or URL"""

    # Check if it's a URL
    if file_path.startswith(('http://', 'https://')):
        logger.info(f"Reading from URL: {file_path}")
        try:
            with urllib.request.urlopen(file_path) as response:
                content = response.read().decode('utf-8')
            return content
        except Exception as e:
            raise Exception(f"Failed to read URL '{file_path}': {e}")

    # Treat as local file path
    else:
        logger.info(f"Reading from file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            raise Exception(f"File '{file_path}' not found")
        except Exception as e:
            raise Exception(f"Error reading file '{file_path}': {e}")

# Example usage as a module
def parse_text_for_structures(text: str, create: bool = True, output_dir: str = "./output", logger=None):
    """
    Simple function to parse text and optionally create folder structures

    Args:
        text: Text containing folder structures
        create: Whether to actually create files/folders
        output_dir: Base directory for output
        logger: Optional logger instance

    Returns:
        List of found structures with creation status
    """
    parser = DocumentParser()
    return parser.parse_document(text, create, output_dir, logger)

# Usage Examples
"""
Command Line Usage:

# Basic usage - parse local file
python integration_example.py --file document.md --output ./my_projects

# Parse from URL with logging
python integration_example.py --file https://raw.githubusercontent.com/user/repo/main/README.md --output ./projects --log ./logs/parser.log

# Test mode - parse and log but don't create files
python integration_example.py --file document.md --output ./test --log ./test.log --test

# Full example with all options
python integration_example.py \\
    --file https://example.com/project-structure.md \\
    --output ./output/projects \\
    --log ./logs/structure_parser.log \\
    --test

Module Usage:

import logging
from integration_example import parse_text_for_structures, read_file_or_url

# Setup logging
logger = logging.getLogger('my_app')
logger.setLevel(logging.INFO)

# Parse from file
with open('structure.md', 'r') as f:
    content = f.read()

results = parse_text_for_structures(content,
                                  create=True,
                                  output_dir='./output',
                                  logger=logger)

# Parse from URL
content = read_file_or_url('https://example.com/structure.md', logger)
results = parse_text_for_structures(content, create=False, logger=logger)  # Test mode
"""

if __name__ == "__main__":
    main()

# Quick test with sample data
def quick_test():
    import logging

    # Setup simple logging for test
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    logger = logging.getLogger('test')

    sample_text = """
# Project Setup Guide

Here's the folder structure for the new project:

my-project/
├── src/
│   ├── __init__.py
│   ├── main.py
│   └── utils/
│       └── helpers.py
├── tests/
│   └── test_main.py
└── README.md

## Another Section

And here's another structure:

```
api-service/
├── app/
│   ├── __init__.py
│   └── routes.py
└── requirements.txt
```

That's all for now.
    """

    logger.info("=== Quick Test ===")
    results = parse_text_for_structures(sample_text, create=True, output_dir="./test_output", logger=logger)

    for i, result in enumerate(results, 1):
        logger.info(f"\nStructure {i}: {result['root_folder']}")
        logger.info(f"  Items: {len(result['items'])}")
        if result['created']:
            logger.info(f"  Created: ✅")
            for path in result['created_paths'][:3]:  # Show first 3
                logger.info(f"    {path}")
        else:
            logger.info(f"  Created: ❌")
if __name__ == "__main__":
    # Uncomment to run quick test
    # quick_test()
    main()