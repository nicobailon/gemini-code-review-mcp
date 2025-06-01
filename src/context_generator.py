#!/usr/bin/env python3
"""
Context generator module.

This module houses the primary orchestration logic for gathering all necessary data
(task info, git changes, configurations), preparing the final review context data,
and handling the output (saving to file, calling Gemini).
"""

import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Import necessary modules
try:
    from .config_types import CodeReviewConfig
    from .configuration_context import ClaudeMemoryFile, CursorRule
    from .context_builder import (
        DiscoveredConfigurations,
        discover_project_configurations_with_flags,
        format_configuration_context_for_ai,
        get_applicable_rules_for_files,
    )
    from .gemini_api_client import send_to_gemini_for_review
    from .git_utils import generate_file_tree, get_changed_files
    from .model_config_manager import load_model_config
    from .task_list_parser import (
        PhaseData,
        TaskData,
        extract_prd_summary,
        generate_prd_summary_from_task_list,
        parse_task_list,
    )
except ImportError:
    # Fallback for absolute imports
    from config_types import CodeReviewConfig
    from configuration_context import ClaudeMemoryFile, CursorRule
    from context_builder import (
        DiscoveredConfigurations,
        discover_project_configurations_with_flags,
        format_configuration_context_for_ai,
        get_applicable_rules_for_files,
    )
    from gemini_api_client import send_to_gemini_for_review
    from git_utils import generate_file_tree, get_changed_files
    from model_config_manager import load_model_config
    from task_list_parser import (
        PhaseData,
        TaskData,
        extract_prd_summary,
        generate_prd_summary_from_task_list,
        parse_task_list,
    )

# Import GitHub PR integration (optional)
try:
    from .github_pr_integration import get_complete_pr_analysis, parse_github_pr_url
except ImportError:
    try:
        from github_pr_integration import get_complete_pr_analysis, parse_github_pr_url
    except ImportError:
        print("⚠️  GitHub PR integration not available")
        parse_github_pr_url = None
        get_complete_pr_analysis = None

logger = logging.getLogger(__name__)


def extract_clean_prompt_content(auto_prompt_content: str) -> str:
    """
    Extract clean prompt content from auto-generated prompt response.

    Since auto-prompt generation now returns raw content without headers/footers,
    this function primarily handles basic cleanup and formatting.

    Args:
        auto_prompt_content: Auto-prompt response (should be clean already)

    Returns:
        Clean prompt content suitable for user_instructions
    """
    # Basic cleanup - remove any extra whitespace
    content = auto_prompt_content.strip()

    # Remove any remaining code block markers if present (just in case)
    if content.startswith("```") and content.endswith("```"):
        lines = content.split("\n")
        if len(lines) > 2:
            content = "\n".join(lines[1:-1]).strip()

    # Collapse multiple blank lines
    content = re.sub(r"\n\n\n+", "\n\n", content)

    return content


