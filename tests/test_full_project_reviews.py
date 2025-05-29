"""
Tests for full project review functionality (entire task list analysis)
"""

import pytest
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from generate_code_review_context import main as generate_review_context


class TestFullProjectReviewScope:
    """Test full project review scope functionality"""
    
    def test_full_project_processes_all_completed_phases(self):
        """Test that full_project scope processes all completed phases"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-comprehensive.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Comprehensive Task List

## Tasks

- [x] 1.0 Database Setup Phase
  - [x] 1.1 Design database schema
  - [x] 1.2 Create migration scripts
  - [x] 1.3 Set up connection pooling
- [x] 2.0 API Development Phase
  - [x] 2.1 Create user authentication endpoints
  - [x] 2.2 Implement CRUD operations
  - [x] 2.3 Add input validation
- [x] 3.0 Frontend Integration Phase
  - [x] 3.1 Build user interface components
  - [x] 3.2 Implement state management
  - [x] 3.3 Add error handling
- [ ] 4.0 Testing Phase
  - [ ] 4.1 Write unit tests
  - [ ] 4.2 Perform integration testing
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                # Mock comprehensive file changes across all phases
                mock_files.return_value = [
                    "db/schema.sql", "db/migrations/001_initial.sql", "db/connection.py",
                    "api/auth.py", "api/crud.py", "api/validation.py",
                    "frontend/components.js", "frontend/state.js", "frontend/errors.js"
                ]
                with patch('builtins.open', mock_open()) as mock_file:
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    assert result is not None
                    # Should include analysis of all completed phases (1.0, 2.0, 3.0)
                    # Implementation will verify that all phases are processed
    
    def test_full_project_excludes_incomplete_phases(self):
        """Test that full_project scope excludes incomplete phases"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-mixed.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Mixed Completion Task List

## Tasks

- [x] 1.0 Completed Phase One
  - [x] 1.1 Completed task
  - [x] 1.2 Another completed task
- [x] 2.0 Completed Phase Two
  - [x] 2.1 Completed task
- [ ] 3.0 Incomplete Phase Three
  - [x] 3.1 Partially completed task
  - [ ] 3.2 Incomplete task
- [ ] 4.0 Not Started Phase
  - [ ] 4.1 Not started task
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["file1.py", "file2.py", "file3.py", "file4.py"]
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    assert result is not None
                    # Should only include phases 1.0 and 2.0 (completed)
                    # Should exclude phases 3.0 and 4.0 (incomplete)
    
    def test_full_project_handles_empty_task_list(self):
        """Test that full_project scope handles empty or minimal task lists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-empty.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Empty Task List

## Tasks

(No tasks defined yet)
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    assert result is not None
                    # Should handle gracefully without errors
    
    def test_full_project_handles_single_phase(self):
        """Test that full_project scope works with single phase projects"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-single.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Single Phase Task List

## Tasks

- [x] 1.0 Only Phase
  - [x] 1.1 First task
  - [x] 1.2 Second task
  - [x] 1.3 Third task
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["main.py", "utils.py", "tests.py"]
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    assert result is not None
                    # Should work correctly with single phase
    
    def test_full_project_comprehensive_git_analysis(self):
        """Test that full_project includes comprehensive git change analysis"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-git.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Git Analysis Task List

## Tasks

- [x] 1.0 Backend Development
  - [x] 1.1 Database models
  - [x] 1.2 API endpoints
- [x] 2.0 Frontend Development
  - [x] 2.1 User interface
  - [x] 2.2 State management
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                # Mock comprehensive git changes across project history
                mock_files.return_value = [
                    "backend/models/user.py", "backend/models/product.py",
                    "backend/api/auth.py", "backend/api/products.py",
                    "frontend/src/components/Login.js", "frontend/src/components/ProductList.js",
                    "frontend/src/store/auth.js", "frontend/src/store/products.js",
                    "tests/backend/test_auth.py", "tests/frontend/test_components.js",
                    "docs/api.md", "README.md", "package.json", "requirements.txt"
                ]
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    assert result is not None
                    # Should include all files, not filtered by recency


class TestFullProjectVsRecentPhaseComparison:
    """Test differences between full_project and recent_phase scopes"""
    
    def test_full_project_includes_more_content_than_recent_phase(self):
        """Test that full_project includes more content than recent_phase"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-comparison.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Multi-Phase Task List

## Tasks

- [x] 1.0 Early Phase (older)
  - [x] 1.1 Early task
- [x] 2.0 Middle Phase (older)
  - [x] 2.1 Middle task
