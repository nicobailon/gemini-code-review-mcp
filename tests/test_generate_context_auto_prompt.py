"""
Test suite for auto_prompt_content parameter in generate_code_review_context_main function.

Following TDD Protocol: Writing tests first to define expected behavior.
The underlying context generation function should accept auto_prompt_content 
and embed it in the <user_instructions> section of the generated context file.
"""

import pytest
from unittest.mock import patch, Mock, mock_open
import tempfile
import os
from pathlib import Path


class TestGenerateContextAutoPrompt:
    """Test auto_prompt_content parameter in context generation."""
    
    def test_generate_context_main_accepts_auto_prompt_content(self):
        """Test that generate_code_review_context_main accepts auto_prompt_content parameter."""
        from src.generate_code_review_context import generate_code_review_context_main
        import inspect
        
        # Check function signature includes auto_prompt_content parameter
        sig = inspect.signature(generate_code_review_context_main)
        params = list(sig.parameters.keys())
        
        # Should include auto_prompt_content parameter
        assert 'auto_prompt_content' in params, f"auto_prompt_content parameter missing. Current params: {params}"
        
        # Parameter should have Optional[str] type hint and default to None
        param = sig.parameters['auto_prompt_content']
        assert param.default is None, "auto_prompt_content should default to None"
    
    def test_context_file_user_instructions_with_auto_prompt_content(self):
        """Test that auto_prompt_content is embedded in <user_instructions> section."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create minimal project structure
            project_path = Path(temp_dir)
            tasks_dir = project_path / "tasks"
            tasks_dir.mkdir()
            
            # Create a simple task file
            task_file = tasks_dir / "tasks-test.md"
            task_file.write_text("""## Tasks
- [x] 1.0 Setup project structure
  - [x] 1.1 Initialize repository
  - [x] 1.2 Add basic files
""")
            
            # Create CLAUDE.md
            claude_file = project_path / "CLAUDE.md" 
            claude_file.write_text("# Project guidelines")
            
            test_auto_prompt = """You are a meticulous code reviewer for this specific project.
Focus on these areas:
1. Type safety compliance
2. Test coverage validation
3. Security vulnerabilities"""
            
            # Mock file operations to capture written content
            written_files = {}
            
            original_open = open
            def mock_open_func(filename, mode='r', **kwargs):
                if 'w' in mode:
                    # Capture write operations
                    file_obj = mock_open().return_value
                    file_obj.write = lambda content: written_files.update({filename: content})
                    return file_obj
                else:
                    # Allow normal read operations
                    return original_open(filename, mode, **kwargs)
            
            with patch('builtins.open', side_effect=mock_open_func):
                with patch('src.generate_code_review_context.subprocess.run') as mock_subprocess:
                    # Mock git commands
                    mock_subprocess.return_value.stdout = ""
                    mock_subprocess.return_value.returncode = 0
                    
                    from src.generate_code_review_context import generate_code_review_context_main
                    
                    # Call with auto_prompt_content
                    result = generate_code_review_context_main(
                        project_path=str(project_path),
                        auto_prompt_content=test_auto_prompt,
                        enable_gemini_review=False
                    )
                    
                    # Verify a context file was written
                    context_files = [f for f in written_files.keys() if 'context' in f.lower()]
                    assert len(context_files) > 0, f"No context file written. Files: {list(written_files.keys())}"
                    
                    context_content = written_files[context_files[0]]
                    
                    # Verify auto_prompt_content is in user_instructions section
                    assert '<user_instructions>' in context_content
                    assert '</user_instructions>' in context_content
                    
                    # Extract user_instructions content
                    start_tag = '<user_instructions>'
                    end_tag = '</user_instructions>'
                    start_idx = context_content.find(start_tag) + len(start_tag)
                    end_idx = context_content.find(end_tag)
                    user_instructions = context_content[start_idx:end_idx].strip()
                    
                    # Verify auto_prompt_content is embedded
                    assert "meticulous code reviewer for this specific project" in user_instructions
                    assert "Type safety compliance" in user_instructions  
                    assert "Test coverage validation" in user_instructions
                    assert "Security vulnerabilities" in user_instructions
    
    def test_context_file_default_instructions_without_auto_prompt(self):
        """Test that default instructions are used when auto_prompt_content is None."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            tasks_dir = project_path / "tasks"
            tasks_dir.mkdir()
            
            task_file = tasks_dir / "tasks-test.md"
            task_file.write_text("""## Tasks
- [x] 1.0 Complete feature X
  - [x] 1.1 Implement core logic
""")
            
            claude_file = project_path / "CLAUDE.md"
            claude_file.write_text("# Guidelines")
            
            # Mock file operations
            written_files = {}
            
            original_open = open  
            def mock_open_func(filename, mode='r', **kwargs):
                if 'w' in mode:
                    file_obj = mock_open().return_value
                    file_obj.write = lambda content: written_files.update({filename: content})
                    return file_obj
                else:
                    return original_open(filename, mode, **kwargs)
            
            with patch('builtins.open', side_effect=mock_open_func):
                with patch('src.generate_code_review_context.subprocess.run') as mock_subprocess:
                    mock_subprocess.return_value.stdout = ""
                    mock_subprocess.return_value.returncode = 0
                    
                    from src.generate_code_review_context import generate_code_review_context_main
                    
                    # Call without auto_prompt_content (should use default instructions)
                    result = generate_code_review_context_main(
                        project_path=str(project_path),
                        auto_prompt_content=None,
                        enable_gemini_review=False
                    )
                    
                    context_files = [f for f in written_files.keys() if 'context' in f.lower()]
                    assert len(context_files) > 0
                    
                    context_content = written_files[context_files[0]]
                    
                    # Verify default instructions are used
                    assert '<user_instructions>' in context_content
                    assert '</user_instructions>' in context_content
                    
                    # Should contain default phrases, not auto-prompt content
                    user_instructions_section = context_content[
                        context_content.find('<user_instructions>'):
                        context_content.find('</user_instructions>') + len('</user_instructions>')
                    ]
                    
                    # Default instructions should mention PRD and code review
                    assert "PRD" in user_instructions_section or "code review" in user_instructions_section
                    # Should NOT contain auto-prompt specific content
                    assert "meticulous code reviewer for this specific project" not in user_instructions_section
    
    def test_auto_prompt_content_overrides_default_instructions(self):
        """Test that auto_prompt_content completely replaces default instructions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            tasks_dir = project_path / "tasks"
            tasks_dir.mkdir()
            
            task_file = tasks_dir / "tasks-test.md"
            task_file.write_text("""## Tasks  
