"""Test error handling and error taxonomy."""

import pytest

from gemini_code_review_mcp.errors import (
    ERROR_MESSAGES,
    ConfigurationError,
    ContextBuildError,
    DependencyError,
    FileSystemError,
    GeminiError,
    GitError,
    NetworkError,
    ReviewModeError,
    TaskListError,
    ValidationError,
    format_error_message,
)


class TestErrorTaxonomy:
    def test_base_error(self):
        error = GeminiError("Test error")
        assert str(error) == "Test error"
        assert error.exit_code == 1

    def test_specific_errors_exit_codes(self):
        errors_and_codes = [
            (ConfigurationError("config"), 2),
            (ValidationError("validation"), 3),
            (GitError("git"), 4),
            (FileSystemError("fs"), 5),
            (TaskListError("task"), 6),
            (ReviewModeError("mode"), 7),
            (NetworkError("network"), 8),
            (DependencyError("dep"), 9),
            (ContextBuildError("context"), 10),
        ]

        for error, expected_code in errors_and_codes:
            assert error.exit_code == expected_code

    def test_error_inheritance(self):
        # All custom errors should inherit from GeminiError
        error_classes = [
            ConfigurationError,
            ValidationError,
            GitError,
            FileSystemError,
            TaskListError,
            ReviewModeError,
            NetworkError,
            DependencyError,
            ContextBuildError,
        ]

        for error_class in error_classes:
            assert issubclass(error_class, GeminiError)
            assert issubclass(error_class, Exception)


class TestErrorMessages:
    def test_format_error_message_success(self):
        # Test successful formatting
        msg = format_error_message("no_task_list")
        assert "No task list file found" in msg
        assert "tasks/tasks-feature-name.md" in msg

        msg = format_error_message("invalid_pr_url", url="bad-url")
        assert "Invalid GitHub PR URL format: bad-url" in msg

        msg = format_error_message("phase_not_found", phase="2.0", available="1.0, 3.0")
        assert "Phase 2.0 not found" in msg
        assert "Available phases: 1.0, 3.0" in msg

    def test_format_error_message_missing_params(self):
        # Test with missing parameters
        msg = format_error_message("invalid_pr_url")
        # Should handle missing params gracefully
        assert "Invalid GitHub PR URL format:" in msg

    def test_format_error_message_unknown_key(self):
        # Test with unknown error key
        msg = format_error_message("unknown_error", foo="bar")
        assert "Unknown error" in msg
        assert "unknown_error" in msg

    def test_all_error_messages_defined(self):
        # Check that all error message keys exist
        expected_keys = [
            "no_task_list",
            "invalid_pr_url",
            "git_not_installed",
            "not_git_repo",
            "phase_not_found",
            "task_not_found",
            "mutually_exclusive_modes",
            "file_not_found",
            "permission_denied",
            "project_path_not_found",
        ]

        for key in expected_keys:
            assert key in ERROR_MESSAGES
            assert isinstance(ERROR_MESSAGES[key], str)


class TestErrorUsageInStrategies:
    """Test that strategies properly use the error types."""

    def test_configuration_errors_are_raised(self):
        from gemini_code_review_mcp.config_types import CodeReviewConfig
        from gemini_code_review_mcp.strategies import GeneralStrategy, GitHubPRStrategy, TaskDrivenStrategy

        # Task-driven strategy
        strategy = TaskDrivenStrategy()
        config = CodeReviewConfig(scope="specific_phase")  # Missing phase_number
        with pytest.raises(ConfigurationError) as exc_info:
            strategy.validate_config(config)
        assert exc_info.value.exit_code == 2

        # General strategy
        strategy = GeneralStrategy()
        config = CodeReviewConfig(scope="specific_phase")  # Invalid for general
        with pytest.raises(ConfigurationError) as exc_info:
            strategy.validate_config(config)
        assert exc_info.value.exit_code == 2

        # GitHub PR strategy
        strategy = GitHubPRStrategy()
        config = CodeReviewConfig()  # Missing github_pr_url
        with pytest.raises(ConfigurationError) as exc_info:
            strategy.validate_config(config)
        assert exc_info.value.exit_code == 2
