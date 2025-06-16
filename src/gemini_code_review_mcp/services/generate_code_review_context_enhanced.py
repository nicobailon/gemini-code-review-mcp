#!/usr/bin/env python3
"""
Enhanced code review context generation with multi-phase support.

This module provides the main entry point for multi-phase code review generation,
handling large changesets by intelligently splitting them into phases.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple, TypedDict, Union

from ..config_types import CodeReviewConfig
from .context_generator import process_and_output_review
from .context_generator_enhanced import (
    BaseTemplateData,
    generate_context_data_multi_phase,
    process_and_output_multi_phase_review,
    generate_phase_template_data,
)
from .template_formatter import format_review_template

logger = logging.getLogger(__name__)


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
    context_strategy: str = "balanced",
    max_context_tokens: Optional[int] = None,
    per_file_token_limit: int = 10_000,
    review_mode: str = "multi-phase",
    save_intermediate_files: bool = False,
) -> Union[Tuple[str, Optional[str]], List[Tuple[str, Optional[str]]]]:
    """
    Generate code review context with multi-phase support.
    
    Args:
        Same as original, plus:
        review_mode: "single" (force single file), "multi-phase" (split if needed), "overview-only"
        
    Returns:
        For single mode: Tuple of (context_file_path, gemini_review_path)
        For multi-phase mode: List of tuples, one per phase
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
        context_strategy=context_strategy,
        max_context_tokens=max_context_tokens,
        per_file_token_limit=per_file_token_limit,
        review_mode=review_mode,
        save_intermediate_files=save_intermediate_files,
    )
    
    return _generate_code_review_context_impl(config)


def _generate_code_review_context_impl(
    config: CodeReviewConfig,
) -> Union[Tuple[str, Optional[str]], List[Tuple[str, Optional[str]]]]:
    """
    Internal implementation with multi-phase support.
    """
    try:
        # Generate context data with multi-phase support
        base_data, multi_phase_context = generate_context_data_multi_phase(config)
        
        # Handle overview-only mode
        if config.review_mode == "overview-only":
            if multi_phase_context:
                # Generate overview with manifest
                overview_content = [
                    "# Code Review Overview - Change Manifest",
                    "",
                    multi_phase_context.manifest.to_markdown(),
                    "",
                    "## Review Strategy",
                    f"Model: {multi_phase_context.model_name}",
                    f"Strategy: {multi_phase_context.strategy}",
                    f"Total files: {multi_phase_context.manifest.total_files}",
                    f"Would require {len(multi_phase_context.phases)} phases for full review",
                    "",
                    "### File Categories",
                ]
                
                # Add category breakdown
                from collections import Counter
                category_counts = Counter(e.category.value for e in multi_phase_context.manifest.entries)
                for category, count in category_counts.most_common():
                    overview_content.append(f"- {category.replace('_', ' ').title()}: {count} files")
                
                # Save overview
                output_path = os.path.join(
                    config.project_path or os.getcwd(),
                    "code-review-overview.md"
                )
                with open(output_path, "w") as f:
                    f.write('\n'.join(overview_content))
                
                print(f"📋 Generated change overview: {os.path.basename(output_path)}")
                return [(output_path, None)]
            else:
                # Single phase overview
                print("ℹ️  All files fit in single phase - generating standard review")
                return _handle_single_phase(config, base_data)
        
        # Check if multi-phase is needed
        if multi_phase_context and config.review_mode != "single":
            # Multi-phase review needed
            return process_and_output_multi_phase_review(config, base_data, multi_phase_context)
        else:
            # Single phase is sufficient or forced
            return _handle_single_phase(config, base_data)
            
    except Exception as e:
        logger.error(f"Error generating review context: {e}")
        raise


def _handle_single_phase(
    config: CodeReviewConfig,
    base_data: BaseTemplateData
) -> List[Tuple[str, Optional[str]]]:
    """Handle single-phase review generation."""
    # For single phase, use the original context_generator flow
    from .context_generator import generate_review_context_data, process_and_output_review
    
    # Generate standard template data
    template_data = generate_review_context_data(config)
    
    # Process and output
    # Wrap single result in a list to match expected return type
    result = process_and_output_review(config, template_data)
    return [result]