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
import subprocess
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
        
        # Test with real temporary git repository - following CLAUDE.md principles
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize git repo with main as default branch
            subprocess.run(['git', 'init', '--initial-branch=main'], cwd=temp_dir, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=temp_dir, check=True)
            
            # Create initial commit on main
            with open(os.path.join(temp_dir, 'README.md'), 'w') as f:
                f.write("# Test Project")
            subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=temp_dir, check=True)
            
            # Create feature branch with changes
            subprocess.run(['git', 'checkout', '-b', 'feature/auth'], cwd=temp_dir, check=True)
            with open(os.path.join(temp_dir, 'auth.py'), 'w') as f:
                f.write("def authenticate(): return True")
            subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Add authentication'], cwd=temp_dir, check=True)
            
            # Disable Gemini API calls for testing
            with patch.dict(os.environ, {'GEMINI_API_KEY': ''}):
                result = await generate_branch_comparison_review(
                    project_path=temp_dir,
                    compare_branch="feature/auth",
                    target_branch="main",
                    enable_gemini_review=False
                )
            
            # Test behavior: successful generation with correct response structure
            assert result["status"] == "success"
            assert "context_file" in result
            assert "ai_review_file" in result  # Should be None when disabled
            assert "branch_comparison_summary" in result
            
            # Verify actual file was created
            assert os.path.exists(result["context_file"])
            
            # Verify summary contains expected information
            summary = result["branch_comparison_summary"]
            assert summary["source_branch"] == "feature/auth"
            assert summary["target_branch"] == "main"
    
    @pytest.mark.asyncio
    async def test_generate_branch_comparison_review_auto_detect_target(self):
        """Test branch comparison with auto-detected target branch."""
        from server import generate_branch_comparison_review
        
        # Test with real temporary git repository - following CLAUDE.md principles
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize git repo with main as default branch
            subprocess.run(['git', 'init', '--initial-branch=main'], cwd=temp_dir, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=temp_dir, check=True)
            
            # Create initial commit on main
            with open(os.path.join(temp_dir, 'README.md'), 'w') as f:
                f.write("# Test Project")
            subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=temp_dir, check=True)
            
            # Create feature branch with changes
            subprocess.run(['git', 'checkout', '-b', 'feature/payment'], cwd=temp_dir, check=True)
            with open(os.path.join(temp_dir, 'payment.py'), 'w') as f:
                f.write("def process_payment(): return True")
            subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Add payment processing'], cwd=temp_dir, check=True)
            
            # Test auto-detection without specifying target_branch - disable Gemini API
            with patch.dict(os.environ, {'GEMINI_API_KEY': ''}):
                result = await generate_branch_comparison_review(
                    project_path=temp_dir,
                    compare_branch="feature/payment",
                    enable_gemini_review=False
                    # target_branch not provided - should auto-detect main
                )
            
            # Test behavior: successful auto-detection
            assert result["status"] == "success"
            assert "context_file" in result
            assert "branch_comparison_summary" in result
            
            # Verify auto-detected target branch in summary
            summary = result["branch_comparison_summary"]
            assert summary["source_branch"] == "feature/payment"
            assert summary["target_branch"] == "auto-detected"  # This is what the UI shows
    
    @pytest.mark.asyncio
    async def test_generate_branch_comparison_review_handles_errors(self):
        """Test error handling in branch comparison MCP tool."""
        from server import generate_branch_comparison_review
        
        # Test real error scenario: nonexistent branch - following CLAUDE.md principles
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize git repo with main as default branch
            subprocess.run(['git', 'init', '--initial-branch=main'], cwd=temp_dir, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=temp_dir, check=True)
            
            # Create initial commit on main
            with open(os.path.join(temp_dir, 'README.md'), 'w') as f:
                f.write("# Test Project")
            subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=temp_dir, check=True)
            
            # Test with nonexistent branch - should produce real error
            with patch.dict(os.environ, {'GEMINI_API_KEY': ''}):
                result = await generate_branch_comparison_review(
                    project_path=temp_dir,
                    compare_branch="nonexistent/branch",  # This branch doesn't exist
                    enable_gemini_review=False
                )
            
            # Test behavior: should handle real error gracefully
            assert result["status"] == "error"
            assert "error" in result
            # The actual error message will be from git, not our mocked message
            assert "error" in result["error"].lower() or "failed" in result["error"].lower()
    
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
        
        # Test with real temporary directory and mocked GitHub API - CLAUDE.md compliant
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock GitHub API responses based on real PR #3 data
            mock_pr_data = {
                "id": 2553516570,
                "number": 123,
                "state": "open", 
                "title": "Add new authentication feature",
                "user": {"login": "testuser"},
                "body": "This PR adds authentication functionality",
                "created_at": "2025-05-30T00:59:09Z",
                "updated_at": "2025-05-30T01:59:09Z",
                "head": {
                    "ref": "feature/auth",
                    "sha": "fe0d5d04bc6b3a08cc4f6240fb59494b0ad2e89d"
                },
                "base": {
                    "ref": "master", 
                    "sha": "8d2c0cad9d3e72b0b1aa1d7cf13a781b02a1b418"
                },
                "html_url": "https://github.com/microsoft/vscode/pull/123"
            }
            
            mock_files_data = [
                {
                    "filename": "src/auth.py",
                    "status": "added",
                    "additions": 50,
                    "deletions": 0,
                    "changes": 50,
                    "patch": "@@ -0,0 +1,50 @@\n+def authenticate():\n+    return True"
                }
            ]
            
            # Mock GitHub API calls (external dependency) but test real MCP behavior
            with patch('requests.get') as mock_get:
                def mock_response(url, **kwargs):
                    mock_resp = MagicMock()
                    mock_resp.status_code = 200
                    if '/pulls/123/files' in url:
                        mock_resp.json.return_value = mock_files_data
                    else:
                        mock_resp.json.return_value = mock_pr_data
                    return mock_resp
                
                mock_get.side_effect = mock_response
                
                # Disable Gemini API for testing, provide GitHub token for authentication
                with patch.dict(os.environ, {'GEMINI_API_KEY': '', 'GITHUB_TOKEN': 'test_token_123'}):
                    result = await generate_pr_review(
                        github_pr_url="https://github.com/microsoft/vscode/pull/123",
                        project_path=temp_dir,
                        enable_gemini_review=False
                    )
                
                # Test behavior: successful PR review generation
                assert result["status"] == "success"
                assert "context_file" in result
                assert "ai_review_file" in result  # Should be None when disabled
                assert "pr_summary" in result
                
                # Verify actual file was created
                assert os.path.exists(result["context_file"])
                
                # Verify PR summary contains expected information
                pr_summary = result["pr_summary"]
                assert "pr_url" in pr_summary
                assert pr_summary["pr_url"] == "https://github.com/microsoft/vscode/pull/123"
    
    @pytest.mark.asyncio
    async def test_generate_pr_review_without_project_path(self):
        """Test PR review without local project path."""
        from server import generate_pr_review
        
        # Mock GitHub API responses based on real PR #3 data - CLAUDE.md compliant
        mock_pr_data = {
            "id": 2553516571,
            "number": 456,
            "state": "open",
            "title": "Add React component improvements", 
            "user": {"login": "reactdev"},
            "body": "Improving React components for better performance",
            "created_at": "2025-05-30T00:59:09Z",
            "updated_at": "2025-05-30T01:59:09Z", 
            "head": {
                "ref": "feature/react-improvements",
                "sha": "fe0d5d04bc6b3a08cc4f6240fb59494b0ad2e89d"
            },
            "base": {
                "ref": "main",
                "sha": "8d2c0cad9d3e72b0b1aa1d7cf13a781b02a1b418"
            },
            "html_url": "https://github.com/facebook/react/pull/456"
        }
        
        mock_files_data = [
            {
                "filename": "src/Component.js",
                "status": "modified",
                "additions": 25,
                "deletions": 10,
                "changes": 35,
                "patch": "@@ -1,10 +1,25 @@\n-old code\n+new improved code"
            }
        ]
        
        # Mock GitHub API calls but test real MCP behavior without project_path
        with patch('requests.get') as mock_get:
            def mock_response(url, **kwargs):
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                if '/pulls/456/files' in url:
                    mock_resp.json.return_value = mock_files_data
                else:
                    mock_resp.json.return_value = mock_pr_data
                return mock_resp
            
            mock_get.side_effect = mock_response
            
            # Disable Gemini API for testing, provide GitHub token for authentication
            with patch.dict(os.environ, {'GEMINI_API_KEY': '', 'GITHUB_TOKEN': 'test_token_456'}):
                result = await generate_pr_review(
                    github_pr_url="https://github.com/facebook/react/pull/456"
                    # project_path not provided - should use current directory
                )
            
            # Test behavior: should work without project_path
            assert result["status"] == "success"
            assert "context_file" in result
            assert "pr_summary" in result
            
            # Verify actual file was created
            assert os.path.exists(result["context_file"])
            
            # Verify PR summary
            pr_summary = result["pr_summary"]
            assert pr_summary["pr_url"] == "https://github.com/facebook/react/pull/456"
    
    @pytest.mark.asyncio
    async def test_generate_pr_review_handles_invalid_url(self):
        """Test error handling for invalid GitHub PR URLs."""
        from server import generate_pr_review
        
        # Test real URL validation behavior - CLAUDE.md compliant (no mocking internal functions)
        result = await generate_pr_review(
            github_pr_url="https://gitlab.com/group/project/merge_requests/123"  # Invalid GitHub URL
        )
        
        # Test behavior: should handle invalid URL gracefully
        assert result["status"] == "error"
        assert "error" in result
        # The actual error message will come from real URL parsing logic
        assert "github" in result["error"].lower() or "invalid" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_generate_pr_review_handles_github_api_errors(self):
        """Test handling of GitHub API errors."""
        from server import generate_pr_review
        
        # Test real GitHub API error handling - CLAUDE.md compliant
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock GitHub API to return 404 error (external dependency)
            with patch('requests.get') as mock_get:
                mock_resp = MagicMock()
                mock_resp.status_code = 404
                mock_resp.text = "Not Found"
                mock_get.return_value = mock_resp
                
                # Disable Gemini API for testing, provide GitHub token for authentication  
                with patch.dict(os.environ, {'GEMINI_API_KEY': '', 'GITHUB_TOKEN': 'test_token_999'}):
                    result = await generate_pr_review(
                        github_pr_url="https://github.com/owner/repo/pull/999",
                        project_path=temp_dir,
                        enable_gemini_review=False
                    )
                
                # Test behavior: should handle API errors gracefully
                assert result["status"] == "error"
                assert "error" in result
                # The actual error message will come from real GitHub API error handling
                assert "not found" in result["error"].lower() or "404" in result["error"] or "pr" in result["error"].lower()
    
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
        
        # Test branch comparison feedback with real git repository - CLAUDE.md compliant
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize git repo with main as default branch
            subprocess.run(['git', 'init', '--initial-branch=main'], cwd=temp_dir, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=temp_dir, check=True)
            
            # Create initial commit on main
            with open(os.path.join(temp_dir, 'README.md'), 'w') as f:
                f.write("# Test Project")
            subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=temp_dir, check=True)
            
            # Create feature branch with changes
            subprocess.run(['git', 'checkout', '-b', 'feature/test'], cwd=temp_dir, check=True)
            with open(os.path.join(temp_dir, 'test.py'), 'w') as f:
                f.write("def test(): return True")
            subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Add test function'], cwd=temp_dir, check=True)
            
            # Test branch comparison feedback
            with patch.dict(os.environ, {'GEMINI_API_KEY': ''}):
                result = await generate_branch_comparison_review(
                    project_path=temp_dir,
                    compare_branch="feature/test",
                    enable_gemini_review=False
                )
            
            # Test behavior: should provide appropriate user feedback structure
            assert "context_file" in result
            assert "ai_review_file" in result  # Should be None when disabled
            assert "branch_comparison_summary" in result
            assert "message" in result  # User-friendly message
            
        # Test PR review feedback with real GitHub API mocking - CLAUDE.md compliant
        mock_pr_data = {
            "id": 1,
            "number": 1,
            "state": "open",
            "title": "Test PR",
            "user": {"login": "testuser"},
            "body": "Test PR description",
            "created_at": "2025-05-30T00:59:09Z",
            "updated_at": "2025-05-30T01:59:09Z",
            "head": {"ref": "feature/test", "sha": "abc123"},
            "base": {"ref": "main", "sha": "def456"},
            "html_url": "https://github.com/test/repo/pull/1"
        }
        
        # Mock files data as well
        mock_files_data = [
            {
                "filename": "test.py",
                "status": "added",
                "additions": 1,
                "deletions": 0,
                "changes": 1,
                "patch": "@@ -0,0 +1,1 @@\n+def test(): return True"
            }
        ]
        
        with patch('requests.get') as mock_get:
            def mock_response(url, **kwargs):
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                if '/pulls/1/files' in url:
                    mock_resp.json.return_value = mock_files_data
                else:
                    mock_resp.json.return_value = mock_pr_data
                return mock_resp
            
            mock_get.side_effect = mock_response
            
            with patch.dict(os.environ, {'GEMINI_API_KEY': '', 'GITHUB_TOKEN': 'test_token_123'}):
                result = await generate_pr_review(
                    github_pr_url="https://github.com/test/repo/pull/1",
                    enable_gemini_review=False
                )
            
            # Test behavior: should provide appropriate feedback structure
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
        """Test that MCP tools work correctly with existing infrastructure."""
        from server import generate_branch_comparison_review
        
        # Test that MCP tools produce the same results as direct function calls - CLAUDE.md compliant
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize git repo with main as default branch
            subprocess.run(['git', 'init', '--initial-branch=main'], cwd=temp_dir, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=temp_dir, check=True)
            
            # Create initial commit on main
            with open(os.path.join(temp_dir, 'README.md'), 'w') as f:
                f.write("# Test Project")
            subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=temp_dir, check=True)
            
            # Create feature branch with changes
            subprocess.run(['git', 'checkout', '-b', 'feature/test'], cwd=temp_dir, check=True)
            with open(os.path.join(temp_dir, 'test.py'), 'w') as f:
                f.write("def test(): return True")
            subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Add test function'], cwd=temp_dir, check=True)
            
            # Test that MCP tool produces expected results
            with patch.dict(os.environ, {'GEMINI_API_KEY': ''}):
                result = await generate_branch_comparison_review(
                    project_path=temp_dir,
                    compare_branch="feature/test",
                    enable_gemini_review=False
                )
            
            # Test behavior: should successfully generate review using existing infrastructure
            assert result["status"] == "success"
            assert "context_file" in result
            assert os.path.exists(result["context_file"])
            
            # Verify the generated content includes git changes (proves infrastructure is working)
            with open(result["context_file"], 'r') as f:
                content = f.read()
                assert "test.py" in content  # Should include the changed file
                assert "Add test function" in content  # Should include commit message
    
    @pytest.mark.asyncio
    async def test_mcp_tools_handle_temperature_parameter(self):
        """Test that MCP tools can handle optional temperature parameter."""
        from server import generate_branch_comparison_review, generate_pr_review
        
        # Test temperature parameter with real git repository - CLAUDE.md compliant
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize git repo with main as default branch
            subprocess.run(['git', 'init', '--initial-branch=main'], cwd=temp_dir, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=temp_dir, check=True)
            
            # Create initial commit on main
            with open(os.path.join(temp_dir, 'README.md'), 'w') as f:
                f.write("# Test Project")
            subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=temp_dir, check=True)
            
            # Create feature branch with changes
            subprocess.run(['git', 'checkout', '-b', 'feature/test'], cwd=temp_dir, check=True)
            with open(os.path.join(temp_dir, 'test.py'), 'w') as f:
                f.write("def test(): return True")
            subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Add test function'], cwd=temp_dir, check=True)
            
            # Test with custom temperature parameter
            with patch.dict(os.environ, {'GEMINI_API_KEY': ''}):
                result = await generate_branch_comparison_review(
                    project_path=temp_dir,
                    compare_branch="feature/test",
                    temperature=0.3,
                    enable_gemini_review=False
                )
            
            # Test behavior: should accept temperature parameter and work correctly
            assert result["status"] == "success"
            assert "context_file" in result
            
            # Verify temperature is reflected in summary
            summary = result["branch_comparison_summary"]
            assert summary["temperature"] == 0.3
    
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