"""GitHub PR review tool for MCP server."""

import datetime
import io
import os
from contextlib import redirect_stderr, redirect_stdout
from typing import List, Optional, Union

from ..context_generators import generate_context_in_memory
from ..services.gemini_api_client import send_to_gemini_for_review
from ..services.generate_code_review_context import generate_code_review_context_main
from ..services.meta_prompt_analyzer import generate_optimized_meta_prompt


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
) -> str:
    """Generate code review for a GitHub Pull Request with configuration discovery.

    Args:
        github_pr_url: GitHub PR URL (e.g., 'https://github.com/owner/repo/pull/123')
        project_path: Optional local project path for context (default: current directory)
        temperature: Temperature for AI model (default: 0.5, range: 0.0-2.0)
        enable_gemini_review: Enable Gemini AI code review generation (default: true)
        include_claude_memory: Include CLAUDE.md files in context (default: true)
        include_cursor_rules: Include Cursor rules files in context (default: false)
        auto_meta_prompt: Automatically generate and embed meta prompt in user_instructions (default: true)
        use_templated_instructions: Use templated backup instructions instead of generated meta prompt (default: false)
        create_context_file: Save context to file and return context content (default: false)
        raw_context_only: Return raw context content without AI processing (default: false)
        text_output: Return content directly without saving (default: false - saves to timestamped .md file)
        thinking_budget: Optional token budget for thinking mode (if supported by model)
        url_context: Optional URL(s) to include in context - can be string or list of strings

    Returns:
        Default: Saves review to pr-review-feedback-[timestamp].md file and returns success message
        If text_output=True: Returns AI review content directly as text (no file created)
        If raw_context_only=True: Context content or success message with context file path
    """
    try:
        # Validate required parameters per test expectations
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

        # Initialize variables to avoid unbound variable issues
        context_content = ""
        output_file = None

        # Generate GitHub PR review
        # Capture stdout to detect error messages
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            # Generate meta prompt if requested and not overridden by use_templated_instructions
            auto_prompt_content = None
            if auto_meta_prompt and not use_templated_instructions:
                try:
                    # Use optimized meta prompt generation without creating intermediate files
                    meta_prompt_result = generate_optimized_meta_prompt(
                        project_path=project_path,
                        scope="recent_phase",  # Default scope for PR reviews
                        temperature=temperature,
                        thinking_budget=thinking_budget,
                    )
                    auto_prompt_content = meta_prompt_result.get("generated_prompt")
                    if not auto_prompt_content:
                        # Fall back to templated instructions instead of failing
                        auto_prompt_content = None
                except Exception:
                    # Fall back to templated instructions instead of failing
                    auto_prompt_content = None

            # Handle raw_context_only mode first (overrides other settings)
            if raw_context_only:
                # Mode: Generate and save context file (for raw context requests)
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    output_file, _gemini_file = generate_code_review_context_main(
                        project_path=project_path,
                        enable_gemini_review=False,  # Don't generate AI review for raw context
                        temperature=temperature,
                        github_pr_url=github_pr_url,
                        include_claude_memory=include_claude_memory,
                        include_cursor_rules=include_cursor_rules,
                        auto_prompt_content=auto_prompt_content,
                    )
            elif create_context_file:
                # Mode: Create context file (for backward compatibility)
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    output_file, _gemini_file = generate_code_review_context_main(
                        project_path=project_path,
                        enable_gemini_review=False,  # Don't let it create AI feedback files
                        temperature=temperature,
                        github_pr_url=github_pr_url,
                        include_claude_memory=include_claude_memory,
                        include_cursor_rules=include_cursor_rules,
                        auto_prompt_content=auto_prompt_content,
                    )
            else:
                # DEFAULT behavior: Pure in-memory context generation (NO intermediate files created)
                try:
                    # Use our pure in-memory function that creates NO files at all
                    context_content = generate_context_in_memory(
                        github_pr_url=github_pr_url,
                        project_path=project_path,
                        include_claude_memory=include_claude_memory,
                        include_cursor_rules=include_cursor_rules,
                        auto_prompt_content=auto_prompt_content,
                        temperature=temperature,
                    )

                    # No files created - context is purely in memory
                    output_file = None

                except Exception as e:
                    return f"ERROR: Failed to generate context in memory: {str(e)}"

            # Check captured output for error indicators
            captured_output = stdout_capture.getvalue()
            if "❌ Failed to fetch PR data" in captured_output:
                # Extract the specific error message
                if "Invalid GitHub token" in captured_output:
                    error_msg = "Invalid GitHub token or insufficient permissions"
                elif "PR not found" in captured_output:
                    error_msg = "PR not found"
                elif "Invalid GitHub PR URL" in captured_output:
                    error_msg = "Invalid GitHub PR URL"
                else:
                    error_msg = "Failed to fetch PR data"

                return f"ERROR: GitHub PR review failed: {error_msg}"

        except ValueError as e:
            # This catches explicit errors from the generate_review_context function
            return f"ERROR: GitHub PR review failed: {str(e)}"

        # Handle different output modes based on parameters
        try:
            # Handle raw_context_only case first (highest priority)
            if raw_context_only:
                if output_file and os.path.exists(output_file):
                    with open(output_file, "r", encoding="utf-8") as f:
                        context_content = f.read()

                    if text_output:
                        # Return context content directly WITHOUT creating any files
                        return context_content
                    else:
                        # Save context to properly named file and return success message
                        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                        context_filename = (
                            f"code-review-context-github-pr-{timestamp}.md"
                        )
                        context_filepath = os.path.join(project_path, context_filename)

                        with open(context_filepath, "w", encoding="utf-8") as f:
                            f.write(context_content)

                        return f"Code review context generated successfully: {context_filename}"
                else:
                    return "ERROR: Failed to generate context for raw_context_only mode"

            # Handle create_context_file case (backward compatibility)
            elif create_context_file:
                if output_file and os.path.exists(output_file):
                    with open(output_file, "r", encoding="utf-8") as f:
                        context_content = f.read()

                    # Save context to properly named file
                    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                    context_filename = f"code-review-context-github-pr-{timestamp}.md"
                    context_filepath = os.path.join(project_path, context_filename)

                    with open(context_filepath, "w", encoding="utf-8") as f:
                        f.write(context_content)

                    return f"Code review context generated successfully: {context_filename}"
                else:
                    return "ERROR: Failed to generate context file"

            # DEFAULT case: Context already generated in memory
            else:
                # For default case, context_content should already be available from in-memory generation
                if "context_content" not in locals():
                    return "ERROR: No context content available - in-memory generation failed"

                # Generate AI feedback from context
                # Determine user instructions based on auto_meta_prompt setting
                if auto_prompt_content:
                    # Use generated meta prompt as user instructions
                    user_instructions = auto_prompt_content
                else:
                    # Use templated backup instructions
                    user_instructions = """Please provide a comprehensive code review analysis for the following GitHub PR context.

Focus on:
1. Code quality and best practices
2. Security vulnerabilities  
3. Performance optimizations
4. Maintainability improvements
5. Documentation suggestions

Provide specific, actionable feedback with examples where appropriate."""

                # Generate AI review from the context with proper user instructions
                ai_review_content = send_to_gemini_for_review(
                    context_content=f"""{user_instructions}

{context_content}""",
                    temperature=temperature,
                    return_text=True,  # Return text directly instead of saving to file
                    thinking_budget=thinking_budget,
                )

                # Handle return based on text_output setting
                if ai_review_content:
                    if text_output:
                        # DEFAULT: Return AI content directly (NO files created)
                        return ai_review_content
                    else:
                        # text_output=False: Save to file and return success message
                        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                        feedback_filename = f"pr-review-feedback-{timestamp}.md"
                        feedback_filepath = os.path.join(
                            project_path, feedback_filename
                        )

                        with open(feedback_filepath, "w", encoding="utf-8") as f:
                            f.write(ai_review_content)

                        return f"AI code review generated successfully: {feedback_filename}"
                else:
                    return "ERROR: Failed to generate AI review content"

        except Exception as e:
            return f"ERROR: Failed to generate AI review from context: {str(e)}"

    except Exception as e:
        return f"ERROR: Failed to generate GitHub PR review: {str(e)}"