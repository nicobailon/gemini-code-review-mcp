#!/usr/bin/env python3
"""
CLI main module.

This module serves as the main command-line interface entry point for the
generate-code-review tool, handling argument parsing, validation, and execution
of the core workflow.
"""

import argparse
import logging
import os
import sys
import warnings
from typing import Any, Dict, List, Optional

# Import the main generation function from the old module
try:
    from .services.generate_code_review_context import generate_code_review_context_main
    from .services.meta_prompt_analyzer import generate_optimized_meta_prompt
except ImportError:
    from .services.generate_code_review_context import generate_code_review_context_main
    from .services.meta_prompt_analyzer import generate_optimized_meta_prompt

# Load environment variables from .env file (optional)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv not available, continue without it

logger = logging.getLogger(__name__)


def suggest_path_corrections(provided_path: str, expected_type: str = "project") -> str:
    """
    Generate helpful path correction suggestions based on common mistakes.

    Args:
        provided_path: The path the user provided
        expected_type: Type of path expected ("project", "file", "directory")

    Returns:
        String with suggestion messages
    """
    suggestions: List[str] = []
    current_dir = os.getcwd()

    # Check if path exists but is wrong type
    if os.path.exists(provided_path):
        if expected_type == "project" and os.path.isfile(provided_path):
            parent_dir = os.path.dirname(provided_path)
            suggestions.append(
                "  # You provided a file, try the parent directory instead:"
            )
            suggestions.append(
                f"  generate-code-review {parent_dir if parent_dir else '.'}"
            )
    else:
        # Path doesn't exist - suggest common corrections
        abs_path = os.path.abspath(provided_path)
        parent_dir = os.path.dirname(abs_path)

        # Check if parent exists
        if os.path.exists(parent_dir):
            suggestions.append("  # Parent directory exists. Maybe there's a typo?")
            similar_items: List[str] = []
            try:
                for item in os.listdir(parent_dir):
                    if item.lower().startswith(
                        os.path.basename(provided_path).lower()[:3]
                    ):
                        similar_items.append(item)
                if similar_items:
                    suggestions.append(
                        f"  # Similar items found: {', '.join(similar_items[:3])}"
                    )
                    suggestions.append(
                        f"  generate-code-review {os.path.join(parent_dir, similar_items[0])}"
                    )
            except PermissionError:
                suggestions.append(f"  # Permission denied accessing {parent_dir}")

        # Check if it's a relative path issue
        basename = os.path.basename(provided_path)
        for root, dirs, _ in os.walk(current_dir):
            if basename in dirs:
                rel_path = os.path.relpath(os.path.join(root, basename), current_dir)
                suggestions.append("  # Found similar directory:")
                suggestions.append(f"  generate-code-review {rel_path}")
                break
            if len(suggestions) > 6:  # Limit suggestions
                break

        # Common path corrections
        if provided_path.startswith("/"):
            suggestions.append("  # Try relative path instead:")
            suggestions.append(
                f"  generate-code-review ./{os.path.basename(provided_path)}"
            )
        else:
            suggestions.append("  # Try absolute path:")
            suggestions.append(f"  generate-code-review {abs_path}")

    # Check for common project structure issues
    if expected_type == "project":
        tasks_path = (
            os.path.join(provided_path, "tasks")
            if os.path.exists(provided_path)
            else None
        )
        if tasks_path and not os.path.exists(tasks_path):
            suggestions.append("  # Directory exists but missing tasks/ folder:")
            suggestions.append(f"  mkdir {tasks_path}")
            suggestions.append("  # Then add PRD and task files to tasks/")

    return "\n".join(suggestions) if suggestions else "  # Check the path and try again"


def create_argument_parser():
    """Create and configure the argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description="Generate code review context with enhanced scope options",
        epilog="""
🚀 QUICK START:
  # Most common usage - analyze current project
  generate-code-review .
  
  # With environment variable for API key
  export GEMINI_API_KEY=your_key && generate-code-review .

