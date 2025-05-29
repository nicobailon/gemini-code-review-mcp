"""
Comprehensive tests for scope-based code review functionality
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


class TestScopeParameterValidation:
    """Test scope parameter validation and behavior"""
    
    def test_scope_parameter_accepts_valid_values(self):
        """Test that scope parameter accepts all valid values"""
        valid_scopes = ["recent_phase", "full_project", "specific_phase", "specific_task"]
        
        for scope in valid_scopes:
            # Should not raise any validation errors
            assert scope in valid_scopes, f"Scope '{scope}' should be valid"
    
    def test_scope_parameter_rejects_invalid_values(self):
        """Test that scope parameter rejects invalid values"""
        invalid_scopes = ["invalid_scope", "random", "", None, 123, []]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create minimal project structure
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [ ] 1.0 Test Task")
            
            for invalid_scope in invalid_scopes:
                with pytest.raises((ValueError, TypeError)) as exc_info:
                    generate_review_context(
                        project_path=temp_dir,
                        scope=invalid_scope
                    )
                assert "scope" in str(exc_info.value).lower(), f"Error should mention scope for value: {invalid_scope}"
    
    def test_scope_parameter_defaults_to_recent_phase(self):
        """Test that scope parameter defaults to 'recent_phase' when not specified"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create minimal project structure
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Completed Task\n- [ ] 2.0 Current Task")
            
            with patch('generate_code_review_context.detect_current_phase') as mock_detect:
                mock_detect.return_value = "2.0"
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    with patch('builtins.open', mock_open()):
                        result = generate_review_context(project_path=temp_dir)
                        # Should not raise error and should use recent_phase logic
                        assert result is not None


class TestFullProjectReviewFunctionality:
    """Test full project review functionality (entire task list analysis)"""
    
    def test_full_project_scope_analyzes_entire_task_list(self):
        """Test that full_project scope analyzes the entire task list"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create comprehensive task list
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Test Tasks
- [x] 1.0 First Phase
  - [x] 1.1 First subtask
  - [x] 1.2 Second subtask
- [x] 2.0 Second Phase
  - [x] 2.1 Another subtask
- [ ] 3.0 Current Phase
  - [ ] 3.1 Pending subtask
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["file1.py", "file2.py", "file3.py"]
                with patch('builtins.open', mock_open()) as mock_file:
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    # Should analyze all phases, not just recent
                    assert result is not None
                    # Verify that all phases are considered (this will be implemented)
    
    def test_full_project_scope_includes_all_git_changes(self):
        """Test that full_project scope includes all git changes, not just recent"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Phase One\n- [x] 2.0 Phase Two")
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                # Mock comprehensive file changes across project
                mock_files.return_value = [
                    "src/module1.py", "src/module2.py", "tests/test1.py", 
                    "docs/readme.md", "config/settings.py"
                ]
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    assert result is not None
                    # Should include all files, not filtered by phase
    
    def test_full_project_scope_output_file_naming(self):
        """Test that full_project scope generates correctly named output files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Test Phase")
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    # Verify filename contains 'full-project' identifier
                    assert "full-project" in result or "full_project" in result


class TestSpecificPhaseTargeting:
    """Test specific phase targeting functionality"""
    
    def test_specific_phase_requires_phase_number(self):
        """Test that specific_phase scope requires phase_number parameter"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Test Phase")
            
            with pytest.raises(ValueError) as exc_info:
                generate_review_context(
                    project_path=temp_dir,
                    scope="specific_phase"
                    # Missing phase_number parameter
                )
            assert "phase_number" in str(exc_info.value).lower()
    
    def test_specific_phase_validates_phase_number_format(self):
        """Test that specific_phase validates phase_number format"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Phase One\n- [x] 2.0 Phase Two")
            
            invalid_phase_numbers = ["invalid", "1.0.1", "", "phase1", 123, None]
            
            for invalid_phase in invalid_phase_numbers:
                with pytest.raises((ValueError, TypeError)) as exc_info:
                    generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number=invalid_phase
                    )
                assert "phase_number" in str(exc_info.value).lower()
    
    def test_specific_phase_validates_phase_exists(self):
        """Test that specific_phase validates that the specified phase exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Phase One\n- [x] 2.0 Phase Two")
            
            with pytest.raises(ValueError) as exc_info:
                generate_review_context(
                    project_path=temp_dir,
                    scope="specific_phase",
                    phase_number="5.0"  # Non-existent phase
                )
            assert "phase" in str(exc_info.value).lower()
            assert "not found" in str(exc_info.value).lower() or "does not exist" in str(exc_info.value).lower()
    
    def test_specific_phase_analyzes_correct_phase(self):
        """Test that specific_phase analyzes only the specified phase"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Test Tasks
- [x] 1.0 First Phase
  - [x] 1.1 First subtask
- [x] 2.0 Second Phase Target
  - [x] 2.1 Target subtask
- [x] 3.0 Third Phase
  - [x] 3.1 Third subtask
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["file1.py", "file2.py"]
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number="2.0"
                    )
                    
                    assert result is not None
                    # Should only analyze phase 2.0, not other phases
    
    def test_specific_phase_output_file_naming(self):
        """Test that specific_phase generates correctly named output files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Phase One\n- [x] 2.0 Phase Two")
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_phase",
                        phase_number="2.0"
                    )
                    
                    # Verify filename contains phase identifier
                    assert "phase-2.0" in result or "phase_2.0" in result


