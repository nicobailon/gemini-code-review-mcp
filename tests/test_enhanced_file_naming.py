"""
Tests for enhanced file naming conventions by scope
"""

import pytest
import sys
import tempfile
import re
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from generate_code_review_context import main as generate_review_context


class TestBasicFileNamingConventions:
    """Test basic file naming conventions across all scopes"""
    
    def test_all_scopes_include_timestamp(self):
        """Test that all scope file names include timestamp"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-timestamp.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Timestamp Test Task List

## Tasks

- [x] 1.0 Test Phase
  - [x] 1.1 Test Task
- [x] 2.0 Another Phase
  - [x] 2.1 Another Task
"""
            task_file.write_text(task_content)
            
            scopes_and_params = [
                ("recent_phase", {}),
                ("full_project", {}),
                ("specific_phase", {"phase_number": "1.0"}),
                ("specific_task", {"task_number": "1.1"})
            ]
            
            for scope, extra_params in scopes_and_params:
                with patch('generate_code_review_context.detect_current_phase') as mock_detect:
                    mock_detect.return_value = "2.0"
                    with patch('generate_code_review_context.get_changed_files') as mock_files:
                        mock_files.return_value = []
                        with patch('builtins.open', mock_open()):
                            result = generate_review_context(
                                project_path=temp_dir,
                                scope=scope,
                                **extra_params
                            )
                            
                            assert result is not None
                            # Should contain timestamp pattern (YYYYMMDD-HHMMSS format)
                            timestamp_pattern = r'\d{8}-\d{6}'
                            assert re.search(timestamp_pattern, result), f"No timestamp found in {scope} result: {result}"
    
    def test_all_scopes_include_base_prefix(self):
        """Test that all scope file names include base prefix"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-prefix.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Prefix Test\n- [x] 1.0 Test Phase\n  - [x] 1.1 Test Task")
            
            scopes_and_params = [
                ("recent_phase", {}),
                ("full_project", {}),
                ("specific_phase", {"phase_number": "1.0"}),
                ("specific_task", {"task_number": "1.1"})
            ]
            
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
                            # Should start with "code-review-context"
                            assert "code-review-context" in result, f"Missing base prefix in {scope} result: {result}"
    
    def test_all_scopes_end_with_md_extension(self):
        """Test that all scope file names end with .md extension"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-extension.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Extension Test\n- [x] 1.0 Test Phase\n  - [x] 1.1 Test Task")
            
            scopes_and_params = [
                ("recent_phase", {}),
                ("full_project", {}),
                ("specific_phase", {"phase_number": "1.0"}),
                ("specific_task", {"task_number": "1.1"})
            ]
            
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
                            assert result.endswith(".md"), f"Missing .md extension in {scope} result: {result}"


class TestRecentPhaseFileNaming:
    """Test file naming patterns for recent_phase scope"""
    
    def test_recent_phase_file_naming_pattern(self):
        """Test recent_phase follows correct naming pattern"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-recent.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Recent Phase Test\n- [x] 1.0 Recent Phase")
            
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
                        # Expected pattern: code-review-context-recent-phase-{timestamp}.md
                        pattern = r'code-review-context-recent-phase-\d{8}-\d{6}\.md'
                        assert re.search(pattern, result), f"Pattern mismatch for recent_phase: {result}"
    
    def test_recent_phase_distinguishable_from_other_scopes(self):
        """Test that recent_phase naming is distinguishable from other scopes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-distinguish.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Distinguish Test\n- [x] 1.0 Test Phase")
            
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
                        # Should contain "recent-phase" identifier
                        assert "recent-phase" in result or "recent_phase" in result


class TestFullProjectFileNaming:
    """Test file naming patterns for full_project scope"""
    
    def test_full_project_file_naming_pattern(self):
        """Test full_project follows correct naming pattern"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-full.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Full Project Test\n- [x] 1.0 Phase One\n- [x] 2.0 Phase Two")
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    assert result is not None
                    # Expected pattern: code-review-context-full-project-{timestamp}.md
                    pattern = r'code-review-context-full-project-\d{8}-\d{6}\.md'
                    assert re.search(pattern, result), f"Pattern mismatch for full_project: {result}"
    
    def test_full_project_identifier_in_filename(self):
        """Test that full_project includes proper identifier in filename"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-identifier.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Identifier Test\n- [x] 1.0 Test Phase")
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="full_project"
                    )
                    
                    assert result is not None
                    # Should contain "full-project" identifier
                    assert "full-project" in result or "full_project" in result


