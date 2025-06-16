#!/usr/bin/env python3
"""
Enhanced context generator with multi-phase review support.

This module extends the basic context generator to support intelligent
multi-phase reviews when dealing with large changesets.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, TypedDict, Union

from ..config_types import CodeReviewConfig
from ..errors import ConfigurationError
from ..models.review_context import ReviewContext
from ..models.review_mode import ReviewMode
from ..models.task_info import TaskInfo
from ..models.converters import review_context_to_dict
from .task_list_parser import TaskData as ParserTaskData
from .context_generator import (
    handle_task_list_mode,
    extract_prd_summary,
    process_review_scope,
    discover_configurations,
    gather_changes,
    convert_to_file_info,
    create_minimal_task_data,
)
from .context_builder import (
    format_configuration_context_for_ai,
    get_applicable_rules_for_files,
)
from .template_formatter import format_review_template
from .token_manager_enhanced import (
    MultiPhaseContextBuilder,
    MultiPhaseContext,
    ReviewPhase,
    generate_multi_phase_summary,
)
from ..helpers.git_utils import generate_file_tree
from ..helpers.model_config_manager import load_model_config
from .gemini_api_client import send_to_gemini_for_review

logger = logging.getLogger(__name__)


@dataclass
class PhaseResult:
    """Holds phase content and optional file paths."""
    phase_number: int
    phase_name: str
    context_content: str
    review_content: Optional[str] = None
    context_file_path: Optional[str] = None
    review_file_path: Optional[str] = None


# Use TaskData from task_list_parser to avoid type conflicts
TaskData = ParserTaskData


class DiscoveredConfigurations(TypedDict):
    """Type definition for discovered configurations."""
    claude_memory_files: List[Dict[str, str]]
    cursor_rules: List[Dict[str, Union[str, List[str]]]]
    discovery_errors: List[str]
    performance_stats: Dict[str, float]


class PRData(TypedDict, total=False):
    """Type definition for PR data."""
    mode: str
    pr_data: Dict[str, Union[str, int]]
    summary: Dict[str, int]
    repository: Dict[str, str]


class BaseTemplateData(TypedDict):
    """Type definition for base template data."""
    review_mode: str
    task_data: TaskData
    prd_summary: Optional[str]
    effective_scope: str
    configurations: DiscoveredConfigurations
    pr_data: Optional[PRData]
    project_path: Optional[str]
    file_tree: str
    configuration_content: str
    url_context_content: Optional[str]
    raw_context_only: bool


def generate_context_data_multi_phase(config: CodeReviewConfig) -> Tuple[BaseTemplateData, Optional[MultiPhaseContext]]:
    """
    Generate context data with multi-phase support.
    
    Returns:
        Tuple of (base_template_data, multi_phase_context)
        If multi_phase_context is None, single phase was sufficient.
    """
    # Step 1: Determine review mode
    review_mode = "github_pr" if config.github_pr_url else "task_list_based"
    
    # Display review mode
    if review_mode == "github_pr":
        print("🔗 Review mode: GitHub PR analysis")
        print(f"🌐 PR URL: {config.github_pr_url}")
    else:
        print(f"📊 Review scope: {config.scope}")
    
    # Step 2: Load model config and prepare task data
    model_config = load_model_config()
    prd_summary = None
    task_data = None
    
    if review_mode == "github_pr":
        prd_summary = "GitHub Pull Request Code Review"
        task_data = create_minimal_task_data("PR Review", "Pull Request code review")
    elif config.task_list:
        task_data = handle_task_list_mode(config)
        prd_summary = extract_prd_summary(config, task_data)
    else:
        logger.info("General review mode - task-list discovery skipped")
        prd_summary = config.default_prompt or model_config["defaults"]["default_prompt"]
        task_data = create_minimal_task_data(
            "General Review", "Code review without specific task context"
        )
    
    assert task_data is not None, "task_data should be initialized"
    
    # Step 3: Process scope-based review logic
    effective_scope = process_review_scope(config, task_data)
    
    # Step 4: Discover configuration files
    configurations = discover_configurations(config)
    
    # Step 5: Gather git changes or PR data
    changed_files, pr_data = gather_changes(config, review_mode)
    
    # Step 6: Apply multi-phase token management
    file_infos = convert_to_file_info(changed_files)
    
    # Get current model from environment or config
    # Default to Gemini Flash 2.0 for cost efficiency
    current_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    if "GEMINI_MODEL" not in os.environ:
        print("💡 Using gemini-2.0-flash for cost-efficient processing")
    
    # Check if multi-phase is explicitly disabled
    enable_multi_phase = config.review_mode != "single"
    
    # Build context with multi-phase support
    multi_phase_builder = MultiPhaseContextBuilder(
        model_name=current_model,
        strategy=config.context_strategy,
        max_tokens_override=config.max_context_tokens,
        per_file_limit=config.per_file_token_limit,
        enable_multi_phase=enable_multi_phase
    )
    
    result = multi_phase_builder.build_context(file_infos)
    
    # Check if we got multi-phase context
    multi_phase_context = None
    if isinstance(result, MultiPhaseContext):
        multi_phase_context = result
        print("\n" + generate_multi_phase_summary(multi_phase_context))
    else:
        # Single phase was sufficient
        print(f"\n✅ Single phase review: All {len(result)} files fit within token limits")
    
    # Build base template data (common to all phases)
    if not config.project_path:
        raise ConfigurationError("Project path is required for file tree generation")
    file_tree = generate_file_tree(config.project_path)
    
    # Get configuration content
    configuration_content = format_configuration_context_for_ai(
        configurations["claude_memory_files"], 
        configurations["cursor_rules"]
    )
    
    # Process URL context
    url_context_content = None
    if config.url_context:
        urls = config.url_context if isinstance(config.url_context, list) else [config.url_context]
        if urls:
            url_context_content = "\n## Additional Context URLs\n\n"
            url_context_content += "Please analyze the following URLs for additional context:\n"
            for url in urls:
                url_context_content += f"- {url}\n"
    
    # Create base template data
    base_template_data: BaseTemplateData = {
        "review_mode": review_mode,
        "task_data": task_data,
        "prd_summary": prd_summary,
        "effective_scope": effective_scope,
        "configurations": configurations,
        "pr_data": pr_data,
        "project_path": config.project_path,
        "file_tree": file_tree,
        "configuration_content": configuration_content,
        "url_context_content": url_context_content,
        "raw_context_only": config.raw_context_only,
    }
    
    return base_template_data, multi_phase_context


def generate_phase_template_data(
    base_data: BaseTemplateData,
    phase: ReviewPhase,
    manifest_markdown: str,
    config: CodeReviewConfig
) -> Dict[str, object]:
    """Generate template data for a specific phase."""
    # Convert phase files back to changed_files format
    changed_files = []
    for file_info in phase.included_files:
        changed_file = {
            "path": file_info.path,
            "file_path": file_info.path,
            "status": file_info.status,
            "content": file_info.content,
            "additions": file_info.additions,
            "deletions": file_info.deletions,
        }
        changed_files.append(changed_file)
    
    # Get applicable rules for this phase's files
    changed_file_paths = [f["path"] for f in changed_files]
    applicable_rules = get_applicable_rules_for_files(
        base_data["configurations"]["cursor_rules"], 
        changed_file_paths
    )
    
    # Create ReviewContext for this phase
    review_mode_enum = ReviewMode.GITHUB_PR if base_data["review_mode"] == "github_pr" else ReviewMode.TASK_DRIVEN
    
    task_info = None
    task_data = base_data["task_data"]
    if task_data.get("current_phase_number") and task_data.get("current_phase_description"):
        task_info = TaskInfo(
            phase_number=str(task_data["current_phase_number"]),
            task_number=str(config.task_number) if config.task_number else None,
            description=task_data["current_phase_description"],
        )
    
    # Generate phase-specific metaprompt if auto_meta_prompt is enabled
    phase_metaprompt = config.auto_prompt_content or ""
    if config.auto_meta_prompt and not config.raw_context_only:
        try:
            from ..services.meta_prompt_analyzer import generate_optimized_meta_prompt
            
            # Generate metaprompt for this specific phase
            # Include phase information in the metaprompt generation
            if not config.project_path:
                raise ConfigurationError("Project path is required for meta prompt generation")
            
            meta_result = generate_optimized_meta_prompt(
                project_path=config.project_path,
                scope=config.scope,
                temperature=config.temperature,
                thinking_budget=config.thinking_budget,
                phase_info={
                    "phase_number": phase.phase_number,
                    "phase_name": phase.name,
                    "total_phases": phase.total_phases,
                    "included_files": changed_file_paths,
                    "file_count": len(changed_file_paths),
                }
            )
            
            phase_specific_prompt = meta_result.get("generated_prompt")
            if phase_specific_prompt:
                phase_metaprompt = phase_specific_prompt
                logger.info(f"Generated phase-specific metaprompt for Phase {phase.phase_number}")
        except Exception as e:
            logger.warning(f"Failed to generate phase-specific metaprompt: {e}")
            # Fall back to the original metaprompt or default
    
    review_context = ReviewContext(
        mode=review_mode_enum,
        default_prompt=phase_metaprompt,
        prd_summary=base_data["prd_summary"],
        task_info=task_info,
        changed_files=changed_file_paths,
    )
    
    # Add phase-specific information
    phase_metadata = phase.to_metadata_markdown()
    
    # Build extra template data
    extra_template_data = {
        "total_phases": task_data.get("total_phases", 0),
        "previous_phase_completed": task_data.get("previous_phase_completed", ""),
        "next_phase": task_data.get("next_phase", ""),
        "subtasks_completed": task_data.get("subtasks_completed", []),
        "project_path": base_data["project_path"],
        "file_tree": base_data["file_tree"],
        "changed_files": changed_files,
        "scope": base_data["effective_scope"],
        "branch_comparison_data": base_data["pr_data"],
        "configuration_content": base_data["configuration_content"],
        "claude_memory_files": base_data["configurations"]["claude_memory_files"],
        "cursor_rules": base_data["configurations"]["cursor_rules"],
        "applicable_rules": applicable_rules,
        "configuration_errors": base_data["configurations"]["discovery_errors"],
        "raw_context_only": base_data["raw_context_only"],
        "url_context_content": base_data["url_context_content"],
        # Multi-phase specific
        "change_manifest": manifest_markdown,
        "phase_metadata": phase_metadata,
        "review_phase_number": phase.phase_number,
        "review_phase_total": phase.total_phases,
    }
    
    # Convert to template data
    return review_context_to_dict(review_context, extra_template_data)


def process_and_output_multi_phase_review(
    config: CodeReviewConfig,
    base_data: BaseTemplateData,
    multi_phase_context: MultiPhaseContext,
    return_phase_results: bool = False
) -> Union[List[Tuple[str, Optional[str]]], List[PhaseResult]]:
    """
    Process and output multi-phase review files.
    
    Args:
        config: Code review configuration
        base_data: Base template data
        multi_phase_context: Multi-phase context data
        return_phase_results: If True, return PhaseResult objects instead of tuples
    
    Returns:
        List of (context_file_path, gemini_review_path) tuples for each phase
        OR List of PhaseResult objects if return_phase_results=True
    """
    phase_results = []
    manifest_markdown = multi_phase_context.manifest.to_markdown()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    for phase in multi_phase_context.phases:
        # Generate template data for this phase
        phase_template_data = generate_phase_template_data(
            base_data, phase, manifest_markdown, config
        )
        
        # Format the review context
        review_context = format_review_template(phase_template_data)
        
        # Create phase result
        phase_result = PhaseResult(
            phase_number=phase.phase_number,
            phase_name=phase.name,
            context_content=review_context,
        )
        
        # Save context file if requested
        if config.save_intermediate_files:
            # Generate phase-specific filename
            phase_suffix = f"phase-{phase.phase_number}-of-{phase.total_phases}"
            
            if base_data["review_mode"] == "github_pr":
                mode_prefix = f"github-pr-{phase_suffix}"
            else:
                mode_prefix = f"{config.scope}-{phase_suffix}"
            
            output_path = os.path.join(
                config.project_path or os.getcwd(),
                f"code-review-context-{mode_prefix}-{timestamp}.md"
            )
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(review_context)
            
            phase_result.context_file_path = output_path
            print(f"\n📝 Generated review context Phase {phase.phase_number}: {os.path.basename(output_path)}")
        else:
            print(f"\n📝 Processing Phase {phase.phase_number} (in memory)")
        
        # Send to Gemini if enabled
        if config.enable_gemini_review:
            print(f"🔄 Sending Phase {phase.phase_number} to Gemini for AI review...")
            
            # Always get review as text first
            review_text = send_to_gemini_for_review(
                review_context,
                config.project_path or os.getcwd(),
                config.temperature,
                thinking_budget=config.thinking_budget,
                return_text=True,  # Always return as text
            )
            
            if review_text:
                phase_result.review_content = review_text
                
                # Save to file if requested
                if config.save_intermediate_files:
                    timestamp_review = datetime.now().strftime("%Y%m%d-%H%M%S")
                    review_path = os.path.join(
                        config.project_path or os.getcwd(),
                        f"code-review-comprehensive-feedback-{timestamp_review}.md"
                    )
                    with open(review_path, "w", encoding="utf-8") as f:
                        f.write(review_text)
                    phase_result.review_file_path = review_path
                    print(f"✅ AI review completed for Phase {phase.phase_number}: {os.path.basename(review_path)}")
                else:
                    print(f"✅ AI review completed for Phase {phase.phase_number} (in memory)")
            else:
                print(f"⚠️  AI review failed for Phase {phase.phase_number}")
        
        phase_results.append(phase_result)
    
    # Collect feedback from all phases for synthesis
    all_feedback = []
    phase_feedback_sections = []
    
    for phase_result in phase_results:
        if phase_result.review_content:
            # Extract main sections from feedback (skip header/footer)
            lines = phase_result.review_content.split('\n')
            main_content = []
            in_main_content = False
            
            for line in lines:
                # Skip header lines
                if line.startswith('# Comprehensive Code Review Feedback'):
                    continue
                elif line.startswith('*Generated on'):
                    in_main_content = True
                    continue
                elif line.startswith('---\n*Review conducted by'):
                    break
                elif in_main_content:
                    main_content.append(line)
            
            phase_feedback = '\n'.join(main_content).strip()
            if phase_feedback:
                all_feedback.append(phase_feedback)
                phase_feedback_sections.append(f"## Phase {phase_result.phase_number} Feedback: {phase_result.phase_name}\n\n{phase_feedback}")
    
    # Generate summary file with all phases info
    summary_content = [
        "# Multi-Phase Code Review Summary",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Model: {multi_phase_context.model_name}",
        f"Strategy: {multi_phase_context.strategy}",
        "",
        multi_phase_context.manifest.to_markdown(),
        "",
    ]
    
    # Add synthesized feedback if available
    if all_feedback:
        summary_content.extend([
            "## 🎯 Synthesized Feedback from All Phases",
            "",
            "This section provides a consolidated view of the key findings from all review phases.",
            "",
        ])
        
        # Extract and deduplicate key themes
        key_themes = {
            "overall_assessment": [],
            "code_quality": [],
            "architecture": [],
            "security": [],
            "performance": [],
            "testing": [],
            "next_steps": []
        }
        
        # Parse feedback to extract themes
        for feedback in all_feedback:
            sections = feedback.split('\n**')
            for section in sections:
                lower_section = section.lower()
                if 'overall assessment' in lower_section:
                    key_themes["overall_assessment"].append(section)
                elif 'code quality' in lower_section or 'best practices' in lower_section:
                    key_themes["code_quality"].append(section)
                elif 'architecture' in lower_section or 'design' in lower_section:
                    key_themes["architecture"].append(section)
                elif 'security' in lower_section:
                    key_themes["security"].append(section)
                elif 'performance' in lower_section:
                    key_themes["performance"].append(section)
                elif 'testing' in lower_section or 'maintainability' in lower_section:
                    key_themes["testing"].append(section)
                elif 'next steps' in lower_section:
                    key_themes["next_steps"].append(section)
        
        # Add consolidated themes to summary
        if key_themes["overall_assessment"]:
            summary_content.extend(["### Overall Assessment", ""])
            summary_content.append("Combined insights from all phases:")
            for assessment in key_themes["overall_assessment"]:
                summary_content.append(assessment.strip())
            summary_content.append("")
        
        if key_themes["code_quality"]:
            summary_content.extend(["### Code Quality & Best Practices", ""])
            summary_content.append("Key code quality findings across all phases:")
            for finding in key_themes["code_quality"]:
                summary_content.append(finding.strip())
            summary_content.append("")
        
        if key_themes["architecture"]:
            summary_content.extend(["### Architecture & Design", ""])
            summary_content.append("Architectural observations from the review:")
            for observation in key_themes["architecture"]:
                summary_content.append(observation.strip())
            summary_content.append("")
        
        if key_themes["security"]:
            summary_content.extend(["### Security Considerations", ""])
            summary_content.append("Security-related findings:")
            for security_item in key_themes["security"]:
                summary_content.append(security_item.strip())
            summary_content.append("")
        
        if key_themes["performance"]:
            summary_content.extend(["### Performance Implications", ""])
            summary_content.append("Performance considerations identified:")
            for perf_item in key_themes["performance"]:
                summary_content.append(perf_item.strip())
            summary_content.append("")
        
        if key_themes["testing"]:
            summary_content.extend(["### Testing & Maintainability", ""])
            summary_content.append("Testing and maintainability insights:")
            for test_item in key_themes["testing"]:
                summary_content.append(test_item.strip())
            summary_content.append("")
        
        if key_themes["next_steps"]:
            summary_content.extend(["### Consolidated Next Steps", ""])
            summary_content.append("Prioritized action items from all phases:")
            # Deduplicate next steps
            unique_steps = set()
            for steps in key_themes["next_steps"]:
                lines = steps.strip().split('\n')
                for line in lines:
                    if line.strip() and line.strip().startswith('*'):
                        unique_steps.add(line.strip())
            for step in sorted(unique_steps):
                summary_content.append(step)
            summary_content.append("")
    
    # Add note about missing phases if any
    failed_phases = [pr.phase_number for pr in phase_results if not pr.review_content]
    if failed_phases:
        summary_content.extend([
            "## ⚠️ Missing Phase Reviews",
            "",
            f"The following phases failed to generate AI reviews: {', '.join(map(str, failed_phases))}",
            "Consider re-running the review for these specific phases or checking the error logs.",
            ""
        ])
    
    # Add phase metadata section
    summary_content.extend([
        "## 📊 Review Phases Metadata",
        ""
    ])
    
    for i, (phase, phase_result) in enumerate(zip(multi_phase_context.phases, phase_results)):
        if config.save_intermediate_files:
            summary_content.extend([
                f"### Phase {phase.phase_number}: {phase.name}",
                f"- Context file: `{os.path.basename(phase_result.context_file_path) if phase_result.context_file_path else 'In memory'}`",
                f"- AI review: `{os.path.basename(phase_result.review_file_path) if phase_result.review_file_path else 'In memory' if phase_result.review_content else 'Not generated'}`",
                f"- Files included: {len(phase.included_files)}",
                f"- Token usage: {phase.token_count:,}/{phase.token_limit:,}",
                ""
            ])
        else:
            summary_content.extend([
                f"### Phase {phase.phase_number}: {phase.name}",
                f"- Files included: {len(phase.included_files)}",
                f"- Token usage: {phase.token_count:,}/{phase.token_limit:,}",
                f"- Status: {'✓ Completed' if phase_result.review_content else '✗ Failed'}",
                ""
            ])
    
    summary_path = os.path.join(
        config.project_path or os.getcwd(),
        f"code-review-multi-phase-summary-{timestamp}.md"
    )
    
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write('\n'.join(summary_content))
    
    print(f"\n📋 Multi-phase summary: {os.path.basename(summary_path)}")
    
    # Return PhaseResult objects or tuples based on parameter
    if return_phase_results:
        return phase_results
    else:
        # Convert PhaseResult objects to tuples for backward compatibility
        results = []
        for phase_result in phase_results:
            context_path = phase_result.context_file_path or summary_path  # Use summary as fallback
            review_path = phase_result.review_file_path
            results.append((context_path, review_path))
        
        return results


def smart_extract_diff_content(file_content: str, file_path: str, max_context_lines: int = 10) -> str:
    """
    Extract smart diff content from a file, focusing on actual changes.
    
    This function parses git diff output and extracts the changes with
    surrounding context for better understanding.
    """
    if not file_content or file_content == "[Content not available]":
        return file_content
    
    lines = file_content.split('\n')
    
    # Check if this is a git diff
    if lines and lines[0].startswith('diff --git'):
        # This is a git diff, parse it smartly
        result_lines = []
        in_hunk = False
        context_lines = []
        
        for line in lines:
            if line.startswith('@@'):
                # New hunk
                if context_lines:
                    # Add separator between hunks
                    result_lines.append('...')
                result_lines.append(line)
                in_hunk = True
                context_lines = []
            elif line.startswith('+++') or line.startswith('---'):
                # File headers
                result_lines.append(line)
            elif in_hunk:
                if line.startswith('+') or line.startswith('-'):
                    # This is a change line
                    # Include previous context if any
                    if context_lines:
                        start_idx = max(0, len(context_lines) - max_context_lines)
                        result_lines.extend(context_lines[start_idx:])
                        context_lines = []
                    result_lines.append(line)
                else:
                    # Context line
                    context_lines.append(line)
                    if len(context_lines) > max_context_lines * 2:
                        # Keep only recent context
                        context_lines = context_lines[-max_context_lines:]
        
        return '\n'.join(result_lines)
    else:
        # Not a git diff, return as is (might be full file content)
        # For very large files, we could extract key parts
        if len(lines) > 500:
            # Extract imports, class definitions, and function signatures
            key_lines = []
            for i, line in enumerate(lines[:100]):  # First 100 lines usually have imports
                if line.strip() and not line.strip().startswith('#'):
                    key_lines.append(line)
            
            key_lines.append('\n... [Content abbreviated for space] ...\n')
            
            # Extract class and function definitions
            for i, line in enumerate(lines):
                if line.strip().startswith(('class ', 'def ', 'async def ')):
                    # Include the definition and docstring if present
                    key_lines.append(line)
                    if i + 1 < len(lines) and '"""' in lines[i + 1]:
                        key_lines.append(lines[i + 1])
            
            return '\n'.join(key_lines)
        
        return file_content