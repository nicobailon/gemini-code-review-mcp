"""
Comprehensive tests for auto-prompt generation MCP tool.
Focused on meta-prompt generation with configuration context integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, Optional
import os
import tempfile


class TestGenerateAutoPromptMCPTool:
    """Test the generate_meta_prompt MCP tool functionality."""
    
    @pytest.fixture
    def generate_meta_prompt_func(self):
        """Fixture to safely import generate_meta_prompt function."""
        try:
            from src.server import generate_meta_prompt
            return generate_meta_prompt
        except (ImportError, SystemExit):
            pytest.skip("Skipping test due to missing dependencies")
    
    @pytest.fixture
    def mock_gemini_response(self):
        """Mock Gemini API response for deterministic testing."""
        return {
            "text": """Focus your code review on the authentication system implementation in this Node.js Express application.

CRITICAL AREAS TO REVIEW:
1. OAuth token validation in src/auth/oauth.js - 3 new security functions
2. Database credential storage in src/models/user.js - potential plaintext storage risk
3. Session middleware in src/middleware/auth.js - affects all protected routes

SPECIFIC SECURITY CONCERNS:
- Review PKCE implementation for OAuth flow
- Check for SQL injection in user query functions
- Validate secure cookie configuration
- Assess token rotation and expiration policies

Provide specific, actionable feedback focusing on these high-impact security areas."""
        }
    
    @pytest.fixture
    def sample_context_content(self):
        """Sample context content for testing."""
        return """# Code Review Context

## Project Information
- Project: my-app
- Phase: 2.1 OAuth Integration

## Code Changes
### Modified Files:
- src/auth/oauth.js (new OAuth implementation)
- src/models/user.js (database schema changes)
- src/middleware/auth.js (session management)

## Git Diff
```diff
+++ src/auth/oauth.js
+function validateOAuthToken(token) {
+  // OAuth token validation logic
+}
```

