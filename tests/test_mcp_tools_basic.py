"""
Basic tests for MCP tools to verify thinking_budget and url_context parameters.
"""

import os
import sys
import tempfile
from typing import Any, Dict, List, Protocol, cast
from unittest.mock import patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# Protocol to define the expected interface of the FastMCP instance for type checking
class FastMCPWithTools(Protocol):
    async def get_tools(self) -> Dict[str, Any]: ...


class ToolManager(Protocol):
    tools: Dict[str, Any]


class FastMCPWithToolManager(Protocol):
    _tool_manager: ToolManager


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini API client."""
    with patch("src.gemini_api_client.send_to_gemini_for_review") as mock:
        mock.return_value = "Mock AI review content"
        yield mock


@pytest.fixture
def mock_github_pr():
    """Mock GitHub PR integration."""
    with patch("src.github_pr_integration.get_complete_pr_analysis") as mock:
        mock.return_value = {
            "pr_data": {
                "title": "Test PR",
                "author": "testuser",
                "source_branch": "feature",
                "target_branch": "main",
                "state": "open",
                "body": "Test PR description",
            },
            "file_changes": {
                "summary": {
                    "files_changed": 2,
                    "total_additions": 10,
                    "total_deletions": 5,
                },
                "changed_files": [],
            },
        }
        yield mock


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestMCPToolsBasic:
    """Test MCP tools accept new parameters."""

    def test_thinking_budget_parameter_accepted(self):
        """Test that thinking_budget parameter is accepted by tools."""
        import inspect

        from src.server import (
            generate_ai_code_review,
            generate_code_review_context,
            generate_meta_prompt,
            generate_pr_review,
        )

        # Get the actual functions from FunctionTool objects
        pr_review_func = generate_pr_review.func if hasattr(generate_pr_review, 'func') else generate_pr_review
        ai_review_func = generate_ai_code_review.func if hasattr(generate_ai_code_review, 'func') else generate_ai_code_review
        context_func = generate_code_review_context.func if hasattr(generate_code_review_context, 'func') else generate_code_review_context

        # Check generate_pr_review has thinking_budget parameter
        sig = inspect.signature(pr_review_func)
        assert "thinking_budget" in sig.parameters

        # Check generate_ai_code_review has thinking_budget parameter
        sig = inspect.signature(ai_review_func)
        assert "thinking_budget" in sig.parameters

        # Check generate_code_review_context has thinking_budget parameter
        sig = inspect.signature(context_func)
        assert "thinking_budget" in sig.parameters

        # Check generate_meta_prompt has thinking_budget parameter
        sig = inspect.signature(generate_meta_prompt)
        assert "thinking_budget" in sig.parameters

    def test_url_context_parameter_accepted(self):
        """Test that url_context parameter is accepted by tools."""
        import inspect

        from src.server import (
            generate_ai_code_review,
            generate_code_review_context,
            generate_file_context,
            generate_meta_prompt,
            generate_pr_review,
        )

        # Get the actual functions from FunctionTool objects
        pr_review_func = generate_pr_review.func if hasattr(generate_pr_review, 'func') else generate_pr_review
        ai_review_func = generate_ai_code_review.func if hasattr(generate_ai_code_review, 'func') else generate_ai_code_review
        context_func = generate_code_review_context.func if hasattr(generate_code_review_context, 'func') else generate_code_review_context

        # Check generate_pr_review has url_context parameter
        sig = inspect.signature(pr_review_func)
        assert "url_context" in sig.parameters

        # Check generate_ai_code_review has url_context parameter
        sig = inspect.signature(ai_review_func)
        assert "url_context" in sig.parameters

        # Check generate_code_review_context has url_context parameter
        sig = inspect.signature(context_func)
        sig = inspect.signature(generate_code_review_context)
        assert "url_context" in sig.parameters

        # Check generate_meta_prompt has url_context parameter
        sig = inspect.signature(generate_meta_prompt)
        assert "url_context" in sig.parameters

        # Check generate_file_context has url_context parameter
        sig = inspect.signature(generate_file_context)
        assert "url_context" in sig.parameters

    def test_backward_compatibility_parameters(self):
        """Test that new parameters have defaults (backward compatibility)."""
        import inspect

        from src.server import generate_ai_code_review

        # Get the actual function from FunctionTool object
        ai_review_func = generate_ai_code_review.func if hasattr(generate_ai_code_review, 'func') else generate_ai_code_review
        
        sig = inspect.signature(ai_review_func)

        # Check thinking_budget has default None
        assert sig.parameters["thinking_budget"].default is None

        # Check url_context has default None
        assert sig.parameters["url_context"].default is None

    def test_correct_mcp_tools_are_exposed(self):
        """Test that correct MCP tools are exposed."""
        from src.server import get_mcp_tools

        tools = get_mcp_tools()
        # still exposed
        assert "generate_ai_code_review" in tools
        assert "generate_pr_review" in tools
        assert "ask_gemini" in tools
        # no longer exposed
        assert "generate_file_context" not in tools
        assert "generate_code_review_context" not in tools
        assert "generate_meta_prompt" not in tools

    @pytest.mark.asyncio
    async def test_mcp_tools_list_matches_registry(self):
        """Test that get_mcp_tools() matches the actual MCP registry."""
        from src.server import get_mcp_tools, mcp

        # Get the list from get_mcp_tools()
        reported_tools = get_mcp_tools()

        # Get the actual registered tools from the MCP instance
        # The mcp object is a TypedMCPServer wrapper, so we access the underlying FastMCP instance.
        # We use getattr and cast to satisfy the linter when accessing the untyped library.
        actual_tools: List[str] = []

        if hasattr(mcp, "_server"):
            # Access the wrapped FastMCP instance using getattr to avoid private access error
            fastmcp_instance = getattr(mcp, "_server")

            if hasattr(fastmcp_instance, "get_tools"):
                # get_tools() is async in FastMCP and returns a dict
                # Cast to our protocol to inform the type checker of the method
                typed_instance = cast(FastMCPWithTools, fastmcp_instance)
                tools_dict = await typed_instance.get_tools()
                actual_tools = list(tools_dict.keys())
            elif hasattr(fastmcp_instance, "_tool_manager"):
                # Fallback: try accessing through _tool_manager
                typed_instance_with_mgr = cast(FastMCPWithToolManager, fastmcp_instance)
                if hasattr(typed_instance_with_mgr, "_tool_manager"):
                    tool_manager = getattr(typed_instance_with_mgr, "_tool_manager")
                    if hasattr(tool_manager, "tools"):
                        actual_tools = list(tool_manager.tools.keys())

        # Sort both lists for comparison
        reported_tools_sorted = sorted(reported_tools)
        actual_tools_sorted = sorted(actual_tools)

        # They should match exactly
        assert reported_tools_sorted == actual_tools_sorted, (
            f"Mismatch between get_mcp_tools() and actual registry.\n"
            f"Reported: {reported_tools_sorted}\n"
            f"Actual:   {actual_tools_sorted}"
        )