class TestSpecificPhaseFileNaming:
    """Test file naming patterns for specific_phase scope"""
    
    def test_specific_phase_file_naming_pattern(self):
        """Test specific_phase follows correct naming pattern"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-specific-phase.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Specific Phase Test\n- [x] 1.0 Phase One\n- [x] 2.0 Phase Two\n- [x] 3.0 Phase Three")
            
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
                        # Expected pattern: code-review-context-phase-{phase}-{timestamp}.md
                        phase_safe = phase.replace(".", "-")
                        pattern = f'code-review-context-phase-{phase_safe}-\\d{{8}}-\\d{{6}}\\.md'
                        assert re.search(pattern, result), f"Pattern mismatch for phase {phase}: {result}"
    
    def test_specific_phase_includes_phase_number(self):
        """Test that specific_phase includes phase number in filename"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-phase-number.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Phase Number Test\n- [x] 5.0 Special Phase\n- [x] 10.0 Double Digit Phase")
            
            test_cases = [
                ("5.0", "5-0"),
                ("10.0", "10-0")
            ]
            
            for phase_input, phase_expected in test_cases:
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    with patch('builtins.open', mock_open()):
                        result = generate_review_context(
                            project_path=temp_dir,
                            scope="specific_phase",
                            phase_number=phase_input
                        )
                        
                        assert result is not None
                        # Should contain phase number with dots converted to dashes
                        assert f"phase-{phase_expected}" in result, f"Phase {phase_expected} not found in: {result}"
    
    def test_specific_phase_different_phases_different_names(self):
        """Test that different phases generate different file names"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-different-phases.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Different Phases\n- [x] 1.0 Phase One\n- [x] 2.0 Phase Two")
            
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
                    assert result_1 != result_2
                    assert "phase-1-0" in result_1
                    assert "phase-2-0" in result_2


class TestSpecificTaskFileNaming:
    """Test file naming patterns for specific_task scope"""
    
    def test_specific_task_file_naming_pattern(self):
        """Test specific_task follows correct naming pattern"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-specific-task.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Specific Task Test
- [x] 1.0 Phase One
  - [x] 1.1 Task One
  - [x] 1.2 Task Two
- [x] 2.0 Phase Two
  - [x] 2.5 Task Five
"""
            task_file.write_text(task_content)
            
            test_tasks = ["1.1", "1.2", "2.5"]
            
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
                        # Expected pattern: code-review-context-task-{task}-{timestamp}.md
                        task_safe = task.replace(".", "-")
                        pattern = f'code-review-context-task-{task_safe}-\\d{{8}}-\\d{{6}}\\.md'
                        assert re.search(pattern, result), f"Pattern mismatch for task {task}: {result}"
    
    def test_specific_task_includes_task_number(self):
        """Test that specific_task includes task number in filename"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-task-number.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Task Number Test
- [x] 3.0 Phase Three
  - [x] 3.7 Special Task
- [x] 15.0 Phase Fifteen
  - [x] 15.25 Complex Task
"""
            task_file.write_text(task_content)
            
            test_cases = [
                ("3.7", "3-7"),
                ("15.25", "15-25")
            ]
            
            for task_input, task_expected in test_cases:
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    with patch('builtins.open', mock_open()):
                        result = generate_review_context(
                            project_path=temp_dir,
                            scope="specific_task",
                            task_number=task_input
                        )
                        
                        assert result is not None
                        # Should contain task number with dots converted to dashes
                        assert f"task-{task_expected}" in result, f"Task {task_expected} not found in: {result}"
    
    def test_specific_task_different_tasks_different_names(self):
        """Test that different tasks generate different file names"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-different-tasks.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Different Tasks
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
                    assert result_1_1 != result_1_2
                    assert "task-1-1" in result_1_1
                    assert "task-1-2" in result_1_2


