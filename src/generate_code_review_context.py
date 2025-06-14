#!/usr/bin/env python3
"""
Generate code review context by parsing PRD, task lists, and git changes.

This is now a thin wrapper that imports functionality from modularized components.
The main implementation has been split into smaller, focused modules for better
maintainability and testing.

Note: Helper functions are re-exported for backward compatibility. For new code,
consider importing directly from the specific modules:
- cli_main: CLI argument parsing and validation
- context_generator: Core review context generation
- model_config_manager: Model configuration management
"""

import logging
from typing import Any, List, Optional, Union

# Import only what's actually used in this module
try:
    # Try relative imports first (when used as a package)
    from .context_generator import (
        generate_review_context_data,
        process_and_output_review,
    )

except ImportError:
    # Fallback to absolute imports (when modules are imported directly)
    from context_generator import (
        generate_review_context_data,
        process_and_output_review,
    )


# Import configuration types
try:
    from .config_types import CodeReviewConfig
except ImportError:
    from config_types import CodeReviewConfig


# Re-export CLI functions for backward compatibility
# These are imported lazily to avoid circular imports
def suggest_path_corrections(*args: Any, **kwargs: Any) -> str:
    """Lazy import wrapper for suggest_path_corrections"""
    try:
        from .cli_main import suggest_path_corrections as _func
    except ImportError:
        from cli_main import suggest_path_corrections as _func
    return _func(*args, **kwargs)


def create_argument_parser(*args: Any, **kwargs: Any) -> Any:
    """Lazy import wrapper for create_argument_parser"""
    try:
        from .cli_main import create_argument_parser as _func
    except ImportError:
        from cli_main import create_argument_parser as _func
    return _func(*args, **kwargs)


def validate_cli_arguments(*args: Any, **kwargs: Any) -> None:
    """Lazy import wrapper for validate_cli_arguments"""
    try:
        from .cli_main import validate_cli_arguments as _func
    except ImportError:
        from cli_main import validate_cli_arguments as _func
    return _func(*args, **kwargs)


def execute_auto_prompt_workflow(*args: Any, **kwargs: Any) -> str:
    """Lazy import wrapper for execute_auto_prompt_workflow"""
    try:
        from .cli_main import execute_auto_prompt_workflow as _func
    except ImportError:
        from cli_main import execute_auto_prompt_workflow as _func
    return _func(*args, **kwargs)


def format_auto_prompt_output(*args: Any, **kwargs: Any) -> str:
    """Lazy import wrapper for format_auto_prompt_output"""
    try:
        from .cli_main import format_auto_prompt_output as _func
    except ImportError:
        from cli_main import format_auto_prompt_output as _func
    return _func(*args, **kwargs)


def detect_execution_mode(*args: Any, **kwargs: Any) -> str:
    """Lazy import wrapper for detect_execution_mode"""
    try:
        from .cli_main import detect_execution_mode as _func
    except ImportError:
        from cli_main import detect_execution_mode as _func
    return _func(*args, **kwargs)


def cli_main(*args: Any, **kwargs: Any) -> None:
    """Lazy import wrapper for cli_main"""
    try:
        from .cli_main import cli_main as _func
    except ImportError:
        from cli_main import cli_main as _func
    return _func(*args, **kwargs)


def main(*args: Any, **kwargs: Any) -> None:
    """Lazy import wrapper for main"""
    try:
        from .cli_main import main as _func
    except ImportError:
        from cli_main import main as _func
    return _func(*args, **kwargs)


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Import for re-export
def load_model_config(*args: Any, **kwargs: Any) -> Any:
    """Lazy import wrapper for load_model_config"""
    try:
        from .model_config_manager import load_model_config as _func
    except ImportError:
        from model_config_manager import load_model_config as _func
    return _func(*args, **kwargs)


# Re-export for backward compatibility
__all__ = ["CodeReviewConfig", "load_model_config"]


def generate_code_review_context_main(
    project_path: Optional[str] = None,
    phase: Optional[str] = None,
    output: Optional[str] = None,
    enable_gemini_review: bool = True,
    scope: str = "recent_phase",
    phase_number: Optional[str] = None,
    task_number: Optional[str] = None,
    temperature: float = 0.5,
    task_list: Optional[str] = None,
    default_prompt: Optional[str] = None,
    compare_branch: Optional[str] = None,
    target_branch: Optional[str] = None,
    github_pr_url: Optional[str] = None,
    include_claude_memory: bool = False,
    include_cursor_rules: bool = False,
    raw_context_only: bool = False,
    auto_prompt_content: Optional[str] = None,
    thinking_budget: Optional[int] = None,
    url_context: Optional[Union[str, List[str]]] = None,
) -> tuple[str, Optional[str]]:
    """
    Generate code review context with enhanced configuration discovery.

    This is the main entry point that coordinates all the modularized components.
    It now delegates to specialized modules for each aspect of the generation process.

    Args:
        project_path: Path to project root
        phase: Legacy parameter - specific phase to review (deprecated, use scope/phase_number)
        output: Custom output file path
        enable_gemini_review: Whether to run Gemini AI review
        scope: Review scope - "recent_phase", "full_project", "specific_phase", "specific_task"
        phase_number: Phase number for specific_phase scope (e.g., "2.0")
        task_number: Task number for specific_task scope (e.g., "1.2")
        temperature: Temperature for AI model (0.0-2.0)
        task_list: Specific task list file to use (e.g., 'tasks-feature-x.md')
        default_prompt: Custom default prompt when no task list exists
        compare_branch: Branch to compare against target (deprecated - use github_pr_url)
        target_branch: Target branch for comparison (deprecated - use github_pr_url)
        github_pr_url: GitHub PR URL to review
        include_claude_memory: Whether to include CLAUDE.md files
        include_cursor_rules: Whether to include Cursor rules files
        raw_context_only: Exclude AI review instructions (for intermediate processing)
        auto_prompt_content: Pre-generated meta-prompt content to use

    Returns:
        Tuple of (context_file_path, gemini_review_path)
    """
    # Create configuration object
    config = CodeReviewConfig(
        project_path=project_path,
        phase=phase,
        output=output,
        enable_gemini_review=enable_gemini_review,
        scope=scope,
        phase_number=phase_number,
        task_number=task_number,
        temperature=temperature,
        task_list=task_list,
        default_prompt=default_prompt,
        compare_branch=compare_branch,
        target_branch=target_branch,
        github_pr_url=github_pr_url,
        include_claude_memory=include_claude_memory,
        include_cursor_rules=include_cursor_rules,
        raw_context_only=raw_context_only,
        auto_prompt_content=auto_prompt_content,
        thinking_budget=thinking_budget,
        url_context=url_context,
    )

    return _generate_code_review_context_impl(config)


def _generate_code_review_context_impl(
    config: CodeReviewConfig,
) -> tuple[str, Optional[str]]:
    """
    Internal implementation using the new modularized architecture.

    This function now orchestrates calls to specialized modules:
    1. context_generator.generate_review_context_data() for data gathering
    2. context_generator.process_and_output_review() for output generation
    """
    try:
        # Step 1: Generate all review context data
        template_data = generate_review_context_data(config)

        # Step 2: Process and output the review
        return process_and_output_review(config, template_data)

    except Exception as e:
        logger.error(f"Error generating review context: {e}")
        raise


# For backward compatibility, keep the module runnable
if __name__ == "__main__":
    from cli_main import cli_main

    cli_main()