def format_review_template(data: Dict[str, Any]) -> str:
    """
    Format the final review template.

    Args:
        data: Dictionary containing all template data

    Returns:
        Formatted markdown template
    """
    # Add scope information to header
    review_mode = data.get("review_mode", "task_list_based")
    if review_mode == "github_pr":
        scope_info = "Review Mode: GitHub PR Analysis"
    else:
        scope_info = f"Review Scope: {data['scope']}"
        if data.get("phase_number"):
            scope_info += f" (Phase: {data['phase_number']})"
        elif data.get("task_number"):
            scope_info += f" (Task: {data['task_number']})"

    template = f"""# Code Review Context - {scope_info}
"""

    # Check if we have task list data (total_phases > 0 indicates a task list exists)
    has_task_list = data.get('total_phases', 0) > 0
    
    if has_task_list:
        # Include PRD/task list related tags only when task list exists
        template += f"""
<overall_prd_summary>
{data['prd_summary']}
</overall_prd_summary>

<total_phases>
{data['total_phases']}
</total_phases>

<current_phase_number>
{data['current_phase_number']}
</current_phase_number>
"""

        # Only add previous phase if it exists
        if data["previous_phase_completed"]:
            template += f"""
<previous_phase_completed>
{data['previous_phase_completed']}
</previous_phase_completed>
"""

        # Only add next phase if it exists
        if data["next_phase"]:
            template += f"""
<next_phase>
{data['next_phase']}
</next_phase>
"""

        template += f"""<current_phase_description>
{data['current_phase_description']}
</current_phase_description>

<subtasks_completed>
{chr(10).join(f"- {subtask}" for subtask in data['subtasks_completed'])}
</subtasks_completed>"""
    else:
        # For projects without task lists, just include the summary/prompt
        if data.get('prd_summary'):
            template += f"""
<project_context>
{data['prd_summary']}
</project_context>"""

    # Add GitHub PR metadata if available
    branch_data = data.get("branch_comparison_data")
    if branch_data and branch_data["mode"] == "github_pr":
        pr_data = branch_data["pr_data"]
        summary = branch_data.get("summary", {})
        template += f"""
<github_pr_metadata>
Repository: {branch_data['repository']}
PR Number: {pr_data['pr_number']}
Title: {pr_data['title']}
Author: {pr_data['author']}
Source Branch: {pr_data['source_branch']}
Target Branch: {pr_data['target_branch']}
Source SHA: {pr_data.get('source_sha', 'N/A')[:8]}...
Target SHA: {pr_data.get('target_sha', 'N/A')[:8]}...
State: {pr_data['state']}
Created: {pr_data['created_at']}
Updated: {pr_data['updated_at']}
Files Changed: {summary.get('files_changed', 'N/A')}
Files Added: {summary.get('files_added', 'N/A')}
Files Modified: {summary.get('files_modified', 'N/A')}
Files Deleted: {summary.get('files_deleted', 'N/A')}"""
        if pr_data.get("body") and pr_data["body"].strip():
            # Show first 200 chars of PR description
            description = pr_data["body"].strip()[:200]
            if len(pr_data["body"]) > 200:
                description += "..."
            template += f"""
Description: {description}"""
        template += """
</github_pr_metadata>"""

    template += f"""
<project_path>
{data['project_path']}
</project_path>"""

    # Add configuration content section if available
    if data.get("configuration_content"):
        template += f"""
<configuration_context>
{data['configuration_content']}
</configuration_context>"""

        # Add applicable rules summary if available
        applicable_rules = data.get("applicable_rules", [])
        if applicable_rules:
            template += f"""
<applicable_configuration_rules>
The following configuration rules apply to the changed files:
{chr(10).join(f"- {rule.description} (from {rule.file_path})" for rule in applicable_rules)}
</applicable_configuration_rules>"""

    template += f"""
<file_tree>
{data['file_tree']}
</file_tree>

<files_changed>"""

    for file_info in data["changed_files"]:
        file_ext = os.path.splitext(file_info["path"])[1].lstrip(".")
        if not file_ext:
            file_ext = "txt"

        template += f"""
File: {file_info['path']} ({file_info['status']})
```{file_ext}
{file_info['content']}
```"""

    template += """
</files_changed>"""

    # Add AI review instructions only if not raw_context_only
    if not data.get("raw_context_only", False):
        template += """

<user_instructions>"""

        # Check if auto-generated meta-prompt should be used
        auto_prompt_content = data.get("auto_prompt_content")
        if auto_prompt_content:
            # Extract clean prompt content (remove headers, metadata, and formatting)
            clean_prompt = extract_clean_prompt_content(auto_prompt_content)
            # Use the auto-generated meta-prompt as user instructions
            template += clean_prompt
        else:
            # Use default template-based instructions
            # Customize instructions based on review mode and scope
            review_mode = data.get("review_mode", "task_list_based")
            branch_data = data.get("branch_comparison_data")

            if review_mode == "github_pr" and branch_data:
                config_note = ""
                if data.get("configuration_content"):
                    config_note = "\n\nPay special attention to the configuration context (Claude memory and Cursor rules) provided above, which contains project-specific guidelines and coding standards that should be followed."

                template += f"""You are reviewing a GitHub Pull Request that contains changes from branch '{branch_data['pr_data']['source_branch']}' to '{branch_data['pr_data']['target_branch']}'.

The PR "{branch_data['pr_data']['title']}" by {branch_data['pr_data']['author']} includes {branch_data['summary']['files_changed']} changed files with {branch_data['summary']['files_added']} additions, {branch_data['summary']['files_modified']} modifications, and {branch_data['summary']['files_deleted']} deletions.{config_note}

Based on the PR metadata, commit history, and file changes shown above, conduct a comprehensive code review focusing on:
1. Code quality and best practices
2. Security implications of the changes
3. Performance considerations
4. Testing coverage and approach
5. Documentation completeness
6. Integration and compatibility issues

Identify specific lines, files, or patterns that are concerning and provide actionable feedback."""
            elif data["scope"] == "full_project":
                config_note = ""
                if data.get("configuration_content"):
                    config_note = "\n\nImportant: Refer to the configuration context (Claude memory and Cursor rules) provided above for project-specific guidelines and coding standards that should be followed throughout the project."

                template += f"""We have completed all phases (and subtasks within) of this project: {data['current_phase_description']}.{config_note}

Based on the PRD, all completed phases, all subtasks that were finished across the entire project, and the files changed in the working directory, your job is to conduct a comprehensive code review and output your code review feedback for the entire project. Identify specific lines or files that are concerning when appropriate."""
            elif data["scope"] == "specific_task":
                config_note = ""
                if data.get("configuration_content"):
                    config_note = "\n\nImportant: Refer to the configuration context (Claude memory and Cursor rules) provided above for project-specific guidelines and coding standards."

                template += f"""We have just completed task #{data['current_phase_number']}: "{data['current_phase_description']}".{config_note}

Based on the PRD, the completed task, and the files changed in the working directory, your job is to conduct a code review and output your code review feedback for this specific task. Identify specific lines or files that are concerning when appropriate."""
            else:
                config_note = ""
                if data.get("configuration_content"):
                    config_note = "\n\nImportant: Refer to the configuration context (Claude memory and Cursor rules) provided above for project-specific guidelines and coding standards."

                template += f"""We have just completed phase #{data['current_phase_number']}: "{data['current_phase_description']}".{config_note}

Based on the PRD, the completed phase, all subtasks that were finished in that phase, and the files changed in the working directory, your job is to conduct a code review and output your code review feedback for the completed phase. Identify specific lines or files that are concerning when appropriate."""

        template += """
</user_instructions>"""

    return template


