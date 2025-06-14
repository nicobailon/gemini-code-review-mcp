import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..interfaces import FileSystem

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProjectFiles:
    """Container for discovered project files."""

    prd_file: Optional[Path] = None
    task_list_file: Optional[Path] = None


class FileFinder:
    """Service responsible for locating PRD and task list files."""

    def __init__(self, filesystem: FileSystem):
        self.fs = filesystem

    def find_project_files(
        self, project_path: Path, task_list_name: Optional[str] = None
    ) -> ProjectFiles:
        """
        Find PRD and task list files in the project.

        Args:
            project_path: Path to project root
            task_list_name: Optional specific task list file name

        Returns:
            ProjectFiles object with discovered files
        """
        tasks_dir = project_path / "tasks"

        # Check if tasks directory exists
        if not self.fs.exists(tasks_dir):
            logger.info(
                f"Tasks directory not found: {tasks_dir}. "
                "This is OK - the tool can work without task lists."
            )
            return ProjectFiles()

        prd_file = self._find_prd_file(project_path, tasks_dir)
        task_list_file = self._find_task_list_file(
            project_path, tasks_dir, task_list_name
        )

        return ProjectFiles(prd_file=prd_file, task_list_file=task_list_file)

    def _find_prd_file(self, project_path: Path, tasks_dir: Path) -> Optional[Path]:
        """Find PRD file in tasks directory or project root."""
        # Look for PRD files in tasks directory
        prd_files = self._glob_files(tasks_dir, "prd-*.md")

        if not prd_files:
            # Also check root directory
            root_prd = project_path / "prd.md"
            if self.fs.exists(root_prd) and self.fs.is_file(root_prd):
                prd_files = [root_prd]

        if not prd_files:
            logger.info("No PRD file found. This is optional.")
            return None

        if len(prd_files) > 1:
            logger.warning(
                f"Multiple PRD files found: {[str(f) for f in prd_files]}. "
                f"Using: {prd_files[0]}"
            )

        return prd_files[0]

    def _find_task_list_file(
        self, project_path: Path, tasks_dir: Path, task_list_name: Optional[str] = None
    ) -> Optional[Path]:
        """Find task list file."""
        if task_list_name:
            # Look for specific task list
            specific_path = tasks_dir / task_list_name
            if self.fs.exists(specific_path) and self.fs.is_file(specific_path):
                return specific_path

            # Try with .md extension if not provided
            if not task_list_name.endswith(".md"):
                specific_path = tasks_dir / f"{task_list_name}.md"
                if self.fs.exists(specific_path) and self.fs.is_file(specific_path):
                    return specific_path

            logger.error(
                f"Specified task list not found: {task_list_name} " f"in {tasks_dir}"
            )
            return None

        # Find all task list files
        task_files = self._glob_files(tasks_dir, "tasks-*.md")

        if not task_files:
            # Also check for generic task list
            generic_task_list = tasks_dir / "tasks.md"
            if self.fs.exists(generic_task_list) and self.fs.is_file(generic_task_list):
                task_files = [generic_task_list]

        if not task_files:
            logger.info(
                "No task list file found. For task-driven reviews, create "
                "a file like 'tasks/tasks-feature-name.md'"
            )
            return None

        # Find the most recently modified task list
        if len(task_files) > 1:
            # In production, we'd check modification times
            # For now, just use the first one and log a warning
            logger.warning(
                f"Multiple task list files found: {[str(f) for f in task_files]}. "
                f"Using: {task_files[0]}. "
                "Tip: Specify which one with --task-list flag"
            )

        return task_files[0]

    def _glob_files(self, directory: Path, pattern: str) -> List[Path]:
        """Helper to glob files and filter to only files."""
        try:
            all_matches = self.fs.glob(directory, pattern)
            return [p for p in all_matches if self.fs.is_file(p)]
        except Exception as e:
            logger.error(f"Error globbing {pattern} in {directory}: {e}")
            return []