class TestFileNamingConflictAvoidance:
    """Test that file naming avoids conflicts"""
    
    def test_avoids_existing_file_conflicts(self):
        """Test that new files don't overwrite existing files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-conflicts.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Conflict Test\n- [x] 1.0 Test Phase")
            
            # Create an existing file with a similar name pattern
            existing_file = Path(temp_dir) / "code-review-context-recent-phase-20240101-120000.md"
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
                        # Should generate a different filename
                        assert result != str(existing_file)
    
    def test_handles_rapid_successive_calls(self):
        """Test that rapid successive calls generate unique filenames"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-rapid.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Rapid Test\n- [x] 1.0 Test Phase")
            
            results = []
            
            with patch('generate_code_review_context.detect_current_phase') as mock_detect:
                mock_detect.return_value = "1.0"
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    with patch('builtins.open', mock_open()):
                        # Make multiple rapid calls
                        for _ in range(3):
                            result = generate_review_context(
                                project_path=temp_dir,
                                scope="recent_phase"
                            )
                            assert result is not None
                            results.append(result)
            
            # All results should be unique (due to timestamps)
            assert len(set(results)) == len(results), f"Duplicate filenames found: {results}"


class TestFileNamingCustomOutput:
    """Test file naming with custom output paths"""
    
    def test_custom_output_path_overrides_naming(self):
        """Test that custom output path overrides automatic naming"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-custom.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Custom Output Test\n- [x] 1.0 Test Phase")
            
            custom_path = str(Path(temp_dir) / "my-custom-review.md")
            
            with patch('generate_code_review_context.detect_current_phase') as mock_detect:
                mock_detect.return_value = "1.0"
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    with patch('builtins.open', mock_open()):
                        result = generate_review_context(
                            project_path=temp_dir,
                            scope="recent_phase",
                            output_path=custom_path
                        )
                        
                        assert result is not None
                        # Should use custom path instead of automatic naming
                        assert custom_path in result or result == custom_path
    
    def test_custom_output_works_with_all_scopes(self):
        """Test that custom output path works with all scopes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-all-scopes.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# All Scopes Test\n- [x] 1.0 Test Phase\n  - [x] 1.1 Test Task")
            
            scopes_and_params = [
                ("recent_phase", {}),
                ("full_project", {}),
                ("specific_phase", {"phase_number": "1.0"}),
                ("specific_task", {"task_number": "1.1"})
            ]
            
            for i, (scope, extra_params) in enumerate(scopes_and_params):
                custom_path = str(Path(temp_dir) / f"custom-{scope}-{i}.md")
                
                with patch('generate_code_review_context.detect_current_phase') as mock_detect:
                    mock_detect.return_value = "1.0"
                    with patch('generate_code_review_context.get_changed_files') as mock_files:
                        mock_files.return_value = []
                        with patch('builtins.open', mock_open()):
                            result = generate_review_context(
                                project_path=temp_dir,
                                scope=scope,
                                output_path=custom_path,
                                **extra_params
                            )
                            
                            assert result is not None
                            # Should respect custom path for all scopes
                            assert custom_path in result or result == custom_path


class TestFileNamingEdgeCases:
    """Test edge cases for file naming"""
    
    def test_handles_special_characters_in_project_path(self):
        """Test file naming with special characters in project path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory with special characters
            special_dir = Path(temp_dir) / "project with spaces & symbols"
            special_dir.mkdir()
            
            task_file = special_dir / "tasks" / "tasks-special.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Special Chars Test\n- [x] 1.0 Test Phase")
            
            with patch('generate_code_review_context.detect_current_phase') as mock_detect:
                mock_detect.return_value = "1.0"
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    with patch('builtins.open', mock_open()):
                        result = generate_review_context(
                            project_path=str(special_dir),
                            scope="recent_phase"
                        )
                        
                        assert result is not None
                        # Should handle special characters gracefully
                        assert result.endswith(".md")
    
    def test_timestamp_format_consistency(self):
        """Test that timestamp format is consistent across calls"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-timestamp-format.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Timestamp Format Test\n- [x] 1.0 Test Phase")
            
            timestamp_pattern = r'\d{8}-\d{6}'  # YYYYMMDD-HHMMSS
            
            with patch('generate_code_review_context.detect_current_phase') as mock_detect:
                mock_detect.return_value = "1.0"
                with patch('generate_code_review_context.get_changed_files') as mock_files:
                    mock_files.return_value = []
                    with patch('builtins.open', mock_open()):
                        # Test multiple scopes for timestamp consistency
                        for scope in ["recent_phase", "full_project"]:
                            result = generate_review_context(
                                project_path=temp_dir,
                                scope=scope
                            )
                            
                            assert result is not None
                            matches = re.findall(timestamp_pattern, result)
                            assert len(matches) == 1, f"Should have exactly one timestamp in {scope}: {result}"
                            
                            # Verify timestamp format is valid
                            timestamp = matches[0]
                            date_part = timestamp[:8]
                            time_part = timestamp[9:]
                            
                            # Basic format validation
                            assert len(date_part) == 8, f"Date part should be 8 digits: {date_part}"
                            assert len(time_part) == 6, f"Time part should be 6 digits: {time_part}"
                            assert date_part.isdigit(), f"Date part should be numeric: {date_part}"
                            assert time_part.isdigit(), f"Time part should be numeric: {time_part}"
    
    def test_filename_length_reasonable(self):
        """Test that generated filenames are reasonable length"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-length.md"
            task_file.parent.mkdir(exist_ok=True)
            task_content = """# Length Test
