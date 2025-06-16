"""MCP server for AI-powered code review tools."""

import logging
from typing import Any, Dict, List, Optional, Union

# MCP wrapper and type safety
from .mcp_wrapper import create_mcp_server

# Configure logging
logger = logging.getLogger(__name__)

# Import tool implementations
from .tools import ask_gemini as ask_gemini_impl
from .tools import generate_ai_code_review as generate_ai_code_review_impl
from .tools import generate_pr_review as generate_pr_review_impl

# Import enhanced implementations for multi-phase support
try:
    from .tools.pr_review_enhanced import generate_pr_review as generate_pr_review_enhanced
    from .tools.ai_code_review_enhanced import generate_ai_code_review as generate_ai_code_review_enhanced
    from .tools.multiphase_review import generate_multiphase_review as generate_multiphase_review_impl
    _enhanced_tools_available = True
    logger.info("Enhanced tools loaded successfully")
except ImportError as e:
    _enhanced_tools_available = False
    generate_pr_review_enhanced = None
    generate_ai_code_review_enhanced = None
    generate_multiphase_review_impl = None
    logger.warning(f"Enhanced tools not available: {e}")

# Create FastMCP server with type-safe wrapper
mcp = create_mcp_server("MCP Server - Code Review Context Generator")

# Create alias for the app to match test expectations
app = mcp


# ========== MCP Tool Registrations ==========

@mcp.tool()
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
    context_strategy: str = "balanced",
    max_context_tokens: Optional[int] = None,
    per_file_token_limit: int = 10_000,
    review_mode: str = "multi-phase",
    save_intermediate_files: bool = False,
) -> str:
    """Generate code review for a GitHub Pull Request with automatic multi-phase support.

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
        context_strategy: Context size strategy - 'focused', 'balanced', 'comprehensive' (default: balanced)
        max_context_tokens: Override maximum context tokens (overrides strategy)
        per_file_token_limit: Maximum tokens per file (default: 10,000)
        review_mode: Review mode - 'single', 'multi-phase', 'overview-only' (default: multi-phase)
        save_intermediate_files: Save intermediate context and review files for each phase (default: false)

    Returns:
        Default: Saves review to pr-review-feedback-[timestamp].md file and returns success message
        If text_output=True: Returns AI review content directly as text (no file created)
        If raw_context_only=True: Context content or success message with context file path
        
    Multi-Phase Behavior:
        - Automatically detects when PR exceeds token limits and splits into phases
        - Use save_intermediate_files=True to save each phase's context and review as separate .md files
        - Phase files are named: code-review-context-{mode}-phase-{N}-of-{total}-{timestamp}.md
        - A summary file is always generated: code-review-multi-phase-summary-{timestamp}.md
    """
    # Use enhanced version if available and not explicitly single mode
    if _enhanced_tools_available and review_mode != "single" and generate_pr_review_enhanced is not None:
        return await generate_pr_review_enhanced(
            github_pr_url=github_pr_url,
            project_path=project_path,
            temperature=temperature,
            enable_gemini_review=enable_gemini_review,
            include_claude_memory=include_claude_memory,
            include_cursor_rules=include_cursor_rules,
            auto_meta_prompt=auto_meta_prompt,
            use_templated_instructions=use_templated_instructions,
            create_context_file=create_context_file,
            raw_context_only=raw_context_only,
            text_output=text_output,
            thinking_budget=thinking_budget,
            url_context=url_context,
            context_strategy=context_strategy,
            max_context_tokens=max_context_tokens,
            per_file_token_limit=per_file_token_limit,
            review_mode=review_mode,
            save_intermediate_files=save_intermediate_files,
        )
    
    # Fallback to standard implementation
    return await generate_pr_review_impl(
        github_pr_url=github_pr_url,
        project_path=project_path,
        temperature=temperature,
        enable_gemini_review=enable_gemini_review,
        include_claude_memory=include_claude_memory,
        include_cursor_rules=include_cursor_rules,
        auto_meta_prompt=auto_meta_prompt,
        use_templated_instructions=use_templated_instructions,
        create_context_file=create_context_file,
        raw_context_only=raw_context_only,
        text_output=text_output,
        thinking_budget=thinking_budget,
        url_context=url_context,
    )


@mcp.tool()
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
    context_strategy: str = "balanced",
    max_context_tokens: Optional[int] = None,
    per_file_token_limit: int = 10_000,
    review_mode: str = "multi-phase",
    save_intermediate_files: bool = False,
) -> str:
    """Generate AI-powered code review with automatic multi-phase support.

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
        context_strategy: Context size strategy - 'focused', 'balanced', 'comprehensive' (default: balanced)
        max_context_tokens: Override maximum context tokens (overrides strategy)
        per_file_token_limit: Maximum tokens per file (default: 10,000)
        review_mode: Review mode - 'single', 'multi-phase', 'overview-only' (default: multi-phase)
        save_intermediate_files: Save intermediate context and review files for each phase (default: false)

    Returns:
        Default (text_output=True): Generated AI review content as text string for AI agent chaining
        If text_output=False: Saves to code-review-ai-feedback-[timestamp].md and returns success message
        
    Multi-Phase Behavior:
        - Automatically detects when changes exceed token limits (~60K for gemini-2.0-flash)
        - Intelligently groups files by priority (critical changes, supporting changes, documentation)
        - Use save_intermediate_files=True to save each phase's context and review as separate .md files
        - Phase files include complete change manifest for cross-reference
        - Summary file provides consolidated findings across all phases
    """
    # Use enhanced version if available and not explicitly single mode
    if _enhanced_tools_available and review_mode != "single" and generate_ai_code_review_enhanced is not None:
        return await generate_ai_code_review_enhanced(
            context_file_path=context_file_path,
            context_content=context_content,
            project_path=project_path,
            scope=scope,
            phase_number=phase_number,
            task_number=task_number,
            task_list=task_list,
            default_prompt=default_prompt,
            output_path=output_path,
            model=model,
            temperature=temperature,
            custom_prompt=custom_prompt,
            text_output=text_output,
            auto_meta_prompt=auto_meta_prompt,
            include_claude_memory=include_claude_memory,
            include_cursor_rules=include_cursor_rules,
            thinking_budget=thinking_budget,
            url_context=url_context,
            context_strategy=context_strategy,
            max_context_tokens=max_context_tokens,
            per_file_token_limit=per_file_token_limit,
            review_mode=review_mode,
            save_intermediate_files=save_intermediate_files,
        )
    
    # Fallback to standard implementation
    return await generate_ai_code_review_impl(
        context_file_path=context_file_path,
        context_content=context_content,
        project_path=project_path,
        scope=scope,
        phase_number=phase_number,
        task_number=task_number,
        task_list=task_list,
        default_prompt=default_prompt,
        output_path=output_path,
        model=model,
        temperature=temperature,
        custom_prompt=custom_prompt,
        text_output=text_output,
        auto_meta_prompt=auto_meta_prompt,
        include_claude_memory=include_claude_memory,
        include_cursor_rules=include_cursor_rules,
        thinking_budget=thinking_budget,
        url_context=url_context,
    )


