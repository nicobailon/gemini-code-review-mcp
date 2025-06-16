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
from ..services.github_pr_integration import (
    get_complete_pr_analysis,
    parse_github_pr_url,
    validate_github_token,
)
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

        # Validate URL format using the service
        try:
            parse_github_pr_url(config.github_pr_url)
        except ValueError as e:
            raise ConfigurationError(
                format_error_message("invalid_pr_url", url=config.github_pr_url)
            ) from e

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

        # Validate GitHub token is available and valid
        try:
            import os
            token = os.getenv("GITHUB_TOKEN")
            if token and not validate_github_token(token):
                logger.warning(
                    "GitHub token validation failed. PR analysis may be limited."
                )
            elif not token:
                logger.warning(
                    "GITHUB_TOKEN not set. PR analysis may be limited."
                )
        except Exception as e:
            logger.warning(f"Could not validate GitHub token: {e}")

    def print_banner(self) -> None:
        """Print GitHub PR mode banner."""
        print("🐙 Operating in GitHub PR Review mode.")
        print("   This mode analyzes a GitHub Pull Request for comprehensive review.")

    def build_context(self, config: CodeReviewConfig) -> ReviewContext:
        """Build context for GitHub PR review using the actual GitHub API."""
        try:
            # Get complete PR analysis from the service
            pr_analysis = get_complete_pr_analysis(config.github_pr_url or "")
            
            # Extract data from the analysis
            pr_data = pr_analysis.get("pr_data", {})
            file_changes = pr_analysis.get("file_changes", {})
            
            # Build the prompt
            default_prompt = (
                config.default_prompt
                or f"Review GitHub PR #{pr_data.get('pr_number', '?')}: {pr_data.get('title', 'Unknown Title')}"
            )
            
            # Extract changed files list
            changed_files = [
                file_info["path"]
                for file_info in file_changes.get("changed_files", [])
            ]
            
            # Build summary for PRD field
            prd_summary = f"""GitHub PR #{pr_data.get('pr_number', '?')}: {pr_data.get('title', 'Unknown Title')}
Author: {pr_data.get('author', 'Unknown')}
Target Branch: {pr_data.get('target_branch', 'Unknown')} ← {pr_data.get('source_branch', 'Unknown')}

{pr_data.get('body', 'No description provided.')}"""

            return ReviewContext(
                mode=ReviewMode.GITHUB_PR,
                default_prompt=default_prompt,
                prd_summary=prd_summary,
                task_info=None,
                changed_files=changed_files,
                # Store the full PR analysis for use in context generation
                metadata={
                    "pr_analysis": pr_analysis,
                    "pr_url": config.github_pr_url,
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch GitHub PR data: {e}")
            # Fall back to basic information from URL
            pr_info = parse_github_pr_url(config.github_pr_url or "")
            
            default_prompt = (
                config.default_prompt
                or f"Review GitHub PR #{pr_info['pr_number']} in {pr_info['owner']}/{pr_info['repo']}"
            )
            
            return ReviewContext(
                mode=ReviewMode.GITHUB_PR,
                default_prompt=default_prompt,
                prd_summary=f"GitHub PR #{pr_info['pr_number']} (Failed to fetch details: {str(e)})",
                task_info=None,
                changed_files=[],
                metadata={
                    "pr_url": config.github_pr_url,
                    "error": str(e),
                }
            )