- [x] 10.0 A Very Long Phase Name That Could Potentially Create Issues
  - [x] 10.25 An Even Longer Task Name With Many Words And Details
"""
            task_file.write_text(task_content)
            
            with patch('generate_code_review_context.get_changed_files') as mock_files:
                mock_files.return_value = []
                with patch('builtins.open', mock_open()):
                    result = generate_review_context(
                        project_path=temp_dir,
                        scope="specific_task",
                        task_number="10.25"
                    )
                    
                    assert result is not None
                    filename = Path(result).name
                    # Reasonable filename length (under 255 characters for most filesystems)
                    assert len(filename) < 255, f"Filename too long: {len(filename)} chars - {filename}"
                    # But not too short either (should include all necessary info)
                    assert len(filename) > 20, f"Filename too short: {len(filename)} chars - {filename}"


class TestFileNamingConsistency:
    """Test consistency of file naming across different scenarios"""
    
    def test_scope_identifier_uniqueness(self):
        """Test that each scope has a unique identifier in filename"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-uniqueness.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Uniqueness Test\n- [x] 1.0 Test Phase\n  - [x] 1.1 Test Task")
            
            scope_identifiers = []
            
            scopes_and_params = [
                ("recent_phase", {}),
                ("full_project", {}),
                ("specific_phase", {"phase_number": "1.0"}),
                ("specific_task", {"task_number": "1.1"})
            ]
            
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
                            
                            # Extract scope identifier from filename
                            filename = Path(result).name
                            # Remove base prefix and timestamp to isolate scope identifier
                            base_removed = filename.replace("code-review-context-", "")
                            timestamp_removed = re.sub(r'-\d{8}-\d{6}\.md$', '', base_removed)
                            scope_identifiers.append(timestamp_removed)
            
            # All scope identifiers should be unique
            assert len(set(scope_identifiers)) == len(scope_identifiers), f"Duplicate scope identifiers: {scope_identifiers}"
            
            # Verify expected identifiers
            expected_identifiers = ["recent-phase", "full-project", "phase-1-0", "task-1-1"]
            for expected in expected_identifiers:
                assert expected in scope_identifiers, f"Missing expected identifier: {expected}"
    
    def test_naming_pattern_documentation_compliance(self):
        """Test that naming patterns comply with documented conventions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "tasks" / "tasks-compliance.md"
            task_file.parent.mkdir(exist_ok=True)
            task_file.write_text("# Compliance Test\n- [x] 1.0 Test Phase\n  - [x] 1.1 Test Task")
            
            # Expected patterns from PRD documentation
            expected_patterns = {
                "recent_phase": r'code-review-context-recent-phase-\d{8}-\d{6}\.md',
                "full_project": r'code-review-context-full-project-\d{8}-\d{6}\.md',
                "specific_phase": r'code-review-context-phase-1-0-\d{8}-\d{6}\.md',
                "specific_task": r'code-review-context-task-1-1-\d{8}-\d{6}\.md'
            }
            
            scopes_and_params = [
                ("recent_phase", {}),
                ("full_project", {}),
                ("specific_phase", {"phase_number": "1.0"}),
                ("specific_task", {"task_number": "1.1"})
            ]
            
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
                            filename = Path(result).name
                            expected_pattern = expected_patterns[scope]
                            
                            assert re.match(expected_pattern, filename), f"Pattern mismatch for {scope}: expected {expected_pattern}, got {filename}"