- [x] 1.0 Test task
""")
            
            custom_instructions = "CUSTOM REVIEW INSTRUCTIONS: Focus only on security issues."
            
            written_files = {}
            
            original_open = open
            def mock_open_func(filename, mode='r', **kwargs):
                if 'w' in mode:
                    file_obj = mock_open().return_value
                    file_obj.write = lambda content: written_files.update({filename: content})
                    return file_obj
                else:
                    return original_open(filename, mode, **kwargs)
            
            with patch('builtins.open', side_effect=mock_open_func):
                with patch('src.generate_code_review_context.subprocess.run') as mock_subprocess:
                    mock_subprocess.return_value.stdout = ""
                    mock_subprocess.return_value.returncode = 0
                    
                    from src.generate_code_review_context import generate_code_review_context_main
                    
                    result = generate_code_review_context_main(
                        project_path=str(project_path),
                        auto_prompt_content=custom_instructions,
                        enable_gemini_review=False
                    )
                    
                    context_files = [f for f in written_files.keys() if 'context' in f.lower()]
                    context_content = written_files[context_files[0]]
                    
                    # Extract user_instructions
                    start_idx = context_content.find('<user_instructions>') + len('<user_instructions>')
                    end_idx = context_content.find('</user_instructions>')
                    user_instructions = context_content[start_idx:end_idx].strip()
                    
                    # Should contain ONLY the custom instructions
                    assert user_instructions == custom_instructions
                    # Should NOT contain default instruction phrases  
                    assert "Based on the PRD" not in user_instructions
                    assert "conduct a code review" not in user_instructions


class TestTypeLevel:
    """Type-level tests for auto_prompt_content parameter."""
    
    def test_auto_prompt_content_parameter_type(self):
        """Test that auto_prompt_content parameter has correct type."""
        from src.generate_code_review_context import generate_code_review_context_main
        import inspect
        from typing import get_type_hints
        
        # Get type hints
        hints = get_type_hints(generate_code_review_context_main)
        
        # auto_prompt_content should be Optional[str] type
        if 'auto_prompt_content' in hints:
            # Check if it's Optional[str] (which is Union[str, None])
            hint = hints['auto_prompt_content']
            assert hasattr(hint, '__origin__') or hint == str, "auto_prompt_content should be Optional[str]"