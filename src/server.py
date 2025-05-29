"""
FastMCP server for generating code review context from PRDs and git changes
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from fastmcp import FastMCP
    from generate_code_review_context import main as generate_review_context
except ImportError as e:
    print(f"Required dependencies not available: {e}", file=sys.stderr)
    sys.exit(1)

# Create FastMCP server with ERROR log level to avoid info noise
mcp = FastMCP("MCP Server - Code Review Context Generator", log_level="ERROR")


@mcp.tool()
def generate_code_review_context(
    project_path: str,
    current_phase: Optional[str] = None,
    output_path: Optional[str] = None,
    enable_gemini_review: bool = True
) -> str:
    """Generate code review context based on PRD and current task phase.
    
    Args:
        project_path: Absolute path to project root directory
        current_phase: Current phase number (e.g., '2.0'). If not provided, auto-detects from task list
        output_path: Custom output file path. If not provided, uses default timestamped path
        enable_gemini_review: Enable Gemini AI code review generation (default: true)
    
    Returns:
        Success message with generated content and output file path
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
        
        # Generate review context using existing logic
        try:
            output_file = generate_review_context(
                project_path=project_path,
                phase=current_phase,
                output=output_path,
                enable_gemini_review=enable_gemini_review
            )
            
            # Read the generated content to return
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                content = f"Generated file at: {output_file} (could not read content: {e})"
            
            return f"Successfully generated code review context.\n\nOutput file: {output_file}\n\nContent:\n{content[:2000]}{'...' if len(content) > 2000 else ''}"
            
        except Exception as e:
            return f"ERROR: Error generating code review context: {str(e)}"
            
    except Exception as e:
        # Catch-all to ensure no exceptions escape the tool function
        return f"ERROR: Unexpected error: {str(e)}"


def main():
    """Entry point for uvx execution"""
    # FastMCP handles all the server setup, protocol, and routing
    # Use stdio transport explicitly (more reliable than SSE/streamable-http)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()