import logging
from pathlib import Path
from typing import Optional

from ..config_types import CodeReviewConfig
from ..errors import ConfigurationError
from ..interfaces import (
    FileSystem,
    GitClient,
    ProductionFileSystem,
    ProductionGitClient,
)
from ..models import ReviewContext, ReviewMode
from ..services import FileFinder
from .base import ReviewStrategy

logger = logging.getLogger(__name__)


class GeneralStrategy(ReviewStrategy):
    """Strategy for general code reviews without task lists."""

    def __init__(
        self,
        filesystem: Optional[FileSystem] = None,
        git_client: Optional[GitClient] = None,
        file_finder: Optional[FileFinder] = None,
    ):
        self.fs = filesystem or ProductionFileSystem()
        self.git = git_client or ProductionGitClient()
        self.file_finder = file_finder or FileFinder(self.fs)

    def validate_config(self, config: CodeReviewConfig) -> None:
        """Validate configuration for general review."""
        if config.scope == "specific_phase":
            raise ConfigurationError(
                "Cannot use 'specific_phase' scope without a task list. "
                "Either create a task list or use --scope full_project"
            )

        if config.scope == "specific_task":
            raise ConfigurationError(
                "Cannot use 'specific_task' scope without a task list. "
                "Either create a task list or use --scope full_project"
            )

        if config.phase_number or config.task_number:
            raise ConfigurationError(
                "Phase/task numbers are only valid with task-driven reviews. "
                "Remove --phase-number and --task-number flags."
            )

        # Validate that we're not mixing incompatible options
        if config.github_pr_url:
            raise ConfigurationError(
                "Cannot use GitHub PR URL with general review. "
                "Remove --github-pr-url flag."
            )

    def print_banner(self) -> None:
        """Print general mode banner."""
        print("🔍 Operating in General Review mode.")
        print(
            "   This mode performs a comprehensive review without task list guidance."
        )

    def build_context(self, config: CodeReviewConfig) -> ReviewContext:
        """Build context for general review."""
        project_path = Path(config.project_path or ".")

        # Try to find project files (optional)
        project_files = self.file_finder.find_project_files(project_path)

        # Get PRD summary if available
        prd_summary = None
        if project_files.prd_file:
            try:
                prd_content = self.fs.read_text(project_files.prd_file)
                prd_summary = self._extract_prd_summary(prd_content)
            except Exception as e:
                logger.warning(f"Failed to read PRD file: {e}")

        # Get changed files
        changed_files = self._get_changed_files(project_path, config)

        # Determine default prompt
        default_prompt = config.default_prompt or self._generate_default_prompt(config)

        return ReviewContext(
            mode=ReviewMode.GENERAL_REVIEW,
            default_prompt=default_prompt,
            prd_summary=prd_summary,
            task_info=None,  # No task info in general mode
            changed_files=changed_files,
        )

    def _extract_prd_summary(self, prd_content: str) -> str:
        """Extract summary from PRD content."""
        # Placeholder - would use actual PRD parser
        lines = prd_content.strip().split("\n")
        summary_lines: list[str] = []
        for line in lines[1:6]:  # Skip title, take next 5 lines
            if line.strip() and not line.startswith("#"):
                summary_lines.append(line.strip())
        return " ".join(summary_lines) if summary_lines else "General project review"

    def _get_changed_files(
        self, project_path: Path, config: CodeReviewConfig
    ) -> list[str]:
        """Get list of changed files."""
        try:
            if self.git.is_git_repo(project_path):
                if config.compare_branch and config.target_branch:
                    # Compare two branches
                    changes = self.git.get_changed_files(
                        project_path,
                        base_ref=config.target_branch,
                        head_ref=config.compare_branch,
                    )
                else:
                    # Get all uncommitted changes
                    changes = self.git.get_changed_files(project_path)
                return [change.file_path for change in changes]
        except Exception as e:
            logger.warning(f"Failed to get git changes: {e}")
        return []

    def _generate_default_prompt(self, config: CodeReviewConfig) -> str:
        """Generate default prompt based on scope."""
        if config.scope == "full_project":
            return "Conduct a comprehensive code review for the entire project."
        else:
            # Default to recent changes
            return "Conduct a code review for recent changes in the project."
