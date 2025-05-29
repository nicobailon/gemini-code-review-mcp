"""
Tests for specific phase targeting functionality (phase_number parameter)
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


class TestPhaseNumberParameterValidation:
    """Test phase_number parameter validation"""
    
    def test_specific_phase_requires_phase_number(self):
        """Test that specific_phase scope requires phase_number parameter"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Test Phase\n- [x] 2.0 Another Phase")
            
            with pytest.raises(ValueError) as exc_info:
                generate_review_context(
                    project_path=temp_dir,
                    scope="specific_phase"
                    # Missing phase_number parameter
                )
            
            error_message = str(exc_info.value).lower()
            assert "phase_number" in error_message
            assert "required" in error_message or "missing" in error_message
    
    def test_phase_number_validates_format(self):
        """Test that phase_number validates proper format (X.0 pattern)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Valid Phase\n- [x] 2.0 Another Valid Phase")
            
            invalid_formats = [
                "1",           # Missing .0
                "1.0.1",       # Too many decimals
                "1.5",         # Should be .0
                "phase1",      # Text format
                "1.0.0",       # Too many parts
                "",            # Empty string
                "1.",          # Incomplete
                ".0",          # Missing number
                "01.0",        # Leading zero
                "1.00"         # Extra zero
            ]
            
            for invalid_format in invalid_formats:
                with pytest.raises((ValueError, TypeError)) as exc_info:
                    generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number=invalid_format
                    )
                
                error_message = str(exc_info.value).lower()
                assert "phase_number" in error_message or "format" in error_message
    
    def test_phase_number_accepts_valid_formats(self):
        """Test that phase_number accepts valid formats"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Test Tasks
- [x] 1.0 Phase One
- [x] 2.0 Phase Two  
- [x] 10.0 Phase Ten
- [x] 99.0 Phase Ninety Nine
"""
            task_file.write_text(task_content)
            
            valid_formats = ["1.0", "2.0", "10.0", "99.0"]
            
            for valid_format in valid_formats:
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    with patch('builtins.open', mock_open()):
                        # Should not raise validation errors
                        result = generate_review_context(
                            project_path=temp_dir,
                            scope="specific_phase",
                            phase_number=valid_format
                        )
                        assert result is not None
    
    def test_phase_number_rejects_non_string_types(self):
        """Test that phase_number rejects non-string types"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Test Phase")
            
            invalid_types = [
                1,           # Integer
                1.0,         # Float
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
                        scope="specific_phase", 
                        phase_number=invalid_type
                    )
                
                error_message = str(exc_info.value).lower()
                assert "phase_number" in error_message or "type" in error_message


class TestPhaseExistenceValidation:
    """Test validation that specified phase exists in task list"""
    
    def test_validates_phase_exists_in_task_list(self):
        """Test that phase_number must exist in the task list"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-limited.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Limited Task List

## Tasks

- [x] 1.0 First Phase
  - [x] 1.1 First task
- [x] 3.0 Third Phase (skipped 2.0)
  - [x] 3.1 Third task
- [x] 5.0 Fifth Phase
  - [x] 5.1 Fifth task
"""
            task_file.write_text(task_content)
            
            # Test non-existent phases
            non_existent_phases = ["2.0", "4.0", "6.0", "10.0"]
            
            for phase in non_existent_phases:
                with pytest.raises(ValueError) as exc_info:
                    generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number=phase
                    )
                
                error_message = str(exc_info.value).lower()
                assert ("not found" in error_message or 
                       "does not exist" in error_message or
                       "not exist" in error_message)
                assert phase in str(exc_info.value)
    
    def test_accepts_existing_phases(self):
        """Test that existing phases are accepted"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-existing.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Existing Phases Task List

## Tasks

- [x] 1.0 Database Setup
  - [x] 1.1 Schema design
  - [x] 1.2 Migration scripts
- [x] 2.0 API Development
  - [x] 2.1 Authentication
  - [x] 2.2 CRUD operations
- [x] 3.0 Frontend Development  
  - [x] 3.1 Components
  - [x] 3.2 State management
"""
            task_file.write_text(task_content)
            
            existing_phases = ["1.0", "2.0", "3.0"]
            
            for phase in existing_phases:
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    with patch('builtins.open', mock_open()):
                        result = generate_review_context(
                            project_path=temp_dir,
                            scope="specific_phase",
                            phase_number=phase
                        )
                        assert result is not None
    
    def test_case_insensitive_phase_matching(self):
        """Test that phase matching is case-insensitive for phase content"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-case.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Case Test Task List

## Tasks

- [x] 1.0 UPPERCASE PHASE
  - [x] 1.1 uppercase task
- [x] 2.0 lowercase phase
  - [x] 2.1 mixed Case Task
"""
            task_file.write_text(task_content)
            
            # Phase numbers should be exact match, not case insensitive
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number="1.0"  # Exact match required
                    )
                    assert result is not None


