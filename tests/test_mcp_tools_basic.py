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
        from server import generate_pr_review, generate_ai_code_review, generate_code_review_context, generate_meta_prompt
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
        from server import generate_pr_review, generate_ai_code_review, generate_code_review_context, generate_meta_prompt, generate_file_context
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
        from server import generate_ai_code_review
        import inspect
        
        sig = inspect.signature(generate_ai_code_review)
        
        # Check thinking_budget has default None
        assert sig.parameters['thinking_budget'].default is None
        
        # Check url_context has default None  
        assert sig.parameters['url_context'].default is None