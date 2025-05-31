"""
Test suite for ensuring auto meta prompt creates only one context file.

Following TDD Protocol: Writing tests first to define expected behavior.
The issue is that auto_meta_prompt currently creates two files:
1. Initial context file without meta prompt
2. Final context file with meta prompt

Expected behavior: Only create ONE final context file with meta prompt embedded.
"""

import pytest
from unittest.mock import patch, Mock, mock_open
import tempfile
import os
import glob
from pathlib import Path
from typing import List, Dict, Any


class TestSingleFileAutoPrompt:
    """Test that auto meta prompt creates only one context file."""
    
    def test_mcp_tool_auto_prompt_creates_single_file(self):
        """Test MCP tool with auto_meta_prompt=True creates only one context file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create minimal project structure
            Path(temp_dir, "src").mkdir()
            Path(temp_dir, "CLAUDE.md").write_text("# Test project guidelines")
            
            # Track all file creation operations
            created_files = []
            original_open = open
            
            def track_file_creation(filename, mode='r', **kwargs):
                if 'w' in mode and 'context' in str(filename).lower():
                    created_files.append(str(filename))
                    # Return mock file for writing
                    return mock_open().return_value
                else:
                    # Allow normal read operations
                    return original_open(filename, mode, **kwargs)
            
            with patch('builtins.open', side_effect=track_file_creation):
                with patch('src.server.generate_meta_prompt') as mock_meta_prompt:
                    with patch('src.server.generate_review_context') as mock_context:
                        # Mock meta prompt generation
                        test_meta_prompt = "Custom review instructions for this project"
                        mock_meta_prompt.return_value = {
                            "generated_prompt": test_meta_prompt,
                            "template_used": "default",
                            "configuration_included": True,
                            "analysis_completed": True,
                            "context_analyzed": 1500
                        }
                        
                        # Mock context generation to return single file
                        final_context_file = f"{temp_dir}/context-with-meta-prompt.md"
                        mock_context.return_value = (final_context_file, None)
                        
                        from src.server import generate_code_review_context
                        
                        result = generate_code_review_context(
                            project_path=temp_dir,
                            auto_meta_prompt=True,
                            text_output=False
                        )
                        
                        # Verify only ONE context file was created
                        context_files = [f for f in created_files if 'context' in f.lower()]
                        assert len(context_files) == 1, f"Expected 1 context file, but {len(context_files)} were created: {context_files}"
                        
                        # Verify meta prompt generation was called once
                        mock_meta_prompt.assert_called_once()
                        
                        # Verify context generation was called once with meta prompt
                        mock_context.assert_called_once()
                        call_kwargs = mock_context.call_args[1]
                        assert call_kwargs.get('auto_prompt_content') == test_meta_prompt
    
    def test_mcp_tool_auto_prompt_file_contains_meta_prompt(self):
        """Test that the single context file contains meta prompt in user_instructions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "CLAUDE.md").write_text("# Project guidelines")
            
            test_meta_prompt = """You are a specialized code reviewer for this project.
Focus on:
- Type safety violations
- Security vulnerabilities  
- Performance issues"""
            
            # Mock file content storage
            file_contents = {}
            
            def mock_write_file(filename, mode='r', **kwargs):
                if 'w' in mode:
                    file_obj = mock_open().return_value
                    file_obj.write = lambda content: file_contents.update({filename: content})
                    return file_obj
                else:
                    return open(filename, mode, **kwargs)
            
            with patch('builtins.open', side_effect=mock_write_file):
                with patch('src.server.generate_meta_prompt') as mock_meta_prompt:
                    with patch('src.server.generate_review_context') as mock_context:
                        mock_meta_prompt.return_value = {
                            "generated_prompt": test_meta_prompt,
                            "template_used": "default",
                            "configuration_included": True,
                            "analysis_completed": True,
                            "context_analyzed": 1200
                        }
                        
                        # Mock context generation to write file with meta prompt
                        def context_side_effect(*args, **kwargs):
                            if 'auto_prompt_content' in kwargs:
                                context_content = f"""# Code Review Context

<user_instructions>
{kwargs['auto_prompt_content']}
</user_instructions>

<configuration_context>
# Project configuration
</configuration_context>

<files_changed>
# Changed files
</files_changed>"""
                                file_contents['final_context.md'] = context_content
                            return ('final_context.md', None)
                        
                        mock_context.side_effect = context_side_effect
                        
                        from src.server import generate_code_review_context
                        
                        result = generate_code_review_context(
                            project_path=temp_dir,
                            auto_meta_prompt=True,
                            text_output=False
                        )
                        
                        # Verify the file contains meta prompt in user_instructions
                        assert 'final_context.md' in file_contents
                        content = file_contents['final_context.md']
                        
                        assert '<user_instructions>' in content
                        assert '</user_instructions>' in content
                        assert 'specialized code reviewer for this project' in content
                        assert 'Type safety violations' in content
                        assert 'Security vulnerabilities' in content
    
    def test_no_intermediate_files_created(self):
        """Test that no intermediate context files are created during auto prompt process."""
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "CLAUDE.md").write_text("# Test")
            
            # Track all file operations by filename patterns
            all_file_operations = []
            
            def track_all_files(filename, mode='r', **kwargs):
                operation_info = {
                    'filename': str(filename),
                    'mode': mode,
                    'is_context_file': 'context' in str(filename).lower(),
                    'is_write': 'w' in mode
                }
                all_file_operations.append(operation_info)
                
                if 'w' in mode:
                    return mock_open().return_value
                else:
                    return open(filename, mode, **kwargs)
            
            with patch('builtins.open', side_effect=track_all_files):
                with patch('src.server.generate_meta_prompt') as mock_meta_prompt:
                    with patch('src.server.generate_review_context') as mock_context:
                        mock_meta_prompt.return_value = {
                            "generated_prompt": "Test meta prompt",
                            "template_used": "default",
                            "configuration_included": True,
                            "analysis_completed": True,
                            "context_analyzed": 800
                        }
                        
                        mock_context.return_value = (f"{temp_dir}/final-context.md", None)
                        
                        from src.server import generate_code_review_context
                        
                        result = generate_code_review_context(
                            project_path=temp_dir,
                            auto_meta_prompt=True,
                            text_output=False
                        )
                        
                        # Check how many context files were written to
                        context_write_operations = [
                            op for op in all_file_operations 
                            if op['is_context_file'] and op['is_write']
                        ]
                        
                        assert len(context_write_operations) <= 1, (
                            f"Expected at most 1 context file write operation, "
                            f"but found {len(context_write_operations)}: "
                            f"{[op['filename'] for op in context_write_operations]}"
                        )
    
    def test_mcp_tool_without_auto_prompt_unchanged(self):
        """Test that normal operation without auto_meta_prompt is unchanged."""
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "CLAUDE.md").write_text("# Test")
            
            created_files = []
            
            def track_files(filename, mode='r', **kwargs):
                if 'w' in mode and 'context' in str(filename).lower():
                    created_files.append(str(filename))
                    return mock_open().return_value
                else:
                    return open(filename, mode, **kwargs)
            
            with patch('builtins.open', side_effect=track_files):
                with patch('src.server.generate_meta_prompt') as mock_meta_prompt:
                    with patch('src.server.generate_review_context') as mock_context:
                        mock_context.return_value = (f"{temp_dir}/normal-context.md", None)
                        
                        from src.server import generate_code_review_context
                        
                        # Call without auto_meta_prompt (should be default behavior)
                        result = generate_code_review_context(
                            project_path=temp_dir,
                            auto_meta_prompt=False,
                            text_output=False
                        )
                        
                        # Meta prompt should NOT be called
                        mock_meta_prompt.assert_not_called()
                        
                        # Context generation should be called once without meta prompt
                        mock_context.assert_called_once()
                        call_kwargs = mock_context.call_args[1]
                        assert call_kwargs.get('auto_prompt_content') is None