📋 SCOPE OPTIONS:
  # Auto-detect most recent incomplete phase (default)
  generate-code-review /path/to/project
  
  # Review entire completed project
  generate-code-review . --scope full_project
  
  # Review specific phase only
  generate-code-review . --scope specific_phase --phase-number 2.0
  
  # Review individual task
  generate-code-review . --scope specific_task --task-number 1.3

🤖 AUTO-PROMPT GENERATION:
  # Generate optimized prompt using Gemini analysis and use it for review
  generate-code-review . --auto-prompt
  
  # Only generate the optimized prompt (no code review)
  generate-code-review . --generate-prompt-only
  
  # Combine with other options
  generate-code-review . --auto-prompt --temperature 0.3 --scope full_project

🔀 GIT BRANCH COMPARISON:
  # Compare current branch against main/master
  generate-code-review . --compare-branch feature/auth-system
  
  # Compare specific branches
  generate-code-review . --compare-branch feature/payment --target-branch develop
  
  # Review GitHub Pull Request
  generate-code-review --github-pr-url https://github.com/owner/repo/pull/123
  
  # Combined with existing features
  generate-code-review . --compare-branch feature/new-ui --temperature 0.3

🎛️ TEMPERATURE CONTROL:
  # Focused/deterministic review (good for production code)
  generate-code-review . --temperature 0.0
  
  # Balanced review (default, recommended)
  generate-code-review . --temperature 0.5
  
  # Creative review (good for early development)
  generate-code-review . --temperature 1.0

📏 CONTEXT SIZE MANAGEMENT:
  # Quick review of essential files only (30% of model limit)
  generate-code-review . --context-strategy focused
  
  # Default balanced approach (100% of model limit)
  generate-code-review . --context-strategy balanced
  
  # Comprehensive review (150% of model limit - best for Gemini 2.5 Pro)
  generate-code-review . --context-strategy comprehensive
  
  # Custom token limit
  generate-code-review . --max-context-tokens 250000
  
  # Combine with model selection for optimal results
  GEMINI_MODEL=gemini-2.5-pro-preview-06-05 generate-code-review . --context-strategy comprehensive

⚙️ ENVIRONMENT SETUP:
  # Using uvx (recommended for latest version)
  GEMINI_API_KEY=your_key uvx gemini-code-review-mcp generate-code-review .
  
  # With .env file (project-specific)
  echo "GEMINI_API_KEY=your_key" > .env && generate-code-review .
  
  # Global config (~/.gemini-code-review-mcp.env)
  echo "GEMINI_API_KEY=your_key" > ~/.gemini-code-review-mcp.env

🛠️ ADVANCED OPTIONS:
  # Generate context only (no AI review)
  generate-code-review . --context-only --output /custom/path/review.md
  
  # Custom model via environment variable
  GEMINI_MODEL=gemini-2.5-pro-preview generate-code-review .
  
  # Override temperature via environment
  GEMINI_TEMPERATURE=0.3 generate-code-review .

📁 PROJECT STRUCTURE OPTIONS:
  
  # With task list (recommended)
  your-project/
  ├── tasks/
  │   ├── prd-feature.md       # Optional: Product Requirements Document  
  │   └── tasks-feature.md     # Task list file (auto-selected if multiple)
  └── ... (your source code)
  
  # Without task lists (uses default prompt)
  your-project/
  └── ... (your source code)

📋 TASK LIST DISCOVERY (Opt-in):
  # General review mode (default - no task discovery)
  generate-code-review .
  
  # Enable task-driven review (auto-selects most recent tasks-*.md file)
  generate-code-review . --task-list
  
  # Use specific task list
  generate-code-review . --task-list tasks-auth-system.md
  
  # Multiple task lists found? Tool shows which was selected:
  # "Multiple task lists found: tasks-auth.md, tasks-payment.md"
  # "Auto-selected most recent: tasks-payment.md"

