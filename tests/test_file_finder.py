from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.interfaces import InMemoryFileSystem
from src.services import FileFinder, ProjectFiles


class TestFileFinder:
    def setup_method(self):
        """Set up test environment before each test."""
        self.fs = InMemoryFileSystem()
        self.finder = FileFinder(self.fs)
        self.project_path = Path("/project")

        # Create basic directory structure
        self.fs.mkdir(self.project_path, parents=True)
        self.fs.mkdir(self.project_path / "tasks")

    def test_find_no_files(self):
        """Test when no PRD or task files exist."""
        result = self.finder.find_project_files(self.project_path)
        assert result.prd_file is None
        assert result.task_list_file is None

    def test_find_prd_in_tasks_dir(self):
        """Test finding PRD file in tasks directory."""
        prd_path = self.project_path / "tasks" / "prd-feature.md"
        self.fs.write_text(prd_path, "# PRD Content")

        result = self.finder.find_project_files(self.project_path)
        assert result.prd_file == prd_path
        assert result.task_list_file is None

    def test_find_prd_in_root_dir(self):
        """Test finding PRD file in root directory."""
        prd_path = self.project_path / "prd.md"
        self.fs.write_text(prd_path, "# PRD Content")

        result = self.finder.find_project_files(self.project_path)
        assert result.prd_file == prd_path
        assert result.task_list_file is None

    def test_find_task_list(self):
        """Test finding task list file."""
        task_path = self.project_path / "tasks" / "tasks-feature.md"
        self.fs.write_text(task_path, "## Tasks")

        result = self.finder.find_project_files(self.project_path)
        assert result.prd_file is None
        assert result.task_list_file == task_path

    def test_find_both_files(self):
        """Test finding both PRD and task list."""
        prd_path = self.project_path / "tasks" / "prd-feature.md"
        task_path = self.project_path / "tasks" / "tasks-feature.md"
        self.fs.write_text(prd_path, "# PRD")
        self.fs.write_text(task_path, "## Tasks")

        result = self.finder.find_project_files(self.project_path)
        assert result.prd_file == prd_path
        assert result.task_list_file == task_path

    def test_find_specific_task_list(self):
        """Test finding specific task list by name."""
        # Create multiple task lists
        task1 = self.project_path / "tasks" / "tasks-feature1.md"
        task2 = self.project_path / "tasks" / "tasks-feature2.md"
        self.fs.write_text(task1, "## Tasks 1")
        self.fs.write_text(task2, "## Tasks 2")

        # Find specific one
        result = self.finder.find_project_files(
            self.project_path, task_list_name="tasks-feature2.md"
        )
        assert result.task_list_file == task2

    def test_find_specific_task_list_without_extension(self):
        """Test finding specific task list without .md extension."""
        task_path = self.project_path / "tasks" / "tasks-feature.md"
        self.fs.write_text(task_path, "## Tasks")

        result = self.finder.find_project_files(
            self.project_path, task_list_name="tasks-feature"
        )
        assert result.task_list_file == task_path

    def test_multiple_prd_files_warning(self):
        """Test warning when multiple PRD files exist."""
        prd1 = self.project_path / "tasks" / "prd-feature1.md"
        prd2 = self.project_path / "tasks" / "prd-feature2.md"
        self.fs.write_text(prd1, "# PRD 1")
        self.fs.write_text(prd2, "# PRD 2")

        result = self.finder.find_project_files(self.project_path)
        # Should use the first one (alphabetically)
        assert result.prd_file in [prd1, prd2]

    def test_generic_task_list_fallback(self):
        """Test finding generic tasks.md when no tasks-*.md exists."""
        task_path = self.project_path / "tasks" / "tasks.md"
        self.fs.write_text(task_path, "## Generic Tasks")

        result = self.finder.find_project_files(self.project_path)
        assert result.task_list_file == task_path

    def test_no_tasks_directory(self):
        """Test when tasks directory doesn't exist."""
        # Remove tasks directory
        self.fs.rmdir(self.project_path / "tasks")

        result = self.finder.find_project_files(self.project_path)
        assert result.prd_file is None
        assert result.task_list_file is None

    def test_specified_task_list_not_found(self):
        """Test when specified task list doesn't exist."""
        result = self.finder.find_project_files(
            self.project_path, task_list_name="non-existent.md"
        )
        assert result.task_list_file is None

    def test_ignore_directories_in_glob(self):
        """Test that directories matching patterns are ignored."""
        # Create a directory that matches the pattern
        dir_path = self.project_path / "tasks" / "prd-folder.md"
        self.fs.mkdir(dir_path)

        # Create an actual file
        file_path = self.project_path / "tasks" / "prd-real.md"
        self.fs.write_text(file_path, "# Real PRD")

        result = self.finder.find_project_files(self.project_path)
        assert result.prd_file == file_path

    def test_glob_files_error_handling(self):
        """Test error handling in _glob_files method."""
        # Create a mock filesystem that raises an exception
        mock_fs = Mock()
        mock_fs.glob.side_effect = Exception("Glob error")
        mock_fs.is_file.return_value = True
        
        finder = FileFinder(mock_fs)
        
        # Test that _glob_files handles the error gracefully
        with patch('src.services.file_finder.logger') as mock_logger:
            result = finder._glob_files(Path("/test"), "*.md")
            assert result == []
            mock_logger.error.assert_called_once()
            assert "Error globbing *.md" in mock_logger.error.call_args[0][0]

    def test_multiple_task_files_warning_with_logging(self):
        """Test that warning is logged when multiple task files found."""
        # Create multiple task files
        task1 = self.project_path / "tasks" / "tasks-feature1.md"
        task2 = self.project_path / "tasks" / "tasks-feature2.md"
        self.fs.write_text(task1, "# Tasks 1")
        self.fs.write_text(task2, "# Tasks 2")
        
        with patch('src.services.file_finder.logger') as mock_logger:
            result = self.finder.find_project_files(self.project_path)
            # Result should have one of the task files
            assert result.task_list_file in [task1, task2]
            # Warning should be logged
            mock_logger.warning.assert_called_once()
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "Multiple task list files found" in warning_msg
            assert "tasks-feature1.md" in warning_msg
            assert "tasks-feature2.md" in warning_msg
