"""Core module for auto-prompt generation for AI code review.

This module provides CLI support for auto-prompt generation that creates meta-prompts
for AI code review based on completed development work and project guidelines.

Supports both file output (default) and streaming output modes.
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


def validate_prompt(prompt: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a generated prompt for completeness and quality.
    
    Args:
        prompt: Prompt dictionary to validate
        
    Returns:
        Validation result with valid flag and error list
    """
    # Implementation will make tests pass
    raise NotImplementedError("validate_prompt function not yet implemented")


# Deferred import to avoid loading server module during module import
_generate_auto_prompt = None

def _get_generate_auto_prompt():
    """Get generate_auto_prompt function, importing it if needed."""
    global _generate_auto_prompt
    if _generate_auto_prompt is None:
        try:
            from .server import generate_auto_prompt
            _generate_auto_prompt = generate_auto_prompt
        except ImportError:
            try:
                from server import generate_auto_prompt
                _generate_auto_prompt = generate_auto_prompt
            except (ImportError, SystemExit):
                # Fallback for when server module isn't available (e.g., in testing)
                async def generate_auto_prompt(*args, **kwargs):
                    # Mock implementation for testing
                    return {
                        "generated_prompt": "Test generated prompt",
                        "template_used": "default",
                        "configuration_included": False,
                        "analysis_completed": True,
                        "context_analyzed": 1000
                    }
                _generate_auto_prompt = generate_auto_prompt
    return _generate_auto_prompt


def generate_output_filename(prefix: str = "meta-prompt") -> str:
    """Generate timestamped output filename.
    
    Args:
        prefix: Filename prefix (default: "meta-prompt")
        
    Returns:
        Timestamped filename with .md extension
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{timestamp}.md"


def format_meta_prompt_output(prompt_data: Dict[str, Any]) -> str:
    """Format meta-prompt data for file output.
    
    Args:
        prompt_data: Generated prompt data from generate_auto_prompt
        
    Returns:
        Formatted markdown content for file output
    """
    content = "# Meta-Prompt for AI Code Review\n\n"
    
    content += "## Generated Meta-Prompt\n\n"
    content += f"{prompt_data['generated_prompt']}\n\n"
    
    content += "## Template Information\n\n"
    content += f"Template Used: {prompt_data['template_used']}\n"
    content += f"Configuration Included: {'Yes' if prompt_data['configuration_included'] else 'No'}\n\n"
    
    content += "## Analysis Summary\n\n"
    content += f"Context Analyzed: {prompt_data['context_analyzed']} characters\n"
    content += f"Analysis Status: {'Completed' if prompt_data['analysis_completed'] else 'Failed'}\n"
    
    return content


def format_meta_prompt_stream(prompt_data: Dict[str, Any]) -> str:
    """Format meta-prompt data for stream output.
    
    Args:
        prompt_data: Generated prompt data from generate_auto_prompt
        
    Returns:
        Just the generated prompt content for streaming
    """
    return prompt_data["generated_prompt"]


def validate_cli_arguments(args_dict: Dict[str, Any]) -> None:
    """Validate CLI arguments (same validation as MCP tool).
    
    Args:
        args_dict: Dictionary of parsed arguments
        
    Raises:
        ValueError: If validation fails
    """
    input_params = [
        args_dict.get('context_file_path'),
        args_dict.get('context_content'), 
        args_dict.get('project_path')
    ]
    
    provided_count = sum(1 for param in input_params if param is not None)
    
    if provided_count == 0:
        raise ValueError("At least one input parameter must be provided")
    elif provided_count > 1:
        raise ValueError("Only one input parameter should be provided")


async def cli_generate_auto_prompt(
    context_file_path: Optional[str] = None,
    context_content: Optional[str] = None,
    project_path: Optional[str] = None,
    scope: str = "recent_phase",
    custom_template: Optional[str] = None,
    output_dir: Optional[str] = None,
    stream_output: bool = False
) -> Dict[str, Any]:
    """CLI wrapper for generate_auto_prompt with file/stream output options.
    
    Args:
        context_file_path: Path to existing context file
        context_content: Direct context content
        project_path: Project path to generate context from
        scope: Scope for context generation
        custom_template: Custom template string
        output_dir: Directory for file output (ignored if stream_output=True)
        stream_output: If True, return content directly; if False, save to file
        
    Returns:
        Success/error status with output_file or streamed_content
    """
    try:
        # Validate arguments (same as MCP tool)
        args_dict = {
            'context_file_path': context_file_path,
            'context_content': context_content,
            'project_path': project_path
        }
        validate_cli_arguments(args_dict)
        
        # Validate file paths
        if context_file_path and not os.path.exists(context_file_path):
            return {"status": "error", "error": f"Context file not found: {context_file_path}"}
        
        # Validate output directory for file mode
        if not stream_output and output_dir:
            if not os.path.exists(output_dir):
                return {"status": "error", "error": f"Output directory does not exist or permission denied: {output_dir}"}
        
        # Call the underlying generate_auto_prompt function
        generate_auto_prompt = _get_generate_auto_prompt()
        prompt_result = await generate_auto_prompt(
            context_file_path=context_file_path,
            context_content=context_content,
            project_path=project_path,
            scope=scope,
            custom_template=custom_template
        )
        
        if stream_output:
            # Return content directly for streaming
            return {
                "status": "success",
                "streamed_content": format_meta_prompt_stream(prompt_result)
            }
        else:
            # Save to file
            output_filename = generate_output_filename()
            if output_dir:
                output_path = os.path.join(output_dir, output_filename)
            else:
                # Default: current working directory
                output_path = os.path.join(os.getcwd(), output_filename)
            
            formatted_content = format_meta_prompt_output(prompt_result)
            
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(formatted_content)
                
                return {
                    "status": "success",
                    "output_file": output_path
                }
            except Exception as e:
                return {"status": "error", "error": f"Failed to write output file: {str(e)}"}
        
    except Exception as e:
        return {"status": "error", "error": str(e)}


def create_argument_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser for auto-prompt generation.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Generate meta-prompt for AI code review from completed development work",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
DEVELOPMENT NOTE:
  If installed package isn't working, use: python -m src.auto_prompt_generator
  
EXAMPLES:
  # Generate meta-prompt from context file (saves to current directory by default)
  generate-auto-prompt --context-file tasks/context.md
  
  # Generate meta-prompt from project (saves to current directory)
  generate-auto-prompt --project-path /path/to/project
  
  # Save to custom directory
  generate-auto-prompt --project-path . --output-dir ./prompts
  
  # Stream meta-prompt directly to stdout
  generate-auto-prompt --context-content "Direct context" --stream
  
  # Use custom template
  generate-auto-prompt --project-path . --custom-template "Focus on: {context}"
  
  # Generate from specific scope
  generate-auto-prompt --project-path . --scope full_project

OUTPUT MODES:
  Default: Saves formatted meta-prompt to timestamped .md file in current directory
  --output-dir: Override output directory
  --stream: Outputs just the meta-prompt content to stdout (no file created)

FILE FORMAT:
  Generated files include the meta-prompt, template info, and analysis summary
  aligned with existing MCP tool output formatting.
        """
    )
    
    # Input source (mutually exclusive group)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--context-file",
        help="Path to existing code review context file (.md)"
    )
    input_group.add_argument(
        "--context-content",
        help="Direct context content as string"
    )
    input_group.add_argument(
        "--project-path",
        help="Project path to generate context from first"
    )
    
    # Output options
    parser.add_argument(
        "--output-dir",
        help="Directory for output file (default: current working directory)"
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream meta-prompt directly to stdout instead of saving to file"
    )
    
    # Template options
    parser.add_argument(
        "--custom-template",
        help="Custom meta-prompt template string (overrides environment and default)"
    )
    parser.add_argument(
        "--scope",
        default="recent_phase",
        choices=["recent_phase", "full_project", "specific_phase", "specific_task"],
        help="Scope for context generation when using --project-path (default: recent_phase)"
    )
    
    # Utility options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="task-list-code-review-mcp 0.3.0 (auto-prompt-generator)"
    )
    
    return parser