def find_project_files(
    project_path: str, task_list_name: Optional[str] = None
) -> tuple[Optional[str], Optional[str]]:
    """
    Find PRD and task list files in the project. PRD files are now optional.

    Args:
        project_path: Path to project root
        task_list_name: Optional specific task list file name (e.g., 'tasks-feature-x.md')

    Returns:
        Tuple of (prd_file_path, task_list_path). prd_file_path may be None.
    """
    import glob

    tasks_dir = os.path.join(project_path, "tasks")

    # Create tasks directory if it doesn't exist (for new projects)
    if not os.path.exists(tasks_dir):
        logger.info(
            f"Tasks directory not found: {tasks_dir}. This is OK - the tool can work without task lists."
        )
        return None, None

    # Find PRD files (optional)
    prd_file = None
    prd_files = glob.glob(os.path.join(tasks_dir, "prd-*.md"))
    if not prd_files:
        # Also check root directory
        prd_files = glob.glob(os.path.join(project_path, "prd.md"))

    if prd_files:
        # Use most recently modified if multiple
        prd_file = max(prd_files, key=os.path.getmtime)
        logger.info(f"Found PRD file: {os.path.basename(prd_file)}")
    else:
        print(
            "ℹ️  No PRD files found - using task list or default prompt for context generation"
        )

    # Find task list files
    task_file = None

    if task_list_name:
        # User specified exact task list file
        if not task_list_name.endswith(".md"):
            task_list_name += ".md"

        specified_path = os.path.join(tasks_dir, task_list_name)
        if os.path.exists(specified_path):
            task_file = specified_path
            logger.info(f"Using specified task list: {task_list_name}")
        else:
            # Try to find similar files
            available_files = [
                f
                for f in os.listdir(tasks_dir)
                if f.startswith("tasks-") and f.endswith(".md")
            ]
            error_msg = f"""Specified task list not found: {task_list_name}

Available task lists in {tasks_dir}:
{chr(10).join(f'  - {f}' for f in available_files) if available_files else '  (no task list files found)'}

Working examples:
  # Use specific task list
  generate-code-review . --task-list tasks-feature-auth.md
  
  # Let tool auto-select most recent task list
  generate-code-review ."""
            raise FileNotFoundError(error_msg)
    else:
        # Auto-discover task list files
        task_files = glob.glob(os.path.join(tasks_dir, "tasks-*.md"))

        if task_files:
            # Use most recently modified if multiple
            task_file = max(task_files, key=os.path.getmtime)
            if len(task_files) > 1:
                available_files = [os.path.basename(f) for f in task_files]
                logger.info(f"Multiple task lists found: {', '.join(available_files)}")
                logger.info(f"Auto-selected most recent: {os.path.basename(task_file)}")
            else:
                logger.info(f"Found task list: {os.path.basename(task_file)}")
        else:
            logger.info(
                "No task list files found. Will use default prompt for code review."
            )

    return prd_file, task_file


