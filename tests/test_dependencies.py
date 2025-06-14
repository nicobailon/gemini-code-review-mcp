import pytest

from src.dependencies import (
    DependencyContainer,
    get_container,
    get_production_container,
    get_test_container,
)
from src.interfaces import (
    InMemoryFileSystem,
    InMemoryGitClient,
    ProductionFileSystem,
    ProductionGitClient,
)
from src.services import FileFinder


class TestDependencyContainer:
    def test_production_container(self):
        container = DependencyContainer(use_production=True)

        # Check that production implementations are used
        assert isinstance(container.filesystem, ProductionFileSystem)
        assert isinstance(container.git_client, ProductionGitClient)
        assert isinstance(container.file_finder, FileFinder)

        # Check that same instances are returned (singleton behavior)
        fs1 = container.filesystem
        fs2 = container.filesystem
        assert fs1 is fs2

    def test_test_container(self):
        container = DependencyContainer(use_production=False)

        # Check that in-memory implementations are used
        assert isinstance(container.filesystem, InMemoryFileSystem)
        assert isinstance(container.git_client, InMemoryGitClient)
        assert isinstance(container.file_finder, FileFinder)

    def test_file_finder_uses_correct_filesystem(self):
        container = DependencyContainer(use_production=False)

        # File finder should use the same filesystem instance
        assert container.file_finder.fs is container.filesystem

    def test_get_dependencies(self):
        container = DependencyContainer(use_production=False)
        deps = container.get_dependencies()

        assert deps.filesystem is container.filesystem
        assert deps.git_client is container.git_client
        assert deps.file_finder is container.file_finder

    def test_reset(self):
        container = DependencyContainer(use_production=False)

        # Get instances
        fs1 = container.filesystem
        git1 = container.git_client

        # Reset
        container.reset()

        # Get new instances
        fs2 = container.filesystem
        git2 = container.git_client

        # Should be different instances after reset
        assert fs1 is not fs2
        assert git1 is not git2


class TestGlobalContainers:
    def test_get_production_container(self):
        container = get_production_container()
        assert container.use_production is True
        assert isinstance(container.filesystem, ProductionFileSystem)

    def test_get_test_container(self):
        container = get_test_container()
        assert container.use_production is False
        assert isinstance(container.filesystem, InMemoryFileSystem)

    def test_get_container(self):
        prod = get_container(use_production=True)
        assert prod is get_production_container()

        test = get_container(use_production=False)
        assert test is get_test_container()