@mcp.tool()
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
    return await ask_gemini_impl(
        user_instructions=user_instructions,
        file_selections=file_selections,
        project_path=project_path,
        include_claude_memory=include_claude_memory,
        include_cursor_rules=include_cursor_rules,
        auto_meta_prompt=auto_meta_prompt,
        temperature=temperature,
        model=model,
        thinking_budget=thinking_budget,
        text_output=text_output,
    )


@mcp.tool()
async def generate_multiphase_review(
    project_path: Optional[str] = None,
    github_pr_url: Optional[str] = None,
    scope: str = "full_project",
    phase_number: Optional[str] = None,
    task_number: Optional[str] = None,
    task_list: Optional[str] = None,
    default_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.5,
    auto_meta_prompt: bool = True,
    include_claude_memory: bool = True,
    include_cursor_rules: bool = False,
    thinking_budget: Optional[int] = None,
    url_context: Optional[Union[str, List[str]]] = None,
    context_strategy: str = "balanced",
    max_context_tokens: Optional[int] = None,
    per_file_token_limit: int = 10_000,
    output_format: str = "structured",
    phases_to_process: Optional[List[int]] = None,
) -> Union[str, Dict[str, Union[str, List[Dict[str, str]]]]]:
    """
    Generate multi-phase code review with explicit control over phases.
    
    This dedicated tool provides better control over multi-phase reviews,
    allowing users to:
    - Get structured output with phase metadata
    - Process specific phases only
    - Access individual phase results programmatically
    
    Args:
        project_path: Project path for analysis
        github_pr_url: GitHub PR URL for PR-based reviews
        scope: Review scope - 'recent_phase', 'full_project', 'specific_phase', 'specific_task'
        phase_number: Phase number for specific_phase scope
        task_number: Task number for specific_task scope
        task_list: Specific task list file to use
        default_prompt: Custom default prompt when no task list exists
        model: Optional Gemini model name
        temperature: Temperature for AI model (0.0-2.0)
        auto_meta_prompt: Automatically generate meta prompt
        include_claude_memory: Include CLAUDE.md files
        include_cursor_rules: Include Cursor rules files
        thinking_budget: Optional token budget for thinking mode
        url_context: Optional URL(s) to include in context
        context_strategy: 'focused', 'balanced', 'comprehensive'
        max_context_tokens: Override maximum context tokens
        per_file_token_limit: Maximum tokens per file
        output_format: 'structured' (dict) or 'markdown' (string)
        phases_to_process: List of phase numbers to process (e.g., [1, 3])
        
    Returns:
        If output_format='structured':
            Dict with keys:
            - summary: Multi-phase summary info
            - phases: List of phase results with metadata
            - manifest: Phase manifest markdown
            - metadata: Review metadata
            
        If output_format='markdown':
            Formatted markdown string with all phases
    """
    if not _enhanced_tools_available or generate_multiphase_review_impl is None:
        return {"error": "Multi-phase review tool not available. Enhanced tools failed to load."}
    
    return await generate_multiphase_review_impl(
        project_path=project_path,
        github_pr_url=github_pr_url,
        scope=scope,
        phase_number=phase_number,
        task_number=task_number,
        task_list=task_list,
        default_prompt=default_prompt,
        model=model,
        temperature=temperature,
        auto_meta_prompt=auto_meta_prompt,
        include_claude_memory=include_claude_memory,
        include_cursor_rules=include_cursor_rules,
        thinking_budget=thinking_budget,
        url_context=url_context,
        context_strategy=context_strategy,
        max_context_tokens=max_context_tokens,
        per_file_token_limit=per_file_token_limit,
        output_format=output_format,
        phases_to_process=phases_to_process,
    )


# ========== Helper Functions ==========

def get_mcp_tools():
    """Get list of available MCP tools for testing.

    Note: Keep this list in sync with tools decorated with @mcp.tool().
    Consider adding a test to verify registry consistency.
    """
    return [
        "generate_ai_code_review",
        "generate_pr_review",
        "ask_gemini",
        "generate_multiphase_review",
    ]


def main():
    """Entry point for uvx execution"""
    # Configure logging for MCP context
    from .helpers.logging_config import setup_mcp_logging
    
    setup_mcp_logging()
    
    # FastMCP handles all the server setup, protocol, and routing
    # Default transport is stdio (best for local tools and command-line scripts)
    mcp.run()


if __name__ == "__main__":
    main()