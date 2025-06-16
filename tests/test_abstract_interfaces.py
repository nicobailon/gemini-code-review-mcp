"""Test abstract interfaces to ensure they define the right methods."""

from abc import ABC

import pytest

from gemini_code_review_mcp.interfaces import FileSystem, GitClient
from gemini_code_review_mcp.strategies.base import ReviewStrategy


class TestAbstractInterfaces:
    def test_filesystem_is_abstract(self):
        # Cannot instantiate abstract class
        with pytest.raises(TypeError):
            FileSystem()  # type: ignore

        # Check required methods
        required_methods = {
            "exists",
            "is_file",
            "is_dir",
            "read_text",
            "write_text",
            "list_dir",
            "glob",
            "mkdir",
            "remove",
            "rmdir",
            "get_cwd",
            "resolve",
        }
        for method in required_methods:
            assert hasattr(FileSystem, method)
            assert getattr(FileSystem, method).__isabstractmethod__

    def test_git_client_is_abstract(self):
        # Cannot instantiate abstract class
        with pytest.raises(TypeError):
            GitClient()  # type: ignore

        # Check required methods
        required_methods = {
            "is_git_repo",
            "get_repo_root",
            "get_current_branch",
            "get_changed_files",
            "get_file_diff",
            "get_commits",
            "get_remote_url",
            "get_file_content",
        }
        for method in required_methods:
            assert hasattr(GitClient, method)
            assert getattr(GitClient, method).__isabstractmethod__

    def test_review_strategy_protocol(self):
        # ReviewStrategy is a Protocol, not ABC, but check it has required methods
        required_methods = {"validate_config", "print_banner", "build_context"}
        for method in required_methods:
            assert hasattr(ReviewStrategy, method)
