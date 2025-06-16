"""Dedicated multi-phase review tool for explicit phase handling."""

import os
from datetime import datetime
from typing import Dict, List, Optional, Union

from ..config_types import CodeReviewConfig
from ..services.context_generator_enhanced import (
    generate_context_data_multi_phase,
    process_and_output_multi_phase_review,
)


async def generate_multiphase_review(
    project_path: Optional[str] = None,
    github_pr_url: Optional[str] = None,
    scope: str = "full_project",
    phase_number: Optional[str] = None,
    task_number: Optional[str] = None,
    task_list: Optional[str] = None,
    default_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.5,
    auto_meta_prompt: bool = True,
    include_claude_memory: bool = True,
    include_cursor_rules: bool = False,
    thinking_budget: Optional[int] = None,
    url_context: Optional[Union[str, List[str]]] = None,
    context_strategy: str = "balanced",
    max_context_tokens: Optional[int] = None,
    per_file_token_limit: int = 10_000,
    output_format: str = "structured",
    phases_to_process: Optional[List[int]] = None,
) -> Union[str, Dict[str, Union[str, List[Dict[str, str]]]]]:
    """
    Generate multi-phase code review with explicit control over phases.
    
    This dedicated tool provides better control over multi-phase reviews,
    allowing users to:
    - Get structured output with phase metadata
    - Process specific phases only
    - Access individual phase results programmatically
    
    Args:
        project_path: Project path for analysis
        github_pr_url: GitHub PR URL for PR-based reviews
        scope: Review scope - 'recent_phase', 'full_project', 'specific_phase', 'specific_task'
        phase_number: Phase number for specific_phase scope
        task_number: Task number for specific_task scope
        task_list: Specific task list file to use
        default_prompt: Custom default prompt when no task list exists
        model: Optional Gemini model name
        temperature: Temperature for AI model (0.0-2.0)
        auto_meta_prompt: Automatically generate meta prompt
        include_claude_memory: Include CLAUDE.md files
        include_cursor_rules: Include Cursor rules files
        thinking_budget: Optional token budget for thinking mode
        url_context: Optional URL(s) to include in context
        context_strategy: 'focused', 'balanced', 'comprehensive'
        max_context_tokens: Override maximum context tokens
        per_file_token_limit: Maximum tokens per file
        output_format: 'structured' (dict) or 'markdown' (string)
        phases_to_process: List of phase numbers to process (e.g., [1, 3])
        
    Returns:
        If output_format='structured':
            Dict with keys:
            - summary: Multi-phase summary info
            - phases: List of phase results with metadata
            - manifest: Phase manifest markdown
            - metadata: Review metadata
            
        If output_format='markdown':
            Formatted markdown string with all phases
    """
    try:
        # Validate inputs
        if not project_path and not github_pr_url:
            raise ValueError("Either project_path or github_pr_url is required")
        
        if project_path and not os.path.isabs(project_path):
            return {"error": "project_path must be an absolute path"}
        
        if temperature == 0.5:
            temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.5"))
        
        # Create configuration
        config = CodeReviewConfig(
            project_path=project_path or os.getcwd(),
            github_pr_url=github_pr_url,
            scope=scope,
            phase_number=phase_number,
            task_number=task_number,
            task_list=task_list,
            default_prompt=default_prompt,
            temperature=temperature,
            enable_gemini_review=True,
            include_claude_memory=include_claude_memory,
            include_cursor_rules=include_cursor_rules,
            thinking_budget=thinking_budget,
            url_context=url_context,
            context_strategy=context_strategy,
            max_context_tokens=max_context_tokens,
            per_file_token_limit=per_file_token_limit,
            review_mode="multi-phase",  # Always multi-phase for this tool
            save_intermediate_files=False,  # Keep in memory
            auto_meta_prompt=auto_meta_prompt,
        )
        
        # Generate context with multi-phase support
        base_data, multi_phase_context = generate_context_data_multi_phase(config)
        
        if not multi_phase_context:
            # Single phase was sufficient
            return {
                "summary": {
                    "status": "single_phase",
                    "message": "Content fits in a single phase",
                    "total_files": len(base_data.get("changed_files", [])),
                },
                "phases": [],
                "manifest": "Single phase review - no manifest needed",
                "metadata": {
                    "model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                    "strategy": context_strategy,
                }
            }
        
        # Get phase results
        phase_results = process_and_output_multi_phase_review(
            config, base_data, multi_phase_context, return_phase_results=True
        )
        
        # Filter phases if requested
        if phases_to_process:
            phase_results = [
                pr for pr in phase_results 
                if pr.phase_number in phases_to_process
            ]
        
        # Build structured output
        if output_format == "structured":
            phases_data = []
            for phase_result in phase_results:
                phase_data = {
                    "phase_number": phase_result.phase_number,
                    "phase_name": phase_result.phase_name,
                    "file_count": len(phase_result.context_content.split('### File:')) - 1 if phase_result.context_content else 0,
                    "has_review": bool(phase_result.review_content),
                }
                
                # Include review content if available
                if phase_result.review_content:
                    phase_data["review"] = phase_result.review_content
                
                # Include token info from multi_phase_context
                for phase in multi_phase_context.phases:
                    if phase.phase_number == phase_result.phase_number:
                        phase_data["token_count"] = phase.token_count
                        phase_data["token_limit"] = phase.token_limit
                        phase_data["utilization"] = f"{(phase.token_count / phase.token_limit * 100):.1f}%"
                        break
                
                phases_data.append(phase_data)
            
            return {
                "summary": {
                    "status": "multi_phase",
                    "total_phases": len(multi_phase_context.phases),
                    "phases_processed": len(phase_results),
                    "total_files": sum(p.file_count for p in multi_phase_context.phases),
                    "total_tokens": multi_phase_context.total_tokens_all_phases,
                    "model": multi_phase_context.model_name,
                    "strategy": multi_phase_context.strategy,
                },
                "phases": phases_data,
                "manifest": multi_phase_context.manifest.to_markdown(),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "token_limit_per_phase": getattr(multi_phase_context, 'token_limit', 60000),
                }
            }
        
        else:  # markdown format
            # Build formatted markdown output
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            markdown_parts = [
                "# 🔄 MULTI-PHASE CODE REVIEW REPORT",
                f"Generated: {timestamp}",
                f"Project: {project_path or 'GitHub PR'}",
                f"Model: {multi_phase_context.model_name}",
                f"Total Phases: {len(multi_phase_context.phases)}",
                f"Phases Processed: {len(phase_results)}",
                "",
                "=" * 80,
                "",
                "## 📊 PHASE MANIFEST",
                "",
                multi_phase_context.manifest.to_markdown(),
                "",
                "=" * 80,
                "",
            ]
            
            # Add individual phase reviews
            for phase_result in phase_results:
                phase_info = next(
                    (p for p in multi_phase_context.phases if p.phase_number == phase_result.phase_number),
                    None
                )
                
                markdown_parts.extend([
                    f"## 📄 PHASE {phase_result.phase_number}/{len(multi_phase_context.phases)}: {phase_result.phase_name}",
                    f"Files: {phase_info.file_count if phase_info else 'N/A'}",
                    f"Tokens: {phase_info.token_count if phase_info else 'N/A'} ({(phase_info.token_count / phase_info.token_limit * 100):.1f}% utilization)" if phase_info else "",
                    "",
                ])
                
                if phase_result.review_content:
                    markdown_parts.extend([
                        "### Review Content:",
                        "",
                        phase_result.review_content,
                        "",
                    ])
                else:
                    markdown_parts.append("⚠️ Review not generated for this phase\n")
                
                markdown_parts.extend(["=" * 80, ""])
            
            # Add metadata footer
            markdown_parts.extend([
                "## 📋 REVIEW METADATA",
                f"- Total Files Reviewed: {sum(p.file_count for p in multi_phase_context.phases)}",
                f"- Total Tokens Used: {multi_phase_context.total_tokens_all_phases:,}",
                f"- Token Strategy: {multi_phase_context.strategy}",
                f"- Phases to Process Filter: {phases_to_process if phases_to_process else 'All phases'}",
                "",
                "---",
                "End of Multi-Phase Code Review Report",
            ])
            
            return '\n'.join(markdown_parts)
    
    except Exception as e:
        if output_format == "structured":
            return {"error": str(e)}
        else:
            return f"ERROR: {str(e)}"