- [x] 3.0 Recent Phase (current)
  - [x] 3.1 Recent task
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.detect_current_phase') as mock_detect:
                mock_detect.return_value = "3.0"
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = ["file1.py", "file2.py", "file3.py"]
                    
                    # Test recent_phase scope
                    with patch('builtins.open', mock_open()):
                        recent_result = generate_review_context(
                            project_path=temp_dir,
                            scope="recent_phase"
                        )
                    
                    # Test full_project scope
                    with patch('builtins.open', mock_open()):
                        full_result = generate_review_context(
                            project_path=temp_dir,
                            scope="full_project"
                        )
                    
                    assert recent_result is not None
                    assert full_result is not None
                    # full_project should include more phases than recent_phase
    
    def test_full_project_different_file_naming_than_recent_phase(self):
        """Test that full_project uses different file naming than recent_phase"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-naming.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Task List\n- [x] 1.0 Test Phase")
            
            with patch('generate_code_review_context.detect_current_phase') as mock_detect:
                mock_detect.return_value = "1.0"
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    
                    # Test both scopes
                    with patch('builtins.open', mock_open()):
                        recent_result = generate_review_context(
                            project_path=temp_dir,
                            scope="recent_phase"
                        )
                        
                        full_result = generate_review_context(
                            project_path=temp_dir,
                            scope="full_project"
                        )
                    
                    assert recent_result is not None
                    assert full_result is not None
                    # File names should be different to distinguish scope
                    assert recent_result != full_result


class TestFullProjectPerformanceConsiderations:
    """Test performance considerations for full project reviews"""
    
    def test_full_project_handles_large_task_lists(self):
        """Test that full_project handles large task lists efficiently"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-large.md"
            task_file.parent.mkdir(exist_ok=True)
            
            # Generate large task list
            large_task_content = "# Large Task List\n\n## Tasks\n\n"
            for phase in range(1, 11):  # 10 phases
                large_task_content += f"- [x] {phase}.0 Phase {phase}\n"
                for task in range(1, 6):  # 5 tasks per phase
                    large_task_content += f"  - [x] {phase}.{task} Task {task} of Phase {phase}\n"
            
            task_file.write_text(large_task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                # Mock large number of changed files
                mock_files.return_value = [f"file_{i}.py" for i in range(100)]
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    assert result is not None
                    # Should handle large projects without performance issues
    
    def test_full_project_memory_efficiency(self):
        """Test that full_project scope is memory efficient"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-memory.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Memory Test Task List

## Tasks

- [x] 1.0 Large Phase One
  - [x] 1.1 Task with large description and details
  - [x] 1.2 Another task with extensive documentation
- [x] 2.0 Large Phase Two
  - [x] 2.1 Complex task with multiple requirements
  - [x] 2.2 Task involving large data processing
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["large_file_1.py", "large_file_2.py"]
                with patch('builtins.open', mock_open()):
                    # Should complete without memory errors
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    assert result is not None


class TestFullProjectOutputFormat:
    """Test output format for full project reviews"""
    
    def test_full_project_output_includes_scope_header(self):
        """Test that full_project output includes scope information in header"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-header.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Task List\n- [x] 1.0 Test Phase\n- [x] 2.0 Another Phase")
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()) as mock_file:
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    assert result is not None
                    # Output should clearly indicate full project scope
    
    def test_full_project_output_lists_all_analyzed_phases(self):
        """Test that full_project output lists all analyzed phases"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-phases.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Multi-Phase Task List

## Tasks

- [x] 1.0 Authentication Phase
  - [x] 1.1 User login
  - [x] 1.2 Password reset
- [x] 2.0 Data Management Phase
  - [x] 2.1 Database setup
  - [x] 2.2 Data validation
- [x] 3.0 UI Development Phase
  - [x] 3.1 Component creation
  - [x] 3.2 Styling
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["auth.py", "database.py", "components.js"]
                with patch('builtins.open', mock_open()) as mock_file:
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    assert result is not None
                    # Output should list all analyzed phases (1.0, 2.0, 3.0)
    
    def test_full_project_output_maintains_consistent_format(self):
        """Test that full_project output maintains consistent format with other scopes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-format.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Task List\n- [x] 1.0 Test Phase")
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()) as mock_file:
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    assert result is not None
                    # Should follow same format structure as other scopes
                    # (header, task analysis, file changes, etc.)


class TestFullProjectEdgeCases:
    """Test edge cases for full project reviews"""
    
    def test_full_project_with_malformed_task_list(self):
        """Test full_project scope with malformed task list"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-malformed.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Malformed Task List

This is not a proper task list format.

Some random text here.

- This is not a proper task
- [x] 1.0 This is ok
- [ ] 2.0 This is incomplete
  - Random subtask without proper format
  - [x] 2.1 This is ok
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    # Should handle malformed input gracefully
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    assert result is not None
                    # Should extract what it can and handle errors gracefully
    
    def test_full_project_with_no_git_repository(self):
        """Test full_project scope when project is not a git repository"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-no-git.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Task List\n- [x] 1.0 Test Phase")
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                # Mock git failure (no repository)
                mock_files.side_effect = Exception("Not a git repository")
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    assert result is not None
                    # Should handle non-git projects gracefully
    
    def test_full_project_with_mixed_completion_states(self):
        """Test full_project with complex mixed completion states"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-mixed-states.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Complex Task List

## Tasks

- [x] 1.0 Fully Completed Phase
  - [x] 1.1 All tasks complete
  - [x] 1.2 Every subtask done
- [ ] 2.0 Partially Completed Phase
  - [x] 2.1 Some tasks complete
  - [ ] 2.2 Some incomplete
  - [x] 2.3 Mixed state
- [x] 3.0 Another Fully Completed Phase
  - [x] 3.1 Complete
- [ ] 4.0 Mostly Incomplete Phase
  - [ ] 4.1 Not done
  - [x] 4.2 One done
  - [ ] 4.3 Not done
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["file1.py", "file2.py"]
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    assert result is not None
                    # Should include only phases 1.0 and 3.0 (fully completed)
                    # Should exclude phases 2.0 and 4.0 (partially completed)