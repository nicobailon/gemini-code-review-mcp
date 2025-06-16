#!/usr/bin/env python3
"""
Context generator module - Orchestrator for code review context generation.

This module coordinates all the data gathering and processing steps required for
generating code review contexts. It acts as the main orchestrator, delegating
specific responsibilities to specialized modules while maintaining the overall
workflow.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Import necessary modules
try:
    from ..config_types import CodeReviewConfig
    from ..errors import ConfigurationError
    from ..models.review_context import ReviewContext
    from ..models.review_mode import ReviewMode
    from ..models.task_info import TaskInfo
    from ..models.converters import review_context_to_dict
    from .context_builder import (
        DiscoveredConfigurations,
        discover_project_configurations_with_flags,
        format_configuration_context_for_ai,
        get_applicable_rules_for_files,
    )
    from ..dependencies import get_production_container
    from .gemini_api_client import send_to_gemini_for_review
    from ..helpers.git_utils import generate_file_tree, get_changed_files
    from ..helpers.model_config_manager import load_model_config
    from .task_list_parser import (
        PhaseData,
        TaskData,
        extract_prd_summary as extract_prd_summary_from_content,
        generate_prd_summary_from_task_list,
        parse_task_list,
        create_minimal_task_data,
    )
    from .template_formatter import format_review_template
    from .validation import (
        validate_review_mode,
        validate_scope_parameters,
        validate_github_pr_url,
    )
    from .token_manager import (
        ContextBuilder,
        FileInfo,
        generate_context_summary_message,
    )
except ImportError:
    # Fallback for absolute imports
    from ..config_types import CodeReviewConfig
    from ..errors import ConfigurationError
    from ..models.review_context import ReviewContext
    from ..models.review_mode import ReviewMode
    from ..models.task_info import TaskInfo
    from ..models.converters import review_context_to_dict
    from .context_builder import (
        DiscoveredConfigurations,
        discover_project_configurations_with_flags,
        format_configuration_context_for_ai,
        get_applicable_rules_for_files,
    )
    from ..dependencies import get_production_container
    from .gemini_api_client import send_to_gemini_for_review
    from ..helpers.git_utils import generate_file_tree, get_changed_files
    from ..helpers.model_config_manager import load_model_config
    from .task_list_parser import (
        PhaseData,
        TaskData,
        extract_prd_summary as extract_prd_summary_from_content,
        generate_prd_summary_from_task_list,
        parse_task_list,
        create_minimal_task_data,
    )
    from .template_formatter import format_review_template
    from .validation import (
        validate_review_mode,
        validate_scope_parameters,
        validate_github_pr_url,
    )
    from .token_manager import (
        ContextBuilder,
        FileInfo,
        generate_context_summary_message,
    )

# Import GitHub PR integration (optional)
try:
    from .github_pr_integration import get_complete_pr_analysis
except ImportError:
    try:
        from .github_pr_integration import get_complete_pr_analysis
    except ImportError:
        print("⚠️  GitHub PR integration not available")
        get_complete_pr_analysis = None

logger = logging.getLogger(__name__)


def generate_review_context_data(config: CodeReviewConfig) -> Dict[str, Any]:
    """
    Generate review context data by orchestrating all data gathering steps.

    This function coordinates the entire process of generating review context data:
    1. Validates configuration and review mode
    2. Discovers and parses task lists (if applicable)
    3. Gathers configuration files (Claude memory, Cursor rules)
    4. Collects git changes or PR data
    5. Builds the comprehensive template data structure

    Args:
        config: CodeReviewConfig object with all configuration parameters

    Returns:
        Dictionary containing all data needed for review template

    Raises:
        ConfigurationError: If configuration validation fails
    """
    if config.project_path is None:
        config.project_path = os.getcwd()

    # Step 1: Validate configuration and review mode
    review_mode = validate_review_mode(config)
    validate_scope_parameters(config)
    
    if config.github_pr_url:
        validate_github_pr_url(config.github_pr_url)

    # Initial user feedback
    print(
        f"🔍 Analyzing project: {os.path.basename(os.path.abspath(config.project_path))}"
    )

    # Display review mode
    if review_mode == "github_pr":
        print("🔗 Review mode: GitHub PR analysis")
        print(f"🌐 PR URL: {config.github_pr_url}")
    else:
        print(f"📊 Review scope: {config.scope}")

    if config.enable_gemini_review:
        print(f"🌡️  AI temperature: {config.temperature}")

    # Step 2: Load model config and prepare task data
    model_config = load_model_config()
    prd_summary = None
    task_data: Optional[TaskData] = None

    if review_mode == "github_pr":
        # GitHub PR mode - skip task list discovery
        prd_summary = "GitHub Pull Request Code Review"
        task_data = create_minimal_task_data("PR Review", "Pull Request code review")
    elif config.task_list:
        # Task-driven review explicitly requested
        task_data = handle_task_list_mode(config)
        prd_summary = extract_prd_summary(config, task_data)
    else:
        # General review mode
        logger.info("General review mode - task-list discovery skipped")
        prd_summary = config.default_prompt or model_config["defaults"]["default_prompt"]
        task_data = create_minimal_task_data(
            "General Review", "Code review without specific task context"
        )

    # At this point, task_data is guaranteed to be non-None
    assert task_data is not None, "task_data should be initialized"

    # Step 3: Process scope-based review logic
    effective_scope = process_review_scope(config, task_data)

    # Step 4: Discover configuration files
    configurations = discover_configurations(config)

    # Step 5: Gather git changes or PR data
    changed_files, pr_data = gather_changes(config, review_mode)

    # Step 6: Build comprehensive template data
    template_data = _build_template_data(
        config,
        task_data,
        prd_summary,
        effective_scope,
        configurations,
        changed_files,
        pr_data,
        review_mode,
    )

    return template_data


def handle_task_list_mode(config: CodeReviewConfig) -> TaskData:
    """Handle task list discovery and parsing.
    
    Args:
        config: Code review configuration
        
    Returns:
        Parsed task data
        
    Raises:
        ConfigurationError: If task list is requested but not found
    """
    logger.info("Task-driven review mode enabled via --task-list flag")
    
    # Use FileFinder service to find project files
    from pathlib import Path
    container = get_production_container()
    file_finder = container.file_finder

    if not config.project_path:
        raise ConfigurationError("Project path is required for task list discovery")

    project_files = file_finder.find_project_files(
        Path(config.project_path), config.task_list
    )

    task_file = str(project_files.task_list_file) if project_files.task_list_file else None

    if not task_file:
        # Task list was explicitly requested but not found
        if config.task_list and config.task_list.strip():  # Non-empty task list name
            raise ConfigurationError(
                f"Task list file '{config.task_list}' not found in project.\n"
                f"Please check that the file exists in the tasks/ directory."
            )
        else:  # Empty string provided
            raise ConfigurationError(
                "Empty task list name provided with --task-list flag.\n"
                "Please specify a task list file name or omit the flag entirely."
            )

    # Read and parse task list
    with open(task_file, "r", encoding="utf-8") as f:
        task_content = f.read()
    
    return parse_task_list(task_content)


def extract_prd_summary(config: CodeReviewConfig, task_data: TaskData) -> str:
    """Extract or generate PRD summary.
    
    Args:
        config: Code review configuration
        task_data: Parsed task data
        
    Returns:
        PRD summary text
    """
    # Check if PRD file exists
    from pathlib import Path
    container = get_production_container()
    file_finder = container.file_finder

    if not config.project_path:
        raise ConfigurationError("Project path is required for PRD summary extraction")

    project_files = file_finder.find_project_files(
        Path(config.project_path), config.task_list
    )
    
    prd_file = str(project_files.prd_file) if project_files.prd_file else None

    if prd_file:
        # We have a PRD file - extract summary
        with open(prd_file, "r", encoding="utf-8") as f:
            prd_content = f.read()
        return extract_prd_summary_from_content(prd_content)
    else:
        # Generate summary from task list
        return generate_prd_summary_from_task_list(task_data)


def process_review_scope(config: CodeReviewConfig, task_data: TaskData) -> str:
    """Process and potentially adjust review scope based on task data.
    
    Args:
        config: Code review configuration
        task_data: Parsed task data
        
    Returns:
        Effective scope (may differ from config.scope due to smart defaulting)
        
    Raises:
        ConfigurationError: If specified phase/task is not found
    """
    effective_scope = config.scope

    if config.scope == "recent_phase":
        effective_scope = _handle_recent_phase_scope(config, task_data)
    elif config.scope == "full_project":
        _handle_full_project_scope(task_data)
    elif config.scope == "specific_phase":
        _handle_specific_phase_scope(config, task_data)
    elif config.scope == "specific_task":
        _handle_specific_task_scope(config, task_data)

    return effective_scope


def _handle_recent_phase_scope(config: CodeReviewConfig, task_data: TaskData) -> str:
    """Handle recent phase scope logic with smart defaulting.
    
    Returns:
        Effective scope (may be "full_project" if all phases complete)
    """
    phases: List[PhaseData] = task_data.get("phases", [])
    all_phases_complete = all(p.get("subtasks_complete", False) for p in phases)

    if all_phases_complete and phases:
        # All phases complete - automatically switch to full project review
        completed_phases = [p for p in phases if p.get("subtasks_complete", False)]
        all_completed_subtasks = []
        phase_descriptions = []
        
        for p in completed_phases:
            all_completed_subtasks.extend(p["subtasks_completed"])
            phase_descriptions.append(f"{p['number']} {p['description']}")

        task_data.update({
            "current_phase_number": f"Full Project ({len(completed_phases)} phases)",
            "current_phase_description": f"Analysis of all completed phases: {', '.join(phase_descriptions)}",
            "previous_phase_completed": "",
            "next_phase": "",
            "subtasks_completed": all_completed_subtasks,
        })
        return "full_project"
    
    # Handle legacy phase parameter if provided
    if config.phase:
        _apply_legacy_phase_override(config, task_data)
    
    return config.scope


def _handle_full_project_scope(task_data: TaskData) -> None:
    """Handle full project scope by analyzing all completed phases."""
    phases: List[PhaseData] = task_data.get("phases", [])
    completed_phases = [p for p in phases if p.get("subtasks_complete", False)]
    
    if completed_phases:
        all_completed_subtasks = []
        phase_descriptions = []
        
        for p in completed_phases:
            all_completed_subtasks.extend(p["subtasks_completed"])
            phase_descriptions.append(f"{p['number']} {p['description']}")

        task_data.update({
            "current_phase_number": f"Full Project ({len(completed_phases)} phases)",
            "current_phase_description": f"Analysis of all completed phases: {', '.join(phase_descriptions)}",
            "previous_phase_completed": "",
            "next_phase": "",
            "subtasks_completed": all_completed_subtasks,
        })


def _handle_specific_phase_scope(config: CodeReviewConfig, task_data: TaskData) -> None:
    """Handle specific phase scope validation and setup."""
    phases: List[PhaseData] = task_data.get("phases", [])
    target_phase = None
    
    for i, p in enumerate(phases):
        if p["number"] == config.phase_number:
            target_phase = (i, p)
            break

    if target_phase is None:
        available_phases = [p["number"] for p in phases]
        error_msg = f"""Phase {config.phase_number} not found in task list

