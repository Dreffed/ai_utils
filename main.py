#!/usr/bin/env python3
"""
Code Output Analyzer & Project Generator - Main Runner

This script provides the main interface for the code analyzer tool.
"""

import os
import sys
from pathlib import Path

from analyzer import CodeAnalyzer
from core.utils import read_from_clipboard, read_from_file, CLIPBOARD_AVAILABLE


def main():
    """Main function to run the code analyzer."""
    print("🔍 Code Output Analyzer & Project Generator")
    print("=" * 50)

    analyzer = CodeAnalyzer()

    # Step 1: Get input
    print("\n📥 INPUT OPTIONS:")
    print("1. Read from file path")
    if CLIPBOARD_AVAILABLE:
        print("2. Read from clipboard")

    while True:
        choice = input("\nChoose option (1" + ("/2" if CLIPBOARD_AVAILABLE else "") + "): ").strip()

        if choice == "1":
            file_path = input("Enter file path: ").strip().strip('"').strip("'")
            if not os.path.exists(file_path):
                print("❌ File not found. Please try again.")
                continue
            try:
                content = read_from_file(file_path)
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        elif choice == "2" and CLIPBOARD_AVAILABLE:
            try:
                content = read_from_clipboard()
                if not content.strip():
                    print("❌ Clipboard is empty. Please copy some content first.")
                    continue
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        else:
            print("❌ Invalid choice. Please try again.")

    # Step 2: Analyze content
    print("\n🔍 Analyzing content...")
    analyzer.extract_code_blocks(content)
    analyzer.analyze_structure()

    if not analyzer.code_blocks:
        print("❌ No code blocks found in the input!")
        return

    # Step 3: Display analysis
    analyzer.display_analysis()

    # Step 4: Confirm creation
    create = input("\n❓ Create project structure? (y/n): ").strip().lower()
    if create != 'y':
        print("Operation cancelled.")
        return

    # Step 5: Get output directory
    while True:
        output_dir = input("\n📁 Enter output directory path: ").strip().strip('"').strip("'")
        if not output_dir:
            print("❌ Please enter a valid path.")
            continue

        output_path = Path(output_dir)
        if output_path.exists() and any(output_path.iterdir()):
            overwrite = input(f"⚠️  Directory exists and is not empty. Continue? (y/n): ").strip().lower()
            if overwrite != 'y':
                continue
        break

    # Step 6: Create project
    try:
        analyzer.create_project(output_dir)
    except Exception as e:
        print(f"❌ Error creating project: {e}")
        return

    # Step 7: Initialize git
    git_init = input("\n❓ Initialize git repository? (y/n): ").strip().lower()
    if git_init == 'y':
        analyzer.init_git_repo(output_dir)

    print(f"\n🎉 Project creation completed!")
    print(f"📁 Location: {Path(output_dir).absolute()}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