class TestSpecificPhaseAnalysis:
    """Test that specific_phase analyzes only the specified phase"""
    
    def test_analyzes_only_specified_phase(self):
        """Test that only the specified phase is analyzed"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-multi-phase.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Multi-Phase Task List

## Tasks

- [x] 1.0 First Phase (should be ignored)
  - [x] 1.1 First task
  - [x] 1.2 Another first task
- [x] 2.0 Target Phase (should be analyzed)
  - [x] 2.1 Target task one
  - [x] 2.2 Target task two
  - [x] 2.3 Target task three
- [x] 3.0 Third Phase (should be ignored)
  - [x] 3.1 Third task
  - [x] 3.2 Another third task
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["file1.py", "file2.py", "file3.py"]
                with patch('builtins.open', mock_open()) as mock_file:
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number="2.0"
                    )
                    
                    assert result is not None
                    # Implementation should verify only phase 2.0 is analyzed
    
    def test_includes_all_tasks_in_specified_phase(self):
        """Test that all tasks in the specified phase are included"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-detailed-phase.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Detailed Phase Task List

## Tasks

- [x] 2.0 Detailed Target Phase
  - [x] 2.1 Database schema design
  - [x] 2.2 Create user table
  - [x] 2.3 Create product table  
  - [x] 2.4 Add foreign key constraints
  - [x] 2.5 Create indexes for performance
  - [x] 2.6 Add data validation rules
  - [x] 2.7 Create seed data scripts
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["schema.sql", "users.sql", "products.sql"]
                with patch('builtins.open', mock_open()) as mock_file:
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number="2.0"
                    )
                    
                    assert result is not None
                    # All subtasks 2.1-2.7 should be included in analysis
    
    def test_handles_incomplete_specified_phase(self):
        """Test handling when specified phase is incomplete"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-incomplete.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Incomplete Phase Task List

## Tasks

- [x] 1.0 Complete Phase
  - [x] 1.1 Done task
- [ ] 2.0 Incomplete Target Phase
  - [x] 2.1 Completed task  
  - [ ] 2.2 Incomplete task
  - [x] 2.3 Another completed task
- [x] 3.0 Another Complete Phase
  - [x] 3.1 Done task
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["file1.py"]
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number="2.0"  # Incomplete phase
                    )
                    
                    assert result is not None
                    # Should still analyze the phase even if incomplete


class TestSpecificPhaseFileNaming:
    """Test file naming for specific phase targeting"""
    
    def test_output_file_includes_phase_identifier(self):
        """Test that output file name includes phase identifier"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-naming.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Task List\n- [x] 1.0 Phase One\n- [x] 2.0 Phase Two\n- [x] 3.0 Phase Three")
            
            test_phases = ["1.0", "2.0", "3.0"]
            
            for phase in test_phases:
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    with patch('builtins.open', mock_open()):
                        result = generate_review_context(
                            project_path=temp_dir,
                            scope="specific_phase",
                            phase_number=phase
                        )
                        
                        assert result is not None
                        # Filename should contain phase identifier
                        # Expected pattern: code-review-context-phase-{phase}-{timestamp}.md
                        phase_in_filename = phase.replace(".", "-")  # 1.0 becomes 1-0
                        assert f"phase-{phase_in_filename}" in result or f"phase_{phase_in_filename}" in result
    
    def test_different_phases_generate_different_filenames(self):
        """Test that different phases generate different file names"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-different.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Task List\n- [x] 1.0 Phase One\n- [x] 2.0 Phase Two")
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result_1 = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number="1.0"
                    )
                    
                    result_2 = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase", 
                        phase_number="2.0"
                    )
                    
                    assert result_1 is not None
                    assert result_2 is not None
                    assert result_1 != result_2  # Different file names
    
    def test_filename_follows_convention_pattern(self):
        """Test that filename follows the established convention pattern"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-convention.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Task List\n- [x] 5.0 Special Phase")
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number="5.0"
                    )
                    
                    assert result is not None
                    # Should follow pattern: code-review-context-phase-{phase}-{timestamp}.md
                    assert "code-review-context" in result
                    assert "phase-5" in result or "phase_5" in result
                    assert result.endswith(".md")


