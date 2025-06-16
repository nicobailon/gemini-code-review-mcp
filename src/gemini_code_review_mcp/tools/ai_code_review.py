"""AI code review tool for MCP server."""

import datetime
import os
import tempfile
from typing import List, Optional, Union

from ..services.gemini_api_client import send_to_gemini_for_review
from ..services.generate_code_review_context import generate_code_review_context_main
from ..services.meta_prompt_analyzer import generate_optimized_meta_prompt


async def generate_ai_code_review(
    context_file_path: Optional[str] = None,
    context_content: Optional[str] = None,
    project_path: Optional[str] = None,
    scope: str = "recent_phase",
    phase_number: Optional[str] = None,
    task_number: Optional[str] = None,
    task_list: Optional[str] = None,
    default_prompt: Optional[str] = None,
    output_path: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.5,
    custom_prompt: Optional[str] = None,
    text_output: bool = True,
    auto_meta_prompt: bool = True,
    include_claude_memory: bool = True,
    include_cursor_rules: bool = False,
    thinking_budget: Optional[int] = None,
    url_context: Optional[Union[str, List[str]]] = None,
) -> str:
    """Generate AI-powered code review from context file, content, or project analysis.

    Args:
        context_file_path: Path to existing code review context file (.md)
        context_content: Direct context content (for AI agent chaining)
        project_path: Project path for direct analysis (generates context internally)
        scope: Review scope when using project_path - 'recent_phase', 'full_project', 'specific_phase', 'specific_task'
        phase_number: Phase number for specific_phase scope
        task_number: Task number for specific_task scope
        task_list: Specific task list file to use (overrides automatic discovery)
        default_prompt: Custom default prompt when no task list exists
        output_path: Custom output file path for AI review. If not provided, uses default timestamped path
        model: Optional Gemini model name (e.g., 'gemini-2.0-flash-exp', 'gemini-1.5-pro')
        temperature: Temperature for AI model (default: 0.5, range: 0.0-2.0)
        custom_prompt: Optional custom AI prompt to override default instructions
        text_output: Return review directly as text (default: true - for AI agent chaining)
        auto_meta_prompt: Automatically generate and embed meta prompt (default: true)
        include_claude_memory: Include CLAUDE.md files in context (default: true)
        include_cursor_rules: Include Cursor rules files in context (default: false)
        thinking_budget: Optional token budget for thinking mode (if supported by model)
        url_context: Optional URL(s) to include in context - can be string or list of strings

    Returns:
        Default (text_output=True): Generated AI review content as text string for AI agent chaining
        If text_output=False: Saves to code-review-ai-feedback-[timestamp].md and returns success message
    """

    # Comprehensive error handling
    try:

        # Validate input parameters - exactly one should be provided
        provided_params = sum(
            [
                context_file_path is not None,
                context_content is not None,
                project_path is not None,
            ]
        )

        if provided_params == 0:
            raise ValueError(
                "One of context_file_path, context_content, or project_path is required"
            )
        elif provided_params > 1:
            raise ValueError(
                "Only one of context_file_path, context_content, or project_path should be provided"
            )

        # Validate context_file_path if provided
        if context_file_path is not None:
            if not os.path.isabs(context_file_path):
                return "ERROR: context_file_path must be an absolute path"

            if not os.path.exists(context_file_path):
                return f"ERROR: Context file does not exist: {context_file_path}"

            if not os.path.isfile(context_file_path):
                return f"ERROR: Context file path must be a file: {context_file_path}"

        # Validate context_content if provided
        if context_content is not None:
            if not context_content.strip():
                return "ERROR: context_content cannot be empty"

        # Validate project_path if provided
        if project_path is not None:
            if not os.path.isabs(project_path):
                return "ERROR: project_path must be an absolute path"

            if not os.path.exists(project_path):
                return f"ERROR: Project path does not exist: {project_path}"

            if not os.path.isdir(project_path):
                return f"ERROR: Project path must be a directory: {project_path}"

        # Handle temperature: MCP parameter takes precedence, then env var, then default 0.5
        if temperature == 0.5:  # Default value, check if env var should override
            temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.5"))

        # Generate AI review
        try:
            if context_file_path is not None:
                # Read context file content
                try:
                    with open(context_file_path, "r", encoding="utf-8") as f:
                        file_context_content = f.read().strip()
                except Exception as e:
                    return f"ERROR: Could not read context file: {str(e)}"

                # Generate AI review using Gemini directly
                if custom_prompt:
                    review_content = f"{custom_prompt}\n\n{file_context_content}"
                else:
                    # Use default AI review instructions
                    review_content = f"""Please provide a comprehensive code review analysis for the following code context:

{file_context_content}

Focus on:
1. Code quality and best practices
2. Security vulnerabilities
3. Performance optimizations
4. Maintainability improvements
5. Documentation suggestions

Provide specific, actionable feedback with code examples where appropriate."""

                # Generate AI review using Gemini
                ai_review_content = send_to_gemini_for_review(
                    context_content=review_content,
                    temperature=temperature,
                    model=model,
                    return_text=True,  # Return text directly instead of saving to file
                    thinking_budget=thinking_budget,
                )

                if not ai_review_content:
                    return "ERROR: Gemini API failed to generate AI review"

                # Create AI review file if text_output=False, otherwise keep as None
                if not text_output:
                    # Generate timestamped filename for AI review
                    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                    if output_path:
                        # Use custom output path if provided
                        output_file = output_path
                    else:
                        # Use default naming convention in context file directory
                        context_dir = os.path.dirname(context_file_path)
                        output_file = os.path.join(
                            context_dir, f"code-review-ai-feedback-{timestamp}.md"
                        )

                    # Save AI review content to file
                    try:
                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(ai_review_content)
                    except Exception as e:
                        return f"ERROR: Could not write AI review file: {str(e)}"
                else:
                    # Set output_file to None since we didn't create a file
                    output_file = None

            elif context_content is not None:
                # Handle direct context content mode
                if custom_prompt:
                    review_content = f"{custom_prompt}\n\n{context_content}"
                else:
                    # Use default AI review instructions
                    review_content = f"""Please provide a comprehensive code review analysis for the following code context:

{context_content}

Focus on:
1. Code quality and best practices
2. Security vulnerabilities
3. Performance optimizations
4. Maintainability improvements
5. Documentation suggestions

Provide specific, actionable feedback with code examples where appropriate."""

                # Generate AI review using Gemini
                ai_review_content = send_to_gemini_for_review(
                    context_content=review_content,
                    temperature=temperature,
                    model=model,
                    return_text=True,  # Return text directly instead of saving to file
                    thinking_budget=thinking_budget,
                )

                if not ai_review_content:
                    return "ERROR: Gemini API failed to generate AI review"

                # Create AI review file if text_output=False, otherwise keep as None
                if not text_output:
                    # Generate timestamped filename for AI review
                    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                    if output_path:
                        # Use custom output path if provided
                        output_file = output_path
                    else:
                        # Use default naming convention in current directory
                        output_file = f"code-review-ai-feedback-{timestamp}.md"

                    # Save AI review content to file
                    try:
                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(ai_review_content)
                    except Exception as e:
                        return f"ERROR: Could not write AI review file: {str(e)}"
                else:
                    # Set output_file to None since we didn't create a file
                    output_file = None

            else:
                # Generate context internally from project_path and clean up intermediate files
                # Generate context internally with temporary file cleanup
                temp_context_file = None
                try:
                    # Generate meta prompt if enabled
                    if auto_meta_prompt and project_path:
                        meta_prompt_result = generate_optimized_meta_prompt(
                            project_path=project_path,
                            scope=scope,
                            temperature=temperature,
                            thinking_budget=thinking_budget,
                        )
                        auto_prompt_content = meta_prompt_result.get("generated_prompt")
                    else:
                        auto_prompt_content = None

                    # Create temporary file for context generation
                    with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".md", delete=False
                    ) as temp_file:
                        temp_context_file = temp_file.name

                    # Generate context using existing function with temporary file
                    context_file, _gemini_file = generate_code_review_context_main(
                        project_path=project_path,
                        scope=scope,
                        phase_number=phase_number,
                        task_number=task_number,
                        task_list=task_list,
                        default_prompt=default_prompt,
                        output=temp_context_file,
                        enable_gemini_review=False,  # We'll generate AI review ourselves
                        include_claude_memory=include_claude_memory,
                        include_cursor_rules=include_cursor_rules,
                        raw_context_only=False,
                        auto_prompt_content=auto_prompt_content,
                        temperature=temperature,
                    )

                    # Read the generated context content
                    with open(context_file, "r", encoding="utf-8") as f:
                        internal_context = f.read()

                    # Clean up the temporary context file
                    try:
                        os.unlink(context_file)
                        if temp_context_file and os.path.exists(temp_context_file):
                            os.unlink(temp_context_file)
                    except Exception:
                        pass  # Ignore cleanup errors

                    if not internal_context:
                        return "ERROR: Failed to generate context from project"

                    # Generate AI review using the internal context
                    if custom_prompt:
                        review_content = f"{custom_prompt}\n\n{internal_context}"
                    else:
                        # Use default AI review instructions
                        review_content = f"""Please provide a comprehensive code review analysis for the following code context:

{internal_context}

Focus on:
1. Code quality and best practices
2. Security vulnerabilities
3. Performance optimizations
4. Maintainability improvements
5. Documentation suggestions

Provide specific, actionable feedback with code examples where appropriate."""

                    # Generate AI review using Gemini
                    ai_review_content = send_to_gemini_for_review(
                        context_content=review_content,
                        temperature=temperature,
                        model=model,
                        return_text=True,  # Return text directly instead of saving to file
                        thinking_budget=thinking_budget,
                    )

                    if not ai_review_content:
                        return "ERROR: Gemini API failed to generate AI review"

                    # Create AI review file if text_output=False, otherwise keep as None
                    if not text_output:
                        # Generate timestamped filename for AI review
                        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                        if output_path:
                            # Use custom output path if provided
                            output_file = output_path
                        else:
                            # Use default naming convention in project directory
                            if project_path:
                                output_file = os.path.join(
                                    project_path,
                                    f"code-review-ai-feedback-{timestamp}.md",
                                )
                            else:
                                output_file = f"code-review-ai-feedback-{timestamp}.md"

                        # Save AI review content to file
                        try:
                            with open(output_file, "w", encoding="utf-8") as f:
                                f.write(ai_review_content)
                        except Exception as e:
                            return f"ERROR: Could not write AI review file: {str(e)}"
                    else:
                        # Set output_file to None since we didn't create a persistent file
                        output_file = None

                except Exception as e:
                    # Clean up any temporary files on error
                    if temp_context_file and os.path.exists(temp_context_file):
                        try:
                            os.unlink(temp_context_file)
                        except Exception:
                            pass
                    return f"ERROR: Failed to generate context from project: {str(e)}"

            # Return response based on text_output setting
            if text_output:
                # Return AI review content directly for AI agent chaining
                return ai_review_content
            else:
                # Return user-friendly message with file paths (legacy mode)
                if output_file:
                    return f"Successfully generated AI code review: {output_file}\n\n{ai_review_content}"
                else:
                    return f"Successfully generated AI code review from content:\n\n{ai_review_content}"

        except Exception as e:
            return f"ERROR: Error generating AI code review: {str(e)}"

    except Exception as e:
        # Catch-all to ensure no exceptions escape the tool function
        return f"ERROR: Unexpected error: {str(e)}"