🌐 GET API KEY: https://ai.google.dev/gemini-api/docs/api-key
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "project_path", nargs="?", default=None, help="Path to project root"
    )
    parser.add_argument(
        "--phase", help="Override current phase detection (legacy parameter)"
    )
    parser.add_argument("--output", help="Custom output file path")
    parser.add_argument(
        "--context-only",
        action="store_true",
        help="Generate only the review context, skip AI review generation",
    )
    # Keep --no-gemini for backward compatibility (deprecated)
    parser.add_argument(
        "--no-gemini", action="store_true", help=argparse.SUPPRESS
    )  # Hidden deprecated option

    # Auto-prompt generation flags (mutual exclusion group)
    auto_prompt_group = parser.add_mutually_exclusive_group()
    auto_prompt_group.add_argument(
        "--auto-prompt",
        action="store_true",
        help="Generate optimized prompt using Gemini analysis and use it for AI code review",
    )
    auto_prompt_group.add_argument(
        "--generate-prompt-only",
        action="store_true",
        help="Only generate the optimized prompt, do not run code review",
    )

    # New scope-based parameters
    parser.add_argument(
        "--scope",
        default="recent_phase",
        choices=["recent_phase", "full_project", "specific_phase", "specific_task"],
        help="Review scope: recent_phase (default), full_project, specific_phase, specific_task",
    )
    parser.add_argument(
        "--phase-number", help="Phase number for specific_phase scope (e.g., '2.0')"
    )
    parser.add_argument(
        "--task-number", help="Task number for specific_task scope (e.g., '1.2')"
    )
    parser.add_argument(
        "--task-list",
        help="Enable task-driven review mode and optionally specify which task list file to use (e.g., 'tasks-feature-x.md'). Without this flag, general review mode is used.",
    )
    parser.add_argument(
        "--default-prompt", help="Custom default prompt when no task list exists"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.5,
        help="Temperature for AI model (default: 0.5, range: 0.0-2.0)",
    )

    # Token management parameters
    parser.add_argument(
        "--context-strategy",
        choices=["focused", "balanced", "comprehensive", "unlimited"],
        default="balanced",
        help="Context size strategy: focused (30%% of model limit), balanced (default, 100%%), comprehensive (150%%), unlimited (no limit)",
    )
    parser.add_argument(
        "--max-context-tokens",
        type=int,
        help="Override maximum context tokens (overrides strategy)",
    )
    parser.add_argument(
        "--per-file-token-limit",
        type=int,
        default=10_000,
        help="Maximum tokens per file (default: 10,000)",
    )
    
    # Review mode parameters
    parser.add_argument(
        "--review-mode",
        choices=["single", "multi-phase", "overview-only"],
        default="multi-phase",
        help="Review generation mode: single (force single file), multi-phase (default, split if needed), overview-only (manifest only)",
    )
    
    # Output control parameters
    parser.add_argument(
        "-s", "--save-intermediate-files",
        action="store_true",
        help="Save intermediate context and review files for each phase (default: only save summary)",
    )

    # Git branch comparison parameters
    parser.add_argument(
        "--compare-branch",
        help="Compare this branch against target branch (default: current branch)",
    )
    parser.add_argument(
        "--target-branch",
        help="Target branch for comparison (default: auto-detect main/master)",
    )
    parser.add_argument(
        "--github-pr-url",
        help="GitHub PR URL to review (e.g., 'https://github.com/owner/repo/pull/123')",
    )

    # Configuration inclusion parameters
    # Use mutual exclusion group for claude memory flags
    claude_memory_group = parser.add_mutually_exclusive_group()
    claude_memory_group.add_argument(
        "--include-claude-memory",
        action="store_true",
        help="Include CLAUDE.md files in context (optional - off by default)",
    )
    claude_memory_group.add_argument(
        "--no-claude-memory",
        action="store_true",
        help="[DEPRECATED] Use --include-claude-memory instead. This flag will be removed in a future version.",
    )
    
    parser.add_argument(
        "--include-cursor-rules",
        action="store_true",
        help="Include Cursor rules files (.cursorrules and .cursor/rules/*.mdc)",
    )

    # File-based context generation arguments
    parser.add_argument(
        "--files",
        nargs="+",
        metavar="FILE",
        help="Generate context from specific files (e.g., file1.py file2.py:10-50)",
    )
    parser.add_argument(
        "--file-instructions",
        type=str,
        help="Custom instructions for file-based context generation",
    )

    # Thinking budget and URL context parameters
    parser.add_argument(
        "--thinking-budget",
        type=int,
        help="Token budget for thinking mode (if supported by model)",
    )
    parser.add_argument(
        "--url-context",
        action="append",
        help="URL(s) to include in context (can be repeated for multiple URLs)",
    )

    return parser


