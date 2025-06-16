"""Enhanced GitHub PR review tool with multi-phase support."""

import datetime
import os
from typing import List, Optional, Union

from ..config_types import CodeReviewConfig
from ..services.context_generator_enhanced import (
    generate_context_data_multi_phase,
    process_and_output_multi_phase_review,
    generate_phase_template_data,
)
from ..services.template_formatter import format_review_template
from ..services.gemini_api_client import send_to_gemini_for_review


async def generate_pr_review(
    github_pr_url: Optional[str] = None,
    project_path: Optional[str] = None,
    temperature: float = 0.5,
    enable_gemini_review: bool = True,
    include_claude_memory: bool = True,
    include_cursor_rules: bool = False,
    auto_meta_prompt: bool = True,
    use_templated_instructions: bool = False,
    create_context_file: bool = False,
    raw_context_only: bool = False,
    text_output: bool = False,
    thinking_budget: Optional[int] = None,
    url_context: Optional[Union[str, List[str]]] = None,
    context_strategy: str = "balanced",
    max_context_tokens: Optional[int] = None,
    per_file_token_limit: int = 10_000,
    review_mode: str = "multi-phase",
    save_intermediate_files: bool = False,
) -> str:
    """
    Enhanced PR review with automatic multi-phase support for large PRs.
    
    Same parameters as before, plus:
        context_strategy: Token management strategy
        max_context_tokens: Override token limit
        per_file_token_limit: Max tokens per file
        review_mode: "single", "multi-phase", or "overview-only"
    """
    try:
        # Validate required parameters
        if not github_pr_url:
            return "ERROR: github_pr_url is required"
        
        # Use current directory if project_path not provided
        if not project_path:
            project_path = os.getcwd()
        
        if not os.path.isabs(project_path):
            return "ERROR: project_path must be an absolute path"
        
        if not os.path.exists(project_path):
            return f"ERROR: Project path does not exist: {project_path}"
        
        if not os.path.isdir(project_path):
            return f"ERROR: Project path must be a directory: {project_path}"
        
        # Create configuration
        config = CodeReviewConfig(
            project_path=project_path,
            github_pr_url=github_pr_url,
            temperature=temperature,
            enable_gemini_review=enable_gemini_review and not raw_context_only,
            include_claude_memory=include_claude_memory,
            include_cursor_rules=include_cursor_rules,
            raw_context_only=raw_context_only,
            thinking_budget=thinking_budget,
            url_context=url_context,
            context_strategy=context_strategy,
            max_context_tokens=max_context_tokens,
            per_file_token_limit=per_file_token_limit,
            review_mode=review_mode,
            save_intermediate_files=save_intermediate_files,
        )
        
        # Generate context data with multi-phase support
        base_data, multi_phase_context = generate_context_data_multi_phase(config)
        
        # Handle different modes
        if raw_context_only:
            # Generate context without AI review
            if multi_phase_context and review_mode != "single":
                # Multi-phase raw context
                if text_output:
                    # For text output, return phase 1 context
                    phase = multi_phase_context.phases[0]
                    manifest_markdown = multi_phase_context.manifest.to_markdown()
                    phase_data = generate_phase_template_data(
                        base_data, phase, manifest_markdown, config
                    )
                    return format_review_template(phase_data)
                else:
                    # Save all phase files
                    results = process_and_output_multi_phase_review(
                        config, base_data, multi_phase_context
                    )
                    return f"Generated {len(results)} phase context files for large PR"
            else:
                # Single phase raw context
                from ..services.context_generator import (
                    generate_review_context_data,
                    process_and_output_review,
                )
                template_data = generate_review_context_data(config)
                
                if text_output:
                    return format_review_template(template_data)
                else:
                    output_path, _ = process_and_output_review(config, template_data)
                    return f"Code review context generated successfully: {os.path.basename(output_path)}"
        
        # Full review mode
        if multi_phase_context and review_mode != "single":
            # Multi-phase review
            results = process_and_output_multi_phase_review(
                config, base_data, multi_phase_context
            )
            
            if text_output:
                # For text output, return phase summaries
                summary_lines = [
                    f"# Multi-Phase PR Review Generated",
                    f"PR: {github_pr_url}",
                    f"Total files: {multi_phase_context.manifest.total_files}",
                    f"Review phases: {len(multi_phase_context.phases)}",
                    "",
                ]
                
                for i, (phase, (context_path, review_path)) in enumerate(zip(multi_phase_context.phases, results)):
                    summary_lines.extend([
                        f"## Phase {phase.phase_number}: {phase.name}",
                        f"Files: {len(phase.included_files)}",
                        f"Context: {os.path.basename(context_path)}",
                        f"Review: {os.path.basename(review_path) if review_path else 'Pending'}",
                        "",
                    ])
                
                return '\n'.join(summary_lines)
            else:
                # Return success message
                return f"Multi-phase PR review completed: {len(results)} phases generated"
        else:
            # Single phase review
            from ..services.context_generator import (
                generate_review_context_data,
                process_and_output_review,
            )
            template_data = generate_review_context_data(config)
            context_path, review_path = process_and_output_review(config, template_data)
            
            if text_output and review_path:
                with open(review_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                files = [os.path.basename(context_path)]
                if review_path:
                    files.append(os.path.basename(review_path))
                return f"PR review completed: {', '.join(files)}"
                
    except Exception as e:
        return f"ERROR: {str(e)}"