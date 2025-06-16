"""Helper functions for generating code review context."""

import os
from typing import List, Optional, Union

from ..services.generate_code_review_context import generate_code_review_context_main
from ..services.meta_prompt_analyzer import generate_optimized_meta_prompt
from .model_config_manager import load_model_config


def generate_code_review_context(
    project_path: str,
    scope: str = "recent_phase",
    phase_number: Optional[str] = None,
    task_number: Optional[str] = None,
    current_phase: Optional[str] = None,
    output_path: Optional[str] = None,
    enable_gemini_review: bool = False,
    temperature: float = 0.5,
    include_claude_memory: bool = True,
    include_cursor_rules: bool = False,
    raw_context_only: bool = False,
    text_output: bool = True,
    auto_meta_prompt: bool = True,
    thinking_budget: Optional[int] = None,
    url_context: Optional[Union[str, List[str]]] = None,
) -> str:
    """Prepare analysis data and context for code review (does not generate the actual review).

    Args:
        project_path: Absolute path to project root directory
        scope: Review scope - 'recent_phase' (default), 'full_project', 'specific_phase', 'specific_task'
        phase_number: Phase number for specific_phase scope (e.g., '2.0')
        task_number: Task number for specific_task scope (e.g., '1.2')
        current_phase: Legacy phase override (e.g., '2.0'). If not provided, auto-detects from task list
        output_path: Custom output file path. If not provided, uses default timestamped path
        enable_gemini_review: Enable Gemini AI code review generation (default: true)
        temperature: Temperature for AI model (default: 0.5, range: 0.0-2.0)
        include_claude_memory: Include CLAUDE.md files in context (default: true)
        include_cursor_rules: Include Cursor rules files in context (default: false)
        raw_context_only: Exclude default AI review instructions (default: false)
        text_output: Return context directly as text (default: true - for AI agent chaining)
        auto_meta_prompt: Automatically generate and embed meta prompt in user_instructions (default: true)
        thinking_budget: Optional token budget for thinking mode (if supported by model)
        url_context: Optional URL(s) to include in context - can be string or list of strings

    Returns:
        Default (text_output=True): Generated context content as text string for AI agent chaining
        If text_output=False: Success message with file paths (saves to code-review-context-[timestamp].md)
    """

    # Comprehensive error handling to prevent TaskGroup issues
    try:
        # Validate project_path
        if not project_path:
            return "ERROR: project_path is required"

        if not os.path.isabs(project_path):
            return "ERROR: project_path must be an absolute path"

        if not os.path.exists(project_path):
            return f"ERROR: Project path does not exist: {project_path}"

        if not os.path.isdir(project_path):
            return f"ERROR: Project path must be a directory: {project_path}"

        # Handle temperature: MCP parameter takes precedence, then env var, then default 0.5
        if temperature == 0.5:  # Default value, check if env var should override
            temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.5"))

        # Load model config to show capabilities info
        config = load_model_config()
        model_config = os.getenv("GEMINI_MODEL", config["defaults"]["model"])
        # Resolve model aliases to actual API model names
        resolved_model = config["model_aliases"].get(model_config, model_config)

        # Detect capabilities
        supports_url_context = (
            resolved_model in config["model_capabilities"]["url_context_supported"]
        )
        supports_grounding = (
            "gemini-1.5" in resolved_model
            or "gemini-2.0" in resolved_model
            or "gemini-2.5" in resolved_model
        )
        supports_thinking = (
            resolved_model in config["model_capabilities"]["thinking_mode_supported"]
        )

        # Check if features are actually enabled (considering disable flags)
        disable_url_context = (
            os.getenv("DISABLE_URL_CONTEXT", "false").lower() == "true"
        )
        disable_grounding = os.getenv("DISABLE_GROUNDING", "false").lower() == "true"
        disable_thinking = os.getenv("DISABLE_THINKING", "false").lower() == "true"

        actual_capabilities: List[str] = []
        if supports_url_context and not disable_url_context:
            actual_capabilities.append("URL context")
        if supports_grounding and not disable_grounding:
            actual_capabilities.append("web grounding")
        if supports_thinking and not disable_thinking:
            actual_capabilities.append("thinking mode")

        # Generate meta prompt if requested
        auto_prompt_content = None
        if auto_meta_prompt:
            try:
                # Use optimized meta prompt generation without creating intermediate files
                meta_prompt_result = generate_optimized_meta_prompt(
                    project_path=project_path,
                    scope=scope,
                    thinking_budget=thinking_budget,
                )
                auto_prompt_content = meta_prompt_result.get("generated_prompt")
                if not auto_prompt_content:
                    return "ERROR: Meta prompt generation failed - no content generated"
            except Exception as e:
                return f"ERROR: Meta prompt generation failed: {str(e)}"

        # Generate review context using enhanced logic
        try:
            # Call the main function which now returns a tuple (context_file, gemini_file)
            output_file, gemini_file = generate_code_review_context_main(
                project_path=project_path,
                phase=current_phase,  # Legacy parameter
                output=output_path,
                enable_gemini_review=enable_gemini_review,
                scope=scope,
                phase_number=phase_number,
                task_number=task_number,
                task_list=None,  # No task list for this internal helper
                temperature=temperature,
                include_claude_memory=include_claude_memory,
                include_cursor_rules=include_cursor_rules,
                raw_context_only=raw_context_only,
                auto_prompt_content=auto_prompt_content,
            )

            # Return response based on text_output setting
            if text_output:
                # Return text content directly for AI agent chaining
                try:
                    with open(output_file, "r", encoding="utf-8") as f:
                        context_content = f.read()
                    return context_content
                except Exception as e:
                    return f"ERROR: Could not read generated context file: {str(e)}"
            else:
                # Return user-friendly message with file paths (legacy mode)
                response_parts: List[str] = []
                response_parts.append(
                    f"🔍 Analyzed project: {os.path.basename(os.path.abspath(project_path))}"
                )
                response_parts.append(f"📊 Review scope: {scope}")
                if enable_gemini_review:
                    response_parts.append(f"🌡️ AI temperature: {temperature}")

                response_parts.append(
                    f"\n📝 Generated review context: {os.path.basename(output_file)}"
                )

                if enable_gemini_review:
                    response_parts.append(f"\n🤖 Using Gemini model: {resolved_model}")
                    if actual_capabilities:
                        response_parts.append(
                            f"✨ Enhanced features enabled: {', '.join(actual_capabilities)}"
                        )
                    else:
                        response_parts.append(
                            "⚡ Standard features: Basic text generation"
                        )

                    if gemini_file:
                        response_parts.append(
                            f"✅ AI code review completed: {os.path.basename(gemini_file)}"
                        )
                    else:
                        response_parts.append("⚠️ AI code review failed or was skipped")

                # List generated files
                files_generated: List[str] = [os.path.basename(output_file)]
                if gemini_file:
                    files_generated.append(os.path.basename(gemini_file))
                response_parts.append("\n🎉 Code review process completed!")
                response_parts.append(
                    f"📄 Files generated: {', '.join(files_generated)}"
                )

                # Add file paths for reference
                response_parts.append("\nOutput files:")
                response_parts.append(f"- Context: {output_file}")
                if gemini_file:
                    response_parts.append(f"- AI Review: {gemini_file}")

                return "\n".join(response_parts)

        except Exception as e:
            return f"ERROR: Error generating code review context: {str(e)}"

    except Exception as e:
        # Catch-all to ensure no exceptions escape the tool function
        return f"ERROR: Unexpected error: {str(e)}"