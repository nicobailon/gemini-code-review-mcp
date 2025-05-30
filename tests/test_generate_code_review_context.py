"""
Tests for generate_code_review_context.py

Following test-driven development approach - write tests first,
then implement functionality to make tests pass.
"""
import pytest
from unittest.mock import patch, mock_open
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import will fail initially - that's expected in TDD
try:
    from generate_code_review_context import (
        parse_task_list,
        detect_current_phase,
        extract_prd_summary,
        get_changed_files,
        generate_file_tree,
        format_review_template
    )
except ImportError:
    # Expected during TDD - tests define the interface
    pass


class TestTaskListParser:
    """Test task list parsing functionality."""
    
    def test_parse_task_list_with_completed_phase(self):
        """Test parsing task list and identifying most recently completed phase."""
        content = """
- [x] 1.0 Phase One
  - [x] 1.1 Subtask one
  - [x] 1.2 Subtask two
- [x] 2.0 Phase Two  
  - [x] 2.1 Subtask one
  - [x] 2.2 Subtask two
  - [x] 2.3 Subtask three
- [ ] 3.0 Phase Three
  - [ ] 3.1 Subtask one
"""
        result = parse_task_list(content)
        
        assert result['total_phases'] == 3
        assert result['current_phase_number'] == '2.0'  # Most recently completed
        assert result['previous_phase_completed'] == '1.0 Phase One'
        assert result['next_phase'] == '3.0 Phase Three'
        assert result['current_phase_description'] == 'Phase Two'
        # Implementation now includes descriptions with numbers
        assert len(result['subtasks_completed']) == 3
        assert all('2.' in task for task in result['subtasks_completed'])
    
    def test_parse_task_list_all_phases_complete(self):
        """Test when all phases are complete."""
        content = """
- [x] 1.0 Phase One
  - [x] 1.1 Subtask one
- [x] 2.0 Phase Two
  - [x] 2.1 Subtask one
  - [x] 2.2 Subtask two
"""
        result = parse_task_list(content)
        
        assert result['total_phases'] == 2
        assert result['current_phase_number'] == '2.0'  # Last phase when all complete
        assert result['current_phase_description'] == 'Phase Two'
        # Implementation now includes descriptions with numbers
        assert len(result['subtasks_completed']) == 2
        assert all('2.' in task for task in result['subtasks_completed'])
    
    def test_parse_task_list_with_nested_subtasks(self):
        """Test handling nested subtask levels."""
        content = """
- [ ] 1.0 Phase One
  - [x] 1.1 Subtask one
    - [x] 1.1.1 Sub-subtask
  - [ ] 1.2 Subtask two
"""
        result = parse_task_list(content)
        
        assert result['current_phase_number'] == '1.0'
        # Implementation now includes descriptions with numbers
        assert len(result['subtasks_completed']) == 1
        assert '1.1' in result['subtasks_completed'][0]
    
    def test_detect_most_recently_completed_phase(self):
        """Test detection of most recently completed phase for review."""
        phases = [
            {'number': '1.0', 'completed': True, 'subtasks_complete': True, 'subtasks': ['1.1'], 'subtasks_completed': ['1.1'], 'description': 'Phase One'},
            {'number': '2.0', 'completed': True, 'subtasks_complete': True, 'subtasks': ['2.1', '2.2'], 'subtasks_completed': ['2.1', '2.2'], 'description': 'Phase Two'},
            {'number': '3.0', 'completed': False, 'subtasks_complete': False, 'subtasks': ['3.1'], 'subtasks_completed': [], 'description': 'Phase Three'}
        ]
        
        current = detect_current_phase(phases)
        assert current['current_phase_number'] == '2.0'  # Most recently completed
        assert current['current_phase_description'] == 'Phase Two'
        assert current['subtasks_completed'] == ['2.1', '2.2']
    
    def test_detect_fallback_to_in_progress_phase(self):
        """Test fallback to in-progress phase when no phases are complete."""
        phases = [
            {'number': '1.0', 'completed': False, 'subtasks_complete': False, 'subtasks': ['1.1'], 'subtasks_completed': ['1.1'], 'description': 'Phase One'},
            {'number': '2.0', 'completed': False, 'subtasks_complete': False, 'subtasks': ['2.1'], 'subtasks_completed': [], 'description': 'Phase Two'}
        ]
        
        current = detect_current_phase(phases)
        assert current['current_phase_number'] == '1.0'  # First incomplete phase


