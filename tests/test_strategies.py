from pathlib import Path

import pytest

from gemini_code_review_mcp.config_types import CodeReviewConfig
from gemini_code_review_mcp.errors import ConfigurationError, TaskListError
from gemini_code_review_mcp.interfaces import GitFileChange, InMemoryFileSystem, InMemoryGitClient
from gemini_code_review_mcp.models import ReviewMode, TaskInfo
from gemini_code_review_mcp.services import FileFinder
from gemini_code_review_mcp.strategies import GeneralStrategy, GitHubPRStrategy, TaskDrivenStrategy


class TestTaskDrivenStrategy:
    def setup_method(self):
        self.fs = InMemoryFileSystem()
        self.git = InMemoryGitClient()
        self.file_finder = FileFinder(self.fs)
        self.strategy = TaskDrivenStrategy(
            filesystem=self.fs, git_client=self.git, file_finder=self.file_finder
        )

        # Setup basic project structure
        self.fs.mkdir("/project", parents=True)
        self.fs.mkdir("/project/tasks")
        self.git.setup_repo("/project", current_branch="main")

    def test_validate_config_success(self):
        config = CodeReviewConfig(project_path="/project", scope="recent_phase")
        # Should not raise
        self.strategy.validate_config(config)

    def test_validate_config_specific_phase_missing_number(self):
        config = CodeReviewConfig(project_path="/project", scope="specific_phase")
        with pytest.raises(ConfigurationError, match="specific_phase scope requires"):
            self.strategy.validate_config(config)

    def test_validate_config_specific_task_missing_number(self):
        config = CodeReviewConfig(project_path="/project", scope="specific_task")
        with pytest.raises(ConfigurationError, match="specific_task scope requires"):
            self.strategy.validate_config(config)

    def test_validate_config_incompatible_github_pr(self):
        config = CodeReviewConfig(
            project_path="/project",
            scope="recent_phase",
            github_pr_url="https://github.com/owner/repo/pull/123",
        )
        with pytest.raises(ConfigurationError, match="Cannot use GitHub PR URL"):
            self.strategy.validate_config(config)

    def test_print_banner(self, capsys):
        self.strategy.print_banner()
        captured = capsys.readouterr()
        assert "📝 Operating in Task-Driven mode" in captured.out
        assert "task list to guide" in captured.out

    def test_build_context_no_task_list(self):
        config = CodeReviewConfig(project_path="/project", scope="recent_phase")
        with pytest.raises(TaskListError, match="No task list file found"):
            self.strategy.build_context(config)

    def test_build_context_with_task_list(self):
        # Create task list file
        self.fs.write_text(
            "/project/tasks/tasks-feature.md", "## Tasks\n- [ ] 1.0 Phase 1"
        )

        # Setup git changes
        self.git.setup_repo(
            "/project", changes=[GitFileChange("src/main.py", "Added", 10, 0)]
        )

        config = CodeReviewConfig(project_path="/project", scope="recent_phase")

        context = self.strategy.build_context(config)
        assert context.mode == ReviewMode.TASK_DRIVEN
        assert context.task_info is not None
        assert len(context.changed_files) == 1
        assert context.changed_files[0] == "src/main.py"


class TestGeneralStrategy:
    def setup_method(self):
        self.fs = InMemoryFileSystem()
        self.git = InMemoryGitClient()
        self.file_finder = FileFinder(self.fs)
        self.strategy = GeneralStrategy(
            filesystem=self.fs, git_client=self.git, file_finder=self.file_finder
        )

        # Setup basic project structure
        self.fs.mkdir("/project", parents=True)
        self.git.setup_repo("/project", current_branch="main")

    def test_validate_config_success(self):
        config = CodeReviewConfig(project_path="/project", scope="full_project")
        # Should not raise
        self.strategy.validate_config(config)

    def test_validate_config_invalid_specific_phase(self):
        config = CodeReviewConfig(
            project_path="/project", scope="specific_phase", phase_number="1.0"
        )
        with pytest.raises(
            ConfigurationError, match="Cannot use 'specific_phase' scope"
        ):
            self.strategy.validate_config(config)

    def test_validate_config_invalid_phase_number(self):
        config = CodeReviewConfig(
            project_path="/project", scope="full_project", phase_number="1.0"
        )
        with pytest.raises(
            ConfigurationError, match="Phase/task numbers are only valid"
        ):
            self.strategy.validate_config(config)

    def test_print_banner(self, capsys):
        self.strategy.print_banner()
        captured = capsys.readouterr()
        assert "🔍 Operating in General Review mode" in captured.out
        assert "comprehensive review without task list" in captured.out

    def test_build_context(self):
        # Setup git changes
        self.git.setup_repo(
            "/project",
            changes=[
                GitFileChange("README.md", "Modified", 5, 2),
                GitFileChange("src/utils.py", "Added", 20, 0),
            ],
        )

        config = CodeReviewConfig(project_path="/project", scope="full_project")

        context = self.strategy.build_context(config)
        assert context.mode == ReviewMode.GENERAL_REVIEW
        assert context.task_info is None
        assert len(context.changed_files) == 2
        assert "README.md" in context.changed_files
        assert "src/utils.py" in context.changed_files
        assert "comprehensive code review" in context.default_prompt


class TestGitHubPRStrategy:
    def setup_method(self):
        self.fs = InMemoryFileSystem()
        self.git = InMemoryGitClient()
        self.strategy = GitHubPRStrategy(filesystem=self.fs, git_client=self.git)

    def test_validate_config_success(self):
        config = CodeReviewConfig(
            github_pr_url="https://github.com/owner/repo/pull/123"
        )
        # Should not raise
        self.strategy.validate_config(config)

    def test_validate_config_missing_url(self):
        config = CodeReviewConfig()
        with pytest.raises(ConfigurationError, match="GitHub PR review requires"):
            self.strategy.validate_config(config)

    def test_validate_config_invalid_url(self):
        config = CodeReviewConfig(github_pr_url="https://example.com/not-a-pr")
        with pytest.raises(ConfigurationError, match="Invalid GitHub PR URL format"):
            self.strategy.validate_config(config)

    def test_validate_config_incompatible_phase_number(self):
        config = CodeReviewConfig(
            github_pr_url="https://github.com/owner/repo/pull/123", phase_number="1.0"
        )
        with pytest.raises(ConfigurationError, match="Cannot use phase/task numbers"):
            self.strategy.validate_config(config)

    def test_print_banner(self, capsys):
        self.strategy.print_banner()
        captured = capsys.readouterr()
        assert "🐙 Operating in GitHub PR Review mode" in captured.out
        assert "analyzes a GitHub Pull Request" in captured.out

    def test_build_context(self):
        config = CodeReviewConfig(
            github_pr_url="https://github.com/owner/repo/pull/456"
        )

        context = self.strategy.build_context(config)
        assert context.mode == ReviewMode.GITHUB_PR
        assert context.task_info is None
        assert "PR #456" in context.default_prompt
        assert "owner/repo" in context.default_prompt
        assert "GitHub PR #456" in context.prd_summary