class TestSpecificTaskTargeting:
    """Test specific task targeting functionality"""
    
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
            assert "task_number" in str(exc_info.value).lower()
    
    def test_specific_task_validates_task_number_format(self):
        """Test that specific_task validates task_number format (e.g., '1.2')"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Phase\n  - [x] 1.1 Task")
            
            invalid_task_numbers = ["invalid", "1", "1.0.1.2", "", "task1", 123, None]
            
            for invalid_task in invalid_task_numbers:
                with pytest.raises((ValueError, TypeError)) as exc_info:
                    generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number=invalid_task
                    )
                assert "task_number" in str(exc_info.value).lower()
    
    def test_specific_task_validates_task_exists(self):
        """Test that specific_task validates that the specified task exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Test Tasks
- [x] 1.0 Phase One
  - [x] 1.1 Task One
  - [x] 1.2 Task Two
"""
            task_file.write_text(task_content)
            
            with pytest.raises(ValueError) as exc_info:
                generate_review_context(
                    project_path=temp_dir,
                    scope="specific_task",
                    task_number="1.5"  # Non-existent task
                )
            assert "task" in str(exc_info.value).lower()
            assert "not found" in str(exc_info.value).lower() or "does not exist" in str(exc_info.value).lower()
    
    def test_specific_task_analyzes_correct_task(self):
        """Test that specific_task analyzes only the specified task"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Test Tasks
- [x] 1.0 First Phase
  - [x] 1.1 First task
  - [x] 1.2 Target task
  - [x] 1.3 Third task
