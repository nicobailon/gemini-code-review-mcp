"""Ask Gemini tool for direct API interaction."""

import logging
from typing import Any, Dict, List, Optional

from ..services.file_context_generator import generate_file_context_data
from ..file_context_types import FileContextConfig
from ..helpers.file_selector import normalize_file_selections_from_dicts
from ..services.gemini_api_client import send_to_gemini_for_review

logger = logging.getLogger(__name__)


async def ask_gemini(
    user_instructions: Optional[str] = None,
    file_selections: Optional[List[Dict[str, Any]]] = None,
    project_path: Optional[str] = None,
    include_claude_memory: bool = True,
    include_cursor_rules: bool = False,
    auto_meta_prompt: bool = True,
    temperature: float = 0.5,
    model: Optional[str] = None,
    thinking_budget: Optional[int] = None,
    text_output: bool = True,
) -> str:
    """
    Generates context from files and sends it to Gemini for a response.

    This tool combines context generation with a direct call to the Gemini API.

    Args:
        user_instructions: The primary query or instructions for Gemini.
        file_selections: Optional list of files/line ranges to include in the context.
        project_path: Optional project root for relative paths.
        include_claude_memory: Include CLAUDE.md files in context.
        include_cursor_rules: Include Cursor rules files in context.
        auto_meta_prompt: If no user_instructions, generate a meta-prompt.
        temperature: AI temperature for generation.
        model: Specific Gemini model to use.
        thinking_budget: Optional token budget for thinking mode.
        text_output: If True, return the response as a string. If False, save it to a file.

    Returns:
        The response from Gemini as a string or a success message with the file path.
    """
    try:
        # Step 1: Normalize file selections (handle empty case)
        normalized_selections = normalize_file_selections_from_dicts(file_selections)

        # Log if no files selected
        if not normalized_selections:
            logger.info("No files selected; context will contain only instructions")

        # Optional: Validate that we have something to work with
        if not normalized_selections and not user_instructions:
            raise ValueError(
                "Either file_selections or user_instructions must be provided"
            )

        # Step 2: Create the context generation configuration
        config = FileContextConfig(
            file_selections=normalized_selections,
            project_path=project_path,
            user_instructions=user_instructions,
            include_claude_memory=include_claude_memory,
            include_cursor_rules=include_cursor_rules,
            auto_meta_prompt=auto_meta_prompt,
            temperature=temperature,
        )

        # Step 3: Generate the context content string
        context_result = generate_file_context_data(config)
        context_content = context_result.content

        # Step 4: Send the generated context to Gemini
        gemini_response = send_to_gemini_for_review(
            context_content=context_content,
            project_path=project_path,
            temperature=temperature,
            model=model,
            return_text=text_output,
            thinking_budget=thinking_budget,
        )

        if gemini_response is None:
            raise RuntimeError(
                "Failed to get a response from Gemini. Check API key and logs."
            )

        return gemini_response

    except Exception:
        # Log the full exception for debugging
        logger.error("Error in ask_gemini", exc_info=True)
        # Re-raise the exception for proper error handling
        raise