class TestPRDParser:
    """Test PRD parsing functionality."""
    
    def test_extract_explicit_summary(self):
        """Test extracting summary when explicitly marked."""
        content = """
# Project PRD

## Summary
This project implements an MCP server for code review context generation. It automates the creation of review templates.

## Goals
...
"""
        summary = extract_prd_summary(content)
        expected = "This project implements an MCP server for code review context generation. It automates the creation of review templates."
        assert summary == expected
    
    def test_extract_overview_section(self):
        """Test extracting from Overview section."""
        content = """
# Project PRD

## Overview
This tool automates code review processes. It integrates with git and MCP.

## Technical Details
...
"""
        summary = extract_prd_summary(content)
        expected = "This tool automates code review processes. It integrates with git and MCP."
        assert summary == expected
    
    def test_generate_summary_fallback(self):
        """Test fallback when no summary section exists."""
        content = """
# Project PRD

This is the first paragraph that should be used as fallback summary when no explicit summary section is found.

## Technical Details
More details here...
"""
        summary = extract_prd_summary(content)
        expected = "This is the first paragraph that should be used as fallback summary when no explicit summary section is found."
        assert summary == expected
    
    @patch('google.genai.Client')
    def test_llm_summary_generation(self, mock_genai):
        """Test LLM-based summary generation when available."""
        # Mock Gemini response
        mock_client = mock_genai.return_value
        mock_response = mock_client.models.generate_content.return_value
        mock_response.text = "Generated summary from LLM."
        
        content = "# PRD\n\nLong content without clear summary section..."
        
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
            summary = extract_prd_summary(content)
            assert summary == "Generated summary from LLM."


class TestGitOperations:
    """Test git operations functionality."""
    
    @patch('subprocess.run')
    def test_get_changed_files_mock(self, mock_run):
        """Test git diff parsing with mocked subprocess."""
        # Mock git diff --name-status output
        mock_run.return_value.stdout = "M\tsrc/parser.py\nA\tsrc/new_file.py\nD\told_file.py"
        mock_run.return_value.returncode = 0
        
        # Mock git show output for file content
        def side_effect(*args, **kwargs):
            if 'show' in args[0]:
                if 'src/parser.py' in args[0]:
                    mock_run.return_value.stdout = "def parse_task_list():\n    pass"
                elif 'src/new_file.py' in args[0]:
                    mock_run.return_value.stdout = "# New file content"
            return mock_run.return_value
        
        mock_run.side_effect = side_effect
        
        result = get_changed_files("/test/project")
        
        assert len(result) == 3
        assert result[0]['path'] == 'src/parser.py'
        assert result[0]['status'] == 'M'
        assert 'def parse_task_list' in result[0]['content']
    
    @patch('subprocess.run')
    def test_handle_no_git_repository(self, mock_run):
        """Test graceful handling when not in git repo."""
        # Mock git command failure
        mock_run.side_effect = FileNotFoundError("git command not found")
        
        result = get_changed_files("/not/a/git/repo")
        assert result == []  # Should return empty list, not crash
    
    @patch('subprocess.run')
    def test_handle_binary_files(self, mock_run):
        """Test handling of binary files in git diff."""
        mock_run.return_value.stdout = "M\timage.png\nM\tsrc/code.py"
        mock_run.return_value.returncode = 0
        
        def side_effect(*args, **kwargs):
            if 'show' in args[0]:
                if 'image.png' in args[0]:
                    # Simulate binary file error
                    mock_run.return_value.returncode = 1
                    mock_run.return_value.stderr = "binary file"
                else:
                    mock_run.return_value.stdout = "code content"
                    mock_run.return_value.returncode = 0
            return mock_run.return_value
        
        mock_run.side_effect = side_effect
        
        result = get_changed_files("/test/project")
        
        # Should handle binary files gracefully
        binary_file = next((f for f in result if f['path'] == 'image.png'), None)
        assert binary_file is not None
        assert binary_file['content'] == "[Binary file]"


class TestFileTreeGenerator:
    """Test file tree generation functionality."""
    
    @patch('os.walk')
    @patch('os.path.isdir')
    def test_generate_file_tree_basic(self, mock_isdir, mock_walk):
        """Test basic file tree generation."""
        # Mock directory structure
        mock_walk.return_value = [
            ('/test/project', ['src', 'tests'], ['README.md']),
            ('/test/project/src', [], ['parser.py', 'server.py']),
            ('/test/project/tests', [], ['test_parser.py'])
        ]
        mock_isdir.return_value = True
        
        result = generate_file_tree("/test/project")
        
        expected_lines = [
            "/test/project",
            "├── src/",
            "│   ├── parser.py",
            "│   └── server.py",
            "├── tests/",
            "│   └── test_parser.py",
            "└── README.md"
        ]
        
        for line in expected_lines:
            assert line in result
    
    @patch('os.walk')
    @patch('builtins.open', new_callable=mock_open, read_data="*.pyc\n__pycache__/\n")
    def test_file_tree_respects_gitignore(self, mock_file, mock_walk):
        """Test that gitignore patterns are respected."""
        mock_walk.return_value = [
            ('/test/project', ['src', '__pycache__'], ['README.md', '.gitignore']),
            ('/test/project/src', [], ['parser.py', 'cache.pyc'])
        ]
        
        result = generate_file_tree("/test/project")
        
        # Should exclude gitignore patterns
        assert '__pycache__' not in result
        assert 'cache.pyc' not in result
        assert 'parser.py' in result