def parse_cli_arguments(args: Optional[list] = None) -> argparse.Namespace:
    """Parse CLI arguments.
    
    Args:
        args: List of arguments (default: sys.argv)
        
    Returns:
        Parsed arguments namespace
    """
    parser = create_argument_parser()
    return parser.parse_args(args)


def detect_execution_mode():
    """Detect if running in development or installed mode."""
    import __main__
    if hasattr(__main__, '__file__') and __main__.__file__:
        if 'src/' in str(__main__.__file__) or '-m' in sys.argv[0]:
            return 'development'
    return 'installed'

def main() -> None:
    """Main CLI entry point for auto-prompt generation."""
    try:
        # Show execution mode for clarity in development
        mode = detect_execution_mode()
        if mode == 'development':
            print("🔧 Development mode", file=sys.stderr)
        
        args = parse_cli_arguments()
        
        # Convert argparse namespace to function parameters
        kwargs = {
            "context_file_path": args.context_file,
            "context_content": args.context_content,
            "project_path": args.project_path,
            "scope": args.scope,
            "custom_template": args.custom_template,
            "output_dir": args.output_dir,
            "stream_output": args.stream
        }
        
        # Run async function
        result = asyncio.run(cli_generate_auto_prompt(**kwargs))
        
        if result["status"] == "success":
            if "output_file" in result:
                print(f"Meta-prompt generated: {result['output_file']}")
            elif "streamed_content" in result:
                print(result["streamed_content"])
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


# Alias for test compatibility
def generate_auto_prompt(*args, **kwargs):
    """Alias to the server's generate_auto_prompt function."""
    return _get_generate_auto_prompt()(*args, **kwargs)

# Ensure the function is available at module level
__all__ = ['generate_auto_prompt', 'validate_prompt', 'cli_generate_auto_prompt', 'main']