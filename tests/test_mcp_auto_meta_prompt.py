"""
Test suite for auto meta prompt feature in generate_code_review_context MCP tool.

Following TDD Protocol: Writing tests first to define expected behavior.
The feature should allow the MCP tool to automatically generate a meta prompt
and embed it in the <user_instructions> section of the context file.
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock, mock_open
import tempfile
import os
import json
from pathlib import Path
from typing import Dict, Any


class TestMCPAutoMetaPrompt:
    """Test auto meta prompt feature for MCP tool."""
    
    def test_mcp_tool_accepts_auto_meta_prompt_parameter(self):
        """Test that generate_code_review_context MCP tool accepts auto_meta_prompt parameter."""
        from src.server import generate_code_review_context
        import inspect
        
        # Check function signature includes auto_meta_prompt parameter
        sig = inspect.signature(generate_code_review_context)
        params = list(sig.parameters.keys())
        
        # Should include auto_meta_prompt parameter
        assert 'auto_meta_prompt' in params, f"auto_meta_prompt parameter missing. Current params: {params}"
        
        # Parameter should have boolean type hint and default to False
        param = sig.parameters['auto_meta_prompt']
        assert param.default is False, "auto_meta_prompt should default to False"
        
    def test_mcp_tool_generates_meta_prompt_when_enabled(self):
        """Test MCP tool generates meta prompt when auto_meta_prompt=True."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create minimal project structure
            Path(temp_dir, "src").mkdir()
            Path(temp_dir, "tests").mkdir()
            Path(temp_dir, "CLAUDE.md").write_text("# Test project guidelines")
            
            with patch('src.server.generate_meta_prompt') as mock_generate_meta:
                with patch('src.server.generate_review_context') as mock_generate_context:
                    # Mock meta prompt generation
                    test_meta_prompt = """You are a specialized code reviewer for this project.
Focus on:
1. Type safety violations
2. Test coverage gaps  
3. Performance issues"""
                    
                    mock_generate_meta.return_value = {
                        "generated_prompt": test_meta_prompt,
                        "template_used": "default", 
                        "configuration_included": True,
                        "analysis_completed": True,
                        "context_analyzed": 1500
                    }
                    
                    # Mock context generation to return file paths
                    context_file = f"{temp_dir}/context-with-meta-prompt.md"
                    mock_generate_context.return_value = (context_file, None)
                    
                    from src.server import generate_code_review_context
                    
                    # Call MCP tool with auto_meta_prompt enabled
                    result = generate_code_review_context(
                        project_path=temp_dir,
                        auto_meta_prompt=True,
                        text_output=False
                    )
                    
                    # Verify meta prompt was generated
                    mock_generate_meta.assert_called_once_with(
                        project_path=temp_dir,
                        scope="recent_phase"
                    )
                    
                    # Verify context generation was called with meta prompt
                    mock_generate_context.assert_called_once()
                    call_kwargs = mock_generate_context.call_args[1]
                    assert 'auto_prompt_content' in call_kwargs
                    assert call_kwargs['auto_prompt_content'] == test_meta_prompt
    
    def test_mcp_tool_skips_meta_prompt_when_disabled(self):
        """Test MCP tool skips meta prompt generation when auto_meta_prompt=False."""
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "CLAUDE.md").write_text("# Test project")
            
            with patch('src.server.generate_meta_prompt') as mock_generate_meta:
                with patch('src.server.generate_review_context') as mock_generate_context:
                    mock_generate_context.return_value = (f"{temp_dir}/context.md", None)
                    
                    from src.server import generate_code_review_context
                    
                    # Call MCP tool with auto_meta_prompt disabled (default)
                    result = generate_code_review_context(
                        project_path=temp_dir,
                        auto_meta_prompt=False,
                        text_output=False
                    )
                    
                    # Verify meta prompt was NOT generated
                    mock_generate_meta.assert_not_called()
                    
                    # Verify context generation was called without meta prompt
                    mock_generate_context.assert_called_once()
                    call_kwargs = mock_generate_context.call_args[1]
                    assert 'auto_prompt_content' not in call_kwargs or call_kwargs.get('auto_prompt_content') is None
    
    def test_meta_prompt_embedded_in_context_file_user_instructions(self):
        """Test that generated meta prompt is embedded in context file <user_instructions>."""
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "test-context.md"
            
            # Mock the meta prompt generation
            test_meta_prompt = """Review this codebase focusing on:
- Security vulnerabilities  
- Performance optimizations
- Code maintainability"""
            
            with patch('src.server.generate_meta_prompt') as mock_generate_meta:
                mock_generate_meta.return_value = {
                    "generated_prompt": test_meta_prompt,
                    "template_used": "default",
                    "configuration_included": True,
                    "analysis_completed": True,
                    "context_analyzed": 2000
                }
                
                # Mock file writing to capture content
                written_content = {}
                
                def mock_write_side_effect(content):
                    written_content['context'] = content
                
                mock_file = mock_open()
                mock_file.return_value.write.side_effect = mock_write_side_effect
                
                with patch('builtins.open', mock_file):
                    with patch('src.server.generate_review_context') as mock_generate_context:
                        # Set up context generation to write the file with meta prompt
                        def side_effect(*args, **kwargs):
                            if 'auto_prompt_content' in kwargs:
                                # Simulate writing context file with meta prompt
                                content = f"""# Code Review Context

<user_instructions>
{kwargs['auto_prompt_content']}
</user_instructions>

## Project Summary
Test project summary"""
                                mock_file.return_value.write(content)
                            return (str(context_file), None)
                        
                        mock_generate_context.side_effect = side_effect
                        
                        from src.server import generate_code_review_context
                        
                        result = generate_code_review_context(
                            project_path=temp_dir,
                            auto_meta_prompt=True,
                            text_output=False
                        )
                        
                        # Verify the context file contains meta prompt in user_instructions
                        assert 'context' in written_content
                        content = written_content['context']
                        
                        assert '<user_instructions>' in content
                        assert '</user_instructions>' in content
                        assert 'Security vulnerabilities' in content
                        assert 'Performance optimizations' in content
                        assert 'Code maintainability' in content
    
    def test_error_handling_meta_prompt_generation_fails(self):
        """Test error handling when meta prompt generation fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "CLAUDE.md").write_text("# Test project")
            
            with patch('src.server.generate_meta_prompt') as mock_generate_meta:
                # Mock meta prompt generation failure
                mock_generate_meta.side_effect = Exception("API key not configured")
                
                from src.server import generate_code_review_context
                
                result = generate_code_review_context(
                    project_path=temp_dir,
                    auto_meta_prompt=True,
                    text_output=False
                )
                
                # Should return error message when meta prompt generation fails
                assert isinstance(result, str)
                assert result.startswith("ERROR:")
                assert "meta prompt generation failed" in result.lower() or "api key" in result.lower()
    
    def test_backward_compatibility_default_behavior(self):
        """Test that default behavior is unchanged when auto_meta_prompt not specified."""
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "CLAUDE.md").write_text("# Test project")
            
            with patch('src.server.generate_review_context') as mock_generate_context:
                mock_generate_context.return_value = (f"{temp_dir}/context.md", None)
                
                from src.server import generate_code_review_context
                
                # Call without auto_meta_prompt parameter (should default to False)
                result = generate_code_review_context(
                    project_path=temp_dir,
                    text_output=False
                )
                
                # Verify normal context generation without meta prompt
                mock_generate_context.assert_called_once()
                call_kwargs = mock_generate_context.call_args[1]
                assert call_kwargs.get('auto_prompt_content') is None


class TestMCPAutoMetaPromptIntegration:
    """Test integration between MCP tool and underlying context generation."""
    
    def test_meta_prompt_passed_to_context_generation(self):
        """Test that meta prompt is correctly passed to context generation function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_meta_prompt = "Custom review instructions for this project"
            
            with patch('src.server.generate_meta_prompt') as mock_generate_meta:
                with patch('src.server.generate_review_context') as mock_generate_context:
                    mock_generate_meta.return_value = {
                        "generated_prompt": test_meta_prompt,
                        "template_used": "default",
                        "configuration_included": True,
                        "analysis_completed": True,
                        "context_analyzed": 1200
                    }
                    
                    mock_generate_context.return_value = (f"{temp_dir}/context.md", None)
                    
                    from src.server import generate_code_review_context
                    
                    result = generate_code_review_context(
                        project_path=temp_dir,
                        scope="full_project",
                        auto_meta_prompt=True,
                        temperature=0.7,
                        text_output=False
                    )
                    
                    # Verify meta prompt generation called with correct parameters
                    mock_generate_meta.assert_called_once_with(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    # Verify context generation called with meta prompt content
                    mock_generate_context.assert_called_once()
                    call_kwargs = mock_generate_context.call_args[1]
                    assert call_kwargs['project_path'] == temp_dir
                    assert call_kwargs['scope'] == "full_project"
                    assert call_kwargs['temperature'] == 0.7
                    assert call_kwargs['auto_prompt_content'] == test_meta_prompt
    
    def test_all_mcp_parameters_passed_through(self):
        """Test that all MCP tool parameters are correctly passed to underlying functions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.server.generate_meta_prompt') as mock_generate_meta:
                with patch('src.server.generate_review_context') as mock_generate_context:
                    mock_generate_meta.return_value = {
                        "generated_prompt": "Test prompt",
                        "template_used": "default", 
                        "configuration_included": True,
                        "analysis_completed": True,
                        "context_analyzed": 1000
                    }
                    
                    mock_generate_context.return_value = (f"{temp_dir}/context.md", None)
                    
                    from src.server import generate_code_review_context
                    
                    # Call with all parameters
                    result = generate_code_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number="2.0",
                        task_number="2.1",
                        current_phase="2.0",
                        output_path=f"{temp_dir}/custom-output.md",
                        enable_gemini_review=True,
                        temperature=0.3,
                        include_claude_memory=False,
                        include_cursor_rules=True,
                        raw_context_only=True,
                        auto_meta_prompt=True,
                        text_output=False
                    )
                    
                    # Verify all parameters passed correctly
                    call_kwargs = mock_generate_context.call_args[1]
                    assert call_kwargs['project_path'] == temp_dir
                    assert call_kwargs['scope'] == "specific_phase"
                    assert call_kwargs['phase_number'] == "2.0"
                    assert call_kwargs['task_number'] == "2.1"
                    assert call_kwargs['phase'] == "2.0"  # current_phase -> phase
                    assert call_kwargs['output'] == f"{temp_dir}/custom-output.md"  # output_path -> output
                    assert call_kwargs['enable_gemini_review'] is True
                    assert call_kwargs['temperature'] == 0.3
                    assert call_kwargs['include_claude_memory'] is False
                    assert call_kwargs['include_cursor_rules'] is True
                    assert call_kwargs['raw_context_only'] is True
                    assert call_kwargs['auto_prompt_content'] == "Test prompt"


class TestTypeLevel:
    """Type-level tests to ensure type safety."""
    
    def test_auto_meta_prompt_parameter_type(self):
        """Test that auto_meta_prompt parameter has correct type."""
        from src.server import generate_code_review_context
        import inspect
        from typing import get_type_hints
        
        # Get type hints
        hints = get_type_hints(generate_code_review_context)
        
        # auto_meta_prompt should be bool type
        if 'auto_meta_prompt' in hints:
            assert hints['auto_meta_prompt'] == bool, "auto_meta_prompt should be bool type"
    
    def test_return_type_unchanged(self):
        """Test that return type remains str when auto_meta_prompt added."""
        from src.server import generate_code_review_context
        import inspect
        from typing import get_type_hints
        
        hints = get_type_hints(generate_code_review_context)
        assert hints['return'] == str, "Return type should remain str"