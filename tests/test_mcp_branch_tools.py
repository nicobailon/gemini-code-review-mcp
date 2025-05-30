"""
TDD Tests for MCP Server Branch Comparison Tools

Following test-driven development approach - write tests first,
then implement functionality to make tests pass.

DO NOT create mock implementations.
"""

import pytest
import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestBranchComparisonMCPTool:
    """Test MCP tool for branch comparison functionality."""
    
    def test_generate_branch_comparison_review_tool_exists(self):
        """Test that generate_branch_comparison_review MCP tool is available."""
        # Import will fail initially - that's expected in TDD
        try:
            import server
            
            # Tool should be available via FastMCP
            assert hasattr(server, 'generate_branch_comparison_review')
            assert callable(server.generate_branch_comparison_review)
        except SystemExit:
            # FastMCP not available in test environment - that's OK
            # The functionality exists, just can't be tested without FastMCP
            pytest.skip("FastMCP not available in test environment")
    
    def test_generate_branch_comparison_review_has_correct_parameters(self):
        """Test that branch comparison tool has required parameters."""
        try:
            import inspect
            import server
            
            # Check function signature has required parameters
            sig = inspect.signature(server.generate_branch_comparison_review)
            param_names = list(sig.parameters.keys())
            
            assert "project_path" in param_names
            assert "compare_branch" in param_names
            assert "target_branch" in param_names  # Optional but should be available
        except SystemExit:
            pytest.skip("FastMCP not available in test environment")
    
    @pytest.mark.asyncio
    async def test_generate_branch_comparison_review_success(self):
        """Test successful branch comparison review generation."""
        from server import generate_branch_comparison_review
        
        # Mock the underlying functionality
        with patch('server.main') as mock_main:
            mock_main.return_value = (
                "/test/path/code-review-branch-comparison-20241201-120000.md",
                "/test/path/code-review-comprehensive-feedback-20241201-120000.md"
            )
            
            result = await generate_branch_comparison_review(
                project_path="/test/project",
                compare_branch="feature/auth",
                target_branch="main"
            )
            
            # Should return success with file paths
            assert result["status"] == "success"
            assert "context_file" in result
            assert "ai_review_file" in result
            assert "branch_comparison_summary" in result
            
            # Verify main was called with correct parameters
            mock_main.assert_called_once()
            call_args = mock_main.call_args
            assert call_args[1]["compare_branch"] == "feature/auth"
            assert call_args[1]["target_branch"] == "main"
            assert call_args[1]["project_path"] == "/test/project"
    
    @pytest.mark.asyncio
    async def test_generate_branch_comparison_review_auto_detect_target(self):
        """Test branch comparison with auto-detected target branch."""
        from server import generate_branch_comparison_review
        
        with patch('server.main') as mock_main:
            mock_main.return_value = (
                "/test/path/code-review-branch-comparison-20241201-120000.md", 
                None  # No AI review
            )
            
            result = await generate_branch_comparison_review(
                project_path="/test/project",
                compare_branch="feature/payment"
                # target_branch not provided - should auto-detect
            )
            
            assert result["status"] == "success"
            # Verify target_branch was not explicitly set (will be auto-detected)
            call_args = mock_main.call_args[1]
            assert "target_branch" not in call_args or call_args["target_branch"] is None
    
    @pytest.mark.asyncio
    async def test_generate_branch_comparison_review_handles_errors(self):
        """Test error handling in branch comparison MCP tool."""
        from server import generate_branch_comparison_review
        
        with patch('server.main') as mock_main:
            mock_main.side_effect = ValueError("Branch 'nonexistent' does not exist")
            
            result = await generate_branch_comparison_review(
                project_path="/test/project",
                compare_branch="nonexistent"
            )
            
            assert result["status"] == "error"
            assert "error" in result
            assert "Branch 'nonexistent' does not exist" in result["error"]
    
    @pytest.mark.asyncio
    async def test_generate_branch_comparison_review_parameter_validation(self):
        """Test parameter validation for branch comparison tool."""
        from server import generate_branch_comparison_review
        
        # Test missing project_path
        result = await generate_branch_comparison_review(
            compare_branch="feature/test"
            # project_path missing
        )
        
        assert result["status"] == "error"
        assert "project_path is required" in result["error"]
        
        # Test missing compare_branch
        result = await generate_branch_comparison_review(
            project_path="/test/project"
            # compare_branch missing
        )
        
        assert result["status"] == "error"
        assert "compare_branch is required" in result["error"]


