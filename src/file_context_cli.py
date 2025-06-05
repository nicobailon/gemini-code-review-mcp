#!/usr/bin/env python3
"""
CLI interface for file-based context generation.

Provides command-line access to generate context from specific files with optional
line ranges, matching the functionality of the generate_file_context MCP tool.
"""

import argparse
import sys
import os
from typing import List, Dict, Any, Tuple

from .file_context_generator import generate_file_context_data, save_file_context
from .file_context_types import FileContextConfig, FileSelection
from .gemini_api_client import load_api_key


def parse_file_argument(file_arg: str) -> Dict[str, Any]:
    """
    Parse a file argument with optional line ranges.
    
    Supports formats:
    - path/to/file.py
    - path/to/file.py:10-20
    - path/to/file.py:10-20,30-40
    
    Args:
        file_arg: File argument string
        
    Returns:
        Dictionary with path and optional line_ranges
    """
    if ':' not in file_arg:
        return {"path": file_arg}
    
    path, ranges_str = file_arg.split(':', 1)
    line_ranges: List[Tuple[int, int]] = []
    
    for range_str in ranges_str.split(','):
        if '-' in range_str:
            start, end = range_str.split('-', 1)
            try:
                start_num = int(start.strip())
                end_num = int(end.strip())
                if start_num <= end_num:
                    line_ranges.append((start_num, end_num))
                else:
                    print(f"Warning: Invalid range {start_num}-{end_num}, start > end")
            except ValueError:
                print(f"Warning: Invalid line range '{range_str}', skipping")
        else:
            try:
                line_num = int(range_str.strip())
                line_ranges.append((line_num, line_num))
            except ValueError:
                print(f"Warning: Invalid line number '{range_str}', skipping")
    
    result: Dict[str, Any] = {"path": path}
    if line_ranges:
        result["line_ranges"] = line_ranges
    
    return result


def main():
    """Main entry point for generate-file-context CLI command."""
    parser = argparse.ArgumentParser(
        description="Generate context from specific files with optional line ranges",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate context from specific files
  generate-file-context src/main.py src/utils.py
  
  # Include specific line ranges
  generate-file-context src/auth.py:50-100 src/database.py:20-40,60-80
  
  # Add custom instructions
  generate-file-context src/api.py --instructions "Focus on error handling"
  
  # Save to specific file
  generate-file-context src/*.py --output context.md
  
  # Include project configurations
  generate-file-context main.py --include-cursor-rules
  
  # Exclude CLAUDE.md files
  generate-file-context src/core.py --no-claude-memory

Output Format:
  By default, saves to file-context-[timestamp].md in the current directory.
  Use --output to specify a custom path, or --stdout to print to console.
"""
    )
    
    parser.add_argument(
        "files",
        nargs="+",
        help="Files to include in context (e.g., file.py or file.py:10-20)"
    )
    
    parser.add_argument(
        "--project-path", "-p",
        default=None,
        help="Project root for relative paths (default: current directory)"
    )
    
    parser.add_argument(
        "--instructions", "-i",
        dest="user_instructions",
        help="Custom instructions to include in the context"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: file-context-[timestamp].md)"
    )
    
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print context to stdout instead of saving to file"
    )
    
    parser.add_argument(
        "--no-claude-memory",
        action="store_true",
        help="Exclude CLAUDE.md files from context"
    )
    
    parser.add_argument(
        "--include-cursor-rules",
        action="store_true",
        help="Include Cursor rules files in context"
    )
    
    parser.add_argument(
        "--no-meta-prompt",
        action="store_true",
        help="Disable automatic meta-prompt generation"
    )
    
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.5,
        help="Temperature for meta-prompt generation (0.0-2.0, default: 0.5)"
    )
    
    parser.add_argument(
        "--token-limit",
        type=int,
        default=200000,
        help="Maximum tokens to include (default: 200000)"
    )
    
    parser.add_argument(
        "--model",
        help="Model for meta-prompt generation (e.g., gemini-2.0-flash)"
    )
    
    args = parser.parse_args()
    
    # Check if API key is available (only needed if meta-prompt is enabled)
    if not args.no_meta_prompt and not load_api_key():
        print("Note: GEMINI_API_KEY not found. Meta-prompt generation will be skipped.")
        print("To enable meta-prompts, set GEMINI_API_KEY environment variable.")
        args.no_meta_prompt = True
    
    # Parse file selections
    file_selections = [parse_file_argument(f) for f in args.files]
    
    # Create FileSelection objects
    normalized_selections: List[FileSelection] = []
    for selection in file_selections:
        normalized_selection = FileSelection(
            path=selection["path"],
            line_ranges=selection.get("line_ranges"),
            include_full=True
        )
        normalized_selections.append(normalized_selection)
    
    # Create configuration
    config = FileContextConfig(
        file_selections=normalized_selections,
        project_path=args.project_path,
        user_instructions=args.user_instructions,
        include_claude_memory=not args.no_claude_memory,
        include_cursor_rules=args.include_cursor_rules,
        auto_meta_prompt=not args.no_meta_prompt,
        temperature=args.temperature,
        text_output=args.stdout,
        output_path=args.output if not args.stdout else None,
        model=args.model,
        token_limit=args.token_limit
    )
    
    try:
        # Generate context
        result = generate_file_context_data(config)
        
        if args.stdout:
            # Print to stdout
            print(result.content)
        else:
            # Save to file
            output_path = save_file_context(
                result,
                args.output,
                args.project_path
            )
            
            # Print summary
            print(f"✅ File context generated successfully!")
            print(f"📄 Output file: {output_path}")
            print(f"📊 Included {len(result.included_files)} files, {result.total_tokens} estimated tokens")
            
            if result.excluded_files:
                print(f"\n⚠️  Excluded {len(result.excluded_files)} files:")
                for path, reason in result.excluded_files[:5]:  # Show first 5
                    print(f"   - {path}: {reason}")
                if len(result.excluded_files) > 5:
                    print(f"   ... and {len(result.excluded_files) - 5} more")
            
            if result.meta_prompt:
                print("\n🤖 Meta-prompt generated based on selected files")
            
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())