def generate_review_context_data(config: CodeReviewConfig) -> Dict[str, Any]:
    """
    Generate review context data by gathering all necessary information.

    This function encapsulates all data gathering steps (parsing task lists,
    getting git changes, discovering configurations, etc.) and returns a
    comprehensive dictionary of template_data.

    Args:
        config: CodeReviewConfig object with all configuration parameters

    Returns:
        Dictionary containing all data needed for review template
    """
    if config.project_path is None:
        config.project_path = os.getcwd()

    # Detect and validate review mode
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
        raise ValueError(error_msg)

    # Validate scope parameter
    valid_scopes = ["recent_phase", "full_project", "specific_phase", "specific_task"]
    if config.scope not in valid_scopes:
        raise ValueError(
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
            raise ValueError(error_msg)
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
            raise ValueError(error_msg)

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
            raise ValueError(error_msg)
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
            raise ValueError(error_msg)

    # Validate GitHub PR URL if provided
    if config.github_pr_url:
        try:
            # Check if GitHub PR integration is available
            if not parse_github_pr_url:
                raise ImportError("GitHub PR integration not available")
            parse_github_pr_url(
                config.github_pr_url
            )  # This will raise ValueError if invalid
        except ValueError as e:
            error_msg = f"""Invalid GitHub PR URL: {e}

Working examples:
  # Standard GitHub PR
  generate-code-review --github-pr-url https://github.com/microsoft/vscode/pull/123
  
  # GitHub Enterprise
  generate-code-review --github-pr-url https://github.company.com/team/project/pull/456
  
  # With additional parameters
  generate-code-review --github-pr-url https://github.com/owner/repo/pull/789 --temperature 0.3"""
            raise ValueError(error_msg)

    # Initial user feedback
    print(
        f"🔍 Analyzing project: {os.path.basename(os.path.abspath(config.project_path))}"
    )

    # Display review mode
    current_mode = review_modes[0]
    if current_mode == "github_pr":
        print("🔗 Review mode: GitHub PR analysis")
        print(f"🌐 PR URL: {config.github_pr_url}")
    else:
        print(f"📊 Review scope: {config.scope}")

    if config.enable_gemini_review:
        print(f"🌡️  AI temperature: {config.temperature}")

    # Load model config for default prompt
    model_config = load_model_config()

    # Find project files (PRD is now optional)
    prd_file, task_file = find_project_files(config.project_path, config.task_list)

    # Handle different scenarios
    prd_summary = None
    task_data: Optional[TaskData] = None

    if task_file:
        # We have a task list - read and parse it
        with open(task_file, "r", encoding="utf-8") as f:
            task_content = f.read()
        task_data = parse_task_list(task_content)

        if prd_file:
            # We have both PRD and task list - use PRD summary
            with open(prd_file, "r", encoding="utf-8") as f:
                prd_content = f.read()
            prd_summary = extract_prd_summary(prd_content)
        else:
            # Generate summary from task list
            prd_summary = generate_prd_summary_from_task_list(task_data)
    else:
        # No task list - use default prompt
        if config.default_prompt:
            prd_summary = config.default_prompt
        else:
            prd_summary = model_config["defaults"]["default_prompt"]

        # Create minimal task data for template
        task_data_dict: TaskData = {
            "total_phases": 0,
            "current_phase_number": "General Review",
            "current_phase_description": "Code review without specific task context",
            "previous_phase_completed": "",
            "next_phase": "",
            "subtasks_completed": [],
            "phases": [],
        }
        task_data = task_data_dict

    # At this point, task_data is guaranteed to be non-None
    assert task_data is not None, "task_data should be initialized"

    # Handle scope-based review logic
    effective_scope = config.scope  # Track effective scope without modifying config

    if config.scope == "recent_phase":
        # Smart defaulting: if ALL phases are complete, automatically review full project
        phases: List[PhaseData] = task_data.get("phases", []) if task_data else []
        all_phases_complete = all(p.get("subtasks_complete", False) for p in phases)

        if all_phases_complete and phases:
            # All phases complete - automatically switch to full project review
            completed_phases: List[PhaseData] = [
                p for p in phases if p.get("subtasks_complete", False)
            ]
            all_completed_subtasks: List[Any] = []
            phase_descriptions: List[str] = []
            for p in completed_phases:
                all_completed_subtasks.extend(p["subtasks_completed"])
                phase_descriptions.append(f"{p['number']} {p['description']}")

            task_data.update(
                {
                    "current_phase_number": f"Full Project ({len(completed_phases)} phases)",
                    "current_phase_description": f"Analysis of all completed phases: {', '.join(phase_descriptions)}",
                    "previous_phase_completed": "",
                    "next_phase": "",
                    "subtasks_completed": all_completed_subtasks,
                }
            )
            # Track scope change without modifying config
            effective_scope = "full_project"
        else:
            # Use default behavior (already parsed by detect_current_phase)
            # Override with legacy phase parameter if provided
            if config.phase:
                # Find the specified phase
                phases: List[PhaseData] = (
                    task_data.get("phases", []) if task_data else []
                )
                for i, p in enumerate(phases):
                    if p["number"] == config.phase:
                        # Find previous completed phase
                        previous_phase_completed = ""
                        if i > 0:
                            prev_phase = phases[i - 1]
                            previous_phase_completed = (
                                f"{prev_phase['number']} {prev_phase['description']}"
                            )

                        # Find next phase
                        next_phase = ""
                        if i < len(phases) - 1:
                            next_phase_obj = phases[i + 1]
                            next_phase = f"{next_phase_obj['number']} {next_phase_obj['description']}"

                        # Override the detected phase data
                        task_data.update(
                            {
                                "current_phase_number": p["number"],
                                "current_phase_description": p["description"],
                                "previous_phase_completed": previous_phase_completed,
                                "next_phase": next_phase,
                                "subtasks_completed": p["subtasks_completed"],
                            }
                        )
                        break

    elif config.scope == "full_project":
        # Analyze all completed phases
        phases: List[PhaseData] = task_data.get("phases", []) if task_data else []
        completed_phases = [p for p in phases if p.get("subtasks_complete", False)]
        if completed_phases:
            # Use summary information for all completed phases
            all_completed_subtasks = []
            phase_descriptions = []
            for p in completed_phases:
                all_completed_subtasks.extend(p["subtasks_completed"])
                phase_descriptions.append(f"{p['number']} {p['description']}")

            task_data.update(
                {
                    "current_phase_number": f"Full Project ({len(completed_phases)} phases)",
                    "current_phase_description": f"Analysis of all completed phases: {', '.join(phase_descriptions)}",
                    "previous_phase_completed": "",
                    "next_phase": "",
                    "subtasks_completed": all_completed_subtasks,
                }
            )
        else:
            # No completed phases, use default behavior
            pass

    elif config.scope == "specific_phase":
        # Find and validate the specified phase
        target_phase = None
        phases: List[PhaseData] = task_data.get("phases", []) if task_data else []
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
            raise ValueError(error_msg)

        i, p = target_phase
        # Find previous completed phase
        previous_phase_completed = ""
        if i > 0:
            prev_phase = phases[i - 1]
            previous_phase_completed = (
                f"{prev_phase['number']} {prev_phase['description']}"
            )

        # Find next phase
        next_phase = ""
        if i < len(phases) - 1:
            next_phase_obj = phases[i + 1]
            next_phase = f"{next_phase_obj['number']} {next_phase_obj['description']}"

        # Override with specific phase data
        task_data.update(
            {
                "current_phase_number": p["number"],
                "current_phase_description": p["description"],
                "previous_phase_completed": previous_phase_completed,
                "next_phase": next_phase,
                "subtasks_completed": p["subtasks_completed"],
            }
        )

    elif config.scope == "specific_task":
        # Find and validate the specified task
        target_task = None
        target_phase = None
        phases: List[PhaseData] = task_data.get("phases", []) if task_data else []
        for i, p in enumerate(phases):
            for subtask in p["subtasks"]:
                if subtask["number"] == config.task_number:
                    target_task = subtask
                    target_phase = (i, p)
                    break
            if target_task:
                break

        if target_task is None or target_phase is None:
            # Get available tasks from all phases
            available_tasks: List[str] = []
            for phase in phases:
                subtasks = phase.get("subtasks", [])
                for subtask in subtasks:
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
            raise ValueError(error_msg)

        # Type guard: At this point we know target_phase is not None and is a tuple
        assert (
            target_phase is not None
        ), "target_phase should not be None after validation"
        i, p = target_phase
        # Override with specific task data
        task_data.update(
            {
                "current_phase_number": target_task["number"],
                "current_phase_description": f"Specific task: {target_task['description']} (from {p['number']} {p['description']})",
                "previous_phase_completed": "",
                "next_phase": "",
                "subtasks_completed": [
                    f"{target_task['number']} {target_task['description']}"
                ],
            }
        )

    # Discover configurations early for integration
    config_types: List[str] = []
    if config.include_claude_memory:
        config_types.append("Claude memory")
    if config.include_cursor_rules:
        config_types.append("Cursor rules")

    if config_types:
        print(f"🔍 Discovering {' and '.join(config_types)}...")
        configurations: DiscoveredConfigurations = (
            discover_project_configurations_with_flags(
                config.project_path,
                config.include_claude_memory,
                config.include_cursor_rules,
            )
        )
    else:
        print("ℹ️  Configuration discovery disabled")
        configurations: DiscoveredConfigurations = {
            "claude_memory_files": [],
            "cursor_rules": [],
            "discovery_errors": [],
            "performance_stats": {},
        }

    # Extract typed values from configurations
    claude_memory_files: List[ClaudeMemoryFile] = configurations["claude_memory_files"]
    cursor_rules: List[CursorRule] = configurations["cursor_rules"]
    discovery_errors: List[Dict[str, Any]] = configurations["discovery_errors"]

    claude_files_count = len(claude_memory_files)
    cursor_rules_count = len(cursor_rules)
    errors_count = len(discovery_errors)

    if claude_files_count > 0 or cursor_rules_count > 0:
        print(
            f"✅ Found {claude_files_count} Claude memory files, {cursor_rules_count} Cursor rules"
        )
    else:
        print("ℹ️  No configuration files found (this is optional)")

    if errors_count > 0:
        print(f"⚠️  {errors_count} configuration discovery errors (will continue)")

    # Get git changes based on review mode
    changed_files: List[Dict[str, Any]] = []
    pr_data: Optional[Dict[str, Any]] = None

    if current_mode == "github_pr":
        # GitHub PR analysis mode
        print("🔄 Fetching PR data from GitHub...")
        try:
            # Check if GitHub PR integration is available
            if get_complete_pr_analysis is None:
                raise ImportError("GitHub PR integration not available")

            # Type guard: Ensure github_pr_url is not None
            if config.github_pr_url is None:
                raise ValueError("GitHub PR URL is required for PR analysis mode")

            pr_analysis = get_complete_pr_analysis(config.github_pr_url)

            # Convert PR file changes to our expected format
            for file_change in pr_analysis["file_changes"]["changed_files"]:
                changed_files.append(
                    {
                        "path": os.path.join(config.project_path, file_change["path"]),
                        "status": f"PR-{file_change['status']}",
                        "content": file_change.get("patch", "[Content not available]"),
                    }
                )

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
            # Fallback to task list mode
            changed_files = get_changed_files(config.project_path)

    else:
        # Task list based mode (default)
        changed_files = get_changed_files(config.project_path)

    # Generate file tree
    file_tree = generate_file_tree(config.project_path)

    # Get applicable configuration rules for changed files
    changed_file_paths = [f["path"] for f in changed_files]
    applicable_rules = get_applicable_rules_for_files(cursor_rules, changed_file_paths)

    # Format configuration content for AI consumption
    configuration_content = format_configuration_context_for_ai(
        claude_memory_files, cursor_rules
    )

    # Prepare template data with enhanced configuration support
    template_data: Dict[str, Any] = {
        "prd_summary": prd_summary,
        "total_phases": task_data["total_phases"],
        "current_phase_number": task_data["current_phase_number"],
        "previous_phase_completed": task_data["previous_phase_completed"],
        "next_phase": task_data["next_phase"],
        "current_phase_description": task_data["current_phase_description"],
        "subtasks_completed": task_data["subtasks_completed"],
        "project_path": config.project_path,
        "file_tree": file_tree,
        "changed_files": changed_files,
        "scope": effective_scope,  # Use effective scope to reflect auto-expansion
        "phase_number": (
            config.phase_number if config.scope == "specific_phase" else None
        ),
        "task_number": (
            config.task_number if config.scope == "specific_task" else None
        ),
        "branch_comparison_data": pr_data,
        "review_mode": current_mode,
        # Enhanced configuration data
        "configuration_content": configuration_content,
        "claude_memory_files": configurations["claude_memory_files"],
        "cursor_rules": configurations["cursor_rules"],
        "applicable_rules": applicable_rules,
        "configuration_errors": configurations["discovery_errors"],
        "raw_context_only": config.raw_context_only,
        "auto_prompt_content": config.auto_prompt_content,
    }

    return template_data


def process_and_output_review(
    config: CodeReviewConfig, template_data: Dict[str, Any]
) -> Tuple[str, Optional[str]]:
    """
    Process template data and output review results.

    This function takes the prepared template_data, formats it using
    format_review_template, saves it to a file, and then conditionally
    calls send_to_gemini_for_review.

    Args:
        config: CodeReviewConfig object
        template_data: Dictionary containing all template data

    Returns:
        Tuple of (context_file_path, gemini_review_path)
    """
    # Format template
    review_context = format_review_template(template_data)

    # Save output with scope-based naming
    if config.output is None:
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
                    raise ValueError(
                        "Phase number is required for specific_phase scope"
                    )
                phase_safe = config.phase_number.replace(".", "-")
                mode_prefix = f"phase-{phase_safe}"
            elif config.scope == "specific_task":
                if config.task_number is None:
                    raise ValueError("Task number is required for specific_task scope")
                task_safe = config.task_number.replace(".", "-")
                mode_prefix = f"task-{task_safe}"
            else:
                mode_prefix = "unknown"

        # Ensure project_path is not None
        project_path = (
            config.project_path if config.project_path is not None else os.getcwd()
        )
        config.output = os.path.join(
            project_path, f"code-review-context-{mode_prefix}-{timestamp}.md"
        )

    # config.output is guaranteed to be set at this point
    output_path = config.output
    assert output_path is not None, "Output path should be set by now"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(review_context)

    print(f"📝 Generated review context: {os.path.basename(output_path)}")

    # Send to Gemini for comprehensive review if enabled
    gemini_output = None
    if config.enable_gemini_review:
        print("🔄 Sending to Gemini for AI code review...")
        # Ensure project_path is not None
        project_path = (
            config.project_path if config.project_path is not None else os.getcwd()
        )
        gemini_output = send_to_gemini_for_review(
            review_context, project_path, config.temperature
        )
        if gemini_output:
            print(f"✅ AI code review completed: {os.path.basename(gemini_output)}")
        else:
            print(
                "⚠️  AI code review failed or was skipped (check API key and model availability)"
            )

    return output_path, gemini_output
