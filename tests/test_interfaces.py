from pathlib import Path

import pytest

from src.interfaces import (
    GitCommit,
    GitFileChange,
    InMemoryFileSystem,
    InMemoryGitClient,
)


class TestInMemoryFileSystem:
    def setup_method(self):
        self.fs = InMemoryFileSystem()

    def test_basic_file_operations(self):
        # Create directory
        self.fs.mkdir("/test", parents=True)
        assert self.fs.exists("/test")
        assert self.fs.is_dir("/test")
        assert not self.fs.is_file("/test")

        # Write file
        self.fs.write_text("/test/file.txt", "Hello World")
        assert self.fs.exists("/test/file.txt")
        assert self.fs.is_file("/test/file.txt")
        assert not self.fs.is_dir("/test/file.txt")

        # Read file
        content = self.fs.read_text("/test/file.txt")
        assert content == "Hello World"

        # List directory
        items = self.fs.list_dir("/test")
        assert len(items) == 1
        assert items[0] == Path("/test/file.txt")

    def test_glob_patterns(self):
        self.fs.mkdir("/project/src", parents=True)
        self.fs.mkdir("/project/tests", parents=True)
        self.fs.write_text("/project/src/main.py", "")
        self.fs.write_text("/project/src/utils.py", "")
        self.fs.write_text("/project/tests/test_main.py", "")

        # Test simple glob
        py_files = self.fs.glob("/project/src", "*.py")
        assert len(py_files) == 2
        assert Path("/project/src/main.py") in py_files
        assert Path("/project/src/utils.py") in py_files

        # Test recursive glob
        all_py = self.fs.glob("/project", "**/*.py")
        assert len(all_py) == 3

    def test_file_not_found_errors(self):
        with pytest.raises(FileNotFoundError):
            self.fs.read_text("/nonexistent.txt")

        with pytest.raises(FileNotFoundError):
            self.fs.write_text("/nodir/file.txt", "content")

        with pytest.raises(FileNotFoundError):
            self.fs.list_dir("/nodir")

    def test_remove_operations(self):
        self.fs.mkdir("/test", parents=True)
        self.fs.write_text("/test/file.txt", "content")

        # Remove file
        self.fs.remove("/test/file.txt")
        assert not self.fs.exists("/test/file.txt")

        # Remove directory
        self.fs.rmdir("/test")
        assert not self.fs.exists("/test")

        # Cannot remove non-empty directory
        self.fs.mkdir("/test2", parents=True)
        self.fs.write_text("/test2/file.txt", "content")
        with pytest.raises(OSError):
            self.fs.rmdir("/test2")


class TestInMemoryGitClient:
    def setup_method(self):
        self.git = InMemoryGitClient()
        self.repo_path = "/project"

    def test_basic_repo_setup(self):
        # Initially not a repo
        assert not self.git.is_git_repo(self.repo_path)

        # Setup repo
        self.git.setup_repo(
            self.repo_path,
            current_branch="main",
            files={"README.md": "# Project"},
            changes=[
                GitFileChange(
                    file_path="src/main.py", status="Added", additions=50, deletions=0
                )
            ],
        )

        # Now it's a repo
        assert self.git.is_git_repo(self.repo_path)
        assert self.git.get_repo_root(self.repo_path) == Path(self.repo_path)
        assert self.git.get_current_branch(self.repo_path) == "main"

    def test_changed_files(self):
        changes = [
            GitFileChange("file1.py", "Modified", 10, 5),
            GitFileChange("file2.py", "Added", 20, 0),
            GitFileChange("file3.py", "Deleted", 0, 15),
        ]

        self.git.setup_repo(self.repo_path, changes=changes)

        result = self.git.get_changed_files(self.repo_path)
        assert len(result) == 3
        assert result[0].file_path == "file1.py"
        assert result[0].additions == 10
        assert result[0].deletions == 5

    def test_commits(self):
        commits = [
            GitCommit(
                sha="abc123",
                author="Test User",
                date="2024-01-01",
                message="Initial commit",
            ),
            GitCommit(
                sha="def456",
                author="Test User",
                date="2024-01-02",
                message="Add feature",
            ),
        ]

        self.git.setup_repo(self.repo_path, commits=commits)

        result = self.git.get_commits(self.repo_path, limit=10)
        assert len(result) == 2
        assert result[0].sha == "abc123"
        assert result[1].message == "Add feature"

    def test_file_content(self):
        self.git.setup_repo(
            self.repo_path,
            files={"README.md": "# Project README", "src/main.py": "print('Hello')"},
        )

        content = self.git.get_file_content(self.repo_path, "README.md")
        assert content == "# Project README"

        content = self.git.get_file_content(self.repo_path, "nonexistent.txt")
        assert content is None

    def test_remote_url(self):
        self.git.setup_repo(self.repo_path)

        url = self.git.get_remote_url(self.repo_path)
        assert url == "https://github.com/test/repo.git"

        url = self.git.get_remote_url(self.repo_path, "upstream")
        assert url is None
