"""
Tests for specific task targeting functionality (task_number parameter)
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


class TestTaskNumberParameterValidation:
    """Test task_number parameter validation"""
    
    def test_specific_task_requires_task_number(self):
        """Test that specific_task scope requires task_number parameter"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Test Phase\n  - [x] 1.1 Test Task")
            
            with pytest.raises(ValueError) as exc_info:
                generate_review_context(
                    project_path=temp_dir,
                    scope="specific_task"
                    # Missing task_number parameter
                )
            
            error_message = str(exc_info.value).lower()
            assert "task_number" in error_message
            assert "required" in error_message or "missing" in error_message
    
    def test_task_number_validates_format(self):
        """Test that task_number validates proper format (X.Y pattern)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Phase\n  - [x] 1.1 Task\n  - [x] 1.2 Another Task")
            
            invalid_formats = [
                "1",           # Missing subtask part
                "1.0",         # Phase format, not task
                "1.0.1",       # Too many parts
                "1.1.2",       # Too many parts
                "task1",       # Text format
                "1.1.0.0",     # Too many parts
                "",            # Empty string
                "1.",          # Incomplete
                ".1",          # Missing phase
                "01.1",        # Leading zero in phase
                "1.01",        # Leading zero in task
                "1.10.5",      # Too many decimals
                "1-1",         # Wrong separator
                "1_1"          # Wrong separator
            ]
            
            for invalid_format in invalid_formats:
                with pytest.raises((ValueError, TypeError)) as exc_info:
                    generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number=invalid_format
                    )
                
                error_message = str(exc_info.value).lower()
                assert "task_number" in error_message or "format" in error_message
    
    def test_task_number_accepts_valid_formats(self):
        """Test that task_number accepts valid formats"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Test Tasks
- [x] 1.0 Phase One
  - [x] 1.1 Task One
  - [x] 1.2 Task Two
  - [x] 1.15 Task Fifteen
- [x] 10.0 Phase Ten
  - [x] 10.1 Task One of Ten
  - [x] 10.25 Task Twenty Five of Ten
- [x] 99.0 Phase Ninety Nine
  - [x] 99.99 Task Ninety Nine
"""
            task_file.write_text(task_content)
            
            valid_formats = ["1.1", "1.2", "1.15", "10.1", "10.25", "99.99"]
            
            for valid_format in valid_formats:
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    with patch('builtins.open', mock_open()):
                        # Should not raise validation errors
                        result = generate_review_context(
                            project_path=temp_dir,
                            scope="specific_task",
                            task_number=valid_format
                        )
                        assert result is not None
    
    def test_task_number_rejects_non_string_types(self):
        """Test that task_number rejects non-string types"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Phase\n  - [x] 1.1 Task")
            
            invalid_types = [
                1,           # Integer
                1.1,         # Float
                None,        # None
                [],          # List
                {},          # Dict
                True,        # Boolean
                object()     # Object
            ]
            
            for invalid_type in invalid_types:
                with pytest.raises((ValueError, TypeError)) as exc_info:
                    generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number=invalid_type
                    )
                
                error_message = str(exc_info.value).lower()
                assert "task_number" in error_message or "type" in error_message
    
    def test_task_number_validates_phase_part(self):
        """Test that task_number validates the phase part (X in X.Y)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Phase\n  - [x] 1.1 Task")
            
            invalid_phase_parts = [
                "0.1",         # Phase 0 doesn't exist
                "-1.1",        # Negative phase
                "a.1",         # Non-numeric phase
                "1a.1",        # Mixed alphanumeric
                " 1.1",        # Leading space
                "1 .1"         # Space in middle
            ]
            
            for invalid_task in invalid_phase_parts:
                with pytest.raises((ValueError, TypeError)) as exc_info:
                    generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number=invalid_task
                    )
                
                error_message = str(exc_info.value).lower()
                assert "task_number" in error_message or "format" in error_message or "phase" in error_message
    
    def test_task_number_validates_task_part(self):
        """Test that task_number validates the task part (Y in X.Y)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Phase\n  - [x] 1.1 Task")
            
            invalid_task_parts = [
                "1.0",         # 0 task number (should be subtask, not phase)
                "1.-1",        # Negative task
                "1.a",         # Non-numeric task
                "1.1a",        # Mixed alphanumeric
                "1. 1",        # Space after dot
                "1.1 "         # Trailing space
            ]
            
            for invalid_task in invalid_task_parts:
                with pytest.raises((ValueError, TypeError)) as exc_info:
                    generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number=invalid_task
                    )
                
                error_message = str(exc_info.value).lower()
                assert "task_number" in error_message or "format" in error_message


