"""Initialize and register all review strategies."""

from ..models import ReviewMode
from ..strategies import GeneralStrategy, GitHubPRStrategy, TaskDrivenStrategy
from . import strategy_registry


def initialize_strategies():
    """Register all available strategies."""
    strategy_registry.register(ReviewMode.TASK_DRIVEN, TaskDrivenStrategy)
    strategy_registry.register(ReviewMode.GENERAL_REVIEW, GeneralStrategy)
    strategy_registry.register(ReviewMode.GITHUB_PR, GitHubPRStrategy)