class TestTemplateFormatter:
    """Test template formatting functionality."""
    
    def test_format_review_template(self):
        """Test complete template formatting."""
        data = {
            'prd_summary': 'Test summary for review context.',
            'total_phases': 3,
            'current_phase_number': '2.0',
            'previous_phase_completed': '1.0 Setup phase',
            'next_phase': '3.0 Integration phase',
            'current_phase_description': 'Implementation phase',
            'subtasks_completed': ['2.1', '2.2'],
            'project_path': '/test/project',
            'file_tree': 'mock tree',
            'changed_files': [
                {'path': 'src/test.py', 'content': 'test content', 'status': 'M'}
            ]
        }
        
        result = format_review_template(data)
        
        # Check key template components (updated for current XML-style format)
        assert '<overall_prd_summary>' in result
        assert 'Test summary for review context.' in result
        assert '<total_phases>' in result
        assert '<current_phase_number>' in result
        assert '<file_tree>' in result
        assert '</file_tree>' in result
        assert '<files_changed>' in result
        assert '</files_changed>' in result
        assert '<user_instructions>' in result


class TestMainFunctionBehavior:
    """Test main function behavior and output."""
    
    @patch('generate_code_review_context.find_project_files')
    @patch('generate_code_review_context.get_changed_files')
    @patch('generate_code_review_context.generate_file_tree')
    @patch('builtins.print')  # Mock print to avoid output during tests
    def test_main_returns_tuple_with_context_and_gemini_paths(self, mock_print, mock_tree, mock_files, mock_find):
        """Test that main function returns tuple of (context_path, gemini_path)."""
        import tempfile
        import os
        from generate_code_review_context import main
        
        # Mock dependencies
        mock_find.return_value = (None, None)  # No PRD/task files
        mock_files.return_value = []
        mock_tree.return_value = "mock tree"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test without Gemini review
            context_file, gemini_file = main(
                project_path=temp_dir,
                enable_gemini_review=False
            )
            
            # Should return context file path and None for gemini
            assert isinstance(context_file, str)
            assert os.path.exists(context_file)
            assert gemini_file is None
    
    @patch('generate_code_review_context.find_project_files')
    @patch('generate_code_review_context.get_changed_files')
    @patch('generate_code_review_context.generate_file_tree') 
    @patch('generate_code_review_context.send_to_gemini_for_review')
    @patch('builtins.print')
    def test_main_returns_both_files_when_gemini_succeeds(self, mock_print, mock_gemini, mock_tree, mock_files, mock_find):
        """Test that main returns both files when Gemini review succeeds."""
        import tempfile
        import os
        from generate_code_review_context import main
        
        # Mock dependencies
        mock_find.return_value = (None, None)
        mock_files.return_value = []
        mock_tree.return_value = "mock tree"
        mock_gemini.return_value = "/path/to/gemini_review.md"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file, gemini_file = main(
                project_path=temp_dir,
                enable_gemini_review=True
            )
            
            # Should return both file paths
            assert isinstance(context_file, str)
            assert os.path.exists(context_file)
            assert gemini_file == "/path/to/gemini_review.md"
    
    @patch('generate_code_review_context.find_project_files')
    @patch('generate_code_review_context.get_changed_files')
    @patch('generate_code_review_context.generate_file_tree')
    @patch('generate_code_review_context.send_to_gemini_for_review')
    @patch('builtins.print')
    def test_main_handles_gemini_failure_gracefully(self, mock_print, mock_gemini, mock_tree, mock_files, mock_find):
        """Test that main handles Gemini failure gracefully."""
        import tempfile
        import os
        from generate_code_review_context import main
        
        # Mock dependencies with Gemini failure
        mock_find.return_value = (None, None)
        mock_files.return_value = []
        mock_tree.return_value = "mock tree" 
        mock_gemini.return_value = None  # Gemini failed
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file, gemini_file = main(
                project_path=temp_dir,
                enable_gemini_review=True
            )
            
            # Should still return context file, but gemini_file should be None
            assert isinstance(context_file, str)
            assert os.path.exists(context_file)
            assert gemini_file is None
    
    def test_main_validates_scope_parameters(self):
        """Test that main function validates scope-specific parameters."""
        from generate_code_review_context import main
        
        # Test specific_phase without phase_number
        with pytest.raises(ValueError, match="phase_number is required"):
            main(
                project_path="/tmp",
                scope="specific_phase"
                # Missing phase_number
            )
        
        # Test specific_task without task_number  
        with pytest.raises(ValueError, match="task_number is required"):
            main(
                project_path="/tmp",
                scope="specific_task"
                # Missing task_number
            )
    
    def test_main_validates_phase_number_format(self):
        """Test that main validates phase number format."""
        from generate_code_review_context import main
        
        # Test invalid phase number format
        with pytest.raises(ValueError, match="Invalid phase_number format"):
            main(
                project_path="/tmp",
                scope="specific_phase",
                phase_number="1.1"  # Should be X.0 format
            )
    
    def test_main_validates_task_number_format(self):
        """Test that main validates task number format.""" 
        from generate_code_review_context import main
        
        # Test invalid task number format
        with pytest.raises(ValueError, match="Invalid task_number format"):
            main(
                project_path="/tmp", 
                scope="specific_task",
                task_number="1.0"  # Should be X.Y format (not X.0)
            )


if __name__ == "__main__":
    pytest.main([__file__])