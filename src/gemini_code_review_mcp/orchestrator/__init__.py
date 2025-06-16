import logging
from typing import Any, Dict, Optional, Type

from ..config_types import CodeReviewConfig
from ..errors import GeminiError
from ..models import ReviewContext, ReviewMode
from ..strategies.base import ReviewStrategy

logger = logging.getLogger(__name__)


class StrategyRegistry:
    """Registry for review strategies."""

    def __init__(self):
        self._strategies: Dict[ReviewMode, Type[ReviewStrategy]] = {}

    def register(self, mode: ReviewMode, strategy_class: Type[ReviewStrategy]) -> None:
        """Register a strategy for a specific mode."""
        self._strategies[mode] = strategy_class
        logger.debug(f"Registered strategy {strategy_class.__name__} for mode {mode}")

    def get_strategy(self, mode: ReviewMode) -> Type[ReviewStrategy]:
        """Get the strategy class for a mode."""
        if mode not in self._strategies:
            raise ValueError(f"No strategy registered for mode: {mode}")
        return self._strategies[mode]

    def list_modes(self) -> list[ReviewMode]:
        """List all registered modes."""
        return list(self._strategies.keys())


# Global registry instance
strategy_registry = StrategyRegistry()


class ReviewOrchestrator:
    """Main orchestrator that selects and executes review strategies."""

    def __init__(
        self,
        registry: Optional[StrategyRegistry] = None,
        strategy_factory: Optional[Any] = None,
    ):
        self.registry = registry or strategy_registry
        self.strategy_factory = strategy_factory

    def determine_mode(self, config: CodeReviewConfig) -> ReviewMode:
        """
        Determine the review mode based on configuration.

        Args:
            config: The code review configuration

        Returns:
            The detected review mode
        """
        # Check for GitHub PR mode
        if config.github_pr_url:
            return ReviewMode.GITHUB_PR

        # Check if we have task list data
        # This would be determined by checking if task files exist
        # For now, we'll use a simple heuristic
        if config.scope in ["specific_phase", "specific_task"]:
            return ReviewMode.TASK_DRIVEN

        # Default to general review
        return ReviewMode.GENERAL_REVIEW

    def execute(self, config: CodeReviewConfig) -> ReviewContext:
        """
        Execute the review process.

        Args:
            config: The code review configuration

        Returns:
            ReviewContext with all necessary data
        """
        # Determine the mode
        mode = self.determine_mode(config)
        logger.info(f"Determined review mode: {mode.name}")

        # Get the appropriate strategy
        if self.strategy_factory:
            # Use factory if available
            from ..strategies.factory import StrategyFactory

            if isinstance(self.strategy_factory, StrategyFactory):
                strategy = self.strategy_factory.create_strategy(mode)
            else:
                strategy = self.strategy_factory(mode)
        else:
            # Fall back to registry
            strategy_class = self.registry.get_strategy(mode)
            strategy = strategy_class()

        # Validate configuration
        try:
            strategy.validate_config(config)
        except GeminiError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during validation: {e}")
            # Wrap in GeminiError for consistent handling
            raise GeminiError(f"Validation failed: {e}") from e

        # Print mode banner
        strategy.print_banner()

        # Build and return context
        context = strategy.build_context(config)
        logger.info(f"Successfully built review context for mode: {mode.name}")

        return context


__all__ = [
    "ReviewOrchestrator",
    "StrategyRegistry",
    "strategy_registry",
]
