"""Helper functions for meta-prompt generation."""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from ..config_types import CodeReviewConfig
from ..services.context_builder import discover_project_configurations
from ..services.context_generator import format_review_template, generate_review_context_data
from ..services.gemini_api_client import send_to_gemini_for_review
from .model_config_manager import get_meta_prompt_template


async def generate_meta_prompt(
    context_file_path: Optional[str] = None,
    context_content: Optional[str] = None,
    project_path: Optional[str] = None,
    scope: str = "recent_phase",
    custom_template: Optional[str] = None,
    output_path: Optional[str] = None,
    text_output: bool = False,
    thinking_budget: Optional[int] = None,
    url_context: Optional[Union[str, List[str]]] = None,
) -> Union[Dict[str, Any], str]:
    """Generate meta-prompt for AI code review based on completed work analysis.

    Internal helper that analyzes completed development work and project guidelines to create
    tailored meta-prompts that guide AI agents in providing contextually relevant code reviews.

    Template Priority (highest to lowest):
    1. custom_template parameter - Direct template string via function call
    2. META_PROMPT_TEMPLATE env var - Template via environment configuration
    3. Default template - From model_config.json

    MCP Client Environment Configuration Example:
    {
      "mcpServers": {
        "task-list-reviewer": {
          "command": "uvx",
          "args": ["gemini-code-review-mcp"],
          "env": {
            "GEMINI_API_KEY": "your_key_here",
            "META_PROMPT_TEMPLATE": "Your custom template with {configuration_context} and {context} placeholders"
          }
        }
      }
    }

    Args:
        context_file_path: Path to existing context file to analyze
        context_content: Direct context content to analyze
        project_path: Project path to generate context from first
        scope: Scope for context generation when using project_path
        custom_template: Custom meta-prompt template string (overrides environment and default)
        output_path: Optional path to save the meta-prompt as a file
        text_output: If True, return just the prompt text; if False, return full metadata dict
        thinking_budget: Optional token budget for thinking mode (if supported by model)
        url_context: Optional URL(s) to include in context - can be string or list of strings

    Returns:
        If text_output=True: Just the generated meta-prompt text
        If text_output=False and output_path provided: Success message with file path
        If text_output=False and no output_path: Dict containing generated_prompt and metadata

    Raises:
        ValueError: If input validation fails
        FileNotFoundError: If context file doesn't exist
        Exception: If Gemini API fails
    """
    try:
        # Input validation - exactly one parameter should be provided
        provided_params = sum(
            [
                context_file_path is not None,
                context_content is not None,
                project_path is not None,
            ]
        )

        if provided_params == 0:
            raise ValueError("At least one input parameter must be provided")
        elif provided_params > 1:
            raise ValueError("Only one input parameter should be provided")

        # Initialize variables to avoid unbound variable issues
        content = ""
        analyzed_length = 0
        project_for_config = None

        # Get context content based on input type
        if context_content is not None:
            # Direct content provided
            content = context_content.strip()
            if not content:
                raise ValueError("Context content cannot be empty")
            analyzed_length = len(content)
            project_for_config = None  # No project path available for config discovery

        elif context_file_path is not None:
            # Read from file path
            if not os.path.exists(context_file_path):
                raise FileNotFoundError(f"Context file not found: {context_file_path}")

            with open(context_file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                raise ValueError("Context content cannot be empty")
            analyzed_length = len(content)
            project_for_config = os.path.dirname(
                context_file_path
            )  # Use parent directory for config discovery

        elif project_path is not None:
            # Generate context directly in memory without saving to file
            # Create config for context generation
            review_config = CodeReviewConfig(
                project_path=project_path,
                scope=scope,
                enable_gemini_review=False,
                raw_context_only=True,
                include_claude_memory=True,
                include_cursor_rules=False,
            )

            # Generate context data (this gathers all the data but doesn't save anything)
            template_data = generate_review_context_data(review_config)

            # Format the context as markdown (this just formats the data, no file I/O)
            content = format_review_template(template_data).strip()
            analyzed_length = len(content)
            project_for_config = project_path

        # Discover project configuration (CLAUDE.md/cursor rules)
        configuration_context = ""
        if project_for_config:
            try:
                config_data = discover_project_configurations(project_for_config)

                if config_data and (
                    config_data.get("claude_memory_files")
                    or config_data.get("cursor_rules_files")
                ):
                    configuration_context = "\n# PROJECT CONFIGURATION GUIDELINES\n\n"

                    # Add CLAUDE.md content
                    claude_files = config_data.get("claude_memory_files", [])
                    if claude_files:
                        configuration_context += "## CLAUDE.md Guidelines:\n"
                        for claude_file in claude_files:
                            configuration_context += f"### {claude_file.file_path}:\n{claude_file.content}\n\n"

                    # Add cursor rules content
                    cursor_files = config_data.get("cursor_rules_files", [])
                    if cursor_files:
                        configuration_context += "## Cursor Rules:\n"
                        for cursor_file in cursor_files:
                            configuration_context += f"### {cursor_file.file_path}:\n{cursor_file.content}\n\n"

            except Exception as e:
                print(f"Warning: Could not discover project configuration: {e}")
                configuration_context = ""

        # Load meta-prompt template (priority: custom_template > env var > default)
        if custom_template:
            # Use custom template provided by MCP client via parameter
            template = {
                "name": "Custom Meta-Prompt Template",
                "template": custom_template,
            }
            template_used = "custom"
        else:
            # Check for environment variable override
            env_template = os.getenv("META_PROMPT_TEMPLATE")
            if env_template:
                # Use template from environment variable (MCP client config)
                template = {
                    "name": "Environment Meta-Prompt Template",
                    "template": env_template,
                }
                template_used = "environment"
            else:
                # Load the default meta-prompt template
                template = get_meta_prompt_template("default")
                if not template:
                    raise ValueError(
                        "Default meta-prompt template not found in configuration"
                    )
                template_used = "default"

        # Handle large content (truncate if needed to avoid API limits)
        MAX_CONTEXT_SIZE = 80000  # Leave room for template and config content
        if len(content) > MAX_CONTEXT_SIZE:
            content = content[:MAX_CONTEXT_SIZE]
            analyzed_length = MAX_CONTEXT_SIZE

        # Generate meta-prompt using template
        template_content = template["template"]

        # Replace placeholders in template
        meta_prompt = template_content.format(
            context=content, configuration_context=configuration_context
        )

        # Use Gemini API to generate the final meta-prompt
        try:
            # Use enhanced Gemini function to get response text directly
            generated_prompt = send_to_gemini_for_review(
                context_content=meta_prompt,
                temperature=0.3,  # Lower temperature for more consistent meta-prompt generation
                return_text=True,  # Return text directly instead of saving to file
                include_formatting=False,  # Return raw response without headers/footers for auto-prompt
                thinking_budget=thinking_budget,
            )

            if not generated_prompt:
                raise Exception("Gemini API failed to generate response")

        except Exception as e:
            raise Exception(f"Failed to generate meta-prompt: {str(e)}")

        # Handle output options
        if text_output:
            # Return just the prompt text for easy chaining
            return generated_prompt

        # Prepare the full result dictionary
        result = {
            "generated_prompt": generated_prompt,
            "template_used": template_used,
            "configuration_included": len(configuration_context) > 0,
            "analysis_completed": True,
            "context_analyzed": analyzed_length,
        }

        # Save to file if output_path is provided
        if output_path:
            # Create the full file content with metadata
            file_content = f"""# Generated Meta-Prompt for Code Review
*Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*

## Template Information
- **Template Used**: {template_used}
- **Configuration Included**: {'Yes' if len(configuration_context) > 0 else 'No'}
- **Context Analyzed**: {analyzed_length:,} characters
- **Scope**: {scope}

## Generated Prompt

```text
{generated_prompt}
```

## Metadata
- Analysis completed: {result['analysis_completed']}
- Context size: {result['context_analyzed']:,} characters
"""

            # Ensure directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            # Write the file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(file_content)

            # Return success message
            return f"Meta-prompt saved to: {output_path}"

        # Return the full dictionary if no file output requested
        return result

    except Exception:
        # Re-raise with proper error handling for tests
        raise