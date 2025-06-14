from abc import abstractmethod
from typing import Protocol

from ..config_types import CodeReviewConfig
from ..models import ReviewContext


class ReviewStrategy(Protocol):
    """Protocol for review strategies."""

    @abstractmethod
    def validate_config(self, config: CodeReviewConfig) -> None:
        """
        Validate that the configuration is appropriate for this strategy.

        Raises:
            ValueError: If configuration is invalid for this strategy
        """
        pass

    @abstractmethod
    def print_banner(self) -> None:
        """Print user-facing banner indicating the active mode."""
        pass

    @abstractmethod
    def build_context(self, config: CodeReviewConfig) -> ReviewContext:
        """
        Build the review context based on the configuration.

        Args:
            config: The code review configuration

        Returns:
            ReviewContext object with all necessary data
        """
        pass
