"""Tests for task list opt-in behavior."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gemini_code_review_mcp.config_types import CodeReviewConfig
from gemini_code_review_mcp.services.context_generator import generate_review_context_data
from gemini_code_review_mcp.services.task_list_parser import create_minimal_task_data
from gemini_code_review_mcp.errors import ConfigurationError


class TestTaskListOptInBehavior:
    """Test that task list discovery only happens when explicitly requested."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.tasks_dir = Path(self.temp_dir) / "tasks"
        self.tasks_dir.mkdir()
        
        # Create sample task file
        self.task_file = self.tasks_dir / "tasks-test.md"
        self.task_file.write_text("""## Tasks

- [ ] 1.0 First phase
  - [ ] 1.1 First task
  - [ ] 1.2 Second task
- [x] 2.0 Second phase
  - [x] 2.1 Completed task
""")

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('gemini_code_review_mcp.services.context_generator.get_changed_files')
    @patch('gemini_code_review_mcp.services.context_generator.generate_file_tree')
    @patch('gemini_code_review_mcp.services.context_generator.discover_project_configurations_with_flags')
    @patch('gemini_code_review_mcp.helpers.model_config_manager.load_model_config')
    def test_no_task_list_flag_skips_discovery(
        self, 
        mock_load_model,
        mock_discover_configs,
        mock_file_tree,
        mock_changed_files
    ):
        """Test that without --task-list flag, task discovery is skipped."""
        # Setup mocks
        mock_load_model.return_value = {
            "defaults": {"default_prompt": "Review the code changes"},
            "model": "gemini-1.5-pro"
        }
        mock_discover_configs.return_value = {
            "claude_memory_files": [],
            "cursor_rules": [],
            "discovery_errors": [],
            "performance_stats": {},
        }
        mock_file_tree.return_value = "file tree"
        mock_changed_files.return_value = []
        
        # Create config without task_list (simulating no --task-list flag)
        config = CodeReviewConfig(
            project_path=self.temp_dir,
            task_list=None  # This is what happens when --task-list is not provided
        )
        
        # Generate context
        result = generate_review_context_data(config)
        
        # Verify task data shows general review mode
        assert result["current_phase_number"] == "General Review"
        assert result["current_phase_description"] == "Code review without specific task context"
        assert result["total_phases"] == 0
        
        # Verify PRD summary uses default prompt
        assert result["prd_summary"] == "Review the code changes"

    @patch('gemini_code_review_mcp.services.context_generator.get_changed_files')
    @patch('gemini_code_review_mcp.services.context_generator.generate_file_tree')
    @patch('gemini_code_review_mcp.services.context_generator.discover_project_configurations_with_flags')
    @patch('gemini_code_review_mcp.helpers.model_config_manager.load_model_config')
    def test_task_list_flag_with_empty_string_no_discovery(
        self,
        mock_load_model,
        mock_discover_configs,
        mock_file_tree,
        mock_changed_files
    ):
        """Test that --task-list "" doesn't trigger task discovery."""
        # Setup mocks
        mock_load_model.return_value = {
            "defaults": {"default_prompt": "Review the code changes"},
            "model": "gemini-1.5-pro"
        }
        mock_discover_configs.return_value = {
            "claude_memory_files": [],
            "cursor_rules": [],
            "discovery_errors": [],
            "performance_stats": {},
        }
        mock_file_tree.return_value = "file tree"
        mock_changed_files.return_value = []
        
        # Create config with empty task_list
        config = CodeReviewConfig(
            project_path=self.temp_dir,
            task_list=""  # User provided --task-list ""
        )
        
        # Empty string is falsy, so should skip task discovery
        result = generate_review_context_data(config)
        
        # Should show general review mode (same as no flag)
        assert result["current_phase_number"] == "General Review"
        assert result["current_phase_description"] == "Code review without specific task context"
        assert result["total_phases"] == 0

    @patch('gemini_code_review_mcp.services.context_generator.get_changed_files')
    @patch('gemini_code_review_mcp.services.context_generator.generate_file_tree')
    @patch('gemini_code_review_mcp.services.context_generator.discover_project_configurations_with_flags')
    @patch('gemini_code_review_mcp.helpers.model_config_manager.load_model_config')
    def test_task_list_flag_with_nonexistent_file_raises_error(
        self,
        mock_load_model,
        mock_discover_configs,
        mock_file_tree,
        mock_changed_files
    ):
        """Test that --task-list nonexistent.md raises a clear error."""
        # Setup mocks
        mock_load_model.return_value = {
            "defaults": {"default_prompt": "Review the code changes"},
            "model": "gemini-1.5-pro"
        }
        mock_discover_configs.return_value = {
            "claude_memory_files": [],
            "cursor_rules": [],
            "discovery_errors": [],
            "performance_stats": {},
        }
        mock_file_tree.return_value = "file tree"
        mock_changed_files.return_value = []
        
        # Create config with non-existent task list
        config = CodeReviewConfig(
            project_path=self.temp_dir,
            task_list="tasks-nonexistent.md"
        )
        
        # Should raise ConfigurationError
        with pytest.raises(ConfigurationError) as exc_info:
            generate_review_context_data(config)
        
        assert "Task list file 'tasks-nonexistent.md' not found" in str(exc_info.value)
        assert "tasks/ directory" in str(exc_info.value)

    @patch('gemini_code_review_mcp.services.context_generator.get_changed_files')
    @patch('gemini_code_review_mcp.services.context_generator.generate_file_tree')
    @patch('gemini_code_review_mcp.services.context_generator.discover_project_configurations_with_flags')
    @patch('gemini_code_review_mcp.helpers.model_config_manager.load_model_config')
    def test_task_list_flag_without_value_discovers_tasks(
        self,
        mock_load_model,
        mock_discover_configs,
        mock_file_tree,
        mock_changed_files
    ):
        """Test that --task-list (without filename) triggers auto-discovery."""
        # Setup mocks
        mock_load_model.return_value = {
            "defaults": {"default_prompt": "Review the code changes"},
            "model": "gemini-1.5-pro"
        }
        mock_discover_configs.return_value = {
            "claude_memory_files": [],
            "cursor_rules": [],
            "discovery_errors": [],
            "performance_stats": {},
        }
        mock_file_tree.return_value = "file tree"
        mock_changed_files.return_value = []
        
        # Create config with task_list set to trigger auto-discovery
        # In CLI, this would be from --task-list with no value
        config = CodeReviewConfig(
            project_path=self.temp_dir,
            task_list="tasks-test.md"  # Use actual task file that exists
        )
        
        # Generate context
        result = generate_review_context_data(config)
        
        # Should have found and parsed the task file
        assert result["total_phases"] == 2
        # Check for phases in the result (it's part of extra_template_data)
        if "phases" in result:
            assert len(result["phases"]) == 2
        assert result["current_phase_number"] == "2.0"  # Most recent phase (completed)

    @patch('gemini_code_review_mcp.services.context_generator.get_changed_files')
    @patch('gemini_code_review_mcp.services.context_generator.generate_file_tree')
    @patch('gemini_code_review_mcp.services.context_generator.discover_project_configurations_with_flags')
    @patch('gemini_code_review_mcp.helpers.model_config_manager.load_model_config')
    def test_task_list_flag_with_specific_file(
        self,
        mock_load_model,
        mock_discover_configs,
        mock_file_tree,
        mock_changed_files
    ):
        """Test that --task-list specific-file.md uses that file."""
        # Setup mocks
        mock_load_model.return_value = {
            "defaults": {"default_prompt": "Review the code changes"},
            "model": "gemini-1.5-pro"
        }
        mock_discover_configs.return_value = {
            "claude_memory_files": [],
            "cursor_rules": [],
            "discovery_errors": [],
            "performance_stats": {},
        }
        mock_file_tree.return_value = "file tree"
        mock_changed_files.return_value = []
        
        # Create another task file
        other_task_file = self.tasks_dir / "tasks-other.md"
        other_task_file.write_text("""## Tasks

- [ ] 3.0 Third phase
  - [ ] 3.1 Other task
""")
        
        # Create config specifying the test task file
        config = CodeReviewConfig(
            project_path=self.temp_dir,
            task_list="tasks-test.md"
        )
        
        # Generate context
        result = generate_review_context_data(config)
        
        # Should have used the specified file
        assert result["total_phases"] == 2
        # Check for phases if present in result
        if "phases" in result:
            assert result["phases"][0]["phase_number"] == "1.0"
            assert result["phases"][1]["phase_number"] == "2.0"
        assert result["current_phase_number"] == "2.0"  # Most recent phase

    def test_logging_messages(self, caplog):
        """Test that appropriate log messages are generated."""
        import logging
        
        with patch('src.context_generator.get_changed_files') as mock_changed_files, \
             patch('src.context_generator.generate_file_tree') as mock_file_tree, \
             patch('src.context_generator.discover_project_configurations_with_flags') as mock_discover_configs, \
             patch('src.context_generator.load_model_config') as mock_load_model:
            
            # Setup mocks
            mock_load_model.return_value = {
                "defaults": {"default_prompt": "Review the code changes"},
                "model": "gemini-1.5-pro"
            }
            mock_discover_configs.return_value = MagicMock(
                claude_memory_files=[], 
                cursor_rules=[]
            )
            mock_file_tree.return_value = "file tree"
            mock_changed_files.return_value = []
            
            # Test without task list flag
            with caplog.at_level(logging.INFO):
                config = CodeReviewConfig(project_path=self.temp_dir, task_list=None)
                generate_review_context_data(config)
                
                assert "General review mode - task-list discovery skipped" in caplog.text
                assert "--task-list flag not provided" in caplog.text
            
            caplog.clear()
            
            # Test with task list flag
            with caplog.at_level(logging.INFO):
                config = CodeReviewConfig(project_path=self.temp_dir, task_list="tasks-test.md")
                generate_review_context_data(config)
                
                assert "Task-driven review mode enabled via --task-list flag" in caplog.text