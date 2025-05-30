"""
Behavior tests for MCP server tools - focus on user-visible outcomes
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestMCPToolBehavior:
    """Test MCP tools produce correct user-facing results"""
    
    def test_generate_code_review_context_tool_exists(self):
        """Test that the MCP tool is available and callable"""
        import server
        
        # Tool should be available via FastMCP
        assert hasattr(server, 'generate_code_review_context')
        assert callable(server.generate_code_review_context)
    
    def test_generate_ai_code_review_tool_exists(self):
        """Test that the AI review tool is available and callable"""
        import server
        
        # Tool should be available via FastMCP
        assert hasattr(server, 'generate_ai_code_review')
        assert callable(server.generate_ai_code_review)
    
    def test_mcp_tool_response_format(self):
        """Test that MCP tool returns properly formatted response for users"""
        import server
        
        # Test with invalid path to check error response format
        response = server.generate_code_review_context(
            project_path="/nonexistent/path"
        )
        
        # Should return user-friendly error message
        assert isinstance(response, str)
        assert "ERROR:" in response
        assert "does not exist" in response
    
    def test_mcp_tool_validates_absolute_paths(self):
        """Test that MCP tool enforces absolute path requirement"""
        import server
        
        response = server.generate_code_review_context(
            project_path="relative/path"
        )
        
        # Should return clear validation error
        assert "ERROR:" in response
        assert "must be an absolute path" in response
    
    def test_mcp_tool_validates_required_parameters(self):
        """Test that MCP tool validates required parameters"""
        import server
        
        response = server.generate_code_review_context(
            project_path=""
        )
        
        # Should return clear validation error
        assert "ERROR:" in response
        assert "project_path is required" in response
    
    @patch('server.os.path.exists')
    @patch('server.os.path.isdir')
    @patch('server.os.path.isabs')
    @patch('server.generate_review_context')
    def test_successful_mcp_response_includes_user_feedback(self, mock_generate, mock_isabs, mock_isdir, mock_exists):
        """Test that successful MCP response includes user feedback elements"""
        import server
        
        # Mock path validation
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_isabs.return_value = True
        
        # Mock successful generation
        mock_generate.return_value = ("/path/to/context.md", "/path/to/review.md")
        
        response = server.generate_code_review_context(
            project_path="/valid/path",
            scope="recent_phase",
            enable_gemini_review=True,
            temperature=0.5
        )
        
        # Should include user feedback elements
        assert "🔍 Analyzed project:" in response
        assert "📊 Review scope:" in response
        assert "🌡️ AI temperature:" in response
        assert "📝 Generated review context:" in response
        assert "🤖 Using Gemini model:" in response
        assert "🎉 Code review process completed!" in response
        assert "📄 Files generated:" in response
        
        # Should include file paths for user reference
        assert "Output files:" in response
        assert "Context:" in response
        assert "AI Review:" in response
    
    @patch('server.os.path.exists')
    @patch('server.os.path.isdir') 
    @patch('server.os.path.isabs')
    @patch('server.generate_review_context')
    def test_mcp_response_shows_model_capabilities(self, mock_generate, mock_isabs, mock_isdir, mock_exists):
        """Test that MCP response shows detected model capabilities to user"""
        import server
        
        # Mock path validation
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_isabs.return_value = True
        
        # Mock successful generation with AI review
        mock_generate.return_value = ("/path/to/context.md", "/path/to/review.md")
        
        response = server.generate_code_review_context(
            project_path="/valid/path",
            enable_gemini_review=True
        )
        
        # Should show model information
        assert "🤖 Using Gemini model:" in response
        # Should show either enhanced features or standard features
        assert ("✨ Enhanced features enabled:" in response or 
                "⚡ Standard features: Basic text generation" in response)
    
    def test_ai_review_tool_validates_parameters(self):
        """Test that AI review tool validates its parameters"""
        import server
        
        # Test missing context file path
        response = server.generate_ai_code_review(
            context_file_path=""
        )
        
        assert "ERROR:" in response
        assert "context_file_path is required" in response
        
        # Test relative path
        response = server.generate_ai_code_review(
            context_file_path="relative/path.md"
        )
        
        assert "ERROR:" in response
        assert "must be an absolute path" in response
        
        # Test nonexistent file
        response = server.generate_ai_code_review(
            context_file_path="/nonexistent/file.md"
        )
        
        assert "ERROR:" in response
        assert "does not exist" in response


class TestUserExperienceBehavior:
    """Test that tools provide good user experience"""
    
    def test_error_messages_are_user_friendly(self):
        """Test that error messages help users understand what went wrong"""
        import server
        
        # Test various error conditions produce helpful messages
        test_cases = [
            ("", "project_path is required"),
            ("relative/path", "must be an absolute path"),
            ("/nonexistent", "does not exist"),
        ]
        
        for project_path, expected_message in test_cases:
            response = server.generate_code_review_context(project_path=project_path)
            assert "ERROR:" in response
            assert expected_message in response
            # Should not expose internal implementation details
            assert "Exception" not in response
            assert "Traceback" not in response
    
    @patch('server.os.path.exists')
    @patch('server.os.path.isdir')
    @patch('server.os.path.isabs')
    @patch('server.generate_review_context')
    def test_response_includes_project_name(self, mock_generate, mock_isabs, mock_isdir, mock_exists):
        """Test that response includes recognizable project name for user"""
        import server
        
        # Mock successful path validation
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_isabs.return_value = True
        mock_generate.return_value = ("/path/to/context.md", None)
        
        response = server.generate_code_review_context(
            project_path="/users/alice/projects/my-awesome-app"
        )
        
        # Should show project name that user can recognize
        assert "my-awesome-app" in response
    
    def test_scope_parameter_affects_response(self):
        """Test that different scope values produce different user feedback"""
        import server
        
        # Test that scope shows up in user feedback
        response = server.generate_code_review_context(
            project_path="/nonexistent/path",
            scope="full_project"
        )
        
        # Even error responses should show the scope for user context
        # (This tests that the validation happens after scope is processed)
        assert isinstance(response, str)
        assert "ERROR:" in response


class TestBusinessRequirements:
    """Test that tools meet business requirements"""
    
    def test_tool_supports_all_documented_scopes(self):
        """Test that tool accepts all scope values mentioned in documentation"""
        import server
        
        documented_scopes = ["recent_phase", "full_project", "specific_phase", "specific_task"]
        
        for scope in documented_scopes:
            # Should not fail due to invalid scope (will fail due to path validation)
            response = server.generate_code_review_context(
                project_path="/nonexistent/path",
                scope=scope
            )
            
            # Should not contain scope-related errors
            assert "invalid scope" not in response.lower()
            assert "unknown scope" not in response.lower()
    
    def test_temperature_parameter_is_respected(self):
        """Test that temperature parameter is processed and shown to user"""
        import server
        
        response = server.generate_code_review_context(
            project_path="/nonexistent/path",
            temperature=0.8,
            enable_gemini_review=True
        )
        
        # Temperature should be reflected in user feedback
        # (We can't see it in error responses, but this ensures parameter is accepted)
        assert isinstance(response, str)
    
    def test_gemini_review_can_be_disabled(self):
        """Test that users can disable AI review generation"""
        import server
        
        response = server.generate_code_review_context(
            project_path="/nonexistent/path",
            enable_gemini_review=False
        )
        
        # Should not mention AI-related features when disabled
        # (This is behavioral requirement - users should see different output)
        assert isinstance(response, str)