"""
Factory for creating strategy instances with proper dependencies.
"""

from typing import Optional

from ..dependencies import Dependencies, DependencyContainer, get_production_container
from ..errors import ConfigurationError
from ..models import ReviewMode
from .base import ReviewStrategy
from .general import GeneralStrategy
from .github_pr import GitHubPRStrategy
from .task_driven import TaskDrivenStrategy


class StrategyFactory:
    """Factory for creating review strategies with dependencies."""

    def __init__(self, container: Optional[DependencyContainer] = None):
        """
        Initialize the factory.

        Args:
            container: Dependency container to use. If None, uses production container.
        """
        self.container = container or get_production_container()

    def create_strategy(self, mode: ReviewMode) -> ReviewStrategy:
        """
        Create a strategy instance for the given mode.

        Args:
            mode: The review mode

        Returns:
            Strategy instance with dependencies injected

        Raises:
            ConfigurationError: If mode is not supported
        """
        deps = self.container.get_dependencies()

        if mode == ReviewMode.TASK_DRIVEN:
            return TaskDrivenStrategy(
                filesystem=deps.filesystem,
                git_client=deps.git_client,
                file_finder=deps.file_finder,
            )
        elif mode == ReviewMode.GENERAL_REVIEW:
            return GeneralStrategy(
                filesystem=deps.filesystem,
                git_client=deps.git_client,
                file_finder=deps.file_finder,
            )
        elif mode == ReviewMode.GITHUB_PR:
            return GitHubPRStrategy(
                filesystem=deps.filesystem, git_client=deps.git_client
            )
        else:
            raise ConfigurationError(f"Unsupported review mode: {mode}")

    def create_task_driven_strategy(self) -> TaskDrivenStrategy:
        """Create a task-driven strategy instance."""
        deps = self.container.get_dependencies()
        return TaskDrivenStrategy(
            filesystem=deps.filesystem,
            git_client=deps.git_client,
            file_finder=deps.file_finder,
        )

    def create_general_strategy(self) -> GeneralStrategy:
        """Create a general review strategy instance."""
        deps = self.container.get_dependencies()
        return GeneralStrategy(
            filesystem=deps.filesystem,
            git_client=deps.git_client,
            file_finder=deps.file_finder,
        )

    def create_github_pr_strategy(self) -> GitHubPRStrategy:
        """Create a GitHub PR strategy instance."""
        deps = self.container.get_dependencies()
        return GitHubPRStrategy(filesystem=deps.filesystem, git_client=deps.git_client)