Available phases: {', '.join(available_phases) if available_phases else 'none found'}

Working examples:
  # Use an available phase number
  {f'generate-code-review . --scope specific_phase --phase-number {available_phases[0]}' if available_phases else 'generate-code-review . --scope recent_phase  # Use default scope instead'}
  
  # List all phases
  generate-code-review . --scope full_project
  
  # Use default scope (most recent incomplete phase)
  generate-code-review ."""
        raise ConfigurationError(error_msg)

    i, p = target_phase
    _update_task_data_for_phase(task_data, i, p, phases)


def _handle_specific_task_scope(config: CodeReviewConfig, task_data: TaskData) -> None:
    """Handle specific task scope validation and setup."""
    phases: List[PhaseData] = task_data.get("phases", [])
    target_task = None
    target_phase = None
    
    for i, p in enumerate(phases):
        for subtask in p["subtasks"]:
            if subtask["number"] == config.task_number:
                target_task = subtask
                target_phase = (i, p)
                break
        if target_task:
            break

    if target_task is None or target_phase is None:
        available_tasks = []
        for phase in phases:
            for subtask in phase.get("subtasks", []):
                available_tasks.append(subtask["number"])

        error_msg = f"""Task {config.task_number} not found in task list

Available tasks: {', '.join(available_tasks[:10]) if available_tasks else 'none found'}{' (showing first 10)' if len(available_tasks) > 10 else ''}