def validate_cli_arguments(args: Any):
    """Validate CLI arguments and check for conflicts."""
    
    # Handle deprecated --no-claude-memory flag
    if args.no_claude_memory:
        warnings.warn(
            "--no-claude-memory is deprecated and will be removed in a future version. "
            "Use --include-claude-memory to opt-in to CLAUDE.md inclusion.",
            DeprecationWarning,
            stacklevel=2
        )
        
    # Note: argparse mutual exclusion group handles conflicting flags automatically

    # No need to check for mutually exclusive auto-prompt flags - argparse handles it

    # Check for conflicts with context-only
    if args.generate_prompt_only and args.context_only:
        raise ValueError(
            "--generate-prompt-only and --context-only are mutually exclusive. "
            "Use --generate-prompt-only to generate optimized prompts, or "
            "--context-only to generate raw context without AI review."
        )

    # Project path is optional - defaults to current directory in generate_code_review_context_main

    # Validate temperature range
    if args.temperature < 0.0 or args.temperature > 2.0:
        raise ValueError("Temperature must be between 0.0 and 2.0")

    # Validate scope-specific parameters
    if args.scope == "specific_phase" and not args.phase_number:
        raise ValueError("--phase-number is required when using --scope specific_phase")

    if args.scope == "specific_task" and not args.task_number:
        raise ValueError("--task-number is required when using --scope specific_task")


def execute_auto_prompt_workflow(
    project_path: str,
    scope: str = "recent_phase",
    temperature: float = 0.5,
    auto_prompt: bool = False,
    generate_prompt_only: bool = False,
    **kwargs: Any,
) -> str:
    """Execute auto-prompt generation workflow with optimized single-file approach."""
    try:
        # Step 1: Generate optimized prompt using project analysis (no intermediate files)
        print("🤖 Generating optimized prompt using Gemini analysis...")

        prompt_result = generate_optimized_meta_prompt(
            project_path=project_path, scope=scope
        )

        if not prompt_result.get("analysis_completed"):
            raise Exception("Auto-prompt generation failed")

        generated_prompt = prompt_result["generated_prompt"]

        # Format output for prompt-only mode
        if generate_prompt_only:
            return format_auto_prompt_output(prompt_result, auto_prompt_mode=False)

        # Step 2: For auto-prompt mode, also run AI code review with custom prompt
        if auto_prompt:
            print("🔍 Running AI code review with generated prompt...")

            # First generate context (needed for AI review)
            # Filter kwargs to only include parameters that the function accepts, excluding None values
            context_kwargs: Dict[str, Any] = {
                k: v
                for k, v in kwargs.items()
                if k
                in [
                    "phase",
                    "output",
                    "phase_number",
                    "task_number",
                    "task_list",
                    "default_prompt",
                    "compare_branch",
                    "target_branch",
                    "github_pr_url",
                    "include_claude_memory",
                    "include_cursor_rules",
                    "raw_context_only",
                ]
                and v is not None
            }

            generate_code_review_context_main(
                project_path=project_path,
                scope=scope,
                enable_gemini_review=False,  # Don't run default AI review
                temperature=temperature,
                auto_prompt_content=generated_prompt,  # Pass the meta-prompt to embed in context
                **context_kwargs,
            )

            # Run AI review with custom prompt
            # Note: AI code review generation has been disabled to avoid circular imports
            # The auto-prompt workflow now only generates context + meta prompt
            # AI review should be handled separately via the MCP server tools
            print(
                "ℹ️  Auto-prompt workflow complete - use generate_ai_code_review MCP tool for AI review"
            )
            ai_review_result = None

            return format_auto_prompt_output(
                prompt_result, auto_prompt_mode=True, ai_review_file=ai_review_result
            )

        return format_auto_prompt_output(prompt_result, auto_prompt_mode=False)

    except Exception as e:
        raise Exception(f"Auto-prompt workflow failed: {str(e)}")


