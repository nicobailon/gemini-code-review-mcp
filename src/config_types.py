#!/usr/bin/env python3
"""
Configuration types module.

This module defines shared configuration types used across the codebase.
"""

from dataclasses import dataclass
from typing import Optional, Union, List

# Central configuration defaults
DEFAULT_INCLUDE_CLAUDE_MEMORY = False
DEFAULT_INCLUDE_CURSOR_RULES = False


@dataclass
class CodeReviewConfig:
    """Configuration for code review generation."""

    project_path: Optional[str] = None
    phase: Optional[str] = None
    output: Optional[str] = None
    enable_gemini_review: bool = True
    scope: str = "recent_phase"
    phase_number: Optional[str] = None
    task_number: Optional[str] = None
    temperature: float = 0.5
    task_list: Optional[str] = None
    default_prompt: Optional[str] = None
    compare_branch: Optional[str] = None
    target_branch: Optional[str] = None
    github_pr_url: Optional[str] = None
    include_claude_memory: bool = DEFAULT_INCLUDE_CLAUDE_MEMORY
    include_cursor_rules: bool = DEFAULT_INCLUDE_CURSOR_RULES
    raw_context_only: bool = False
    auto_prompt_content: Optional[str] = None
    thinking_budget: Optional[int] = None
    url_context: Optional[Union[str, List[str]]] = None
