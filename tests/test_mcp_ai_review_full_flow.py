#!/usr/bin/env python3
"""
Test-Driven Development tests for MCP generate_ai_code_review tool full flow behavior.

Tests verify that the MCP tool:
1. Does full flow (meta prompt → context → AI review) from project_path by default
2. Only outputs final AI review file (no intermediate files created)
3. Supports optional context_file_path for existing context
4. Returns text content by default for AI agent chaining
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the MCP tool function
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from server import generate_ai_code_review


class TestMCPAIReviewFullFlow:
    """Test generate_ai_code_review MCP tool full flow behavior."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        self.test_project_dir = tempfile.mkdtemp()
        self.test_files_created = []
        
        # Create a realistic test project structure
        os.makedirs(os.path.join(self.test_project_dir, 'src'), exist_ok=True)
        os.makedirs(os.path.join(self.test_project_dir, 'tests'), exist_ok=True)
        
        # Create test files
        test_file = os.path.join(self.test_project_dir, 'src', 'example.py')
        with open(test_file, 'w') as f:
            f.write("""
def calculate_sum(a, b):
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
""")
        
        # Create task list for project analysis
        task_file = os.path.join(self.test_project_dir, 'tasks', 'test-tasks.md')
        os.makedirs(os.path.dirname(task_file), exist_ok=True)
        with open(task_file, 'w') as f:
            f.write("""
## Tasks
- [x] 1.0 Implement basic calculator
  - [x] 1.1 Add function
  - [x] 1.2 Multiply method
""")
    
    def teardown_method(self):
        """Clean up test fixtures after each test."""
        if os.path.exists(self.test_project_dir):
            shutil.rmtree(self.test_project_dir)
        
        # Clean up any created files
        for file_path in self.test_files_created:
            if os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except Exception:
                    pass

    def test_full_flow_project_path_default_behavior(self):
        """Test that project_path mode does full flow by default with no intermediate files."""
        
        # Mock the Gemini API call to return predictable content
        mock_ai_content = "Mock AI review: The code looks good with proper function definitions."
        
        with patch('generate_code_review_context.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = mock_ai_content
            
            # Track files before the call
            files_before = set(Path(self.test_project_dir).rglob('*'))
            
            # Call the MCP tool with project_path (should do full flow)
            result = generate_ai_code_review(
                project_path=self.test_project_dir
                # auto_meta_prompt=True by default
                # text_output=True by default  
            )
            
            # Track files after the call
            files_after = set(Path(self.test_project_dir).rglob('*'))
            new_files = files_after - files_before
            
            # EXPECTED BEHAVIOR: Only AI review content returned, no intermediate files created
            assert isinstance(result, str), "Should return AI review content as string"
            assert mock_ai_content in result, "Should contain AI review content"
            assert len(new_files) == 0, f"No intermediate files should be created, but found: {new_files}"
            
            # Verify Gemini was called with context that includes meta prompt
            mock_gemini.assert_called_once()
            call_args = mock_gemini.call_args
            context_content = call_args[1]['context_content']
            
            # The context should contain the default AI review instructions and project context
            assert "comprehensive code review analysis" in context_content
            assert "src/example.py" in context_content or "example.py" in context_content

    def test_context_file_path_mode_works_with_existing_file(self):
        """Test that context_file_path mode works with existing context file."""
        
        # Create a test context file
        context_file = os.path.join(self.test_project_dir, 'test-context.md')
        with open(context_file, 'w') as f:
            f.write("""
# Code Review Context

## Project: Test Project

## Files:
- src/example.py: Contains calculator functions

## Recent Changes:
- Added calculate_sum function
- Added Calculator class with multiply method
""")
        
        mock_ai_content = "Mock AI review based on provided context."
        
        with patch('generate_code_review_context.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = mock_ai_content
            
            # Call with existing context file
            result = generate_ai_code_review(
                context_file_path=context_file
            )
            
            # Should return AI review content
            assert isinstance(result, str)
            assert mock_ai_content in result
            
            # Verify Gemini was called with the context file content
            mock_gemini.assert_called_once()
            call_args = mock_gemini.call_args
            context_content = call_args[1]['context_content']
            assert "Test Project" in context_content
            assert "calculate_sum function" in context_content

    def test_context_content_mode_works_with_direct_content(self):
        """Test that context_content mode works with direct content input."""
        
        direct_content = """
# Direct Context Content

This is a test context provided directly as a string parameter.

## Code to Review:
```python
def test_function():
    return "hello world"
```
"""
        
        mock_ai_content = "Mock AI review for direct content."
        
        with patch('generate_code_review_context.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = mock_ai_content
            
            result = generate_ai_code_review(
                context_content=direct_content
            )
            
            assert isinstance(result, str)
            assert mock_ai_content in result
            
            # Verify Gemini was called with the direct content
            mock_gemini.assert_called_once()
            call_args = mock_gemini.call_args
            context_content = call_args[1]['context_content']
            assert "Direct Context Content" in context_content
            assert "test_function" in context_content

    def test_validation_exactly_one_parameter_required(self):
        """Test that exactly one input parameter is required."""
        
        # No parameters - should fail
        result = generate_ai_code_review()
        assert "ERROR:" in result
        assert "required" in result.lower()
        
        # Multiple parameters - should fail  
        context_file = os.path.join(self.test_project_dir, 'dummy.md')
        with open(context_file, 'w') as f:
            f.write("dummy content")
            
        result = generate_ai_code_review(
            context_file_path=context_file,
            project_path=self.test_project_dir
        )
        assert "ERROR:" in result
        assert "Only one" in result

    def test_auto_meta_prompt_can_be_disabled(self):
        """Test that auto_meta_prompt can be disabled for simpler context."""
        
        mock_ai_content = "Mock AI review without meta prompt."
        
        with patch('generate_code_review_context.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = mock_ai_content
            
            with patch('generate_code_review_context.generate_code_review_context_main') as mock_context_gen:
                # Mock the context generation to return dummy files
                dummy_context_file = os.path.join(self.test_project_dir, 'dummy-context.md') 
                with open(dummy_context_file, 'w') as f:
                    f.write("Basic context without meta prompt")
                mock_context_gen.return_value = (dummy_context_file, None)
                
                result = generate_ai_code_review(
                    project_path=self.test_project_dir,
                    auto_meta_prompt=False
                )
                
                # Verify meta prompt generation was NOT called
                mock_context_gen.assert_called_once()
                call_args = mock_context_gen.call_args[1]
                assert call_args.get('auto_prompt_content') is None

    def test_text_output_false_returns_formatted_message(self):
        """Test that text_output=False returns formatted message instead of raw content."""
        
        mock_ai_content = "Mock AI review content."
        
        with patch('generate_code_review_context.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = mock_ai_content
            
            result = generate_ai_code_review(
                project_path=self.test_project_dir,
                text_output=False
            )
            
            # Should return formatted message including the AI content
            assert isinstance(result, str)
            assert "Successfully generated AI code review" in result
            assert mock_ai_content in result

    def test_custom_prompt_overrides_default_instructions(self):
        """Test that custom_prompt parameter overrides default AI instructions."""
        
        custom_prompt = "Focus only on security vulnerabilities in this code."
        mock_ai_content = "Security-focused AI review."
        
        with patch('generate_code_review_context.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = mock_ai_content
            
            result = generate_ai_code_review(
                project_path=self.test_project_dir,
                custom_prompt=custom_prompt
            )
            
            # Verify custom prompt was used
            mock_gemini.assert_called_once()
            call_args = mock_gemini.call_args
            context_content = call_args[1]['context_content']
            assert custom_prompt in context_content
            assert "Focus only on security vulnerabilities" in context_content

    def test_error_handling_invalid_project_path(self):
        """Test error handling for invalid project paths."""
        
        # Non-existent path
        result = generate_ai_code_review(
            project_path="/non/existent/path"
        )
        assert "ERROR:" in result
        assert "does not exist" in result
        
        # File instead of directory
        test_file = os.path.join(self.test_project_dir, 'not_a_dir.txt')
        with open(test_file, 'w') as f:
            f.write("test")
            
        result = generate_ai_code_review(
            project_path=test_file
        )
        assert "ERROR:" in result
        assert "must be a directory" in result

    def test_error_handling_invalid_context_file(self):
        """Test error handling for invalid context files."""
        
        # Non-existent file
        result = generate_ai_code_review(
            context_file_path="/non/existent/file.md"
        )
        assert "ERROR:" in result
        assert "does not exist" in result
        
        # Directory instead of file
        result = generate_ai_code_review(
            context_file_path=self.test_project_dir
        )
        assert "ERROR:" in result
        assert "must be a file" in result

    def test_intermediate_file_cleanup_on_error(self):
        """Test that intermediate files are cleaned up even if errors occur."""
        
        with patch('generate_code_review_context.generate_code_review_context_main') as mock_context_gen:
            # Mock context generation to raise an error
            mock_context_gen.side_effect = Exception("Simulated context generation error")
            
            # Track files before the call
            files_before = set(Path(self.test_project_dir).rglob('*'))
            
            result = generate_ai_code_review(
                project_path=self.test_project_dir
            )
            
            # Should return error message
            assert "ERROR:" in result
            assert "Failed to generate context" in result
            
            # Verify no new files were left behind
            files_after = set(Path(self.test_project_dir).rglob('*'))
            new_files = files_after - files_before
            assert len(new_files) == 0, f"No files should be left behind on error, but found: {new_files}"


if __name__ == "__main__":
    # Run a key test to verify behavior
    test_instance = TestMCPAIReviewFullFlow()
    
    print("Running key test: test_full_flow_project_path_default_behavior")
    try:
        test_instance.setup_method()
        test_instance.test_full_flow_project_path_default_behavior()
        print("✅ PASS: Full flow test passed")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    finally:
        test_instance.teardown_method()
    
    print("\nRunning validation test: test_validation_exactly_one_parameter_required")
    try:
        test_instance.setup_method()
        test_instance.test_validation_exactly_one_parameter_required()
        print("✅ PASS: Validation test passed")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    finally:
        test_instance.teardown_method()