Working examples:
  # Use an available task number
  {f'generate-code-review . --scope specific_task --task-number {available_tasks[0]}' if available_tasks else 'generate-code-review . --scope recent_phase  # Use default scope instead'}
  
  # Review entire phase instead
  generate-code-review . --scope specific_phase --phase-number {config.task_number.split('.')[0] if config.task_number else '1'}.0
  
  # Use default scope (most recent incomplete phase)
  generate-code-review ."""
        raise ConfigurationError(error_msg)

    i, p = target_phase
    task_data.update({
        "current_phase_number": target_task["number"],
        "current_phase_description": f"Specific task: {target_task['description']} (from {p['number']} {p['description']})",
        "previous_phase_completed": "",
        "next_phase": "",
        "subtasks_completed": [f"{target_task['number']} {target_task['description']}"],
    })


def _apply_legacy_phase_override(config: CodeReviewConfig, task_data: TaskData) -> None:
    """Apply legacy phase parameter override if provided."""
    phases: List[PhaseData] = task_data.get("phases", [])
    
    for i, p in enumerate(phases):
        if p["number"] == config.phase:
            _update_task_data_for_phase(task_data, i, p, phases)
            break


def _update_task_data_for_phase(
    task_data: TaskData, 
    phase_index: int, 
    phase: PhaseData, 
    all_phases: List[PhaseData]
) -> None:
    """Update task data for a specific phase."""
    # Find previous completed phase
    previous_phase_completed = ""
    if phase_index > 0:
        prev_phase = all_phases[phase_index - 1]
        previous_phase_completed = f"{prev_phase['number']} {prev_phase['description']}"

    # Find next phase
    next_phase = ""
    if phase_index < len(all_phases) - 1:
        next_phase_obj = all_phases[phase_index + 1]
        next_phase = f"{next_phase_obj['number']} {next_phase_obj['description']}"

    task_data.update({
        "current_phase_number": phase["number"],
        "current_phase_description": phase["description"],
        "previous_phase_completed": previous_phase_completed,
        "next_phase": next_phase,
        "subtasks_completed": phase["subtasks_completed"],
    })


def discover_configurations(config: CodeReviewConfig) -> DiscoveredConfigurations:
    """Discover configuration files based on config flags.
    
    Args:
        config: Code review configuration
        
    Returns:
        Discovered configurations dictionary
    """
    config_types: List[str] = []
    if config.include_claude_memory:
        config_types.append("Claude memory")
    if config.include_cursor_rules:
        config_types.append("Cursor rules")

    if config_types:
        print(f"🔍 Discovering {' and '.join(config_types)}...")
        if not config.project_path:
            raise ConfigurationError("Project path is required for configuration discovery")
        
        configurations = discover_project_configurations_with_flags(
            config.project_path,
            config.include_claude_memory,
            config.include_cursor_rules,
        )
    else:
        print("ℹ️  Configuration discovery disabled")
        configurations: DiscoveredConfigurations = {
            "claude_memory_files": [],
            "cursor_rules": [],
            "discovery_errors": [],
            "performance_stats": {},
        }

    # Display discovery results
    claude_files_count = len(configurations["claude_memory_files"])
    cursor_rules_count = len(configurations["cursor_rules"])
    errors_count = len(configurations["discovery_errors"])

    if claude_files_count > 0 or cursor_rules_count > 0:
        print(
            f"✅ Found {claude_files_count} Claude memory files, {cursor_rules_count} Cursor rules"
        )
    else:
        print("ℹ️  No configuration files found (this is optional)")

    if errors_count > 0:
        print(f"⚠️  {errors_count} configuration discovery errors (will continue)")

    return configurations


def gather_changes(
    config: CodeReviewConfig, review_mode: str
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Gather git changes or PR data based on review mode.
    
    Args:
        config: Code review configuration
        review_mode: Current review mode
        
    Returns:
        Tuple of (changed_files, pr_data)
    """
    changed_files: List[Dict[str, Any]] = []
    pr_data: Optional[Dict[str, Any]] = None

    if review_mode == "github_pr":
        # GitHub PR analysis mode
        print("🔄 Fetching PR data from GitHub...")
        try:
            if get_complete_pr_analysis is None:
                raise ImportError("GitHub PR integration not available")

            if config.github_pr_url is None:
                raise ValueError("GitHub PR URL is required for PR analysis mode")

            pr_analysis = get_complete_pr_analysis(config.github_pr_url)

            # Convert PR file changes to our expected format
            for file_change in pr_analysis["file_changes"]["changed_files"]:
                if not config.project_path:
                    raise ConfigurationError("Project path is required for PR analysis")
                
                changed_files.append({
                    "path": os.path.join(config.project_path, file_change["path"]),
                    "status": f"PR-{file_change['status']}",
                    "content": file_change.get("patch", "[Content not available]"),
                })

            # Store PR metadata for template
            pr_data = {
                "mode": "github_pr",
                "pr_data": pr_analysis["pr_data"],
                "summary": pr_analysis["file_changes"]["summary"],
                "repository": pr_analysis["repository"],
            }

            print(f"✅ Found {len(changed_files)} changed files in PR")
            print(
                f"📊 Files: +{pr_data['summary']['files_added']} "
                f"~{pr_data['summary']['files_modified']} "
                f"-{pr_data['summary']['files_deleted']}"
            )

        except Exception as e:
            print(f"❌ Failed to fetch PR data: {e}")
            # Fallback to local git changes
            if not config.project_path:
                raise ConfigurationError("Project path is required for git changes")
            changed_files = get_changed_files(config.project_path)
    else:
        # Task list based mode (default)
        if not config.project_path:
            raise ConfigurationError("Project path is required for git changes")
        changed_files = get_changed_files(config.project_path)

    return changed_files, pr_data


