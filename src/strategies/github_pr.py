import logging
from typing import Optional

from ..config_types import CodeReviewConfig
from ..errors import ConfigurationError, format_error_message
from ..interfaces import (
    FileSystem,
    GitClient,
    ProductionFileSystem,
    ProductionGitClient,
)
from ..models import ReviewContext, ReviewMode
from .base import ReviewStrategy

logger = logging.getLogger(__name__)


class GitHubPRStrategy(ReviewStrategy):
    """Strategy for GitHub Pull Request reviews."""

    def __init__(
        self,
        filesystem: Optional[FileSystem] = None,
        git_client: Optional[GitClient] = None,
    ):
        self.fs = filesystem or ProductionFileSystem()
        self.git = git_client or ProductionGitClient()

    def validate_config(self, config: CodeReviewConfig) -> None:
        """Validate configuration for GitHub PR review."""
        if not config.github_pr_url:
            raise ConfigurationError("GitHub PR review requires --github-pr-url")

        # Validate URL format
        if not self._is_valid_github_pr_url(config.github_pr_url):
            raise ConfigurationError(
                format_error_message("invalid_pr_url", url=config.github_pr_url)
            )

        # Check for incompatible options
        if config.phase_number or config.task_number:
            raise ConfigurationError(
                "Cannot use phase/task numbers with GitHub PR review. "
                "Remove --phase-number and --task-number flags."
            )

        if config.scope in ["specific_phase", "specific_task"]:
            raise ConfigurationError(
                f"Cannot use '{config.scope}' scope with GitHub PR review. "
                "GitHub PR mode determines its own scope."
            )

    def print_banner(self) -> None:
        """Print GitHub PR mode banner."""
        print("🐙 Operating in GitHub PR Review mode.")
        print("   This mode analyzes a GitHub Pull Request for comprehensive review.")

    def build_context(self, config: CodeReviewConfig) -> ReviewContext:
        """Build context for GitHub PR review."""
        # Extract PR information from URL
        pr_info = self._parse_github_pr_url(config.github_pr_url or "")

        # In a real implementation, we would:
        # 1. Use GitHub API to fetch PR details
        # 2. Get the list of changed files
        # 3. Get commit messages
        # 4. Get PR description

        # For now, return a placeholder context
        default_prompt = (
            config.default_prompt
            or f"Review GitHub PR #{pr_info['number']} in {pr_info['owner']}/{pr_info['repo']}"
        )

        # Placeholder - would get actual changed files from GitHub API
        changed_files: list[str] = []

        return ReviewContext(
            mode=ReviewMode.GITHUB_PR,
            default_prompt=default_prompt,
            prd_summary=f"GitHub PR #{pr_info['number']}: [PR Title would go here]",
            task_info=None,
            changed_files=changed_files,
        )

    def _is_valid_github_pr_url(self, url: str) -> bool:
        """Check if URL is a valid GitHub PR URL."""
        import re

        pattern = r"^https://github\.com/[\w-]+/[\w-]+/pull/\d+/?$"
        return bool(re.match(pattern, url))

    def _parse_github_pr_url(self, url: str) -> dict[str, str]:
        """Parse GitHub PR URL to extract components."""
        import re

        pattern = r"^https://github\.com/([\w-]+)/([\w-]+)/pull/(\d+)/?$"
        match = re.match(pattern, url)
        if not match:
            raise ConfigurationError(f"Invalid GitHub PR URL: {url}")

        return {
            "owner": match.group(1),
            "repo": match.group(2),
            "number": match.group(3),
        }