def format_auto_prompt_output(
    prompt_result: Dict[str, Any],
    auto_prompt_mode: bool = False,
    ai_review_file: Optional[str] = None,
) -> str:
    """Format output for auto-prompt generation results."""
    output_parts: List[str] = []

    # Header
    if auto_prompt_mode:
        output_parts.append("🤖 Auto-Prompt Code Review Complete!")
    else:
        output_parts.append("🤖 Optimized Prompt Generated!")

    # Prompt analysis info
    context_size = prompt_result.get("context_analyzed", 0)
    output_parts.append(f"📊 Context analyzed: {context_size:,} characters")

    # Generated prompt
    generated_prompt = prompt_result.get("generated_prompt", "")
    output_parts.append("\n📝 Generated Prompt:")
    output_parts.append("=" * 50)
    output_parts.append(generated_prompt)
    output_parts.append("=" * 50)

    # AI review info (if applicable)
    if auto_prompt_mode and ai_review_file:
        output_parts.append(
            f"\n✅ AI code review completed: {os.path.basename(ai_review_file)}"
        )
        output_parts.append(f"📄 Review file: {ai_review_file}")

    # Success message
    if auto_prompt_mode:
        output_parts.append("\n🎉 Auto-prompt code review workflow completed!")
    else:
        output_parts.append("\n🎉 Prompt generation completed!")
        output_parts.append(
            "💡 Use this prompt with --custom-prompt for targeted code reviews"
        )

    return "\n".join(output_parts)


def detect_execution_mode():
    """Detect if running in development or installed mode."""
    import __main__

    if hasattr(__main__, "__file__") and __main__.__file__:
        if "src/" in str(__main__.__file__) or "-m" in sys.argv[0]:
            return "development"
    return "installed"


