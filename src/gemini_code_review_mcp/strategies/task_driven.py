import logging
from pathlib import Path
from typing import Any, Optional

from ..config_types import CodeReviewConfig
from ..errors import ConfigurationError, TaskListError, format_error_message
from ..interfaces import (
    FileSystem,
    GitClient,
    ProductionFileSystem,
    ProductionGitClient,
)
from ..models import ReviewContext, ReviewMode, TaskInfo
from ..progress import print_info, progress
from ..services import FileFinder
from .base import ReviewStrategy

logger = logging.getLogger(__name__)


class TaskDrivenStrategy(ReviewStrategy):
    """Strategy for task-driven code reviews."""

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
        """Validate configuration for task-driven review."""
        if config.scope == "specific_phase" and not config.phase_number:
            raise ConfigurationError(
                "specific_phase scope requires --phase-number to be specified. "
                "Example: --scope specific_phase --phase-number 2.0"
            )

        if config.scope == "specific_task" and not config.task_number:
            raise ConfigurationError(
                "specific_task scope requires --task-number to be specified. "
                "Example: --scope specific_task --task-number 2.1"
            )

        # Validate that we're not mixing incompatible options
        if config.github_pr_url:
            raise ConfigurationError(
                "Cannot use GitHub PR URL with task-driven review. "
                "Use one mode at a time."
            )

    def print_banner(self) -> None:
        """Print task-driven mode banner."""
        print("📝 Operating in Task-Driven mode.")
        print("   This mode uses your task list to guide the review process.")

    def build_context(self, config: CodeReviewConfig) -> ReviewContext:
        """Build context for task-driven review."""
        project_path = Path(config.project_path or ".")

        # Find project files
        print_info("Searching for project files...")
        with progress("Finding PRD and task list files"):
            project_files = self.file_finder.find_project_files(
                project_path, config.task_list
            )

        if not project_files.task_list_file:
            raise TaskListError(format_error_message("no_task_list"))

        # Parse task list (placeholder - would use actual parser)
        task_info = self._extract_task_info(config, project_files)

        # Get PRD summary if available
        prd_summary = None
        if project_files.prd_file:
            try:
                prd_content = self.fs.read_text(project_files.prd_file)
                # Extract summary (placeholder - would use actual parser)
                prd_summary = self._extract_prd_summary(prd_content)
            except Exception as e:
                logger.warning(f"Failed to read PRD file: {e}")

        # Get changed files
        changed_files = self._get_changed_files(project_path, config)

        # Determine default prompt
        default_prompt = config.default_prompt or self._generate_default_prompt(
            config, task_info
        )

        return ReviewContext(
            mode=ReviewMode.TASK_DRIVEN,
            default_prompt=default_prompt,
            prd_summary=prd_summary,
            task_info=task_info,
            changed_files=changed_files,
        )

    def _extract_task_info(
        self, config: CodeReviewConfig, project_files: Any
    ) -> TaskInfo:
        """Extract task information based on scope."""
        # This is a placeholder - in real implementation would parse task list
        if config.scope == "specific_phase":
            return TaskInfo(
                phase_number=config.phase_number or "1.0",
                task_number=None,
                description=f"Phase {config.phase_number} implementation",
            )
        elif config.scope == "specific_task":
            task_num = config.task_number or "1.0"
            return TaskInfo(
                phase_number=task_num.split(".")[0] + ".0",
                task_number=task_num,
                description=f"Task {task_num} implementation",
            )
        else:
            # Recent phase - would find most recent incomplete phase
            return TaskInfo(
                phase_number="1.0",
                task_number=None,
                description="Most recent phase implementation",
            )

    def _extract_prd_summary(self, prd_content: str) -> str:
        """Extract summary from PRD content."""
        # Placeholder - would use actual PRD parser
        lines = prd_content.strip().split("\n")
        # Take first few non-empty, non-header lines as summary
        summary_lines: list[str] = []
        for line in lines[1:6]:  # Skip title, take next 5 lines
            if line.strip() and not line.startswith("#"):
                summary_lines.append(line.strip())
        return " ".join(summary_lines) if summary_lines else "Project implementation"

    def _get_changed_files(
        self, project_path: Path, config: CodeReviewConfig
    ) -> list[str]:
        """Get list of changed files."""
        try:
            if self.git.is_git_repo(project_path):
                changes = self.git.get_changed_files(project_path)
                return [change.file_path for change in changes]
        except Exception as e:
            logger.warning(f"Failed to get git changes: {e}")
        return []

    def _generate_default_prompt(
        self, config: CodeReviewConfig, task_info: TaskInfo
    ) -> str:
        """Generate default prompt based on scope."""
        if config.scope == "specific_task":
            return f"Conduct a code review for task {task_info.task_number}: {task_info.description}"
        elif config.scope == "specific_phase":
            return f"Conduct a code review for phase {task_info.phase_number}: {task_info.description}"
        else:
            return f"Conduct a code review for the most recent phase: {task_info.description}"
