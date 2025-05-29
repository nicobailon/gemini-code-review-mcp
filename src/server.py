"""
MCP server wrapper for generate_code_review_context.py

Exposes tool:
- generate_code_review_context: Generate review context for current project phase
"""

import os
import sys
import logging
from typing import Any, Dict
import asyncio

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        CallToolRequest,
        CallToolResult,
    )
except ImportError:
    print("MCP library not available. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

from generate_code_review_context import main as generate_review_context

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server instance
server = Server("code-review-context-generator")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    List available tools.
    """
    return [
        Tool(
            name="generate_code_review_context",
            description="Generate code review context based on PRD and current task phase",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Absolute path to project root"
                    },
                    "current_phase": {
                        "type": "string", 
                        "description": "Current phase number (e.g., '2.0'). If not provided, auto-detects from task list"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Custom output file path. If not provided, uses default timestamped path"
                    },
                    "enable_gemini_review": {
                        "type": "boolean",
                        "description": "Enable Gemini AI code review generation (default: true)",
                        "default": True
                    }
                },
                "required": ["project_path"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle tool calls.
    """
    if name != "generate_code_review_context":
        raise ValueError(f"Unknown tool: {name}")
    
    try:
        # Extract arguments
        project_path = arguments.get("project_path")
        current_phase = arguments.get("current_phase")
        output_path = arguments.get("output_path")
        enable_gemini_review = arguments.get("enable_gemini_review", True)
        
        if not project_path:
            raise ValueError("project_path is required")
        
        if not os.path.exists(project_path):
            raise ValueError(f"Project path does not exist: {project_path}")
        
        if not os.path.isabs(project_path):
            raise ValueError("project_path must be an absolute path")
        
        # Generate review context
        logger.info(f"Generating review context for project: {project_path}")
        
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
            logger.error(f"Failed to read generated file: {e}")
            content = f"Generated file at: {output_file} (could not read content)"
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Successfully generated code review context.\n\nOutput file: {output_file}\n\nContent:\n{content}"
                )
            ]
        )
        
    except Exception as e:
        logger.error(f"Error in generate_code_review_context: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error generating code review context: {str(e)}"
                )
            ],
            isError=True
        )


async def async_main():
    """
    Main entry point for the MCP server.
    """
    # Server initialization options
    options = InitializationOptions(
        server_name="code-review-context-generator",
        server_version="0.1.0",
        capabilities={
            "tools": {}
        }
    )
    
    # Run the server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            options
        )


def main():
    """
    Entry point for the MCP server script.
    """
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()