def cli_main():
    """CLI entry point for generate-code-review command."""
    # Configure logging for CLI context
    try:
        from .helpers.logging_config import setup_cli_logging
    except ImportError:
        from helpers.logging_config import setup_cli_logging
    
    setup_cli_logging()
    
    # Show execution mode for clarity in development
    mode = detect_execution_mode()
    if mode == "development":
        print("🔧 Development mode", file=sys.stderr)

    parser = create_argument_parser()
    args = parser.parse_args()

    # Validate arguments
    try:
        validate_cli_arguments(args)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    try:
        # Validate and improve argument handling

        # Validate project path early
        if args.project_path:
            if not os.path.exists(args.project_path):
                suggestions = suggest_path_corrections(args.project_path, "project")
                error_msg = f"""Project path does not exist: {args.project_path}

💡 PATH SUGGESTIONS:
{suggestions}

📋 WORKING EXAMPLES:
  # Use current directory (if it has tasks/ folder)
  generate-code-review .
  
  # Use absolute path
  generate-code-review /path/to/your/project
  
  # Use relative path
  generate-code-review ../my-project
  
  # Auto-detect from current location
  generate-code-review"""
                raise FileNotFoundError(error_msg)

            if not os.path.isdir(args.project_path):
                suggestions = suggest_path_corrections(args.project_path, "project")
                error_msg = f"""Project path must be a directory: {args.project_path}

💡 PATH SUGGESTIONS:
{suggestions}

📋 WORKING EXAMPLES:
  # Point to directory, not file
  generate-code-review /path/to/project/  ✓
  generate-code-review /path/to/file.md   ✗
  
  # Use parent directory if you're pointing to a file
  generate-code-review {os.path.dirname(args.project_path) if os.path.dirname(args.project_path) else '.'}"""
                raise NotADirectoryError(error_msg)

        # Validate temperature range
        if not (0.0 <= args.temperature <= 2.0):
            error_msg = f"""Temperature must be between 0.0 and 2.0, got {args.temperature}

Working examples:
  # Deterministic/focused (good for code review)
  generate-code-review . --temperature 0.0
  
  # Balanced (default)
  generate-code-review . --temperature 0.5
  
  # Creative (good for brainstorming)
  generate-code-review . --temperature 1.0
  
  # Very creative (experimental)
  generate-code-review . --temperature 1.5
  
  # Use environment variable
  GEMINI_TEMPERATURE=0.3 generate-code-review ."""
            raise ValueError(error_msg)

        # Validate output path if provided
        if args.output:
            output_dir = os.path.dirname(args.output)
            if output_dir and not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                    logger.info(f"Created output directory: {output_dir}")
                except OSError as e:
                    error_msg = f"""Failed to create output directory: {output_dir}
Error: {e}

Working examples:
  # Use existing directory
  generate-code-review . --output /tmp/review.md
  
  # Use relative path
  generate-code-review . --output ./output/review.md
  
  # Let tool auto-create directory
  generate-code-review . --output /path/to/new/dir/review.md
  
  # Or let tool auto-generate in project
  generate-code-review .  # creates in project root"""
                    raise FileNotFoundError(error_msg)

        # Handle both new and legacy flags (prioritize new flag)
        enable_gemini = not (args.context_only or args.no_gemini)

        # Handle temperature: CLI arg takes precedence, then env var, then default 0.5
        temperature = args.temperature
        if temperature == 0.5:  # Default value, check if env var should override
            try:
                temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.5"))
                if not (0.0 <= temperature <= 2.0):
                    logger.warning(
                        f"Invalid GEMINI_TEMPERATURE={temperature}, using default 0.5"
                    )
                    temperature = 0.5
            except ValueError:
                logger.warning("Invalid GEMINI_TEMPERATURE format, using default 0.5")
                temperature = 0.5

        # Handle auto-prompt workflows (new functionality)
        if args.auto_prompt or args.generate_prompt_only:
            try:
                # Prepare kwargs for workflow
                workflow_kwargs = {
                    "phase": args.phase,
                    "output": args.output,
                    "phase_number": args.phase_number,
                    "task_number": args.task_number,
                    "task_list": args.task_list,
                    "default_prompt": args.default_prompt,
                    "compare_branch": args.compare_branch,
                    "target_branch": args.target_branch,
                    "github_pr_url": args.github_pr_url,
                    "include_claude_memory": args.include_claude_memory,
                    "include_cursor_rules": args.include_cursor_rules,
                }

                # Execute auto-prompt workflow
                # Convert project path to absolute path for meta prompt analyzer
                # Use current directory if not specified
                project_path = args.project_path or os.getcwd()
                absolute_project_path = os.path.abspath(project_path)
                result = execute_auto_prompt_workflow(
                    project_path=absolute_project_path,
                    scope=args.scope,
                    temperature=temperature,
                    auto_prompt=args.auto_prompt,
                    generate_prompt_only=args.generate_prompt_only,
                    **workflow_kwargs,
                )

                # Print the formatted result
                print(result)
                return  # Exit early for auto-prompt workflows

            except Exception as e:
                print(f"Error in auto-prompt workflow: {e}", file=sys.stderr)
                sys.exit(1)

        # Check if file-based context generation is requested
        if args.files:
            try:
                from .services.file_context_generator import (
                    generate_file_context_data,
                    save_file_context,
                )
                from .file_context_types import FileContextConfig, FileSelection
                from .helpers.file_selector import parse_file_selection

                # Parse file selections
                file_selections: List[FileSelection] = []
                for file_spec in args.files:
                    try:
                        selection = parse_file_selection(file_spec)
                        file_selections.append(selection)
                    except ValueError as e:
                        print(
                            f"Error parsing file selection '{file_spec}': {e}",
                            file=sys.stderr,
                        )
                        sys.exit(1)

                # Create configuration
                config = FileContextConfig(
                    file_selections=file_selections,
                    project_path=args.project_path,
                    user_instructions=args.file_instructions,
                    include_claude_memory=args.include_claude_memory,
                    include_cursor_rules=args.include_cursor_rules,
                    auto_meta_prompt=args.auto_prompt,
                    temperature=temperature,
                    text_output=False,  # CLI saves to file
                    output_path=args.output,
                )

                # Generate context
                result = generate_file_context_data(config)

                # Save to file
                output_path = save_file_context(result, args.output, args.project_path)

                print(f"\n🎉 File-based context generation completed!")
                print(f"📄 Context file: {output_path}")
                print(
                    f"📊 Included {len(result.included_files)} files, {result.total_tokens} estimated tokens"
                )

                if result.excluded_files:
                    print(f"⚠️  {len(result.excluded_files)} files excluded:")
                    for path, reason in result.excluded_files[:5]:  # Show first 5
                        print(f"   - {path}: {reason}")
                    if len(result.excluded_files) > 5:
                        print(f"   ... and {len(result.excluded_files) - 5} more")

                # Run Gemini review if requested
                if enable_gemini:
                    print("\n🔄 Sending to Gemini for AI code review...")
                    from .services.gemini_api_client import send_to_gemini_for_review

                    gemini_path = send_to_gemini_for_review(
                        result.content, args.project_path, temperature
                    )

                    if gemini_path:
                        print(
                            f"✅ AI code review completed: {os.path.basename(gemini_path)}"
                        )
                    else:
                        print("⚠️  AI code review failed or was skipped")

                return  # Exit after file-based workflow

            except ImportError as e:
                print(
                    f"Error: File context generation modules not available: {e}",
                    file=sys.stderr,
                )
                sys.exit(1)
            except Exception as e:
                print(f"Error in file-based context generation: {e}", file=sys.stderr)
                sys.exit(1)

        # Check if we should use enhanced multi-phase version
        if args.review_mode != "single":
            # Use enhanced version with multi-phase support
            from .services.generate_code_review_context_enhanced import (
                generate_code_review_context_main as generate_enhanced
            )
            
            result = generate_enhanced(
                project_path=args.project_path,
                phase=args.phase,
                output=args.output,
                enable_gemini_review=enable_gemini,
                scope=args.scope,
                phase_number=args.phase_number,
                task_number=args.task_number,
                temperature=temperature,
                task_list=args.task_list,
                default_prompt=args.default_prompt,
                compare_branch=args.compare_branch,
                target_branch=args.target_branch,
                github_pr_url=args.github_pr_url,
                include_claude_memory=args.include_claude_memory,
                include_cursor_rules=args.include_cursor_rules,
                thinking_budget=args.thinking_budget,
                url_context=args.url_context,
                context_strategy=args.context_strategy,
                max_context_tokens=args.max_context_tokens,
                per_file_token_limit=args.per_file_token_limit,
                review_mode=args.review_mode,
                save_intermediate_files=args.save_intermediate_files,
            )
            
            # Handle multi-phase results
            if isinstance(result, list):
                # Multi-phase review
                output_paths = [r[0] for r in result]
                gemini_paths = [r[1] for r in result if r[1]]
                output_path = output_paths[0] if output_paths else None
                gemini_path = gemini_paths[0] if gemini_paths else None
            else:
                # Single phase result
                output_path, gemini_path = result
        else:
            # Standard single-file workflow
            output_path, gemini_path = generate_code_review_context_main(
                project_path=args.project_path,
                phase=args.phase,
                output=args.output,
                enable_gemini_review=enable_gemini,
                scope=args.scope,
                phase_number=args.phase_number,
                task_number=args.task_number,
                temperature=temperature,
                task_list=args.task_list,
                default_prompt=args.default_prompt,
                compare_branch=args.compare_branch,
                target_branch=args.target_branch,
                github_pr_url=args.github_pr_url,
                include_claude_memory=args.include_claude_memory,
                include_cursor_rules=args.include_cursor_rules,
                thinking_budget=args.thinking_budget,
                url_context=args.url_context,
                context_strategy=args.context_strategy,
                max_context_tokens=args.max_context_tokens,
                per_file_token_limit=args.per_file_token_limit,
            )

        print("\n🎉 Code review process completed!")
        files_generated = [os.path.basename(output_path)]
        if gemini_path:
            files_generated.append(os.path.basename(gemini_path))
        print(f"📄 Files generated: {', '.join(files_generated)}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Entry point for installed package."""
    cli_main()


if __name__ == "__main__":
    cli_main()