class TestCLIAutoPromptConsistency:
    """Test that CLI auto-prompt follows same single-file logic."""
    
    def test_cli_auto_prompt_creates_single_file(self):
        """Test CLI with --auto-prompt creates only one context file."""
        # This test documents expected CLI behavior
        # CLI should follow the same optimized logic as MCP tool
        
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "CLAUDE.md").write_text("# CLI test")
            
            # Mock the CLI execution path
            created_files = []
            
            def track_cli_files(filename, mode='r', **kwargs):
                if 'w' in mode and 'context' in str(filename).lower():
                    created_files.append(str(filename))
                    return mock_open().return_value
                else:
                    return open(filename, mode, **kwargs)
            
            with patch('builtins.open', side_effect=track_cli_files):
                # This will test the CLI path once we implement the fix
                # For now, just document the expected behavior
                
                # Expected: CLI with --auto-prompt should create only one file
                # Expected: That file should contain meta prompt in user_instructions
                # Expected: No intermediate files should be created
                
                # The implementation should ensure:
                # 1. generate_meta_prompt doesn't create context files
                # 2. context creation happens once with meta prompt embedded
                # 3. Both CLI and MCP tool use same optimized logic
                
                pass
    
    def test_cli_and_mcp_tool_consistency(self):
        """Test that CLI and MCP tool produce identical results."""
        # This test ensures both paths follow the same logic
        # and produce the same output format and file structure
        
        # Expected behavior:
        # 1. Same number of files created (one)
        # 2. Same content structure in the context file
        # 3. Same meta prompt embedding in user_instructions
        # 4. Same performance characteristics (no duplication)
        
        pass


