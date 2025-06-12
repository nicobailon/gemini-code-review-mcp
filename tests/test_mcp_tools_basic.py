"""
Basic tests for MCP tools to verify thinking_budget and url_context parameters.
"""

import pytest
from unittest.mock import patch
import os
import tempfile
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini API client."""
    with patch('src.gemini_api_client.send_to_gemini_for_review') as mock:
        mock.return_value = "Mock AI review content"
        yield mock


@pytest.fixture  
def mock_github_pr():
    """Mock GitHub PR integration."""
    with patch('src.github_pr_integration.get_complete_pr_analysis') as mock:
        mock.return_value = {
            'pr_data': {
                'title': 'Test PR',
                'author': 'testuser',
                'source_branch': 'feature',
                'target_branch': 'main',
                'state': 'open',
                'body': 'Test PR description'
            },
            'file_changes': {
                'summary': {
                    'files_changed': 2,
                    'total_additions': 10,
                    'total_deletions': 5
                },
                'changed_files': []
            }
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
        from src.server import generate_pr_review, generate_ai_code_review, generate_code_review_context, generate_meta_prompt
        import inspect
        
        # Check generate_pr_review has thinking_budget parameter
        sig = inspect.signature(generate_pr_review)
        assert 'thinking_budget' in sig.parameters
        
        # Check generate_ai_code_review has thinking_budget parameter
        sig = inspect.signature(generate_ai_code_review)
        assert 'thinking_budget' in sig.parameters
        
        # Check generate_code_review_context has thinking_budget parameter
        sig = inspect.signature(generate_code_review_context)
        assert 'thinking_budget' in sig.parameters
        
        # Check generate_meta_prompt has thinking_budget parameter
        sig = inspect.signature(generate_meta_prompt)
        assert 'thinking_budget' in sig.parameters
        
    def test_url_context_parameter_accepted(self):
        """Test that url_context parameter is accepted by tools."""
        from src.server import generate_pr_review, generate_ai_code_review, generate_code_review_context, generate_meta_prompt, generate_file_context
        import inspect
        
        # Check generate_pr_review has url_context parameter
        sig = inspect.signature(generate_pr_review)
        assert 'url_context' in sig.parameters
        
        # Check generate_ai_code_review has url_context parameter
        sig = inspect.signature(generate_ai_code_review)
        assert 'url_context' in sig.parameters
        
        # Check generate_code_review_context has url_context parameter
        sig = inspect.signature(generate_code_review_context)
        assert 'url_context' in sig.parameters
        
        # Check generate_meta_prompt has url_context parameter
        sig = inspect.signature(generate_meta_prompt)
        assert 'url_context' in sig.parameters
        
        # Check generate_file_context has url_context parameter
        sig = inspect.signature(generate_file_context)
        assert 'url_context' in sig.parameters
        
    def test_backward_compatibility_parameters(self):
        """Test that new parameters have defaults (backward compatibility)."""
        from src.server import generate_ai_code_review
        import inspect
        
        sig = inspect.signature(generate_ai_code_review)
        
        # Check thinking_budget has default None
        assert sig.parameters['thinking_budget'].default is None
        
        # Check url_context has default None  
        assert sig.parameters['url_context'].default is None
    
    def test_generate_file_context_deprecation_warning(self, temp_project_dir):
        """Test that generate_file_context raises deprecation warning and does not call Gemini."""
        from src.server import generate_file_context
        import warnings
        
        # Create a test file
        test_file = os.path.join(temp_project_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("print('test')")
        
        file_selections = [{"path": test_file}]
        
        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Mock send_to_gemini_for_review to ensure it's NOT called
            with patch('src.server.send_to_gemini_for_review') as mock_gemini:
                # Call the deprecated function
                result = generate_file_context(
                    file_selections=file_selections,
                    project_path=temp_project_dir,
                    text_output=True
                )
                
                # Verify deprecation warning was raised
                assert len(w) == 1
                assert issubclass(w[0].category, DeprecationWarning)
                assert "generate_file_context" in str(w[0].message)
                assert "ask_gemini" in str(w[0].message)
                
                # Verify it returns context content
                assert isinstance(result, str)
                assert "print('test')" in result
                
                # Verify Gemini was NOT called
                mock_gemini.assert_not_called()
    
    def test_ask_gemini_tool_exists(self):
        """Test that ask_gemini tool is available in MCP tools list."""
        from src.server import get_mcp_tools
        
        tools = get_mcp_tools()
        assert "ask_gemini" in tools
        assert "generate_file_context" in tools  # Should still exist for backward compatibility