#!/usr/bin/env python3
"""
CLI command for generating file context without calling Gemini.

This is a standalone utility for debugging context generation.
"""

import argparse
import os
import sys
from typing import List, Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    # Try relative imports first (when run as module)
    from .file_context_generator import generate_file_context_data, save_file_context
    from .file_context_types import FileContextConfig, FileSelection
    from .file_selector import parse_file_selections
except ImportError:
    try:
        # Fall back to absolute imports for testing or direct execution
        from file_context_generator import generate_file_context_data, save_file_context
        from file_context_types import FileContextConfig, FileSelection
        from file_selector import parse_file_selections
    except ImportError as e:
        print(f"Required dependencies not available: {e}", file=sys.stderr)
        sys.exit(1)


def create_parser():
    """Create argument parser for the CLI command."""
    parser = argparse.ArgumentParser(
        prog="generate-file-context",
        description="Generate context from files for debugging. Does not call Gemini.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Generate context from specific files
  generate-file-context -f src/main.py -f src/utils.py
  
  # With line ranges
  generate-file-context -f "src/main.py:10-50,100-150" -f "src/utils.py:1-30"
  
  # Save to file
  generate-file-context -f src/main.py -o context.md
  
  # With custom instructions
  generate-file-context -f src/main.py --user-instructions "Focus on error handling"
  
  # Exclude CLAUDE.md files
  generate-file-context -f src/main.py --no-claude-memory
        """
    )
    
    parser.add_argument(
        "-f", "--file-selection",
        dest="file_selections",
        action="append",
        required=True,
        help="File to include, with optional line ranges (e.g., 'src/main.py:10-20,30-35')"
    )
    parser.add_argument(
        "--project-path",
        default=os.getcwd(),
        help="Project root for relative paths (default: current directory)"
    )
    parser.add_argument(
        "--user-instructions",
        help="Custom instructions to embed in the context"
    )
    parser.add_argument(
        "--no-claude-memory",
        action="store_true",
        help="Exclude CLAUDE.md files from context"
    )
    parser.add_argument(
        "--include-cursor-rules",
        action="store_true",
        help="Include .cursorrules and .cursor/rules/*.mdc files"
    )
    parser.add_argument(
        "--no-auto-meta-prompt",
        action="store_true",
        help="Disable automatic meta-prompt generation"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.5,
        help="AI temperature for meta-prompt generation (default: 0.5)"
    )
    parser.add_argument(
        "-o", "--output-path",
        help="Save context to specified file path instead of printing to stdout"
    )
    
    return parser


def main():
    """Main entry point for the CLI command."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Parse file selections using the batch parser
        try:
            parsed_selections = parse_file_selections(args.file_selections)
        except ValueError as e:
            print(f"Error parsing file selections: {e}", file=sys.stderr)
            sys.exit(1)
        
        print("Generating file context...")
        
        # Create configuration
        config = FileContextConfig(
            file_selections=parsed_selections,
            project_path=args.project_path,
            user_instructions=args.user_instructions,
            include_claude_memory=not args.no_claude_memory,
            include_cursor_rules=args.include_cursor_rules,
            auto_meta_prompt=not args.no_auto_meta_prompt,
            temperature=args.temperature,
            text_output=not bool(args.output_path),
            output_path=args.output_path,
        )
        
        # Generate context
        result = generate_file_context_data(config)
        
        # Handle output
        if args.output_path:
            saved_path = save_file_context(result, args.output_path, args.project_path)
            print(f"✅ Context saved to: {saved_path}")
            print(f"📊 Included {len(result.included_files)} files, {result.total_tokens} estimated tokens")
        else:
            print("\n--- Generated Context ---")
            print(result.content)
            print("--- End Context ---")
            print(f"\n📊 Included {len(result.included_files)} files, {result.total_tokens} estimated tokens", file=sys.stderr)
        
        # Show excluded files if any
        if result.excluded_files:
            print(f"\n⚠️  {len(result.excluded_files)} files excluded:", file=sys.stderr)
            for path, reason in result.excluded_files[:5]:
                print(f"   - {path}: {reason}", file=sys.stderr)
            if len(result.excluded_files) > 5:
                print(f"   ... and {len(result.excluded_files) - 5} more", file=sys.stderr)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()