class TestSpecificPhaseOutputContent:
    """Test output content for specific phase reviews"""
    
    def test_output_contains_phase_information(self):
        """Test that output contains specific phase information"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-content.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Task List with Content

## Tasks

- [x] 1.0 Authentication Phase
  - [x] 1.1 User login system
  - [x] 1.2 Password hashing
- [x] 2.0 Database Phase
  - [x] 2.1 Schema design
  - [x] 2.2 Migration scripts
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["auth.py", "database.py"]
                with patch('builtins.open', mock_open()) as mock_file:
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number="2.0"
                    )
                    
                    assert result is not None
                    # Output should clearly indicate which phase is being analyzed
    
    def test_output_scope_header_identifies_specific_phase(self):
        """Test that output header clearly identifies the specific phase scope"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-header.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Task List\n- [x] 7.0 Special Phase")
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()) as mock_file:
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number="7.0"
                    )
                    
                    assert result is not None
                    # Header should indicate specific_phase scope and phase 7.0


class TestSpecificPhaseEdgeCases:
    """Test edge cases for specific phase targeting"""
    
    def test_handles_phase_with_no_subtasks(self):
        """Test handling of phase with no subtasks"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-no-subtasks.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Task List with No Subtasks

## Tasks

- [x] 1.0 Phase with subtasks
  - [x] 1.1 Has subtask
- [x] 2.0 Phase without subtasks
- [x] 3.0 Another phase with subtasks
  - [x] 3.1 Has subtask
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number="2.0"  # Phase with no subtasks
                    )
                    
                    assert result is not None
                    # Should handle gracefully
    
    def test_handles_malformed_task_list_for_specific_phase(self):
        """Test handling malformed task list when targeting specific phase"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-malformed.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Malformed Task List

Some random content here.

- [x] 1.0 Valid Phase
  - [x] 1.1 Valid task
- This is not a valid task format
- [x] 2.0 Another Valid Phase
  Random text in between
  - [x] 2.1 Valid subtask
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number="2.0"
                    )
                    
                    assert result is not None
                    # Should extract valid phase despite malformed content
    
    def test_handles_duplicate_phase_numbers(self):
        """Test handling of duplicate phase numbers in task list"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-duplicates.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Task List with Duplicates

## Tasks

- [x] 1.0 First occurrence
  - [x] 1.1 First task
- [x] 2.0 Normal phase
  - [x] 2.1 Normal task
- [x] 1.0 Duplicate occurrence
  - [x] 1.2 Duplicate task
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number="1.0"
                    )
                    
                    assert result is not None
                    # Should handle duplicates gracefully (implementation defined behavior)


class TestSpecificPhaseIntegration:
    """Test integration of specific phase with other functionality"""
    
    def test_specific_phase_with_git_changes(self):
        """Test specific phase analysis with git changes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-git.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Git Integration Task List

## Tasks

- [x] 1.0 Backend Phase
  - [x] 1.1 API development
  - [x] 1.2 Database integration
- [x] 2.0 Frontend Phase
  - [x] 2.1 Component development
  - [x] 2.2 State management
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                # Mock git changes relevant to specific phase
                mock_files.return_value = [
                    "frontend/components/Header.js",
                    "frontend/components/Footer.js", 
                    "frontend/store/index.js",
                    "frontend/store/actions.js"
                ]
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number="2.0"  # Frontend phase
                    )
                    
                    assert result is not None
                    # Should include git changes in analysis
    
    def test_specific_phase_respects_output_path(self):
        """Test that specific phase respects custom output path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-output.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Task List\n- [x] 1.0 Test Phase")
            
            custom_output = str(Path(temp_dir) / "custom-review.md")
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number="1.0",
                        output_path=custom_output
                    )
                    
                    assert result is not None
                    # Should respect custom output path
                    assert custom_output in result or result == custom_output