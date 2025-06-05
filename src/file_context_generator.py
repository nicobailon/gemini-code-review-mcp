#!/usr/bin/env python3
"""
File-based context generation module.

This module orchestrates the generation of context from specific files,
handling file reading, token counting, configuration integration, and
output formatting.
"""

import logging
import os
from datetime import datetime
from typing import List, Optional, Tuple

from .context_builder import (
    discover_project_configurations_with_flags,
    format_configuration_context_for_ai,
)
from .file_context_types import (
    FileContentData,
    FileContextConfig,
    FileContextResult,
    FileSelection,
)
from .file_selector import (
    read_file_with_line_ranges,
    validate_file_paths,
)
from .meta_prompt_analyzer import generate_optimized_meta_prompt
from .model_config_manager import load_model_config

logger = logging.getLogger(__name__)


def generate_file_context_data(config: FileContextConfig) -> FileContextResult:
    """
    Generate context data from selected files.
    
    This is the main orchestration function that coordinates file reading,
    token counting, configuration discovery, and content formatting.
    
    Args:
        config: FileContextConfig with all parameters
        
    Returns:
        FileContextResult with generated content and metadata
        
    Raises:
        TokenLimitExceededError: If content exceeds token limit
    """
    # Set default project path if not provided
    if config.project_path is None:
        config.project_path = os.getcwd()
    
    logger.info(f"Generating file context from {len(config.file_selections)} files")
    
    # Validate file paths
    valid_selections, validation_errors = validate_file_paths(
        config.file_selections, config.project_path
    )
    
    # Read selected files with token tracking
    included_files: List[FileContentData] = []
    excluded_files: List[Tuple[str, str]] = validation_errors.copy()
    total_tokens = 0
    
    # First, discover configurations if requested
    configuration_content = ""
    config_tokens = 0
    
    if config.include_claude_memory or config.include_cursor_rules:
        logger.info("Discovering project configurations...")
        configurations = discover_project_configurations_with_flags(
            config.project_path,
            include_claude_memory=config.include_claude_memory,
            include_cursor_rules=config.include_cursor_rules
        )
        
        # Format configuration content
        configuration_content = format_configuration_context_for_ai(
            configurations["claude_memory_files"],
            configurations["cursor_rules"]
        )
        
        # Estimate tokens for configuration
        config_tokens = len(configuration_content) // 4
        total_tokens += config_tokens
        
        logger.info(f"Configuration content: ~{config_tokens} tokens")
    
    # Read files in order, tracking tokens
    for selection in valid_selections:
        try:
            file_data = read_selected_files([selection], config.project_path)[0]
            
            # Check if adding this file would exceed token limit
            if total_tokens + file_data.estimated_tokens > config.token_limit:
                excluded_files.append((
                    file_data.path,
                    f"Would exceed token limit ({total_tokens + file_data.estimated_tokens} > {config.token_limit})"
                ))
                logger.warning(f"Excluding {file_data.path} due to token limit")
                continue
            
            included_files.append(file_data)
            total_tokens += file_data.estimated_tokens
            
        except Exception as e:
            excluded_files.append((selection["path"], str(e)))
            logger.error(f"Error reading {selection['path']}: {e}")
    
    # Generate file selection summary
    summary = build_file_selection_summary(included_files, excluded_files)
    
    # Format the context template
    context_content = format_file_context_template(
        summary=summary,
        project_path=config.project_path,
        configuration_content=configuration_content,
        included_files=included_files,
        excluded_files=excluded_files,
        user_instructions=config.user_instructions,
        auto_meta_prompt=config.auto_meta_prompt,
        raw_context_only=False  # Include user instructions
    )
    
    # Generate meta-prompt if requested
    meta_prompt = None
    if config.auto_meta_prompt and config.user_instructions is None:
        logger.info("Generating auto meta-prompt...")
        try:
            # Generate meta-prompt
            meta_prompt_result = generate_optimized_meta_prompt(
                project_path=config.project_path,
                scope="recent_phase",  # Default scope for file-based context
                temperature=config.temperature
            )
            meta_prompt = meta_prompt_result.get("generated_prompt")
            
            # Update context with generated meta-prompt
            context_content = format_file_context_template(
                summary=summary,
                project_path=config.project_path,
                configuration_content=configuration_content,
                included_files=included_files,
                excluded_files=excluded_files,
                user_instructions=meta_prompt,
                auto_meta_prompt=False,  # Don't regenerate
                raw_context_only=False
            )
            
        except Exception as e:
            logger.error(f"Failed to generate meta-prompt: {e}")
            # Continue without meta-prompt
    
    return FileContextResult(
        content=context_content,
        total_tokens=total_tokens,
        included_files=included_files,
        excluded_files=excluded_files,
        configuration_content=configuration_content,
        meta_prompt=meta_prompt
    )


