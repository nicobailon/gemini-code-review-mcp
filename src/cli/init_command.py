#!/usr/bin/env python3
"""
CLI init command for scaffolding project structure.

This module provides the 'gemini-code-review init' command that helps users
set up their project with the recommended directory structure and configuration.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Optional

# Default templates for generated files
GITIGNORE_TEMPLATE = """# Gemini Code Review files
/code-review-*.md
/meta-prompt-*.md
/pr-review-*.md
/.env
/.env.local

# Task list work-in-progress files
/tasks/*.tmp
/tasks/*.bak

# Cache directory
/.gemini-cache/
"""

ENV_TEMPLATE = """# Gemini Code Review Configuration
# Copy this file to .env and fill in your API key

# Required: Your Google AI API key from https://makersuite.google.com/app/apikey
GOOGLE_AI_API_KEY=your-api-key-here

# Optional: Default temperature for AI model (0.0-2.0, default: 0.5)
# GEMINI_TEMPERATURE=0.5

# Optional: Default model to use
# GEMINI_MODEL=gemini-1.5-flash

# Optional: Enable caching for performance
# GEMINI_ENABLE_CACHE=true
"""

SAMPLE_TASK_LIST = """## Relevant Files

- `src/main.py` - Main application entry point
- `src/utils.py` - Utility functions
- `tests/test_main.py` - Unit tests for main module

### Notes

- Use `pytest` to run the test suite
- Follow PEP 8 style guidelines

## Tasks

- [ ] 1.0 Set up project structure
  - [ ] 1.1 Create main application module
  - [ ] 1.2 Set up testing framework
  - [ ] 1.3 Configure linting and formatting tools

- [ ] 2.0 Implement core functionality
  - [ ] 2.1 Design data models
  - [ ] 2.2 Implement business logic
  - [ ] 2.3 Add error handling

- [ ] 3.0 Testing and documentation
  - [ ] 3.1 Write unit tests
  - [ ] 3.2 Add integration tests
  - [ ] 3.3 Create user documentation
"""

CLAUDE_MD_TEMPLATE = """# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) and other AI assistants
when working with code in this repository.

## Project Overview

[Describe your project here - its purpose, main features, and target users]

## Architecture

[Describe the high-level architecture, main components, and how they interact]

## Development Guidelines

### Code Style
- [List your coding standards and conventions]
- [Specify any linting or formatting tools used]

### Testing
- [Describe your testing approach]
- [List test commands and coverage requirements]

### Git Workflow
- [Describe your branching strategy]
- [Commit message format]

## Key Directories

- `/src` - Main source code
- `/tests` - Test files
- `/docs` - Documentation
- `/tasks` - Task lists for development phases

## Dependencies

[List major dependencies and their purposes]

## Common Commands

```bash
# Install dependencies
npm install  # or pip install -r requirements.txt

# Run tests
npm test  # or pytest

# Start development server
npm run dev  # or python manage.py runserver
```

## Important Considerations

[List any security considerations, performance requirements, or other critical information]
"""

README_TEMPLATE = """# {project_name}

## Overview

This project uses Gemini Code Review for AI-powered code reviews.

## Getting Started

1. Install dependencies:
   ```bash
   pip install gemini-code-review-mcp
   ```

2. Set up your API key:
   - Copy `.env.example` to `.env`
   - Add your Google AI API key

3. Run a code review:
   ```bash
   generate-code-review
   ```

## Project Structure

```
{project_name}/
├── .env.example      # Example environment configuration
├── .gitignore        # Git ignore patterns
├── CLAUDE.md         # AI assistant guidance
├── README.md         # This file
├── tasks/            # Task lists for development
│   └── tasks-example.md
└── src/              # Source code directory
```

## Using Task-Driven Reviews

1. Create task lists in the `/tasks` directory
2. Run reviews with specific scopes:
   ```bash
   # Review recent work
   generate-code-review --scope recent_phase
   
   # Review specific phase
   generate-code-review --scope specific_phase --phase-number 1.0
   ```

## Documentation

For more information, see the [Gemini Code Review documentation](https://github.com/nicobailon/gemini-code-review-mcp).
"""


def create_directory(path: Path, verbose: bool = True) -> bool:
    """Create a directory if it doesn't exist."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        if verbose and not path.exists():
            print(f"✓ Created directory: {path}")
        return True
    except Exception as e:
        print(f"✗ Failed to create directory {path}: {e}", file=sys.stderr)
        return False


def write_file(
    path: Path, content: str, overwrite: bool = False, verbose: bool = True
) -> bool:
    """Write content to a file."""
    try:
        if path.exists() and not overwrite:
            if verbose:
                print(f"⚠ Skipping existing file: {path}")
            return True

        path.write_text(content, encoding="utf-8")
        if verbose:
            print(f"✓ Created file: {path}")
        return True
    except Exception as e:
        print(f"✗ Failed to create file {path}: {e}", file=sys.stderr)
        return False


def init_project(
    project_path: Path,
    project_name: Optional[str] = None,
    include_src: bool = True,
    include_tests: bool = True,
    include_claude_md: bool = True,
    force: bool = False,
    verbose: bool = True,
) -> bool:
    """
    Initialize a project with the recommended structure.

    Args:
        project_path: Path to the project directory
        project_name: Name of the project (defaults to directory name)
        include_src: Whether to create src directory
        include_tests: Whether to create tests directory
        include_claude_md: Whether to create CLAUDE.md
        force: Overwrite existing files
        verbose: Print progress messages

    Returns:
        True if initialization was successful
    """
    if not project_name:
        project_name = project_path.name

    success = True

    # Create main directories
    directories = [
        project_path / "tasks",
        project_path / "docs",
    ]

    if include_src:
        directories.append(project_path / "src")

    if include_tests:
        directories.append(project_path / "tests")

    for directory in directories:
        if not create_directory(directory, verbose):
            success = False

    # Create files
    files: Dict[Path, str] = {
        project_path / ".gitignore": GITIGNORE_TEMPLATE,
        project_path / ".env.example": ENV_TEMPLATE,
        project_path / "tasks" / "tasks-example.md": SAMPLE_TASK_LIST,
        project_path / "README.md": README_TEMPLATE.format(project_name=project_name),
    }

    if include_claude_md:
        files[project_path / "CLAUDE.md"] = CLAUDE_MD_TEMPLATE

    for file_path, content in files.items():
        if not write_file(file_path, content, overwrite=force, verbose=verbose):
            success = False

    # Create placeholder files in src and tests if requested
    if include_src:
        src_init = project_path / "src" / "__init__.py"
        if not write_file(
            src_init, '"""Main package."""\n', overwrite=force, verbose=verbose
        ):
            success = False

    if include_tests:
        test_init = project_path / "tests" / "__init__.py"
        if not write_file(
            test_init, '"""Test package."""\n', overwrite=force, verbose=verbose
        ):
            success = False

        test_example = project_path / "tests" / "test_example.py"
        test_content = '''"""Example test file."""

def test_example():
    """Example test that always passes."""
    assert True
'''
        if not write_file(test_example, test_content, overwrite=force, verbose=verbose):
            success = False

    return success


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="gemini-code-review init",
        description="Initialize a project with the recommended structure for Gemini Code Review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize in current directory
  gemini-code-review init

  # Initialize in specific directory
  gemini-code-review init /path/to/project

  # Initialize with custom project name
  gemini-code-review init --name "My Awesome Project"

  # Initialize without src/tests directories (for existing projects)
  gemini-code-review init --no-src --no-tests

  # Force overwrite existing files
  gemini-code-review init --force
        """,
    )

    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to initialize (default: current directory)",
    )

    parser.add_argument("--name", help="Project name (default: directory name)")

    parser.add_argument(
        "--no-src", action="store_true", help="Don't create src directory"
    )

    parser.add_argument(
        "--no-tests", action="store_true", help="Don't create tests directory"
    )

    parser.add_argument(
        "--no-claude-md", action="store_true", help="Don't create CLAUDE.md file"
    )

    parser.add_argument("--force", action="store_true", help="Overwrite existing files")

    parser.add_argument(
        "--quiet", action="store_true", help="Suppress progress messages"
    )

    return parser


def main():
    """Main entry point for the init command."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Convert path to Path object
    project_path = Path(args.path).resolve()

    # Create project directory if it doesn't exist
    if not project_path.exists():
        try:
            project_path.mkdir(parents=True)
            if not args.quiet:
                print(f"✓ Created project directory: {project_path}")
        except Exception as e:
            print(f"✗ Failed to create project directory: {e}", file=sys.stderr)
            sys.exit(1)
    elif not project_path.is_dir():
        print(f"✗ Error: {project_path} exists but is not a directory", file=sys.stderr)
        sys.exit(1)

    # Print header
    if not args.quiet:
        print(f"\nInitializing Gemini Code Review project at: {project_path}")
        print("=" * 60)

    # Initialize the project
    success = init_project(
        project_path=project_path,
        project_name=args.name,
        include_src=not args.no_src,
        include_tests=not args.no_tests,
        include_claude_md=not args.no_claude_md,
        force=args.force,
        verbose=not args.quiet,
    )

    if success:
        if not args.quiet:
            print("\n✓ Project initialized successfully!")
            print("\nNext steps:")
            print("1. Copy .env.example to .env and add your Google AI API key")
            print("2. Review and customize CLAUDE.md for your project")
            print("3. Create task lists in the tasks/ directory")
            print("4. Run 'generate-code-review' to start reviewing")
    else:
        print("\n⚠ Project initialization completed with some errors", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
