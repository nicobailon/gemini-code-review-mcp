#!/usr/bin/env python3
"""
Ask Gemini tool - Direct question-answering with optional file context.

This module provides a streamlined way to ask questions to Gemini AI,
optionally including file context for code-specific queries.
"""

import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from .file_context_generator import generate_file_context_data
from .file_context_types import FileContextConfig, FileSelection
from .gemini_api_client import send_to_gemini_for_review

logger = logging.getLogger(__name__)


def ask_gemini(
    question: str,
    file_selections: Optional[List[Dict[str, Any]]] = None,
    project_path: Optional[str] = None,
    user_instructions: Optional[str] = None,
    temperature: float = 0.5,
    include_claude_memory: bool = True,
    include_cursor_rules: bool = False,
    text_output: bool = True,
    output_path: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    Ask Gemini a question with optional file context.
    
    This function provides a direct interface to Gemini AI for answering questions,
    optionally including specific files as context. It combines file context generation
    and Gemini API calls in a single, memory-efficient pipeline.
    
    Args:
        question: The question to ask Gemini (required)
        file_selections: Optional list of files to include as context:
            - path: str (required) - File path
            - line_ranges: Optional[List[Tuple[int, int]]] - Line ranges
        project_path: Optional project root for relative paths
        user_instructions: Additional context or instructions
        temperature: Model temperature (0.0-2.0, default: 0.5)
        include_claude_memory: Include CLAUDE.md files (default: True)
        include_cursor_rules: Include cursor rules (default: False)
        text_output: Return text directly (True) or save to file (False)
        output_path: Custom output path when text_output=False
        model: Optional Gemini model override
        
    Returns:
        If text_output=True: Gemini's response as text
        If text_output=False: Success message with file path
        
    Raises:
        ValueError: If question is empty or invalid parameters
        Exception: If Gemini API fails
    """
    # Validate required parameters
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")
    
    # Set default project path if not provided
    if project_path is None:
        project_path = os.getcwd()
    
    logger.info(f"Processing question for Gemini: {question[:100]}...")
    
    # Build the complete prompt
    prompt_parts: List[str] = []
    
    # Add file context if provided
    if file_selections:
        logger.info(f"Including context from {len(file_selections)} files")
        
        try:
            # Convert file_selections to FileSelection objects
            normalized_selections: List[FileSelection] = []
            for selection in file_selections:
                if "path" not in selection:
                    raise ValueError("Each file selection must have a 'path' field")
                
                normalized_selection = FileSelection(
                    path=selection["path"],
                    line_ranges=selection.get("line_ranges"),
                    include_full=selection.get("include_full", True)
                )
                normalized_selections.append(normalized_selection)
            
            # Generate file context
            config = FileContextConfig(
                file_selections=normalized_selections,
                project_path=project_path,
                user_instructions=None,  # We'll add instructions separately
                include_claude_memory=include_claude_memory,
                include_cursor_rules=include_cursor_rules,
                auto_meta_prompt=False,  # We're providing our own prompt
                temperature=temperature,
                text_output=True,  # Always get content in memory
            )
            
            result = generate_file_context_data(config)
            
            # Add file context to prompt
            prompt_parts.append("## File Context\n")
            prompt_parts.append(result.content)
            prompt_parts.append("\n")
            
            # Report any excluded files
            if result.excluded_files:
                logger.warning(f"Some files were excluded: {result.excluded_files}")
        
        except Exception as e:
            logger.error(f"Failed to generate file context: {e}")
            # Continue without file context rather than failing completely
            prompt_parts.append(f"Note: Failed to load file context: {str(e)}\n\n")
    
    # Add user instructions if provided
    if user_instructions:
        prompt_parts.append("## Additional Instructions\n")
        prompt_parts.append(user_instructions)
        prompt_parts.append("\n\n")
    
    # Add the main question
    prompt_parts.append("## Question\n")
    prompt_parts.append(question)
    
    # Combine all parts
    complete_prompt = "\n".join(prompt_parts)
    
    logger.info("Sending question to Gemini API...")
    
    try:
        # Call Gemini API
        response = send_to_gemini_for_review(
            context_content=complete_prompt,
            temperature=temperature,
            model=model,
            return_text=True,  # Always get text first
            include_formatting=False,  # No headers/footers for Q&A
        )
        
        if not response:
            raise Exception("Gemini API returned empty response")
        
        # Handle output based on text_output setting
        if text_output:
            return response
        else:
            # Save to file with metadata
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            
            if output_path is None:
                # Generate default filename
                output_path = os.path.join(
                    project_path,
                    f"gemini-response-{timestamp}.md"
                )
            
            # Format content with metadata
            file_content = f"""# Gemini Response
*Generated on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}*

## Question
{question}

## Response
{response}

---
*Response generated by Gemini AI*
"""
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Write file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            logger.info(f"Saved response to {output_path}")
            return f"Gemini response saved to: {os.path.basename(output_path)}"
    
    except Exception as e:
        logger.error(f"Failed to get response from Gemini: {e}")
        raise Exception(f"Failed to get response from Gemini: {str(e)}")


def ask_gemini_direct(
    question: str,
    context: Optional[str] = None,
    temperature: float = 0.5,
    model: Optional[str] = None,
) -> str:
    """
    Simplified direct interface to ask Gemini without file handling.
    
    This is a convenience function for simple questions that don't need
    file context management.
    
    Args:
        question: The question to ask
        context: Optional context string
        temperature: Model temperature
        model: Optional model override
        
    Returns:
        Gemini's response as text
    """
    # Build prompt
    if context:
        prompt = f"{context}\n\nQuestion: {question}"
    else:
        prompt = question
    
    # Call Gemini directly
    response = send_to_gemini_for_review(
        context_content=prompt,
        temperature=temperature,
        model=model,
        return_text=True,
        include_formatting=False,
    )
    
    # Ensure we always return a string
    return response if response else ""