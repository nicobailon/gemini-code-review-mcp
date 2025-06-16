"""Validation utilities for code review configurations and parameters."""

import re
from typing import List

from ..config_types import CodeReviewConfig
from ..errors import ConfigurationError


def validate_review_mode(config: CodeReviewConfig) -> str:
    """Detect and validate review mode.
    
    Args:
        config: Code review configuration
        
    Returns:
        The detected review mode
        
    Raises:
        ConfigurationError: If multiple conflicting modes are detected
    """
    review_modes: List[str] = []
    if config.github_pr_url:
        review_modes.append("github_pr")
    if not review_modes:
        review_modes.append("task_list_based")

    # Validate mutually exclusive modes
    if len(review_modes) > 1:
        error_msg = """Multiple review modes detected. Please use only one:

Working examples:
  # Task list based review (default)
  generate-code-review .
  
  # Branch comparison review
  generate-code-review . --compare-branch feature/auth
  
  # GitHub PR review  
  generate-code-review --github-pr-url https://github.com/owner/repo/pull/123
  
  # NOT valid - conflicting modes
  generate-code-review . --compare-branch feature/auth --github-pr-url https://github.com/owner/repo/pull/123"""
        raise ConfigurationError(error_msg)
    
    return review_modes[0]


def validate_scope_parameters(config: CodeReviewConfig) -> None:
    """Validate scope and related parameters.
    
    Args:
        config: Code review configuration
        
    Raises:
        ConfigurationError: If scope or related parameters are invalid
    """
    # Validate scope parameter
    valid_scopes = ["recent_phase", "full_project", "specific_phase", "specific_task"]
    if config.scope not in valid_scopes:
        raise ConfigurationError(
            f"Invalid scope '{config.scope}'. Must be one of: {', '.join(valid_scopes)}"
        )

    # Validate scope-specific parameters
    if config.scope == "specific_phase":
        if not config.phase_number:
            error_msg = """phase_number is required when scope is 'specific_phase'

Working examples:
  # Review a specific phase
  generate-code-review . --scope specific_phase --phase-number 2.0
  
  # Review first phase
  generate-code-review . --scope specific_phase --phase-number 1.0
  
  # Use environment variable for API key
  GEMINI_API_KEY=your_key generate-code-review . --scope specific_phase --phase-number 3.0"""
            raise ConfigurationError(error_msg)
        if not re.match(r"^\d+\.0$", config.phase_number):
            error_msg = f"""Invalid phase_number format '{config.phase_number}'. Must be in format 'X.0'

Working examples:
  # Correct formats
  generate-code-review . --scope specific_phase --phase-number 1.0
  generate-code-review . --scope specific_phase --phase-number 2.0
  generate-code-review . --scope specific_phase --phase-number 10.0
  
  # Incorrect formats
  --phase-number 1    ❌ (missing .0)
  --phase-number 1.1  ❌ (phases end in .0)
  --phase-number v1.0 ❌ (no prefix allowed)"""
            raise ConfigurationError(error_msg)

    if config.scope == "specific_task":
        if not config.task_number:
            error_msg = """task_number is required when scope is 'specific_task'

Working examples:
  # Review a specific task
  generate-code-review . --scope specific_task --task-number 1.2
  
  # Review first subtask of phase 2
  generate-code-review . --scope specific_task --task-number 2.1
  
  # Use with custom temperature
  generate-code-review . --scope specific_task --task-number 3.4 --temperature 0.3"""
            raise ConfigurationError(error_msg)
        if not re.match(
            r"^\d+\.\d+$", config.task_number
        ) or config.task_number.endswith(".0"):
            error_msg = f"""Invalid task_number format '{config.task_number}'. Must be in format 'X.Y'

Working examples:
  # Correct formats
  generate-code-review . --scope specific_task --task-number 1.1
  generate-code-review . --scope specific_task --task-number 2.3
  generate-code-review . --scope specific_task --task-number 10.15
  
  # Incorrect formats
  --task-number 1     ❌ (missing subtask number)
  --task-number 1.0   ❌ (use specific_phase for X.0)
  --task-number 1.a   ❌ (must be numeric)"""
            raise ConfigurationError(error_msg)


def validate_github_pr_url(pr_url: str) -> None:
    """Validate GitHub PR URL format.
    
    Args:
        pr_url: GitHub PR URL to validate
        
    Raises:
        ConfigurationError: If URL is invalid
    """
    try:
        # Import here to avoid circular imports
        from .github_pr_integration import parse_github_pr_url
        
        # Check if GitHub PR integration is available
        if not parse_github_pr_url:
            raise ImportError("GitHub PR integration not available")
        parse_github_pr_url(pr_url)  # This will raise ValueError if invalid
    except ValueError as e:
        error_msg = f"""Invalid GitHub PR URL: {e}

Working examples:
  # Standard GitHub PR
  generate-code-review --github-pr-url https://github.com/microsoft/vscode/pull/123
  
  # GitHub Enterprise
  generate-code-review --github-pr-url https://github.company.com/team/project/pull/456
  
  # With additional parameters
  generate-code-review --github-pr-url https://github.com/owner/repo/pull/789 --temperature 0.3"""
        raise ConfigurationError(error_msg)