class TestGitHubPRMCPTool:
    """Test MCP tool for GitHub PR review functionality."""
    
    def test_generate_pr_review_tool_exists(self):
        """Test that generate_pr_review MCP tool is available."""
        try:
            import server
            
            # Tool should be available via FastMCP
            assert hasattr(server, 'generate_pr_review')
            assert callable(server.generate_pr_review)
        except SystemExit:
            pytest.skip("FastMCP not available in test environment")
    
    def test_generate_pr_review_has_correct_parameters(self):
        """Test that PR review tool has required parameters."""
        try:
            import inspect
            import server
            
            # Check function signature has required parameters  
            sig = inspect.signature(server.generate_pr_review)
            param_names = list(sig.parameters.keys())
            
            assert "github_pr_url" in param_names
            assert "project_path" in param_names  # Optional for context
        except SystemExit:
            pytest.skip("FastMCP not available in test environment")
    
    @pytest.mark.asyncio
    async def test_generate_pr_review_success(self):
        """Test successful GitHub PR review generation."""
        from server import generate_pr_review
        
        with patch('server.main') as mock_main:
            mock_main.return_value = (
                "/test/path/code-review-github-pr-20241201-120000.md",
                "/test/path/code-review-comprehensive-feedback-20241201-120000.md"
            )
            
            result = await generate_pr_review(
                github_pr_url="https://github.com/microsoft/vscode/pull/123",
                project_path="/test/project"
            )
            
            assert result["status"] == "success"
            assert "context_file" in result
            assert "ai_review_file" in result
            assert "pr_summary" in result
            
            # Verify main was called with correct parameters
            mock_main.assert_called_once()
            call_args = mock_main.call_args[1]
            assert call_args["github_pr_url"] == "https://github.com/microsoft/vscode/pull/123"
            assert call_args["project_path"] == "/test/project"
    
    @pytest.mark.asyncio
    async def test_generate_pr_review_without_project_path(self):
        """Test PR review without local project path."""
        from server import generate_pr_review
        
        with patch('server.main') as mock_main:
            mock_main.return_value = (
                "/tmp/code-review-github-pr-20241201-120000.md",
                "/tmp/code-review-comprehensive-feedback-20241201-120000.md"
            )
            
            result = await generate_pr_review(
                github_pr_url="https://github.com/facebook/react/pull/456"
                # project_path not provided
            )
            
            assert result["status"] == "success"
            # Should use temporary directory or current working directory
            call_args = mock_main.call_args[1]
            assert "github_pr_url" in call_args
    
    @pytest.mark.asyncio
    async def test_generate_pr_review_handles_invalid_url(self):
        """Test error handling for invalid GitHub PR URLs."""
        from server import generate_pr_review
        
        with patch('server.main') as mock_main:
            mock_main.side_effect = ValueError("Invalid GitHub PR URL: Must be a GitHub domain")
            
            result = await generate_pr_review(
                github_pr_url="https://gitlab.com/group/project/merge_requests/123"
            )
            
            assert result["status"] == "error"
            assert "error" in result
            assert "Invalid GitHub PR URL" in result["error"]
    
    @pytest.mark.asyncio
    async def test_generate_pr_review_handles_github_api_errors(self):
        """Test handling of GitHub API errors."""
        from server import generate_pr_review
        
        with patch('server.main') as mock_main:
            mock_main.side_effect = ValueError("PR not found: owner/repo/pull/999")
            
            result = await generate_pr_review(
                github_pr_url="https://github.com/owner/repo/pull/999"
            )
            
            assert result["status"] == "error"
            assert "PR not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_generate_pr_review_parameter_validation(self):
        """Test parameter validation for PR review tool."""
        from server import generate_pr_review
        
        # Test missing github_pr_url
        result = await generate_pr_review()
        
        assert result["status"] == "error"
        assert "github_pr_url is required" in result["error"]


