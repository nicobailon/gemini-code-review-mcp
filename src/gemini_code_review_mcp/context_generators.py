"""In-memory context generation functions for code review."""

import datetime
import os
from typing import List, Optional

from .services.context_builder import discover_project_configurations_with_fallback
from .services.github_pr_integration import get_complete_pr_analysis


def generate_context_in_memory(
    github_pr_url: Optional[str] = None,
    project_path: Optional[str] = None,
    include_claude_memory: bool = True,
    include_cursor_rules: bool = False,
    auto_prompt_content: Optional[str] = None,
    temperature: float = 0.5,
) -> str:
    """
    Generate code review context content in memory without creating any files.

    This function extracts the core context generation logic without file I/O operations.
    It's designed for the DEFAULT behavior where no files should be created.

    Args:
        github_pr_url: GitHub PR URL for analysis
        project_path: Project directory path
        include_claude_memory: Include CLAUDE.md files in context
        include_cursor_rules: Include Cursor rules files in context
        auto_prompt_content: Generated meta-prompt content to embed
        temperature: AI temperature setting

    Returns:
        Generated context content as string
    """
    try:
        if not project_path:
            project_path = os.getcwd()

        # Generate timestamp for context header
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")

        # Start building context content
        context_parts: List[str] = []

        # Header
        context_parts.append("# Code Review Context - Review Mode: GitHub PR Analysis")
        context_parts.append(f"*Generated on {timestamp}*")
        context_parts.append("")

        # Add user instructions (meta prompt) if provided
        if auto_prompt_content:
            context_parts.append("<user_instructions>")
            context_parts.append(auto_prompt_content)
            context_parts.append("</user_instructions>")
            context_parts.append("")

        # Project summary
        project_name = os.path.basename(os.path.abspath(project_path))
        context_parts.append("<project_context>")
        context_parts.append(
            f"Generate comprehensive code review for recent development changes focusing on code quality, security, performance, and best practices for project: {project_name}"
        )
        context_parts.append("</project_context>")
        context_parts.append("")

        # GitHub PR Analysis
        if github_pr_url:
            try:
                context_parts.append("## GitHub Pull Request Analysis")
                context_parts.append(f"**PR URL:** {github_pr_url}")
                context_parts.append("")

                # Get PR data
                pr_analysis = get_complete_pr_analysis(github_pr_url)
                pr_data = pr_analysis.get("pr_data", {})
                file_changes = pr_analysis.get("file_changes", {})

                # PR metadata
                context_parts.append("### Pull Request Details")
                context_parts.append(f"- **Title:** {pr_data.get('title', 'N/A')}")
                context_parts.append(f"- **Author:** {pr_data.get('author', 'N/A')}")
                context_parts.append(
                    f"- **Source Branch:** {pr_data.get('source_branch', 'N/A')}"
                )
                context_parts.append(
                    f"- **Target Branch:** {pr_data.get('target_branch', 'N/A')}"
                )
                context_parts.append(f"- **Status:** {pr_data.get('state', 'N/A')}")
                context_parts.append("")

                if pr_data.get("body"):
                    context_parts.append("### PR Description")
                    context_parts.append(pr_data["body"])
                    context_parts.append("")

                # File changes summary
                summary = file_changes.get("summary", {})
                context_parts.append("### Changes Summary")
                context_parts.append(
                    f"- **Files Changed:** {summary.get('files_changed', 0)}"
                )
                context_parts.append(
                    f"- **Lines Added:** {summary.get('total_additions', 0)}"
                )
                context_parts.append(
                    f"- **Lines Deleted:** {summary.get('total_deletions', 0)}"
                )
                context_parts.append("")

                # File changes details
                changed_files = file_changes.get("changed_files", [])
                if changed_files:
                    context_parts.append("### File Changes")
                    for file_change in changed_files:
                        context_parts.append(f"#### {file_change['path']}")
                        context_parts.append(f"**Status:** {file_change['status']}")
                        context_parts.append(
                            f"**Changes:** +{file_change.get('additions', 0)} -{file_change.get('deletions', 0)}"
                        )

                        if file_change.get("patch"):
                            context_parts.append("```diff")
                            context_parts.append(file_change["patch"])
                            context_parts.append("```")
                        context_parts.append("")

            except Exception as e:
                context_parts.append(f"⚠️ Failed to fetch PR data: {str(e)}")
                context_parts.append("")

        # Configuration discovery (CLAUDE.md, Cursor rules, etc.)
        if include_claude_memory or include_cursor_rules:
            try:
                config_data = discover_project_configurations_with_fallback(
                    project_path
                )

                if include_claude_memory and config_data.get("claude_memory_files"):
                    context_parts.append("## Project Configuration - CLAUDE.md Files")
                    for memory_file in config_data["claude_memory_files"]:
                        context_parts.append(f"### {memory_file['path']}")
                        context_parts.append("```markdown")
                        context_parts.append(memory_file["content"])
                        context_parts.append("```")
                        context_parts.append("")

                if include_cursor_rules and config_data.get("cursor_rules"):
                    context_parts.append("## Project Configuration - Cursor Rules")
                    for rule in config_data["cursor_rules"]:
                        context_parts.append(f"### {rule['path']}")
                        context_parts.append("```")
                        context_parts.append(rule["content"])
                        context_parts.append("```")
                        context_parts.append("")

            except Exception as e:
                context_parts.append(f"⚠️ Configuration discovery failed: {str(e)}")
                context_parts.append("")

        # Footer
        context_parts.append("---")
        context_parts.append(
            f"*Context generated in-memory for project: {project_name}*"
        )

        return "\n".join(context_parts)

    except Exception as e:
        # Fallback minimal context
        return f"""# Code Review Context - Error Recovery

⚠️ Failed to generate full context: {str(e)}

## Basic Information
- **Project Path:** {project_path or 'Unknown'}
- **GitHub PR URL:** {github_pr_url or 'Not provided'}
- **Timestamp:** {datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}

Please review the code changes manually or check the error above.
"""