#!/usr/bin/env python3
"""
TDD tests for MCP generate_ai_code_review tool file output behavior.

EXPECTED BEHAVIOR when text_output=false:
1. Should create a timestamped .md file with AI review content
2. Should return message indicating file was created with file path
3. Should use proper naming convention: code-review-ai-feedback-YYYYMMDD-HHMMSS.md
"""

import os
import tempfile
import shutil
import re
from pathlib import Path
from unittest.mock import patch

# Import the MCP tool function
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from server import generate_ai_code_review


class TestMCPAIReviewFileOutput:
    """Test generate_ai_code_review MCP tool file output behavior."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        self.test_project_dir = tempfile.mkdtemp()
        
        # Create a realistic test project structure
        os.makedirs(os.path.join(self.test_project_dir, 'src'), exist_ok=True)
        
        # Create test file
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

    def test_text_output_false_creates_ai_review_file(self):
        """Test that text_output=false creates timestamped AI review .md file."""
        
        mock_ai_content = "# AI Code Review\n\nMock comprehensive AI review content."
        
        with patch('generate_code_review_context.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = mock_ai_content
            
            # Track files before the call
            files_before = set(Path(self.test_project_dir).rglob('*.md'))
            
            # Call the MCP tool with text_output=false
            result = generate_ai_code_review(
                project_path=self.test_project_dir,
                text_output=False  # Should create .md file
            )
            
            # Track files after the call
            files_after = set(Path(self.test_project_dir).rglob('*.md'))
            new_files = files_after - files_before
            
            # EXPECTED BEHAVIOR: Should create exactly one AI review file
            ai_review_files = [f for f in new_files if 'ai' in f.name.lower() and 'review' in f.name.lower()]
            assert len(ai_review_files) == 1, f"Expected exactly 1 AI review file, found: {new_files}"
            
            ai_review_file = ai_review_files[0]
            
            # Verify file naming convention: code-review-ai-feedback-YYYYMMDD-HHMMSS.md
            expected_pattern = r'code-review-ai-feedback-\d{8}-\d{6}\.md'
            assert re.match(expected_pattern, ai_review_file.name), \
                f"AI review file should match pattern {expected_pattern}, got: {ai_review_file.name}"
            
            # Verify file contains the AI review content
            with open(ai_review_file, 'r') as f:
                file_content = f.read()
            assert mock_ai_content in file_content, "AI review file should contain the generated review"
            
            # Verify return message includes file path
            assert isinstance(result, str), "Should return string message"
            assert "Successfully generated AI code review:" in result, "Should indicate success"
            assert str(ai_review_file) in result, "Should include the file path in response"

    def test_text_output_true_does_not_create_file(self):
        """Test that text_output=true (default) does not create any files."""
        
        mock_ai_content = "Mock AI review content for text output."
        
        with patch('generate_code_review_context.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = mock_ai_content
            
            # Track files before the call
            files_before = set(Path(self.test_project_dir).rglob('*.md'))
            
            result = generate_ai_code_review(
                project_path=self.test_project_dir,
                text_output=True  # Should NOT create files
            )
            
            # Track files after the call
            files_after = set(Path(self.test_project_dir).rglob('*.md'))
            new_files = files_after - files_before
            
            # Should not create any new files
            assert len(new_files) == 0, f"text_output=True should not create files, but found: {new_files}"
            
            # Should return content directly
            assert result == mock_ai_content, "Should return AI review content directly"


if __name__ == "__main__":
    # Run a key test to verify current failing behavior
    test_instance = TestMCPAIReviewFileOutput()
    
    print("Running TDD test: test_text_output_false_creates_ai_review_file")
    try:
        test_instance.setup_method()
        test_instance.test_text_output_false_creates_ai_review_file()
        print("✅ PASS: Test passed (unexpected - implementation might already be correct)")
    except Exception as e:
        print(f"❌ FAIL: {e}")
        print("This is expected - the test should fail until we implement the fix")
    finally:
        test_instance.teardown_method()