def convert_to_file_info(changed_files: List[Dict[str, Any]]) -> List[FileInfo]:
    """Convert changed files to FileInfo objects for token management."""
    file_infos = []
    for file_data in changed_files:
        # Extract content - might be in 'content' or 'patch' field
        content = file_data.get('content', file_data.get('patch', ''))
        
        file_info = FileInfo(
            path=file_data.get('path', file_data.get('file_path', '')),
            content=content,
            status=file_data.get('status', 'modified'),
            additions=file_data.get('additions', 0),
            deletions=file_data.get('deletions', 0),
        )
        file_infos.append(file_info)
    return file_infos


def _build_template_data(
    config: CodeReviewConfig,
    task_data: TaskData,
    prd_summary: Optional[str],
    effective_scope: str,
    configurations: DiscoveredConfigurations,
    changed_files: List[Dict[str, Any]],
    pr_data: Optional[Dict[str, Any]],
    review_mode: str,
) -> Dict[str, Any]:
    """Build comprehensive template data structure.
    
    Args:
        config: Code review configuration
        task_data: Parsed task data
        prd_summary: PRD summary text
        effective_scope: Effective review scope
        configurations: Discovered configuration files
        changed_files: List of changed files
        pr_data: PR metadata (if applicable)
        review_mode: Current review mode
        
    Returns:
        Complete template data dictionary
    """
    # Generate file tree
    if not config.project_path:
        raise ConfigurationError("Project path is required for file tree generation")
    file_tree = generate_file_tree(config.project_path)

    # Apply token management to changed files
    file_infos = convert_to_file_info(changed_files)
    
    # Get current model from environment or config
    model_config = load_model_config()
    current_model = os.getenv("GEMINI_MODEL", model_config["defaults"]["default_model"])
    
    # Build context with token management
    context_builder = ContextBuilder(
        model_name=current_model,
        strategy=config.context_strategy,
        max_tokens_override=config.max_context_tokens,
        per_file_limit=config.per_file_token_limit
    )
    
    context_summary = context_builder.build_context(file_infos)
    
    # Print context summary for user
    print("\n" + generate_context_summary_message(context_summary))
    
    # Convert back to changed_files format for template (with potentially truncated content)
    processed_changed_files = []
    for file_info in context_summary.included_files:
        # Find original file data
        orig_file = next((f for f in changed_files if f.get('path', f.get('file_path', '')) == file_info.path), {})
        
        processed_file = {
            "path": file_info.path,
            "file_path": file_info.path,  # Keep both for compatibility
            "status": file_info.status,
            "content": file_info.content,
            "additions": file_info.additions,
            "deletions": file_info.deletions,
        }
        # Preserve any additional fields from original
        for key, value in orig_file.items():
            if key not in processed_file:
                processed_file[key] = value
        
        processed_changed_files.append(processed_file)
    
    # Update changed_files to only include what fits in context
    changed_files = processed_changed_files

    # Get applicable configuration rules for changed files
    changed_file_paths = [f["path"] for f in changed_files]
    applicable_rules = get_applicable_rules_for_files(
        configurations["cursor_rules"], changed_file_paths
    )

    # Format configuration content for AI consumption
    configuration_content = format_configuration_context_for_ai(
        configurations["claude_memory_files"], configurations["cursor_rules"]
    )

    # Process URL context if provided
    url_context_content = None
    if config.url_context:
        urls = (
            config.url_context
            if isinstance(config.url_context, list)
            else [config.url_context]
        )
        if urls:
            url_context_content = "\n## Additional Context URLs\n\n"
            url_context_content += (
                "Please analyze the following URLs for additional context:\n"
            )
            for url in urls:
                url_context_content += f"- {url}\n"

    # Create ReviewContext object for type safety
    review_mode_enum = ReviewMode.GITHUB_PR if review_mode == "github_pr" else ReviewMode.TASK_DRIVEN
    
    # Create TaskInfo if we have task data
    task_info = None
    if task_data.get("current_phase_number") and task_data.get("current_phase_description"):
        task_info = TaskInfo(
            phase_number=str(task_data["current_phase_number"]),
            task_number=str(config.task_number) if config.task_number else None,
            description=task_data["current_phase_description"],
        )
    
    # Extract file paths from changed_files for ReviewContext
    review_changed_file_paths = [f["file_path"] for f in changed_files if "file_path" in f]
    
    # Create ReviewContext
    review_context = ReviewContext(
        mode=review_mode_enum,
        default_prompt=config.auto_prompt_content or "",
        prd_summary=prd_summary,
        task_info=task_info,
        changed_files=review_changed_file_paths,
    )
    
    # Convert to dict with extra data for template compatibility
    extra_template_data: Dict[str, object] = {
        "total_phases": task_data["total_phases"],
        "previous_phase_completed": task_data["previous_phase_completed"],
        "next_phase": task_data["next_phase"],
        "subtasks_completed": task_data["subtasks_completed"],
        "project_path": config.project_path,
        "file_tree": file_tree,
        "changed_files": changed_files,  # Keep original format for template
        "scope": effective_scope,  # Use effective scope to reflect auto-expansion
        "branch_comparison_data": pr_data,
        # Enhanced configuration data
        "configuration_content": configuration_content,
        "claude_memory_files": configurations["claude_memory_files"],
        "cursor_rules": configurations["cursor_rules"],
        "applicable_rules": applicable_rules,
        "configuration_errors": configurations["discovery_errors"],
        "raw_context_only": config.raw_context_only,
        "url_context_content": url_context_content,
    }
    
    # Use converter to create template data with proper typing
    template_data = review_context_to_dict(review_context, extra_template_data)
    
    return template_data