class TestMCPToolConsistency:
    """Test consistency between MCP tools and existing patterns."""
    
    def test_mcp_tools_have_consistent_response_format(self):
        """Test that all MCP tools return consistent response format."""
        try:
            import server
            
            # Check that both new tools exist
            assert hasattr(server, 'generate_branch_comparison_review')
            assert hasattr(server, 'generate_pr_review')
            
            # Check that existing tools still exist (backward compatibility)
            assert hasattr(server, 'generate_code_review_context')
            assert hasattr(server, 'generate_ai_code_review')
        except SystemExit:
            pytest.skip("FastMCP not available in test environment")
    
    @pytest.mark.asyncio
    async def test_mcp_tools_provide_user_feedback(self):
        """Test that MCP tools provide appropriate user feedback."""
        from server import generate_branch_comparison_review, generate_pr_review
        
        # Test branch comparison feedback
        with patch('server.main') as mock_main:
            mock_main.return_value = ("/test/context.md", "/test/review.md")
            
            result = await generate_branch_comparison_review(
                project_path="/test",
                compare_branch="feature/test"
            )
            
            # Should include helpful information for the user
            assert "context_file" in result
            assert "ai_review_file" in result or result["ai_review_file"] is None
            
        # Test PR review feedback
        with patch('server.main') as mock_main:
            mock_main.return_value = ("/test/context.md", "/test/review.md")
            
            result = await generate_pr_review(
                github_pr_url="https://github.com/test/repo/pull/1"
            )
            
            assert "context_file" in result
            assert "pr_summary" in result
    
    def test_mcp_tool_documentation_is_comprehensive(self):
        """Test that MCP tools have comprehensive documentation."""
        try:
            import server
            
            # Check branch comparison tool documentation
            branch_func = server.generate_branch_comparison_review
            assert branch_func.__doc__ is not None
            assert "branch" in branch_func.__doc__.lower()
            assert "comparison" in branch_func.__doc__.lower()
            
            # Check PR review tool documentation
            pr_func = server.generate_pr_review
            assert pr_func.__doc__ is not None
            assert "github" in pr_func.__doc__.lower() or "pull request" in pr_func.__doc__.lower()
        except SystemExit:
            pytest.skip("FastMCP not available in test environment")


class TestMCPToolIntegration:
    """Test integration between MCP tools and existing functionality."""
    
    @pytest.mark.asyncio
    async def test_mcp_tools_use_existing_infrastructure(self):
        """Test that MCP tools properly use existing code infrastructure."""
        from server import generate_branch_comparison_review
        
        # Mock the existing main function to verify it's being used
        with patch('server.main') as mock_main:
            with patch('generate_code_review_context.main') as mock_generate_main:
                mock_main.return_value = ("/test/context.md", "/test/review.md")
                
                await generate_branch_comparison_review(
                    project_path="/test",
                    compare_branch="feature/test"
                )
                
                # Should use the existing main function, not duplicate logic
                mock_main.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mcp_tools_handle_temperature_parameter(self):
        """Test that MCP tools can handle optional temperature parameter."""
        from server import generate_branch_comparison_review, generate_pr_review
        
        with patch('server.main') as mock_main:
            mock_main.return_value = ("/test/context.md", "/test/review.md")
            
            # Test with temperature parameter
            await generate_branch_comparison_review(
                project_path="/test",
                compare_branch="feature/test",
                temperature=0.3
            )
            
            call_args = mock_main.call_args[1]
            assert call_args.get("temperature") == 0.3
    
    def test_fastmcp_tool_registration_format(self):
        """Test that tools are properly available via FastMCP."""
        try:
            import server
            
            # Verify that the app is a FastMCP instance
            assert hasattr(server, 'app')
            assert hasattr(server.app, 'run')
            
            # Check that new tools are available as functions
            expected_new_tools = [
                "generate_branch_comparison_review",
                "generate_pr_review"
            ]
            
            for tool_name in expected_new_tools:
                assert hasattr(server, tool_name), f"Tool {tool_name} should be available"
                assert callable(getattr(server, tool_name)), f"Tool {tool_name} should be callable"
        except SystemExit:
            pytest.skip("FastMCP not available in test environment")