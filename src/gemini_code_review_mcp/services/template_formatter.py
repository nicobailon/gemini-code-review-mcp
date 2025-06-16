"""Template formatting utilities for code review context generation."""

import hashlib
import inspect
import json
import logging
import os
from typing import Any, Dict, List, Optional

from ..cache import get_cache_manager

logger = logging.getLogger(__name__)


def extract_clean_prompt_content(prompt_content: str) -> str:
    """
    Extract clean prompt content from auto-generated meta-prompt.
    
    Removes headers, metadata, and formatting artifacts to get just the prompt text.
    
    Args:
        prompt_content: Raw prompt content that may contain headers and metadata
        
    Returns:
        Clean prompt content without headers or metadata
    """
    if not prompt_content:
        return ""
    
    # Split into lines for processing
    lines = prompt_content.strip().split('\n')
    
    # Find where the actual content starts (skip headers)
    content_start = 0
    for i, line in enumerate(lines):
        # Skip markdown headers and metadata lines
        if line.strip() and not line.startswith('#') and not line.startswith('*') and not line.startswith('---'):
            content_start = i
            break
    
    # Extract the content lines
    content_lines = lines[content_start:]
    
    # Remove any trailing metadata or formatting
    while content_lines and (
        content_lines[-1].strip() == '' or 
        content_lines[-1].startswith('---') or
        content_lines[-1].startswith('*')
    ):
        content_lines.pop()
    
    return '\n'.join(content_lines).strip()


def format_review_template(data: Dict[str, Any], use_cache: bool = True) -> str:
    """
    Format the final review template.

    Args:
        data: Dictionary containing all template data
        use_cache: Whether to use caching for template rendering

    Returns:
        Formatted markdown template
    """
    # Initialize cache variables
    cache = None
    cache_key = None
    
    # Try to get from cache first if enabled
    if use_cache:
        try:
            cache = get_cache_manager()
            
            # Create a cache key from relevant template data
            # Add template version hash to invalidate cache when template changes
            template_code = inspect.getsource(format_review_template)
            template_hash = hashlib.md5(template_code.encode()).hexdigest()[:8]
            
            cache_data = {
                "template_version": template_hash,  # Invalidate when template changes
                "review_mode": data.get("review_mode"),
                "scope": data.get("scope"),
                "phase_number": data.get("phase_number"),
                "task_number": data.get("task_number"),
                "prd_summary": data.get("prd_summary", "")[:100],  # First 100 chars
                "total_phases": data.get("total_phases"),
                "has_config": bool(data.get("configuration_content")),
                "has_url_context": bool(data.get("url_context_content")),
                "changed_files_count": len(data.get("changed_files", [])),
                "file_tree_hash": hashlib.md5(data.get("file_tree", "").encode()).hexdigest()[:8],
            }
            cache_key = hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
            
            cached_result = cache.get("template_render", {"key": cache_key})
            if cached_result is not None:
                logger.debug(f"Using cached template render for key: {cache_key}")
                return cached_result
        except Exception as e:
            logger.debug(f"Cache not available for template rendering: {e}")
            cache = None
            cache_key = None
    
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
    has_task_list = data.get("total_phases", 0) > 0

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
        if data.get("prd_summary"):
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
            template += _get_default_instructions(data)

        template += """
</user_instructions>"""

    # Add URL context if available
    if data.get("url_context_content"):
        template += "\n\n" + data["url_context_content"] + "\n"

    # Cache the result if caching is enabled
    if use_cache and cache is not None and cache_key is not None:
        try:
            # Cache for 30 minutes since templates don't change often
            cache.set("template_render", {"key": cache_key}, template, ttl=1800)
            logger.debug(f"Cached template render for key: {cache_key}")
        except Exception as e:
            logger.debug(f"Failed to cache template render: {e}")

    return template


def _get_default_instructions(data: Dict[str, Any]) -> str:
    """Get default template-based instructions based on review mode and scope."""
    review_mode = data.get("review_mode", "task_list_based")
    branch_data = data.get("branch_comparison_data")

    if review_mode == "github_pr" and branch_data:
        config_note = ""
        if data.get("configuration_content"):
            config_note = "\n\nPay special attention to the configuration context (Claude memory and Cursor rules) provided above, which contains project-specific guidelines and coding standards that should be followed."

        return f"""You are reviewing a GitHub Pull Request that contains changes from branch '{branch_data['pr_data']['source_branch']}' to '{branch_data['pr_data']['target_branch']}'.

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

        return f"""We have completed all phases (and subtasks within) of this project: {data['current_phase_description']}.{config_note}

Based on the PRD, all completed phases, all subtasks that were finished across the entire project, and the files changed in the working directory, your job is to conduct a comprehensive code review and output your code review feedback for the entire project. Identify specific lines or files that are concerning when appropriate."""
    
    elif data["scope"] == "specific_task":
        config_note = ""
        if data.get("configuration_content"):
            config_note = "\n\nImportant: Refer to the configuration context (Claude memory and Cursor rules) provided above for project-specific guidelines and coding standards."

        return f"""We have just completed task #{data['current_phase_number']}: "{data['current_phase_description']}".{config_note}

Based on the PRD, the completed task, and the files changed in the working directory, your job is to conduct a code review and output your code review feedback for this specific task. Identify specific lines or files that are concerning when appropriate."""
    
    else:
        config_note = ""
        if data.get("configuration_content"):
            config_note = "\n\nImportant: Refer to the configuration context (Claude memory and Cursor rules) provided above for project-specific guidelines and coding standards."

        return f"""We have just completed phase #{data['current_phase_number']}: "{data['current_phase_description']}".{config_note}

Based on the PRD, the completed phase, all subtasks that were finished in that phase, and the files changed in the working directory, your job is to conduct a code review and output your code review feedback for the completed phase. Identify specific lines or files that are concerning when appropriate."""