def process_and_output_review(
    config: CodeReviewConfig, template_data: Dict[str, Any]
) -> Tuple[str, Optional[str]]:
    """
    Process template data and output review results.

    This function takes the prepared template_data, formats it using
    format_review_template, saves it to a file, and optionally sends
    it to Gemini for AI review.

    Args:
        config: CodeReviewConfig object
        template_data: Dictionary containing all template data

    Returns:
        Tuple of (context_file_path, gemini_review_path)
    """
    # Format template
    review_context = format_review_template(template_data)

    # Generate output filename
    if config.output is None:
        config.output = _generate_output_filename(config, template_data)

    # Save context to file
    output_path = config.output
    assert output_path is not None, "Output path should be set by now"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(review_context)

    print(f"📝 Generated review context: {os.path.basename(output_path)}")

    # Send to Gemini for AI review if enabled
    gemini_output = None
    if config.enable_gemini_review:
        gemini_output = _send_to_gemini(config, review_context)

    return output_path, gemini_output


def _generate_output_filename(
    config: CodeReviewConfig, template_data: Dict[str, Any]
) -> str:
    """Generate output filename based on review mode and scope.
    
    Args:
        config: Code review configuration
        template_data: Template data containing review mode info
        
    Returns:
        Generated output filename path
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Generate mode and scope-specific filename
    current_mode = template_data.get("review_mode", "task_list_based")
    if current_mode == "github_pr":
        mode_prefix = "github-pr"
    else:
        # Task list based mode - use scope-specific naming
        if config.scope == "recent_phase":
            mode_prefix = "recent-phase"
        elif config.scope == "full_project":
            mode_prefix = "full-project"
        elif config.scope == "specific_phase":
            if config.phase_number is None:
                raise ValueError("Phase number is required for specific_phase scope")
            phase_safe = config.phase_number.replace(".", "-")
            mode_prefix = f"phase-{phase_safe}"
        elif config.scope == "specific_task":
            if config.task_number is None:
                raise ValueError("Task number is required for specific_task scope")
            task_safe = config.task_number.replace(".", "-")
            mode_prefix = f"task-{task_safe}"
        else:
            mode_prefix = "unknown"

    project_path = config.project_path if config.project_path is not None else os.getcwd()
    return os.path.join(
        project_path, f"code-review-context-{mode_prefix}-{timestamp}.md"
    )


def _send_to_gemini(config: CodeReviewConfig, review_context: str) -> Optional[str]:
    """Send review context to Gemini for AI review.
    
    Args:
        config: Code review configuration
        review_context: Formatted review context
        
    Returns:
        Path to Gemini output file, or None if failed
    """
    print("🔄 Sending to Gemini for AI code review...")
    
    project_path = config.project_path if config.project_path is not None else os.getcwd()
    gemini_output = send_to_gemini_for_review(
        review_context,
        project_path,
        config.temperature,
        thinking_budget=config.thinking_budget,
    )
    
    if gemini_output:
        print(f"✅ AI code review completed: {os.path.basename(gemini_output)}")
    else:
        print(
            "⚠️  AI code review failed or was skipped (check API key and model availability)"
        )
    
    return gemini_output