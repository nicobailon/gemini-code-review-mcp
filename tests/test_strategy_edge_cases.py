"""Test edge cases and error handling in strategies."""

from pathlib import Path

import pytest

from gemini_code_review_mcp.config_types import CodeReviewConfig
from gemini_code_review_mcp.errors import ConfigurationError
from gemini_code_review_mcp.interfaces import InMemoryFileSystem, InMemoryGitClient
from gemini_code_review_mcp.models import ReviewMode
from gemini_code_review_mcp.services import FileFinder
from gemini_code_review_mcp.strategies import GeneralStrategy, GitHubPRStrategy, TaskDrivenStrategy


class TestStrategyEdgeCases:
    def setup_method(self):
        self.fs = InMemoryFileSystem()
        self.git = InMemoryGitClient()
        self.file_finder = FileFinder(self.fs)

        # Setup basic project
        self.fs.mkdir("/project", parents=True)
        self.fs.mkdir("/project/tasks")

    def test_task_driven_with_prd_read_error(self):
        """Test when PRD file exists but can't be read."""
        strategy = TaskDrivenStrategy(
            filesystem=self.fs, git_client=self.git, file_finder=self.file_finder
        )

        # Create task list
        self.fs.write_text("/project/tasks/tasks-feature.md", "## Tasks")

        # Create PRD that will cause read error
        # In real scenario this would be permission error, but we'll simulate
        prd_path = Path("/project/tasks/prd-feature.md")
        self.fs.write_text(prd_path, "# PRD")
        # Remove it to simulate read error
        self.fs.remove(prd_path)

        # Should still work without PRD
        self.git.setup_repo("/project")
        config = CodeReviewConfig(project_path="/project", scope="recent_phase")

        # Mock the file finder to return a non-existent PRD
        class MockFileFinder:
            def find_project_files(self, *args, **kwargs):
                from gemini_code_review_mcp.services import ProjectFiles

                return ProjectFiles(
                    prd_file=prd_path,  # Non-existent
                    task_list_file=Path("/project/tasks/tasks-feature.md"),
                )

        strategy.file_finder = MockFileFinder()
        context = strategy.build_context(config)

        # Should work but without PRD summary
        assert context.mode == ReviewMode.TASK_DRIVEN
        assert context.prd_summary is None

    def test_task_driven_specific_phase_with_info(self):
        """Test task driven strategy with specific phase."""
        strategy = TaskDrivenStrategy(
            filesystem=self.fs, git_client=self.git, file_finder=self.file_finder
        )

        # Create files
        self.fs.write_text(
            "/project/tasks/tasks-feature.md", "## Tasks\n- [ ] 2.0 Phase 2"
        )
        self.fs.write_text(
            "/project/tasks/prd-feature.md",
            "# Project PRD\n\nThis is a test project for implementing features.",
        )

        self.git.setup_repo("/project")
        config = CodeReviewConfig(
            project_path="/project", scope="specific_phase", phase_number="2.0"
        )

        context = strategy.build_context(config)
        assert context.task_info.phase_number == "2.0"
        assert "Phase 2.0 implementation" in context.task_info.description
        assert (
            context.prd_summary == "This is a test project for implementing features."
        )

    def test_general_strategy_branch_comparison(self):
        """Test general strategy with branch comparison."""
        strategy = GeneralStrategy(
            filesystem=self.fs, git_client=self.git, file_finder=self.file_finder
        )

        # Setup git with branch comparison
        from gemini_code_review_mcp.interfaces import GitFileChange

        self.git.setup_repo(
            "/project",
            changes=[
                GitFileChange("feature.py", "Added", 100, 0),
                GitFileChange("test_feature.py", "Added", 50, 0),
            ],
        )

        config = CodeReviewConfig(
            project_path="/project",
            scope="full_project",
            compare_branch="feature-branch",
            target_branch="main",
        )

        context = strategy.build_context(config)
        assert len(context.changed_files) == 2
        assert "feature.py" in context.changed_files

    def test_general_strategy_no_git_repo(self):
        """Test general strategy when not in a git repo."""
        strategy = GeneralStrategy(
            filesystem=self.fs, git_client=self.git, file_finder=self.file_finder
        )

        # Don't setup git repo
        config = CodeReviewConfig(project_path="/project", scope="full_project")

        context = strategy.build_context(config)
        # Should work but with no changed files
        assert context.mode == ReviewMode.GENERAL_REVIEW
        assert len(context.changed_files) == 0

    def test_github_pr_custom_prompt(self):
        """Test GitHub PR strategy with custom prompt."""
        strategy = GitHubPRStrategy(filesystem=self.fs, git_client=self.git)

        config = CodeReviewConfig(
            github_pr_url="https://github.com/owner/repo/pull/789",
            default_prompt="Custom PR review instructions",
        )

        context = strategy.build_context(config)
        assert context.default_prompt == "Custom PR review instructions"
        assert "GitHub PR #789" in context.prd_summary

    def test_strategy_validation_edge_cases(self):
        """Test various validation edge cases."""
        # General strategy with GitHub PR URL
        general = GeneralStrategy(self.fs, self.git, self.file_finder)
        config = CodeReviewConfig(
            scope="full_project", github_pr_url="https://github.com/owner/repo/pull/123"
        )
        with pytest.raises(ConfigurationError, match="Cannot use GitHub PR URL"):
            general.validate_config(config)

        # GitHub PR with specific_phase scope
        github = GitHubPRStrategy(self.fs, self.git)
        config = CodeReviewConfig(
            github_pr_url="https://github.com/owner/repo/pull/123",
            scope="specific_phase",
        )
        with pytest.raises(
            ConfigurationError, match="Cannot use 'specific_phase' scope"
        ):
            github.validate_config(config)
