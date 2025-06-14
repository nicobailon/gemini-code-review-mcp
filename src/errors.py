"""
Centralized error taxonomy for the application.

This module defines all custom exceptions used throughout the codebase,
with appropriate exit codes for CLI usage.
"""


class GeminiError(Exception):
    """Base exception for all Gemini code review errors."""

    exit_code: int = 1

    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return user-friendly error message."""
        return self.message or self.__class__.__name__


class ConfigurationError(GeminiError):
    """Raised when there's an issue with configuration."""

    exit_code = 2

    def __str__(self) -> str:
        """Return user-friendly error message."""
        return f"Configuration Error: {self.message}"


class ValidationError(GeminiError):
    """Raised when validation fails."""

    exit_code = 3

    def __str__(self) -> str:
        """Return user-friendly error message."""
        return f"Validation Error: {self.message}"


class GitError(GeminiError):
    """Raised when Git operations fail."""

    exit_code = 4

    def __str__(self) -> str:
        """Return user-friendly error message."""
        return f"Git Error: {self.message}"


class FileSystemError(GeminiError):
    """Raised when file system operations fail."""

    exit_code = 5

    def __str__(self) -> str:
        """Return user-friendly error message."""
        return f"File System Error: {self.message}"


class TaskListError(GeminiError):
    """Raised when there's an issue with task list parsing or handling."""

    exit_code = 6

    def __str__(self) -> str:
        """Return user-friendly error message."""
        return f"Task List Error: {self.message}"


class ReviewModeError(GeminiError):
    """Raised when there's an issue with review mode selection or execution."""

    exit_code = 7

    def __str__(self) -> str:
        """Return user-friendly error message."""
        return f"Review Mode Error: {self.message}"


class NetworkError(GeminiError):
    """Raised when network operations fail (e.g., GitHub API)."""

    exit_code = 8

    def __str__(self) -> str:
        """Return user-friendly error message."""
        return f"Network Error: {self.message}"


class DependencyError(GeminiError):
    """Raised when required dependencies are missing or misconfigured."""

    exit_code = 9

    def __str__(self) -> str:
        """Return user-friendly error message."""
        return f"Dependency Error: {self.message}"


class ContextBuildError(GeminiError):
    """Raised when building review context fails."""

    exit_code = 10

    def __str__(self) -> str:
        """Return user-friendly error message."""
        return f"Context Build Error: {self.message}"


class CacheError(GeminiError):
    """Raised when cache operations fail."""

    exit_code = 11

    def __str__(self) -> str:
        """Return user-friendly error message."""
        return f"Cache Error: {self.message}"


# Error messages for common scenarios
ERROR_MESSAGES = {
    "no_task_list": (
        "No task list file found. Task-driven review requires a task list.\n"
        "Create a file like 'tasks/tasks-feature-name.md' or use --scope full_project"
    ),
    "invalid_pr_url": (
        "Invalid GitHub PR URL format: {url}\n"
        "Expected format: https://github.com/owner/repo/pull/123"
    ),
    "git_not_installed": (
        "Git is not installed or not in PATH.\n"
        "Please install Git: https://git-scm.com/downloads"
    ),
    "not_git_repo": ("Not a Git repository.\n" "Initialize with: git init"),
    "phase_not_found": (
        "Phase {phase} not found in task list.\n" "Available phases: {available}"
    ),
    "task_not_found": (
        "Task {task} not found in task list.\n" "Available tasks: {available}"
    ),
    "mutually_exclusive_modes": (
        "Multiple review modes detected. Please use only one:\n" "{modes}"
    ),
    "file_not_found": (
        "File not found: {path}\n" "Please check the path and try again."
    ),
    "permission_denied": (
        "Permission denied accessing: {path}\n" "Check file permissions."
    ),
    "project_path_not_found": (
        "Project path not found: {path}\n" "Please provide a valid project path."
    ),
}


def format_error_message(error_key: str, **kwargs) -> str:
    """
    Format an error message with the given parameters.

    Args:
        error_key: Key from ERROR_MESSAGES
        **kwargs: Parameters to format the message

    Returns:
        Formatted error message
    """
    template = ERROR_MESSAGES.get(error_key, f"Unknown error: {error_key}")
    try:
        return template.format(**kwargs)
    except KeyError:
        return f"{template} (formatting error with params: {kwargs})"