def read_selected_files(
    file_selections: List[FileSelection],
    project_path: Optional[str] = None
) -> List[FileContentData]:
    """
    Read multiple files with their line ranges.
    
    Args:
        file_selections: List of file selections
        project_path: Optional project path for relative paths
        
    Returns:
        List of FileContentData objects
    """
    results: List[FileContentData] = []
    
    for selection in file_selections:
        try:
            file_data = read_file_with_line_ranges(
                selection["path"],
                selection.get("line_ranges"),
                project_path
            )
            results.append(file_data)
        except Exception as e:
            logger.error(f"Failed to read {selection['path']}: {e}")
            raise
    
    return results


def build_file_selection_summary(
    included_files: List[FileContentData],
    excluded_files: List[Tuple[str, str]]
) -> str:
    """
    Build a summary of the file selection.
    
    Args:
        included_files: List of included files
        excluded_files: List of (path, reason) for excluded files
        
    Returns:
        Summary text
    """
    lines: List[str] = []
    
    # Summary statistics
    total_files = len(included_files) + len(excluded_files)
    total_lines = sum(f.included_lines for f in included_files)
    total_tokens = sum(f.estimated_tokens for f in included_files)
    
    lines.append(f"Selected {len(included_files)} of {total_files} files")
    lines.append(f"Total lines: {total_lines}")
    lines.append(f"Estimated tokens: {total_tokens}")
    
    # File breakdown
    if included_files:
        lines.append("\nIncluded files:")
        for f in included_files:
            if f.line_ranges:
                ranges_str = ", ".join(f"{s}-{e}" for s, e in f.line_ranges)
                lines.append(f"  - {f.path} (lines {ranges_str}): {f.included_lines} lines")
            else:
                lines.append(f"  - {f.path}: {f.included_lines} lines")
    
    if excluded_files:
        lines.append("\nExcluded files:")
        for path, reason in excluded_files:
            lines.append(f"  - {path}: {reason}")
    
    return "\n".join(lines)


def format_file_context_template(
    summary: str,
    project_path: str,
    configuration_content: str,
    included_files: List[FileContentData],
    excluded_files: List[Tuple[str, str]],
    user_instructions: Optional[str] = None,
    auto_meta_prompt: bool = True,
    raw_context_only: bool = False
) -> str:
    """
    Format the context into the standard template structure.
    
    Args:
        summary: File selection summary
        project_path: Project root path
        configuration_content: Claude/Cursor configuration content
        included_files: List of included file data
        excluded_files: List of excluded files with reasons
        user_instructions: Optional custom instructions
        auto_meta_prompt: Whether to indicate meta-prompt should be generated
        raw_context_only: Whether to exclude user instructions section
        
    Returns:
        Formatted context string
    """
    template = f"""# File-Based Code Review Context

<file_selection_summary>
{summary}
</file_selection_summary>

<project_path>
{project_path}
</project_path>"""

    # Add configuration if available
    if configuration_content:
        template += f"""

<configuration_context>
{configuration_content}
</configuration_context>"""

    # Add selected files
    template += """

<selected_files>"""
    
    for file_data in included_files:
        # Determine file extension for syntax highlighting
        file_ext = os.path.splitext(file_data.path)[1].lstrip(".") or "txt"
        
        # Add file header
        if file_data.line_ranges:
            ranges_str = ", ".join(f"{s}-{e}" for s, e in file_data.line_ranges)
            template += f"""
File: {file_data.path} (lines {ranges_str})"""
        else:
            template += f"""
File: {file_data.path} (full file)"""
        
        template += f"""
```{file_ext}
{file_data.content}
```"""
    
    template += """
</selected_files>"""

    # Add excluded files section if any
    if excluded_files:
        template += """

<excluded_files>"""
        for path, reason in excluded_files:
            template += f"""
- {path}: {reason}"""
        template += """
</excluded_files>"""

    # Add user instructions if not raw context
    if not raw_context_only:
        template += """

<user_instructions>"""
        
        if user_instructions:
            template += user_instructions
        elif auto_meta_prompt:
            template += """[Auto-generated meta-prompt will be inserted here based on the selected files and project context]"""
        else:
            # Default instructions
            model_config = load_model_config()
            default_prompt = model_config["defaults"]["default_prompt"]
            template += f"""
Based on the selected files shown above, {default_prompt}

Focus your review on:
1. Code quality and best practices specific to the included files
2. Potential bugs or issues in the implementation
3. Security concerns if applicable
4. Performance considerations
5. Suggestions for improvement

Please provide specific, actionable feedback with line number references where appropriate."""
        
        template += """
</user_instructions>"""
    
    return template


def save_file_context(
    result: FileContextResult,
    output_path: Optional[str] = None,
    project_path: Optional[str] = None
) -> str:
    """
    Save the generated context to a file.
    
    Args:
        result: FileContextResult with content
        output_path: Optional custom output path
        project_path: Optional project path for default naming
        
    Returns:
        Path to saved file
    """
    if output_path is None:
        # Generate default filename
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        base_path = project_path or os.getcwd()
        output_path = os.path.join(
            base_path,
            f"file-context-{timestamp}.md"
        )
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Write content
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result.content)
    
    logger.info(f"Saved context to {output_path}")
    return output_path