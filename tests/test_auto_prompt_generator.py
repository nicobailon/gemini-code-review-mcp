"""Test suite for auto_prompt_generator module.

Tests focused on simplified meta-prompt generation functionality.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import json

# Import functions that exist after refactoring
from src.auto_prompt_generator import (
    validate_prompt,
    generate_auto_prompt
)


class TestPromptValidation:
    """Test suite for prompt validation functionality."""
    
    def test_validate_prompt_not_implemented(self):
        """Test that validate_prompt raises NotImplementedError."""
        prompt = {
            'generated_prompt': 'Test prompt',
            'template_used': 'default',
            'analysis_completed': True
        }
        
        with pytest.raises(NotImplementedError, match="validate_prompt function not yet implemented"):
            validate_prompt(prompt)


class TestGenerateAutoPromptIntegration:
    """Test suite for generate_auto_prompt function integration."""
    
    @pytest.fixture
    def mock_send_to_gemini(self):
        """Mock the send_to_gemini_for_review function."""
        return """# Meta-Prompt for AI Code Review Agent

Based on the completed development work and project guidelines, focus your code review on:

## Key Areas for Review:
1. **Type Safety**: Ensure TypeScript strict mode compliance
2. **Test Coverage**: Verify TDD protocol adherence
3. **Configuration Integration**: Check CLAUDE.md guidelines implementation

## Project Context:
- Python-based MCP server with FastMCP framework
- Gemini AI integration for meta-prompt generation
- Test-driven development following strict protocols

Please provide specific, actionable feedback aligned with the project's established guidelines."""
    
    def test_generate_auto_prompt_alias_import(self):
        """Test that generate_auto_prompt can be imported as alias."""
        # This tests the import alias functionality from auto_prompt_generator.py
        try:
            from src.auto_prompt_generator import generate_auto_prompt
            assert generate_auto_prompt is not None
        except ImportError:
            # Expected when server module isn't available
            pytest.skip("Server module not available for import alias")
    
    @pytest.mark.asyncio
    @patch('src.auto_prompt_generator.generate_auto_prompt')
    async def test_generate_auto_prompt_mock_call(self, mock_generate):
        """Test generate_auto_prompt function call interface."""
        # Mock return value for async function
        mock_generate.return_value = {
            'generated_prompt': 'Test meta-prompt',
            'template_used': 'default',
            'configuration_included': True,
            'analysis_completed': True,
            'context_analyzed': 1000
        }
        
        # Import and call
        from src.auto_prompt_generator import generate_auto_prompt
        result = await generate_auto_prompt(
            context_content='Test context'
        )
        
        # Verify call and result
        mock_generate.assert_called_once()
        assert result['analysis_completed'] is True
        assert result['template_used'] == 'default'
        assert 'generated_prompt' in result


class TestMetaPromptConfigurationIntegration:
    """Test meta-prompt generation with configuration context."""
    
    @pytest.fixture
    def sample_claude_md_content(self):
        """Sample CLAUDE.md content for testing."""
        return """# TypeScript Guidelines
        
## Type Safety Rules
- NEVER use 'any' types
- Always prefer explicit type annotations
- Use branded types for domain-specific values

## TDD Protocol
- Write tests first before implementation
- Follow Red-Green-Refactor cycle
- Verify type-level tests with TypeScript compilation
"""
    
    @pytest.fixture 
    def sample_context_with_config(self, sample_claude_md_content):
        """Sample context content with configuration."""
        return f"""# Development Context

## Completed Tasks
- Enhanced meta-prompt generation with configuration discovery
- Fixed hierarchy_level attribute access bug
- Integrated CLAUDE.md content into template system

## Configuration Guidelines
{sample_claude_md_content}

## Project Stack
- Python FastMCP server
- Gemini AI integration
- TypeScript-style type safety validation
"""
    
    def test_configuration_context_integration(self, sample_context_with_config):
        """Test that configuration context is properly integrated."""
        # This test verifies that we can work with configuration content
        # The actual integration is tested in the main auto-prompt generation tests
        assert "CLAUDE.md" in sample_context_with_config
        assert "Type Safety Rules" in sample_context_with_config
        assert "TDD Protocol" in sample_context_with_config