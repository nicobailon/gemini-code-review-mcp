import pytest

from gemini_code_review_mcp.config_types import CodeReviewConfig
from gemini_code_review_mcp.dependencies import DependencyContainer
from gemini_code_review_mcp.errors import ConfigurationError
from gemini_code_review_mcp.models import ReviewMode
from gemini_code_review_mcp.orchestrator import ReviewOrchestrator, StrategyRegistry
from gemini_code_review_mcp.orchestrator.init_strategies import initialize_strategies
from gemini_code_review_mcp.strategies import GeneralStrategy, GitHubPRStrategy, TaskDrivenStrategy
from gemini_code_review_mcp.strategies.factory import StrategyFactory


class TestStrategyRegistry:
    def test_register_and_get_strategy(self):
        registry = StrategyRegistry()
        registry.register(ReviewMode.TASK_DRIVEN, TaskDrivenStrategy)

        strategy_class = registry.get_strategy(ReviewMode.TASK_DRIVEN)
        assert strategy_class == TaskDrivenStrategy

    def test_get_unregistered_strategy(self):
        registry = StrategyRegistry()

        with pytest.raises(ValueError, match="No strategy registered"):
            registry.get_strategy(ReviewMode.GITHUB_PR)

    def test_list_modes(self):
        registry = StrategyRegistry()
        registry.register(ReviewMode.TASK_DRIVEN, TaskDrivenStrategy)
        registry.register(ReviewMode.GENERAL_REVIEW, GeneralStrategy)

        modes = registry.list_modes()
        assert len(modes) == 2
        assert ReviewMode.TASK_DRIVEN in modes
        assert ReviewMode.GENERAL_REVIEW in modes


class TestReviewOrchestrator:
    def setup_method(self):
        self.registry = StrategyRegistry()
        # Register strategies in our test registry
        self.registry.register(ReviewMode.TASK_DRIVEN, TaskDrivenStrategy)
        self.registry.register(ReviewMode.GENERAL_REVIEW, GeneralStrategy)
        self.registry.register(ReviewMode.GITHUB_PR, GitHubPRStrategy)
        self.orchestrator = ReviewOrchestrator(self.registry)

    def test_determine_mode_github_pr(self):
        config = CodeReviewConfig(
            github_pr_url="https://github.com/owner/repo/pull/123"
        )
        mode = self.orchestrator.determine_mode(config)
        assert mode == ReviewMode.GITHUB_PR

    def test_determine_mode_task_driven(self):
        config = CodeReviewConfig(scope="specific_phase", phase_number="1.0")
        mode = self.orchestrator.determine_mode(config)
        assert mode == ReviewMode.TASK_DRIVEN

    def test_determine_mode_general(self):
        config = CodeReviewConfig(scope="full_project")
        mode = self.orchestrator.determine_mode(config)
        assert mode == ReviewMode.GENERAL_REVIEW

    def test_execute_invalid_config(self):
        config = CodeReviewConfig(
            scope="specific_phase"
            # Missing phase_number
        )

        with pytest.raises(ConfigurationError, match="specific_phase scope requires"):
            self.orchestrator.execute(config)

    def test_execute_with_initialized_strategies(self):
        # Initialize the global registry with strategies
        from gemini_code_review_mcp.orchestrator import strategy_registry
        from gemini_code_review_mcp.orchestrator.init_strategies import initialize_strategies

        initialize_strategies()
        orchestrator = ReviewOrchestrator(strategy_registry)

        # Test that we can execute with proper setup
        config = CodeReviewConfig(
            scope="full_project", project_path="/tmp/test"  # Non-existent path
        )

        # Should succeed and return a context
        context = orchestrator.execute(config)
        assert context.mode == ReviewMode.GENERAL_REVIEW
        assert "comprehensive code review" in context.default_prompt

    def test_execute_with_factory(self):
        # Test using factory instead of registry
        container = DependencyContainer(use_production=False)
        factory = StrategyFactory(container)
        orchestrator = ReviewOrchestrator(strategy_factory=factory)

        config = CodeReviewConfig(scope="full_project")

        context = orchestrator.execute(config)
        assert context.mode == ReviewMode.GENERAL_REVIEW
        assert (
            context.default_prompt
            == "Conduct a comprehensive code review for the entire project."
        )