class TestTaskExistenceValidation:
    """Test validation that specified task exists in task list"""
    
    def test_validates_task_exists_in_task_list(self):
        """Test that task_number must exist in the task list"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-limited.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Limited Task List

## Tasks

- [x] 1.0 First Phase
  - [x] 1.1 First task
  - [x] 1.3 Third task (skipped 1.2)
- [x] 2.0 Second Phase
  - [x] 2.1 Only task in phase 2
- [x] 3.0 Third Phase
  - [x] 3.2 Second task (skipped 3.1)
  - [x] 3.5 Fifth task
"""
            task_file.write_text(task_content)
            
            # Test non-existent tasks
            non_existent_tasks = ["1.2", "1.4", "2.2", "3.1", "3.3", "4.1", "1.10"]
            
            for task in non_existent_tasks:
                with pytest.raises(ValueError) as exc_info:
                    generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number=task
                    )
                
                error_message = str(exc_info.value).lower()
                assert ("not found" in error_message or 
                       "does not exist" in error_message or
                       "not exist" in error_message)
                assert task in str(exc_info.value)
    
    def test_accepts_existing_tasks(self):
        """Test that existing tasks are accepted"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-existing.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Existing Tasks Task List

## Tasks

- [x] 1.0 Database Setup
  - [x] 1.1 Schema design
  - [x] 1.2 Migration scripts
  - [x] 1.3 Seed data
- [x] 2.0 API Development
  - [x] 2.1 Authentication endpoints
  - [x] 2.2 CRUD operations
  - [x] 2.3 Input validation
- [x] 3.0 Frontend Development  
  - [x] 3.1 Component structure
  - [x] 3.2 State management
  - [x] 3.3 API integration
"""
            task_file.write_text(task_content)
            
            existing_tasks = ["1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "3.1", "3.2", "3.3"]
            
            for task in existing_tasks:
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    with patch('builtins.open', mock_open()):
                        result = generate_review_context(
                            project_path=temp_dir,
                            scope="specific_task",
                            task_number=task
                        )
                        assert result is not None
    
    def test_validates_phase_exists_for_task(self):
        """Test that the phase exists for the specified task"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-phase-validation.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Phase Validation Task List

## Tasks

- [x] 1.0 Existing Phase
  - [x] 1.1 Existing task
- [x] 3.0 Another Existing Phase (skipped 2.0)
  - [x] 3.1 Another existing task
"""
            task_file.write_text(task_content)
            
            # Test tasks in non-existent phases
            tasks_in_non_existent_phases = ["2.1", "4.1", "5.1", "10.1"]
            
            for task in tasks_in_non_existent_phases:
                with pytest.raises(ValueError) as exc_info:
                    generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number=task
                    )
                
                error_message = str(exc_info.value).lower()
                assert ("not found" in error_message or 
                       "does not exist" in error_message)


class TestSpecificTaskAnalysis:
    """Test that specific_task analyzes only the specified task"""
    
    def test_analyzes_only_specified_task(self):
        """Test that only the specified task is analyzed"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-multi-task.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Multi-Task Task List

## Tasks

- [x] 1.0 Database Phase
  - [x] 1.1 Schema design (should be ignored)
  - [x] 1.2 Target Task (should be analyzed)
  - [x] 1.3 Migration scripts (should be ignored)
- [x] 2.0 API Phase
  - [x] 2.1 Authentication (should be ignored)
  - [x] 2.2 CRUD operations (should be ignored)
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["database.py", "models.py", "migrations.py"]
                with patch('builtins.open', mock_open()) as mock_file:
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="1.2"
                    )
                    
                    assert result is not None
                    # Implementation should verify only task 1.2 is analyzed
    
    def test_focuses_on_single_task_scope(self):
        """Test that analysis focuses on the scope of a single task"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-detailed-task.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Detailed Task Analysis

## Tasks

- [x] 2.0 User Authentication System
  - [x] 2.1 User registration form
  - [x] 2.2 Password hashing and validation (TARGET TASK)
  - [x] 2.3 Login endpoint
  - [x] 2.4 Session management
  - [x] 2.5 Password reset functionality
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["auth/password.py", "auth/validation.py", "auth/hash.py"]
                with patch('builtins.open', mock_open()) as mock_file:
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="2.2"
                    )
                    
                    assert result is not None
                    # Should focus specifically on password hashing and validation
    
    def test_handles_task_in_incomplete_phase(self):
        """Test handling when specified task is in an incomplete phase"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-incomplete-phase.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Incomplete Phase Task List

## Tasks

- [x] 1.0 Complete Phase
  - [x] 1.1 Complete task
- [ ] 2.0 Incomplete Phase
  - [x] 2.1 Completed task in incomplete phase
  - [ ] 2.2 Incomplete task
  - [x] 2.3 Another completed task (TARGET)
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["file1.py"]
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="2.3"  # Completed task in incomplete phase
                    )
                    
                    assert result is not None
                    # Should analyze the specific task even if parent phase is incomplete
    
    def test_handles_incomplete_specified_task(self):
        """Test handling when the specified task itself is incomplete"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-incomplete-task.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Incomplete Task List

