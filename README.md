# Code Output Analyzer - Modular Version

A modular Python tool that analyzes code output files and generates actual project structures.

## 📁 Project Structure

``` bash
code_analyzer/
├── __init__.py              # Main package init
├── analyzer.py              # Main CodeAnalyzer class
├── main.py                  # Runner script
├── requirements.txt         # Dependencies
├── core/
│   ├── __init__.py         # Core module init
│   ├── models.py           # Data classes (CodeBlock, ProjectStats)
│   └── utils.py            # Utility functions
└── README.md               # This file
```

## 🚀 Quick Start

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the analyzer**:

   ```bash
   python main.py
   ```

3. **Follow the prompts**:
   - Choose input method (file or clipboard)
   - Review analysis results
   - Specify output directory
   - Optionally initialize git repository

## 🔧 Features

- ✅ **Modular Architecture**: Clean separation of concerns
- ✅ **Multiple Input Methods**: File path or clipboard
- ✅ **Smart File Detection**: Distinguishes files from sections
- ✅ **Flexible Parsing**: Handles various markdown formats
- ✅ **Project Generation**: Creates proper folder structure
- ✅ **Git Integration**: Optional repository initialization
- ✅ **Error Handling**: Robust error handling and validation

## 📋 Module Breakdown

### `core/models.py`

- `CodeBlock`: Represents extracted code with metadata
- `ProjectStats`: Statistics about the analyzed project

### `core/utils.py`

- File path detection logic
- Clipboard/file reading functions
- Content normalization utilities
- Language extension mapping

### `analyzer.py`

- `CodeAnalyzer`: Main analysis and extraction class
- Header-style markdown parsing (`## filename.ext`)
- Inline-style code block parsing (` ```python filename.py`)
- Project structure creation

### `main.py`

- Command-line interface
- User interaction and input validation
- Orchestrates the analysis workflow

## 🐛 Bug Fixes Applied

1. **Regex Pattern Fixes**:
   - ✅ Fixed incomplete file detection regex
   - ✅ Added flexible code block end detection (`^```\s*$`)
   - ✅ Proper boolean conversion for `re.match()` results

2. **Content Parsing**:
   - ✅ Line ending normalization
   - ✅ Duplicate content detection
   - ✅ Proper file vs. section classification

3. **Error Handling**:
   - ✅ Graceful handling of missing dependencies
   - ✅ File access error handling
   - ✅ Git command error handling

## 🎯 Usage Examples

### Basic Usage

```bash
python main.py
# Follow interactive prompts
```

### Programmatic Usage

```python
from analyzer import CodeAnalyzer
from core.utils import read_from_file

# Create analyzer
analyzer = CodeAnalyzer()

# Load and analyze content
content = read_from_file('your_code_output.txt')
analyzer.extract_code_blocks(content)
analyzer.analyze_structure()

# Display results
analyzer.display_analysis()

# Create project
analyzer.create_project('./output_directory')
```

## 📊 Supported Formats

The analyzer detects and handles:

- **Header Format**: `## filename.ext` followed by code blocks
- **Inline Format**: ` ```language filename.ext`
- **Languages**: Python, JavaScript, HTML, CSS, YAML, JSON, Bash, etc.
- **Paths**: Both relative and absolute file paths
- **Artifacts**: Code blocks without specific file paths

## 🔄 Migration from Single File

If you have the previous single-file version:

1. Create the directory structure above
2. Copy each module into its respective file
3. Update imports to use the modular structure
4. Run `python main.py` instead of the single script

## 🤝 Contributing

The modular structure makes it easy to:

- Add new parsing methods in `analyzer.py`
- Extend utility functions in `core/utils.py`
- Add new data models in `core/models.py`
- Enhance the CLI in `main.py`

## 📝 License

This project is for educational and personal use.
