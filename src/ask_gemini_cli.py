#!/usr/bin/env python3
"""
CLI interface for the ask_gemini tool.

Provides command-line access to ask questions to Gemini AI with optional file context.
"""

import argparse
import sys
from typing import List, Dict, Any, Tuple

from .ask_gemini import ask_gemini, ask_gemini_direct
from .gemini_api_client import require_api_key


def parse_file_selection(file_arg: str) -> Dict[str, Any]:
    """
    Parse a file selection argument.
    
    Formats supported:
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
                line_ranges.append((int(start.strip()), int(end.strip())))
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
    """Main entry point for ask-gemini CLI command."""
    parser = argparse.ArgumentParser(
        description="Ask Gemini AI questions with optional file context",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple question
  ask-gemini "What are Python decorators?"
  
  # Question with file context
  ask-gemini "How can I optimize this function?" --files src/slow.py:45-90
  
  # Multiple files with instructions
  ask-gemini "Review these authentication functions" \\
    --files auth/login.py auth/validate.py:20-50 \\
    --instructions "Focus on security vulnerabilities"
  
  # Save response to file
  ask-gemini "Explain this algorithm" --files algo.py --output explanation.md
"""
    )
    
    parser.add_argument(
        "question",
        help="The question to ask Gemini"
    )
    
    parser.add_argument(
        "--files", "-f",
        nargs="+",
        help="Files to include as context (e.g., file.py or file.py:10-20)"
    )
    
    parser.add_argument(
        "--project-path", "-p",
        default=None,
        help="Project path for relative file resolution (default: current directory)"
    )
    
    parser.add_argument(
        "--instructions", "-i",
        help="Additional instructions or context for the question"
    )
    
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.5,
        help="Model temperature (0.0-2.0, default: 0.5)"
    )
    
    parser.add_argument(
        "--model", "-m",
        help="Specific Gemini model to use (e.g., gemini-2.0-flash)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Save response to file instead of printing to stdout"
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
    
    args = parser.parse_args()
    
    # Ensure API key is available
    require_api_key()
    
    # Process file selections if provided
    file_selections = None
    if args.files:
        file_selections = [parse_file_selection(f) for f in args.files]
    
    # Determine output mode
    text_output = args.output is None
    
    try:
        # Call ask_gemini with all parameters
        result = ask_gemini(
            question=args.question,
            file_selections=file_selections,
            project_path=args.project_path,
            user_instructions=args.instructions,
            temperature=args.temperature,
            include_claude_memory=not args.no_claude_memory,
            include_cursor_rules=args.include_cursor_rules,
            text_output=text_output,
            output_path=args.output,
            model=args.model
        )
        
        if text_output:
            # Print response to stdout
            print(result)
        else:
            # File was saved, print success message
            print(result)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def direct_main():
    """Main entry point for ask-gemini-direct CLI command."""
    parser = argparse.ArgumentParser(
        description="Ask Gemini AI direct questions (simplified interface)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This is a simplified interface for quick questions without file context.
For file context support, use the 'ask-gemini' command instead.

Examples:
  # Simple question
  ask-gemini-direct "What is the time complexity of quicksort?"
  
  # Question with context provided as argument
  ask-gemini-direct "What does this code do?" --context "def fib(n): return fib(n-1) + fib(n-2) if n > 1 else n"
  
  # Question with specific model
  ask-gemini-direct "Explain quantum computing" --model gemini-1.5-pro
"""
    )
    
    parser.add_argument(
        "question",
        help="The question to ask Gemini"
    )
    
    parser.add_argument(
        "--context", "-c",
        help="Optional context string to include with the question"
    )
    
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.5,
        help="Model temperature (0.0-2.0, default: 0.5)"
    )
    
    parser.add_argument(
        "--model", "-m",
        help="Specific Gemini model to use"
    )
    
    args = parser.parse_args()
    
    # Ensure API key is available
    require_api_key()
    
    try:
        # Call ask_gemini_direct
        result = ask_gemini_direct(
            question=args.question,
            context=args.context,
            temperature=args.temperature,
            model=args.model
        )
        
        print(result)
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    # Determine which command to run based on script name
    if "direct" in sys.argv[0]:
        sys.exit(direct_main())
    else:
        sys.exit(main())