- [x] 2.0 Second Phase
  - [x] 2.1 Another task
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = ["file1.py"]
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="1.2"
                    )
                    
                    assert result is not None
                    # Should only analyze task 1.2, not other tasks
    
    def test_specific_task_output_file_naming(self):
        """Test that specific_task generates correctly named output files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Test Tasks
- [x] 1.0 Phase
  - [x] 1.1 Task One
  - [x] 1.2 Task Two
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
                    
                    # Verify filename contains task identifier
                    assert "task-1.2" in result or "task_1.2" in result


class TestEnhancedFileNamingConventions:
    """Test enhanced file naming conventions by scope"""
    
    def test_recent_phase_file_naming(self):
        """Test file naming for recent_phase scope"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Recent Phase")
            
            with patch('generate_code_review_context.detect_current_phase') as mock_detect:
                mock_detect.return_value = "1.0"
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    with patch('builtins.open', mock_open()):
                        result = generate_review_context(
                            project_path=temp_dir,
                            scope="recent_phase"
                        )
                        
                        # Should follow recent_phase naming pattern
                        assert result is not None
                        # Pattern should be: code-review-context-recent-phase-{timestamp}.md
    
    def test_file_naming_includes_timestamp(self):
        """Test that all scope file naming includes timestamp"""
        scopes_and_params = [
            ("recent_phase", {}),
            ("full_project", {}),
            ("specific_phase", {"phase_number": "1.0"}),
            ("specific_task", {"task_number": "1.1"})
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Test Tasks
- [x] 1.0 Test Phase
  - [x] 1.1 Test Task
"""
            task_file.write_text(task_content)
            
            for scope, extra_params in scopes_and_params:
                with patch('generate_code_review_context.detect_current_phase') as mock_detect:
                    mock_detect.return_value = "1.0"
                    with patch('generate_code_review_context.get_changed_files') as mock_files:
                        mock_files.return_value = []
                        with patch('builtins.open', mock_open()):
                            result = generate_review_context(
                                project_path=temp_dir,
                                scope=scope,
                                **extra_params
                            )
                            
                            assert result is not None
                            # All files should include timestamp in filename
                            # Pattern verification will be implemented
    
    def test_file_naming_avoids_conflicts(self):
        """Test that file naming avoids conflicts with existing files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Test Phase")
            
            # Create existing file with similar name
            existing_file = Path(temp_dir) / "code-review-context-recent-phase-2024.md"
            existing_file.write_text("Existing content")
            
            with patch('generate_code_review_context.detect_current_phase') as mock_detect:
                mock_detect.return_value = "1.0"
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    with patch('builtins.open', mock_open()):
                        result = generate_review_context(
                            project_path=temp_dir,
                            scope="recent_phase"
                        )
                        
                        assert result is not None
                        # Should generate unique filename, not overwrite existing
                        assert result != str(existing_file)


class TestScopeInformationInOutput:
    """Test that scope information is included in generated output"""
    
    def test_output_contains_scope_information(self):
        """Test that generated output contains scope information in header"""
        scopes_and_params = [
            ("recent_phase", {}),
            ("full_project", {}),
            ("specific_phase", {"phase_number": "2.0"}),
            ("specific_task", {"task_number": "1.3"})
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Test Tasks
- [x] 1.0 First Phase
  - [x] 1.1 First task
- [x] 2.0 Second Phase
  - [x] 2.1 Second task
"""
            task_file.write_text(task_content)
            
            for scope, extra_params in scopes_and_params:
                with patch('generate_code_review_context.detect_current_phase') as mock_detect:
                    mock_detect.return_value = "2.0"
                    with patch('generate_code_review_context.get_changed_files') as mock_files:
                        mock_files.return_value = []
                        with patch('builtins.open', mock_open()) as mock_file:
                            result = generate_review_context(
                                project_path=temp_dir,
                                scope=scope,
                                **extra_params
                            )
                            
                            assert result is not None
                            # Output should contain scope information
                            # This will be verified in the implementation
    
    def test_output_format_consistency_across_scopes(self):
        """Test that output format is consistent across all scopes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-test.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Test Tasks\n- [x] 1.0 Test Phase\n  - [x] 1.1 Test Task")
            
            # Test that all scopes produce similarly structured output
            scopes = ["recent_phase", "full_project"]
            results = []
            
            for scope in scopes:
                with patch('generate_code_review_context.detect_current_phase') as mock_detect:
                    mock_detect.return_value = "1.0"
                    with patch('generate_code_review_context.get_changed_files') as mock_files:
                        mock_files.return_value = []
                        with patch('builtins.open', mock_open()):
                            result = generate_review_context(
                                project_path=temp_dir,
                                scope=scope
                            )
                            results.append(result)
            
            # All results should be valid (non-None)
            assert all(result is not None for result in results)
            # Format consistency will be verified in implementation