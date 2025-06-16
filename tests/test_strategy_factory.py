import pytest

from gemini_code_review_mcp.dependencies import DependencyContainer
from gemini_code_review_mcp.errors import ConfigurationError
from gemini_code_review_mcp.models import ReviewMode
from gemini_code_review_mcp.strategies import GeneralStrategy, GitHubPRStrategy, TaskDrivenStrategy
from gemini_code_review_mcp.strategies.factory import StrategyFactory


class TestStrategyFactory:
    def setup_method(self):
        # Use test container with in-memory implementations
        self.container = DependencyContainer(use_production=False)
        self.factory = StrategyFactory(self.container)

    def test_create_task_driven_strategy(self):
        strategy = self.factory.create_strategy(ReviewMode.TASK_DRIVEN)
        assert isinstance(strategy, TaskDrivenStrategy)
        # Check dependencies are injected
        assert strategy.fs is self.container.filesystem
        assert strategy.git is self.container.git_client
        assert strategy.file_finder is self.container.file_finder

    def test_create_general_strategy(self):
        strategy = self.factory.create_strategy(ReviewMode.GENERAL_REVIEW)
        assert isinstance(strategy, GeneralStrategy)
        # Check dependencies are injected
        assert strategy.fs is self.container.filesystem
        assert strategy.git is self.container.git_client
        assert strategy.file_finder is self.container.file_finder

    def test_create_github_pr_strategy(self):
        strategy = self.factory.create_strategy(ReviewMode.GITHUB_PR)
        assert isinstance(strategy, GitHubPRStrategy)
        # Check dependencies are injected
        assert strategy.fs is self.container.filesystem
        assert strategy.git is self.container.git_client

    def test_create_unsupported_mode(self):
        # Create a fake mode by directly setting a value
        # This tests the error handling
        with pytest.raises(ConfigurationError, match="Unsupported review mode"):
            # We can't create a new enum value, so we'll test with None
            self.factory.create_strategy(None)  # type: ignore

    def test_specific_factory_methods(self):
        # Test the convenience methods
        task_driven = self.factory.create_task_driven_strategy()
        assert isinstance(task_driven, TaskDrivenStrategy)

        general = self.factory.create_general_strategy()
        assert isinstance(general, GeneralStrategy)

        github_pr = self.factory.create_github_pr_strategy()
        assert isinstance(github_pr, GitHubPRStrategy)

    def test_factory_with_production_container(self):
        # Test with default production container
        factory = StrategyFactory()
        strategy = factory.create_strategy(ReviewMode.GENERAL_REVIEW)
        assert isinstance(strategy, GeneralStrategy)
        # Should use cached production implementations
        from gemini_code_review_mcp.interfaces import CachedFileSystem, CachedGitClient, ProductionFileSystem, ProductionGitClient

        assert isinstance(strategy.fs, CachedFileSystem)
        assert isinstance(strategy.fs._fs, ProductionFileSystem)
        assert isinstance(strategy.git, CachedGitClient)
        assert isinstance(strategy.git._git, ProductionGitClient)
