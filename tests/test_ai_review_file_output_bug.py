#!/usr/bin/env python3
"""
TDD test to reproduce the exact bug: generate_ai_code_review with text_output=false 
should create a .md file but currently doesn't.

EXPECTED BEHAVIOR:
- Call generate_ai_code_review(project_path=X, text_output=false)
- Should create code-review-ai-feedback-YYYYMMDD-HHMMSS.md file
- Should return message with file path

ACTUAL BEHAVIOR (BUG):
- Returns "Successfully generated AI code review from content:" (no file path)
- No .md file is created
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# Import the MCP tool function
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from server import generate_ai_code_review


def test_real_generate_ai_code_review_text_output_false_creates_file():
    """
    TDD Test: generate_ai_code_review with text_output=false should create .md file.
    
    This test replicates the EXACT call that's failing in the MCP tool.
    It should FAIL until we fix the bug.
    """
    
    # Set up real test project directory (not mocked)
    test_project_dir = tempfile.mkdtemp()
    
    try:
        # Create minimal project structure
        os.makedirs(os.path.join(test_project_dir, 'src'), exist_ok=True)
        
        # Create a simple Python file
        test_file = os.path.join(test_project_dir, 'src', 'example.py')
        with open(test_file, 'w') as f:
            f.write("""
def hello_world():
    print("Hello, World!")

class Calculator:
    def add(self, a, b):
        return a + b
""")
        
        # Create tasks directory with task file for meta prompt generation
        task_file = os.path.join(test_project_dir, 'tasks', 'example-tasks.md')
        os.makedirs(os.path.dirname(task_file), exist_ok=True)
        with open(task_file, 'w') as f:
            f.write("""
## Tasks
- [x] 1.0 Create hello world function
- [x] 2.0 Create Calculator class
  - [x] 2.1 Add addition method
""")
        
        # Track files before the call
        files_before = set(Path(test_project_dir).rglob('*.md'))
        
        # Make the EXACT call that's failing
        result = generate_ai_code_review(
            project_path=test_project_dir,
            text_output=False  # This should create a .md file
        )
        
        # Track files after the call
        files_after = set(Path(test_project_dir).rglob('*.md'))
        new_files = files_after - files_before
        
        # DEBUG: Print what actually happened
        print(f"Result: {result}")
        print(f"Files before: {files_before}")
        print(f"Files after: {files_after}")
        print(f"New files: {new_files}")
        
        # EXPECTED BEHAVIOR (this should pass when bug is fixed)
        
        # 1. Should create exactly one AI review file
        ai_review_files = [f for f in new_files if 'ai' in f.name.lower() and 'feedback' in f.name.lower()]
        assert len(ai_review_files) == 1, f"Expected exactly 1 AI review file, found: {new_files}"
        
        ai_review_file = ai_review_files[0]
        
        # 2. File should follow naming convention
        import re
        expected_pattern = r'code-review-ai-feedback-\d{8}-\d{6}\.md'
        assert re.match(expected_pattern, ai_review_file.name), \
            f"AI review file should match pattern {expected_pattern}, got: {ai_review_file.name}"
        
        # 3. File should contain actual AI review content
        with open(ai_review_file, 'r') as f:
            file_content = f.read()
        assert len(file_content) > 100, "AI review file should contain substantial content"
        assert "review" in file_content.lower(), "AI review file should contain review content"
        
        # 4. Response should indicate file was created with path
        assert isinstance(result, str), "Should return string message"
        assert "Successfully generated AI code review:" in result, "Should indicate success with file"
        assert str(ai_review_file) in result, "Should include the file path in response"
        assert "from content:" not in result, "Should NOT say 'from content' when file is created"
        
    finally:
        # Clean up
        if os.path.exists(test_project_dir):
            shutil.rmtree(test_project_dir)


if __name__ == "__main__":
    # Run the test to see current failing behavior
    print("Running TDD test: test_real_generate_ai_code_review_text_output_false_creates_file")
    try:
        test_real_generate_ai_code_review_text_output_false_creates_file()
        print("✅ PASS: Test passed (bug is fixed!)")
    except Exception as e:
        print(f"❌ FAIL: {e}")
        print("This test should FAIL until we fix the bug")
        print("The bug: text_output=false should create .md file but doesn't")