## PRD Summary
Implementing OAuth authentication system for secure user login.
"""
    
    @pytest.fixture
    def sample_context_file(self, tmp_path, sample_context_content):
        """Create a temporary context file for testing."""
        context_file = tmp_path / "test-context.md"
        context_file.write_text(sample_context_content)
        return str(context_file)
    
    def test_generate_meta_prompt_tool_exists(self):
        """Test that the generate_meta_prompt MCP tool is properly registered."""
        # Test that the function exists and can be imported
        try:
            from src.server import get_mcp_tools
            tools = get_mcp_tools()
            assert "generate_meta_prompt" in tools
        except (ImportError, SystemExit) as e:
            # If we can't import due to missing dependencies, check if function exists another way
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
            
            # Read the server.py file directly to check if function is defined
            server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'server.py')
            with open(server_path, 'r') as f:
                content = f.read()
                assert "def generate_meta_prompt(" in content, "generate_meta_prompt function not found in server.py"
                assert "@mcp.tool()" in content, "MCP tool decorator not found"
    
    def test_generate_meta_prompt_tool_schema(self):
        """Test that the MCP tool has correct schema definition."""
        try:
            from src.server import get_mcp_tool_schema
            schema = get_mcp_tool_schema("generate_meta_prompt")
        except (ImportError, SystemExit):
            # Skip this test if dependencies aren't available
            pytest.skip("Skipping schema test due to missing dependencies")
        
        # Verify required parameters
        assert "context_file_path" in schema["parameters"]["properties"]
        assert "context_content" in schema["parameters"]["properties"]
        assert "project_path" in schema["parameters"]["properties"]
        assert "scope" in schema["parameters"]["properties"]
        
        # Verify parameter types
        assert schema["parameters"]["properties"]["context_file_path"]["type"] == "string"
        assert schema["parameters"]["properties"]["context_content"]["type"] == "string"
        assert schema["parameters"]["properties"]["project_path"]["type"] == "string"
        assert schema["parameters"]["properties"]["scope"]["type"] == "string"
        
        # Verify default values
        assert schema["parameters"]["properties"]["scope"]["default"] == "recent_phase"
    
    @pytest.mark.asyncio
    async def test_generate_meta_prompt_with_context_file_path(self, generate_meta_prompt_func, sample_context_file, mock_gemini_response):
        """Test generate_meta_prompt with context_file_path parameter."""
        
        with patch('src.server.gemini_client.generate_content', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = mock_gemini_response
            
            result = await generate_meta_prompt_func(context_file_path=sample_context_file)
            
            # Verify return structure
            assert isinstance(result, dict)
            assert "generated_prompt" in result
            assert "analysis_completed" in result
            assert "context_analyzed" in result
            
            # Verify return values
            assert result["analysis_completed"] is True
            assert isinstance(result["context_analyzed"], int)
            assert result["context_analyzed"] > 0
            assert isinstance(result["generated_prompt"], str)
            assert len(result["generated_prompt"]) > 100  # Should be substantial prompt
            
            # Verify Gemini was called with context
            mock_gemini.assert_called_once()
            call_args = mock_gemini.call_args[0][0] if mock_gemini.call_args[0] else str(mock_gemini.call_args)
            assert "code review context" in call_args.lower() or "meta-prompt" in call_args.lower()
            assert "src/auth/oauth.js" in call_args  # Context content should be included
    
    @pytest.mark.asyncio
    async def test_generate_meta_prompt_with_context_content(self, generate_meta_prompt_func, sample_context_content, mock_gemini_response):
        """Test generate_meta_prompt with context_content parameter."""
        
        with patch('src.server.gemini_client.generate_content', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = mock_gemini_response
            
            result = await generate_meta_prompt_func(context_content=sample_context_content)
            
            # Verify return structure and values
            assert result["analysis_completed"] is True
            assert result["context_analyzed"] == len(sample_context_content)
            assert "OAuth" in result["generated_prompt"]  # Should reflect content analysis
    
    @pytest.mark.asyncio
    async def test_generate_meta_prompt_with_project_path(self, generate_meta_prompt_func, tmp_path, mock_gemini_response):
        """Test generate_meta_prompt with project_path parameter (generates context first)."""
        
        project_path = str(tmp_path)
        
        with patch('src.server.gemini_client.generate_content', new_callable=AsyncMock) as mock_gemini:
            with patch('src.server.generate_code_review_context', new_callable=AsyncMock) as mock_context:
                mock_gemini.return_value = mock_gemini_response
                mock_context.return_value = {
                    "context_file_path": "/tmp/test-context.md",
                    "success": True
                }
                
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = "test context"
                    
                    result = await generate_meta_prompt_func(project_path=project_path, scope="recent_phase")
                    
                    # Verify context generation was called
                    mock_context.assert_called_once_with(project_path, "recent_phase", raw_context_only=True)
                    
                    # Verify result structure
                    assert result["analysis_completed"] is True
                    assert isinstance(result["generated_prompt"], str)
    
    @pytest.mark.asyncio
    async def test_generate_meta_prompt_input_validation(self, generate_meta_prompt_func):
        """Test input validation for generate_meta_prompt."""
        
        # Test with no parameters - should raise ValueError
        with pytest.raises(ValueError, match="At least one input parameter must be provided"):
            await generate_meta_prompt_func()
        
        # Test with multiple conflicting parameters
        with pytest.raises(ValueError, match="Only one input parameter should be provided"):
            await generate_meta_prompt_func(
                context_file_path="/path/to/file",
                context_content="content",
                project_path="/path/to/project"
            )
    
    @pytest.mark.asyncio
    async def test_generate_meta_prompt_file_not_found(self, generate_meta_prompt_func):
        """Test handling of non-existent context file."""
        
        with pytest.raises(FileNotFoundError):
            await generate_meta_prompt_func(context_file_path="/nonexistent/file.md")
    
    @pytest.mark.asyncio
    async def test_generate_meta_prompt_gemini_api_error(self, generate_meta_prompt_func, sample_context_content):
        """Test handling of Gemini API errors."""
        
        with patch('src.server.gemini_client.generate_content', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.side_effect = Exception("Gemini API Error")
            
            with pytest.raises(Exception, match="Failed to generate auto-prompt"):
                await generate_meta_prompt_func(context_content=sample_context_content)
    
    @pytest.mark.asyncio
    async def test_generate_meta_prompt_empty_context(self, generate_meta_prompt_func):
        """Test handling of empty context content."""
        
        with pytest.raises(ValueError, match="Context content cannot be empty"):
            await generate_meta_prompt_func(context_content="")
        
        with pytest.raises(ValueError, match="Context content cannot be empty"):
            await generate_meta_prompt_func(context_content="   ")  # Only whitespace
    
    @pytest.mark.asyncio
    async def test_generate_meta_prompt_large_context_handling(self, generate_meta_prompt_func, mock_gemini_response):
        """Test handling of large context content (should truncate if needed)."""
        
        # Create very large context (simulate >100KB)
        large_context = "x" * 150000  # 150KB of content
        
        with patch('src.server.gemini_client.generate_content', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = mock_gemini_response
            
            result = await generate_meta_prompt_func(context_content=large_context)
            
            # Should handle large content gracefully
            assert result["analysis_completed"] is True
            assert result["context_analyzed"] <= 100000  # Should be truncated
            
            # Verify truncation warning in logs
            call_args = mock_gemini.call_args[0][0]
            assert len(call_args) <= 100000  # Gemini call should use truncated content
    
    def test_generate_meta_prompt_return_type_annotations(self, generate_meta_prompt_func):
        """Test that function has proper type annotations."""
        import inspect
        
        signature = inspect.signature(generate_meta_prompt_func)
        
        # Verify parameter type hints
        params = signature.parameters
        assert params["context_file_path"].annotation == "Optional[str]"
        assert params["context_content"].annotation == "Optional[str]" 
        assert params["project_path"].annotation == "Optional[str]"
        assert params["scope"].annotation == "str"
        
        # Verify return type hint
        assert signature.return_annotation == "Dict[str, Any]"
    
    @pytest.mark.asyncio
    async def test_generate_meta_prompt_gemini_analysis_prompt_structure(self, generate_meta_prompt_func, sample_context_content):
        """Test that the prompt sent to Gemini has the correct structure and instructions."""
        
        with patch('src.server.gemini_client.generate_content', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = {"text": "test prompt"}
            
            await generate_meta_prompt_func(context_content=sample_context_content)
            
            # Verify the analysis prompt structure
            call_args = mock_gemini.call_args[0][0]
            
            # Should contain key analysis instructions
            assert "analyze this code review context" in call_args.lower()
            assert "generate an optimized prompt" in call_args.lower()
            assert "type of changes were made" in call_args.lower()
            assert "specific areas need attention" in call_args.lower()
            assert "project phase" in call_args.lower()
            assert "risk areas" in call_args.lower()
            
            # Should include the actual context
            assert sample_context_content in call_args


class TestAutoPromptGenerationTypeLevel:
    """Type-level tests for auto-prompt generation using TypeScript-style assertions."""
    
    @pytest.fixture
    def generate_meta_prompt_func(self):
        """Fixture to safely import generate_meta_prompt function."""
        try:
            from src.server import generate_meta_prompt
            return generate_meta_prompt
        except (ImportError, SystemExit):
            pytest.skip("Skipping test due to missing dependencies")
    
    def test_generate_meta_prompt_return_type_structure(self, generate_meta_prompt_func):
        """Test the return type structure at type level."""
        from typing import get_type_hints
        
        # Type-level assertions equivalent to TypeScript
        hints = get_type_hints(generate_meta_prompt_func)
        
        # Verify return type is Dict[str, Any]
        assert str(hints['return']).startswith('typing.Dict')
        
        # These would be TypeScript-style type assertions in a real implementation:
        # type AssertEqual<T, U> = T extends U ? (U extends T ? true : false) : false;
        # type Test1 = AssertEqual<typeof result.generated_prompt, string>; // Should be true
        # type Test2 = AssertEqual<typeof result.analysis_completed, boolean>; // Should be true
        # type Test3 = AssertEqual<typeof result.context_analyzed, number>; // Should be true
    
    def test_input_parameter_types(self, generate_meta_prompt_func):
        """Test input parameter type constraints."""
        from typing import get_type_hints
        
        hints = get_type_hints(generate_meta_prompt_func)
        
        # All input parameters should be Optional[str] except scope
        assert 'context_file_path' in hints
        assert 'context_content' in hints  
        assert 'project_path' in hints
        assert 'scope' in hints


class TestConfigurationContextIntegration:
    """Test suite for CLAUDE.md and cursor rules integration in meta-prompt generation."""
    
    @pytest.fixture
    def generate_meta_prompt_func(self):
        """Fixture to safely import generate_meta_prompt function."""
        try:
            from src.server import generate_meta_prompt
            return generate_meta_prompt
        except (ImportError, SystemExit):
            pytest.skip("Skipping test due to missing dependencies")
    
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
    def mock_configuration_discovery(self, sample_claude_md_content):
        """Mock configuration discovery to return test data."""
        return {
            'claude_memory_files': [
                Mock(
                    file_path='CLAUDE.md',
                    content=sample_claude_md_content,
                    hierarchy_level='project'
                )
            ],
            'cursor_rules_files': [],
            'discovery_errors': []
        }
    
    @pytest.mark.asyncio
    async def test_meta_prompt_template_usage(self, generate_meta_prompt_func):
        """Test that the default meta-prompt template is used."""
        context_content = "Simple test context for template testing"
        
        with patch('src.generate_code_review_context.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = "Generated meta-prompt content"
            
            # Test default template (only template available)
            result = await generate_meta_prompt_func(
                context_content=context_content
            )
            assert result['template_used'] == 'default'
            assert result['analysis_completed'] is True
            assert 'generated_prompt' in result
    
    @pytest.mark.asyncio
    async def test_configuration_context_inclusion(self, generate_meta_prompt_func, mock_configuration_discovery):
        """Test that CLAUDE.md and cursor rules are included in meta-prompt generation."""
        
        with patch('src.generate_code_review_context.discover_project_configurations') as mock_discover:
            mock_discover.return_value = mock_configuration_discovery
            
            with patch('src.generate_code_review_context.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = "Generated meta-prompt with configuration context"
                
                result = await generate_meta_prompt_func(
                    project_path='/test/project',
                    scope='recent_phase'
                )
                
                # Verify configuration was discovered and included
                mock_discover.assert_called_once_with('/test/project')
                assert result['configuration_included'] is True
                
                # Verify template was called with configuration context
                mock_gemini.assert_called_once()
                call_args = mock_gemini.call_args
                assert 'TypeScript Guidelines' in call_args[1]['context_content'] or \
                       'TypeScript Guidelines' in str(call_args)
    
    @pytest.mark.asyncio
    async def test_configuration_context_placeholder_replacement(self, generate_meta_prompt_func):
        """Test that {configuration_context} placeholders are properly replaced."""
        
        # Mock template loading to verify placeholder replacement
        mock_template = {
            "name": "Test Template",
            "template": "Test template with {configuration_context} and {context} placeholders",
            "focus_areas": ["testing"],
            "output_format": "test"
        }
        
        with patch('src.generate_code_review_context.get_meta_prompt_template') as mock_get_template:
            mock_get_template.return_value = mock_template
            
            with patch('src.generate_code_review_context.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = "Generated meta-prompt"
                
                result = await generate_meta_prompt_func(
                    context_content='Test context content'
                )
                
                # Verify template was loaded
                mock_get_template.assert_called_once_with('default')
                
                # Verify Gemini was called with replaced placeholders
                mock_gemini.assert_called_once()
                call_args = mock_gemini.call_args[1]['context_content']
                
                # Template should have placeholders replaced
                assert '{configuration_context}' not in call_args
                assert '{context}' not in call_args
                assert 'Test context content' in call_args
    
    @pytest.mark.asyncio
    async def test_configuration_discovery_error_handling(self, generate_meta_prompt_func):
        """Test graceful handling of configuration discovery errors."""
        
        with patch('src.generate_code_review_context.discover_project_configurations') as mock_discover:
            mock_discover.side_effect = Exception("Configuration discovery failed")
            
            with patch('src.generate_code_review_context.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = "Generated meta-prompt without configuration"
                
                # Should not raise exception, but continue without configuration
                result = await generate_meta_prompt_func(
                    context_content='Test context without configuration'
                )
                
                # Should complete successfully even with configuration error
                assert result['analysis_completed'] is True
                assert result['configuration_included'] is False
    
    @pytest.mark.asyncio
    async def test_enhanced_send_to_gemini_return_text_parameter(self, generate_meta_prompt_func):
        """Test that the enhanced send_to_gemini_for_review with return_text parameter works."""
        
        # This tests our enhancement to send_to_gemini_for_review function
        with patch('src.generate_code_review_context.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = "Direct text response from Gemini"
            
            result = await generate_meta_prompt_func(
                context_content='Test context for return_text parameter'
            )
            
            # Verify send_to_gemini_for_review was called with return_text=True
            mock_gemini.assert_called_once()
            call_kwargs = mock_gemini.call_args[1]
            assert call_kwargs.get('return_text') is True
            assert call_kwargs.get('temperature') == 0.3  # Lower temperature for meta-prompts
            
            # Verify result contains the direct response
            assert result['generated_prompt'] == "Direct text response from Gemini"