## Tasks

- [x] 1.0 Complete Phase
  - [x] 1.1 Complete task
  - [ ] 1.2 Incomplete target task
  - [x] 1.3 Another complete task
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["file1.py"]
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="1.2"  # Incomplete task
                    )
                    
                    assert result is not None
                    # Should still analyze the task even if incomplete


class TestSpecificTaskFileNaming:
    """Test file naming for specific task targeting"""
    
    def test_output_file_includes_task_identifier(self):
        """Test that output file name includes task identifier"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-naming.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Task Naming List
- [x] 1.0 Phase One
  - [x] 1.1 Task One
  - [x] 1.2 Task Two
- [x] 2.0 Phase Two
  - [x] 2.5 Task Five
  - [x] 2.10 Task Ten
"""
            task_file.write_text(task_content)
            
            test_tasks = ["1.1", "1.2", "2.5", "2.10"]
            
            for task in test_tasks:
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    with patch('builtins.open', mock_open()):
                        result = generate_review_context(
                            project_path=temp_dir,
                            scope="specific_task",
                            task_number=task
                        )
                        
                        assert result is not None
                        # Filename should contain task identifier
                        # Expected pattern: code-review-context-task-{task}-{timestamp}.md
                        task_in_filename = task.replace(".", "-")  # 1.2 becomes 1-2
                        assert f"task-{task_in_filename}" in result or f"task_{task_in_filename}" in result
    
    def test_different_tasks_generate_different_filenames(self):
        """Test that different tasks generate different file names"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-different.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Different Tasks List
- [x] 1.0 Phase One
  - [x] 1.1 Task One
  - [x] 1.2 Task Two
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result_1_1 = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="1.1"
                    )
                    
                    result_1_2 = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="1.2"
                    )
                    
                    assert result_1_1 is not None
                    assert result_1_2 is not None
                    assert result_1_1 != result_1_2  # Different file names
    
    def test_filename_follows_convention_pattern(self):
        """Test that filename follows the established convention pattern"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-convention.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Convention Task List
- [x] 5.0 Special Phase
  - [x] 5.7 Special Task
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="5.7"
                    )
                    
                    assert result is not None
                    # Should follow pattern: code-review-context-task-{task}-{timestamp}.md
                    assert "code-review-context" in result
                    assert "task-5-7" in result or "task_5_7" in result
                    assert result.endswith(".md")


class TestSpecificTaskOutputContent:
    """Test output content for specific task reviews"""
    
    def test_output_contains_task_information(self):
        """Test that output contains specific task information"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-content.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Task Content List

## Tasks

- [x] 1.0 User Management Phase
  - [x] 1.1 User registration system
  - [x] 1.2 User profile editing (TARGET TASK)
  - [x] 1.3 User deletion workflow
- [x] 2.0 Product Management Phase
  - [x] 2.1 Product catalog
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["user_profile.py", "profile_forms.py"]
                with patch('builtins.open', mock_open()) as mock_file:
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="1.2"
                    )
                    
                    assert result is not None
                    # Output should clearly indicate which task is being analyzed
    
    def test_output_scope_header_identifies_specific_task(self):
        """Test that output header clearly identifies the specific task scope"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-header.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Header Task List
- [x] 7.0 Special Phase
  - [x] 7.3 Unique Task
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()) as mock_file:
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="7.3"
                    )
                    
                    assert result is not None
                    # Header should indicate specific_task scope and task 7.3
    
    def test_output_focused_on_task_context(self):
        """Test that output is focused on the specific task context"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-focused.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Focused Task Analysis

## Tasks

- [x] 3.0 Payment Processing Phase
  - [x] 3.1 Payment gateway integration
  - [x] 3.2 Credit card validation (FOCUSED TASK)
  - [x] 3.3 Payment confirmation emails
  - [x] 3.4 Refund processing
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["payment/validation.py", "payment/credit_card.py"]
                with patch('builtins.open', mock_open()) as mock_file:
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="3.2"
                    )
                    
                    assert result is not None
                    # Should focus specifically on credit card validation context


class TestSpecificTaskEdgeCases:
    """Test edge cases for specific task targeting"""
    
    def test_handles_task_with_special_characters_in_description(self):
        """Test handling of task with special characters in description"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-special-chars.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Special Characters Task List