class TestPerformanceOptimization:
    """Test performance aspects of the single-file approach."""
    
    def test_no_duplicate_project_analysis(self):
        """Test that project analysis happens only once when auto_meta_prompt=True."""
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "CLAUDE.md").write_text("# Performance test")
            
            # Track expensive operations that should happen only once
            analysis_calls = []
            
            def track_analysis(*args, **kwargs):
                analysis_calls.append({'args': args, 'kwargs': kwargs})
                return "mock analysis result"
            
            # This test will verify that:
            # 1. Project discovery happens once
            # 2. File tree generation happens once  
            # 3. Git diff extraction happens once
            # 4. Configuration parsing happens once
            
            # After fix: all analysis should happen once and feed both
            # meta prompt generation and context file creation
            
            pass
    
    def test_memory_efficiency(self):
        """Test that the optimized approach uses memory efficiently."""
        # This test will verify that:
        # 1. Context data is reused between meta prompt generation and file creation
        # 2. No duplicate data structures are created
        # 3. Large context content is not duplicated in memory
        
        pass


class TestEdgeCases:
    """Test edge cases for single-file auto prompt behavior."""
    
    def test_meta_prompt_generation_failure_cleanup(self):
        """Test that if meta prompt generation fails, no partial files are left."""
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "CLAUDE.md").write_text("# Error test")
            
            created_files = []
            
            def track_files(filename, mode='r', **kwargs):
                if 'w' in mode and 'context' in str(filename).lower():
                    created_files.append(str(filename))
                    return mock_open().return_value
                else:
                    return open(filename, mode, **kwargs)
            
            with patch('builtins.open', side_effect=track_files):
                with patch('src.server.generate_meta_prompt') as mock_meta_prompt:
                    # Mock meta prompt generation failure
                    mock_meta_prompt.side_effect = Exception("API key not configured")
                    
                    from src.server import generate_code_review_context
                    
                    result = generate_code_review_context(
                        project_path=temp_dir,
                        auto_meta_prompt=True,
                        text_output=False
                    )
                    
                    # Should return error message
                    assert isinstance(result, str)
                    assert result.startswith("ERROR:")
                    
                    # Should not have created any context files
                    assert len(created_files) == 0, f"No files should be created on error, but found: {created_files}"
    
    def test_empty_meta_prompt_handling(self):
        """Test handling when meta prompt generation returns empty content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "CLAUDE.md").write_text("# Empty test")
            
            with patch('src.server.generate_meta_prompt') as mock_meta_prompt:
                # Mock empty meta prompt response
                mock_meta_prompt.return_value = {
                    "generated_prompt": "",  # Empty prompt
                    "template_used": "default",
                    "configuration_included": False,
                    "analysis_completed": True,
                    "context_analyzed": 0
                }
                
                from src.server import generate_code_review_context
                
                result = generate_code_review_context(
                    project_path=temp_dir,
                    auto_meta_prompt=True,
                    text_output=False
                )
                
                # Should return error for empty meta prompt
                assert isinstance(result, str)
                assert result.startswith("ERROR:")
                assert "no content generated" in result.lower()


class TestTypeLevel:
    """Type-level tests for single-file auto prompt behavior."""
    
    def test_return_type_consistency(self):
        """Test that return types are consistent between auto_meta_prompt modes."""
        from src.server import generate_code_review_context
        import inspect
        from typing import get_type_hints
        
        # Function should have same return type regardless of auto_meta_prompt value
        hints = get_type_hints(generate_code_review_context)
        assert hints['return'] == str, "Return type should always be str"
    
    def test_parameter_type_validation(self):
        """Test that auto_meta_prompt parameter has correct type validation."""
        from src.server import generate_code_review_context
        import inspect
        
        sig = inspect.signature(generate_code_review_context)
        auto_meta_prompt_param = sig.parameters['auto_meta_prompt']
        
        # Should be boolean type with False default
        assert auto_meta_prompt_param.annotation == bool
        assert auto_meta_prompt_param.default is False