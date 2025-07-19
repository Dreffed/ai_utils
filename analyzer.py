"""
Main CodeAnalyzer class for extracting and analyzing code blocks.
Fixed version with proper nested code block handling.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

from core.models import CodeBlock, ProjectStats
from core.utils import (
    is_likely_filepath, normalize_content, is_duplicate_content,
    get_file_extension_for_language
)


class CodeAnalyzer:
    """Analyzes code output and extracts project structure."""

    def __init__(self):
        self.code_blocks: List[CodeBlock] = []
        self.folder_structure: Dict[str, List[str]] = defaultdict(list)

    def debug_extraction(self, content: str, verbose: bool = False) -> None:
        """Debug the extraction process using state machine approach."""
        normalized_content = normalize_content(content)
        lines = normalized_content.split('\n')

        header_pattern = re.compile(r'^## (.+)')
        code_block_pattern = re.compile(r'^```(.*)$')

        print("🔍 DEBUG: State Machine Extraction")
        print("-" * 50)

        state = "LOOKING_FOR_HEADER"
        current_filename = None
        nesting_level = 0

        for i, line in enumerate(lines):
            line_num = i + 1

            # Show state changes and important lines
            if state == "LOOKING_FOR_HEADER":
                header_match = header_pattern.match(line)
                code_match = code_block_pattern.match(line)

                if header_match:
                    current_filename = header_match.group(1).strip()
                    print(f"Line {line_num:3d}: {line}")
                    print(f"         -> STATE: Found header '{current_filename}'")
                elif current_filename and code_match:
                    state = "IN_CODE_BLOCK"
                    nesting_level = 1
                    lang = code_match.group(1).strip() if code_match.group(1) else 'text'
                    print(f"Line {line_num:3d}: {line}")
                    print(f"         -> STATE: Entering code block (language: {lang}, nesting: {nesting_level})")
                elif verbose:
                    print(f"Line {line_num:3d}: {line}")

            elif state == "IN_CODE_BLOCK":
                code_match = code_block_pattern.match(line)
                if code_match:
                    # This is a ``` line - could be start or end of nested block
                    lang_or_empty = code_match.group(1).strip()

                    if lang_or_empty:
                        # This starts a new nested block
                        nesting_level += 1
                        print(f"Line {line_num:3d}: {line}")
                        print(f"         -> NESTING: Entering nested block (level: {nesting_level})")
                    else:
                        # This ends a block
                        nesting_level -= 1
                        print(f"Line {line_num:3d}: {line}")
                        print(f"         -> NESTING: Exiting block (level: {nesting_level})")

                        if nesting_level == 0:
                            state = "LOOKING_FOR_HEADER"
                            print(f"         -> STATE: Exiting main code block, processing '{current_filename}'")
                            current_filename = None
                elif verbose:
                    print(f"Line {line_num:3d}: {line}")

        print("-" * 50)

    def extract_code_blocks(self, content: str, debug: bool = False) -> None:
        """Extract code blocks from the content using state machine approach."""
        self.code_blocks.clear()

        # Debug extraction if requested
        if debug:
            self.debug_extraction(content)

        # Normalize line endings
        normalized_content = normalize_content(content)

        # Method 1: Try markdown header + code block pattern (## filename.ext)
        self._extract_header_style_blocks(normalized_content)

        # Method 2: Try traditional inline file path pattern (```python filename.py)
        # self._extract_inline_style_blocks(normalized_content)

    def _extract_header_style_blocks(self, content: str) -> None:
        """Extract code blocks that follow markdown headers using state machine approach with nesting support."""
        lines = content.split('\n')

        # Regex patterns
        header_pattern = re.compile(r'^## (.+)')
        code_block_pattern = re.compile(r'^```(.*)$')

        # State machine variables
        state = "LOOKING_FOR_HEADER"  # States: LOOKING_FOR_HEADER, IN_CODE_BLOCK
        current_filename = None
        current_language = None
        current_content_lines = []
        nesting_level = 0

        for i, line in enumerate(lines):
            if state == "LOOKING_FOR_HEADER":
                # State 1: Looking for headers
                header_match = header_pattern.match(line)
                if header_match:
                    current_filename = header_match.group(1).strip()
                    # Don't change state yet, wait for code block start
                    continue

                # Check for code block start (only if we have a filename)
                if current_filename:
                    code_match = code_block_pattern.match(line)
                    if code_match:
                        # Extract language from the opening line
                        lang_and_extra = code_match.group(1).strip() if code_match.group(1) else ''
                        if lang_and_extra:
                            current_language = lang_and_extra.split()[0]
                        else:
                            current_language = 'text'

                        # Change to code block state
                        state = "IN_CODE_BLOCK"
                        current_content_lines = []
                        nesting_level = 1  # We're now inside the main code block
                        continue

            elif state == "IN_CODE_BLOCK":
                # State 2: Inside code block - handle nesting
                code_match = code_block_pattern.match(line)

                if code_match:
                    # This is a ``` line
                    lang_or_empty = code_match.group(1).strip()

                    if lang_or_empty:
                        # This starts a new nested code block
                        nesting_level += 1
                        current_content_lines.append(line)
                    else:
                        # This ends a code block
                        nesting_level -= 1

                        if nesting_level == 0:
                            # We've reached the end of the main code block
                            if current_content_lines and current_filename:
                                code_content = '\n'.join(current_content_lines)

                                # Determine if this is a file path or section header
                                is_file = is_likely_filepath(current_filename)

                                # Only add if not duplicate
                                if not is_duplicate_content(code_content, self.code_blocks):
                                    block = CodeBlock(
                                        language=current_language,
                                        path=current_filename if is_file else None,
                                        content=code_content,
                                        line_count=len(current_content_lines),
                                        is_artifact=not is_file
                                    )
                                    self.code_blocks.append(block)

                            # Reset state
                            state = "LOOKING_FOR_HEADER"
                            current_filename = None
                            current_language = None
                            current_content_lines = []
                        else:
                            # This closes a nested block, add it to content
                            current_content_lines.append(line)
                else:
                    # Regular content line inside code block
                    current_content_lines.append(line)

    def _extract_inline_style_blocks(self, content: str) -> None:
        """Extract code blocks with inline file paths (```python filename.py)."""
        # This method would need similar nesting logic if used
        # For now, keeping the original implementation
        pattern = r'```(\w+)(?:\s+(.+?))?\n(.*?)```'
        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            language = match.group(1)
            path_info = match.group(2)
            code_content = match.group(3).strip()

            # Extract file path if present
            file_path = None
            is_artifact = False

            if path_info:
                # Check if it's a file path or artifact description
                if is_likely_filepath(path_info):
                    file_path = path_info.strip()
                else:
                    is_artifact = True

            # Count lines
            line_count = len(code_content.split('\n'))

            # Only add if we don't already have this content
            if not is_duplicate_content(code_content, self.code_blocks):
                block = CodeBlock(
                    language=language,
                    path=file_path,
                    content=code_content,
                    line_count=line_count,
                    is_artifact=is_artifact
                )
                self.code_blocks.append(block)

    def analyze_structure(self) -> None:
        """Analyze the folder structure from code blocks."""
        self.folder_structure.clear()

        for block in self.code_blocks:
            if block.path:
                # Normalize path separators
                normalized_path = block.path.replace('\\', '/')

                # Split into directory and filename
                if '/' in normalized_path:
                    directory = '/'.join(normalized_path.split('/')[:-1])
                    filename = normalized_path.split('/')[-1]
                else:
                    directory = '.'
                    filename = normalized_path

                self.folder_structure[directory].append(filename)

    def get_statistics(self) -> ProjectStats:
        """Generate statistics about the analyzed project."""
        total_files = len([b for b in self.code_blocks if b.path])
        total_lines = sum(b.line_count for b in self.code_blocks)

        languages = defaultdict(int)
        for block in self.code_blocks:
            languages[block.language] += 1

        folders = list(self.folder_structure.keys())
        artifacts = []

        artifact_count = 1
        for block in self.code_blocks:
            if block.is_artifact or not block.path:
                artifacts.append(f"artifact_{artifact_count}_{block.language}")
                artifact_count += 1

        return ProjectStats(
            total_files=total_files,
            total_lines=total_lines,
            languages=dict(languages),
            folders=folders,
            artifacts=artifacts
        )

    def display_analysis(self) -> None:
        """Display analysis results with line counts."""
        stats = self.get_statistics()

        print("\n" + "="*60)
        print("CODE OUTPUT ANALYSIS RESULTS")
        print("="*60)

        print(f"\n📊 OVERVIEW:")
        print(f"   Total Files: {stats.total_files}")
        print(f"   Total Lines: {stats.total_lines}")
        print(f"   Code Blocks: {len(self.code_blocks)}")

        print(f"\n🗂️  FOLDER STRUCTURE:")
        for folder, files in self.folder_structure.items():
            print(f"   📁 {folder}/")
            for file in files:
                # Find the corresponding block to get line count
                line_count = 0
                for block in self.code_blocks:
                    if block.path and block.path.endswith(file):
                        line_count = block.line_count
                        break
                print(f"      📄 {file} ({line_count} lines)")

        print(f"\n💻 LANGUAGES:")
        for lang, count in stats.languages.items():
            # Calculate total lines for this language
            lang_lines = sum(block.line_count for block in self.code_blocks if block.language == lang)
            print(f"   {lang}: {count} files ({lang_lines} lines)")

        if stats.artifacts:
            print(f"\n🎨 ARTIFACTS:")
            for i, artifact in enumerate(stats.artifacts):
                # Find line count for this artifact
                artifact_blocks = [b for b in self.code_blocks if b.is_artifact or not b.path]
                if i < len(artifact_blocks):
                    line_count = artifact_blocks[i].line_count
                    print(f"   ✨ {artifact} ({line_count} lines)")
                else:
                    print(f"   ✨ {artifact}")

        print("\n" + "="*60)

    def create_project(self, output_dir: str) -> None:
        """Create the actual project structure."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\n🚀 Creating project in: {output_path.absolute()}")

        # Create folders
        for folder in self.folder_structure.keys():
            if folder != '.':
                folder_path = output_path / folder
                folder_path.mkdir(parents=True, exist_ok=True)
                print(f"   📁 Created folder: {folder}")

        # Create files
        files_created = 0
        artifact_count = 1

        for block in self.code_blocks:
            if block.path:
                file_path = output_path / block.path
                file_path.parent.mkdir(parents=True, exist_ok=True)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(block.content)

                print(f"   📄 Created file: {block.path}")
                files_created += 1
            elif block.is_artifact or not block.path:
                # Create artifacts or unidentified code blocks
                extension = get_file_extension_for_language(block.language)
                artifact_name = f"artifact_{artifact_count}.{extension}"
                file_path = output_path / artifact_name

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(block.content)

                print(f"   ✨ Created artifact: {artifact_name}")
                files_created += 1
                artifact_count += 1

        print(f"\n✅ Created {files_created} files successfully!")

    def init_git_repo(self, project_dir: str) -> None:
        """Initialize git repository and make first commit."""
        try:
            os.chdir(project_dir)

            # Check if git is available
            subprocess.run(['git', '--version'], check=True, capture_output=True)

            # Initialize repository
            print(f"\n🔧 Initializing git repository...")
            subprocess.run(['git', 'init'], check=True, capture_output=True)

            # Add all files
            subprocess.run(['git', 'add', '.'], check=True, capture_output=True)

            # Create first commit
            commit_message = "Initial commit: Generated from code output analysis"
            subprocess.run(['git', 'commit', '-m', commit_message], check=True, capture_output=True)

            print(f"   ✅ Git repository initialized")
            print(f"   ✅ First commit created: '{commit_message}'")

        except subprocess.CalledProcessError as e:
            print(f"   ❌ Git error: {e}")
        except FileNotFoundError:
            print(f"   ❌ Git not found. Please install git to use this feature.")