## Tasks

- [x] 1.0 Special Characters Phase
  - [x] 1.1 Task with "quotes" and 'apostrophes'
  - [x] 1.2 Task with (parentheses) and [brackets]
  - [x] 1.3 Task with #hashtags and @mentions
  - [x] 1.4 Task with émojis 🚀 and ünicode
"""
            task_file.write_text(task_content)
            
            special_tasks = ["1.1", "1.2", "1.3", "1.4"]
            
            for task in special_tasks:
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    with patch('builtins.open', mock_open()):
                        result = generate_review_context(
                            project_path=temp_dir,
                            scope="specific_task",
                            task_number=task
                        )
                        
                        assert result is not None
                        # Should handle special characters gracefully
    
    def test_handles_very_long_task_descriptions(self):
        """Test handling of tasks with very long descriptions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-long-desc.md"
            task_file.parent.mkdir(exist_ok=True)
            long_description = "A" * 500  # Very long description
            task_content = f"""# Long Description Task List

## Tasks

- [x] 1.0 Long Description Phase
  - [x] 1.1 {long_description}
  - [x] 1.2 Normal task
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="1.1"
                    )
                    
                    assert result is not None
                    # Should handle long descriptions without issues
    
    def test_handles_malformed_task_list_for_specific_task(self):
        """Test handling malformed task list when targeting specific task"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-malformed.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Malformed Task List

Some random content here.

- [x] 1.0 Valid Phase
  - [x] 1.1 Valid task
  - This is not a valid task format
  - [x] 1.2 Another valid task (TARGET)
  Random text in between
- [x] 2.0 Another Phase
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="1.2"
                    )
                    
                    assert result is not None
                    # Should extract valid task despite malformed content
    
    def test_handles_nested_or_multi_level_indentation(self):
        """Test handling of nested or multi-level task indentation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-nested.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Nested Task List

## Tasks

- [x] 1.0 Main Phase
  - [x] 1.1 Main task
    - Some nested details (not a task)
    - More nested content
  - [x] 1.2 Another main task (TARGET)
    - Implementation notes
    - Technical details
      - Even deeper nesting
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="1.2"
                    )
                    
                    assert result is not None
                    # Should handle nested content correctly


class TestSpecificTaskIntegration:
    """Test integration of specific task with other functionality"""
    
    def test_specific_task_with_git_changes(self):
        """Test specific task analysis with git changes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-git.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Git Integration Task List

## Tasks

- [x] 1.0 API Development Phase
  - [x] 1.1 User authentication endpoints
  - [x] 1.2 Product CRUD operations (TARGET)
  - [x] 1.3 Order processing endpoints
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                # Mock git changes relevant to specific task
                mock_files.return_value = [
                    "api/products.py",
                    "api/product_models.py",
                    "tests/test_products.py",
                    "schemas/product_schema.py"
                ]
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="1.2"  # Product CRUD operations
                    )
                    
                    assert result is not None
                    # Should include git changes in analysis
    
    def test_specific_task_respects_output_path(self):
        """Test that specific task respects custom output path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-output.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Output Path Task List
- [x] 1.0 Test Phase
  - [x] 1.1 Test Task
"""
            task_file.write_text(task_content)
            
            custom_output = str(Path(temp_dir) / "custom-task-review.md")
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="1.1",
                        output_path=custom_output
                    )
                    
                    assert result is not None
                    # Should respect custom output path
                    assert custom_output in result or result == custom_output
    
    def test_specific_task_vs_other_scopes_comparison(self):
        """Test that specific task produces different results than other scopes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-comparison.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Comparison Task List

## Tasks

- [x] 1.0 Development Phase
  - [x] 1.1 Setup database
  - [x] 1.2 Create API endpoints (TARGET)
  - [x] 1.3 Add authentication
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.detect_current_phase') as mock_detect:
                mock_detect.return_value = "1.0"
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = ["api.py", "auth.py", "database.py"]
                    
                    # Test specific_task scope
                    with patch('builtins.open', mock_open()):
                        task_result = generate_review_context(
                            project_path=temp_dir,
                            scope="specific_task",
                            task_number="1.2"
                        )
                    
                    # Test recent_phase scope for comparison
                    with patch('builtins.open', mock_open()):
                        phase_result = generate_review_context(
                            project_path=temp_dir,
                            scope="recent_phase"
                        )
                    
                    assert task_result is not None
                    assert phase_result is not None
                    # Results should be different (different scopes)
                    assert task_result != phase_result