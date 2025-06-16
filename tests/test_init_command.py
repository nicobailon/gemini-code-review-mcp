"""Tests for the init command."""

import tempfile
from pathlib import Path

import pytest

from gemini_code_review_mcp.cli.init_command import create_argument_parser, init_project


class TestInitCommand:
    def test_init_project_creates_structure(self, tmp_path):
        """Test that init_project creates the expected directory structure."""
        # Initialize project
        success = init_project(
            project_path=tmp_path, project_name="test-project", verbose=False
        )

        assert success is True

        # Check directories
        assert (tmp_path / "tasks").is_dir()
        assert (tmp_path / "docs").is_dir()
        assert (tmp_path / "src").is_dir()
        assert (tmp_path / "tests").is_dir()

        # Check files
        assert (tmp_path / ".gitignore").is_file()
        assert (tmp_path / ".env.example").is_file()
        assert (tmp_path / "CLAUDE.md").is_file()
        assert (tmp_path / "README.md").is_file()
        assert (tmp_path / "tasks" / "tasks-example.md").is_file()
        assert (tmp_path / "src" / "__init__.py").is_file()
        assert (tmp_path / "tests" / "__init__.py").is_file()
        assert (tmp_path / "tests" / "test_example.py").is_file()

    def test_init_project_without_optional_dirs(self, tmp_path):
        """Test initialization without src and tests directories."""
        success = init_project(
            project_path=tmp_path, include_src=False, include_tests=False, verbose=False
        )

        assert success is True

        # Check directories
        assert (tmp_path / "tasks").is_dir()
        assert (tmp_path / "docs").is_dir()
        assert not (tmp_path / "src").exists()
        assert not (tmp_path / "tests").exists()

        # Check core files still exist
        assert (tmp_path / ".gitignore").is_file()
        assert (tmp_path / ".env.example").is_file()

    def test_init_project_without_claude_md(self, tmp_path):
        """Test initialization without CLAUDE.md."""
        success = init_project(
            project_path=tmp_path, include_claude_md=False, verbose=False
        )

        assert success is True
        assert not (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / "README.md").is_file()

    def test_init_project_custom_name(self, tmp_path):
        """Test initialization with custom project name."""
        success = init_project(
            project_path=tmp_path, project_name="My Custom Project", verbose=False
        )

        assert success is True

        # Check that README contains custom name
        readme_content = (tmp_path / "README.md").read_text()
        assert "# My Custom Project" in readme_content

    def test_init_project_no_overwrite(self, tmp_path):
        """Test that existing files are not overwritten by default."""
        # Create an existing file
        existing_file = tmp_path / ".gitignore"
        existing_file.write_text("existing content")

        success = init_project(project_path=tmp_path, verbose=False)

        assert success is True

        # Check that existing file was not overwritten
        assert existing_file.read_text() == "existing content"

    def test_init_project_force_overwrite(self, tmp_path):
        """Test that force flag overwrites existing files."""
        # Create an existing file
        existing_file = tmp_path / ".gitignore"
        existing_file.write_text("existing content")

        success = init_project(project_path=tmp_path, force=True, verbose=False)

        assert success is True

        # Check that existing file was overwritten
        assert existing_file.read_text() != "existing content"
        assert "Gemini Code Review files" in existing_file.read_text()

    def test_argument_parser(self):
        """Test that argument parser is configured correctly."""
        parser = create_argument_parser()

        # Test default args
        args = parser.parse_args([])
        assert args.path == "."
        assert args.name is None
        assert args.no_src is False
        assert args.no_tests is False
        assert args.no_claude_md is False
        assert args.force is False
        assert args.quiet is False

        # Test custom args
        args = parser.parse_args(
            [
                "/custom/path",
                "--name",
                "Custom Project",
                "--no-src",
                "--no-tests",
                "--force",
                "--quiet",
            ]
        )
        assert args.path == "/custom/path"
        assert args.name == "Custom Project"
        assert args.no_src is True
        assert args.no_tests is True
        assert args.force is True
        assert args.quiet is True

    def test_env_template_content(self, tmp_path):
        """Test that .env.example has correct content."""
        init_project(project_path=tmp_path, verbose=False)

        env_content = (tmp_path / ".env.example").read_text()
        assert "GOOGLE_AI_API_KEY=your-api-key-here" in env_content
        assert "GEMINI_TEMPERATURE" in env_content
        assert "GEMINI_MODEL" in env_content
        assert "GEMINI_ENABLE_CACHE" in env_content

    def test_gitignore_content(self, tmp_path):
        """Test that .gitignore has correct patterns."""
        init_project(project_path=tmp_path, verbose=False)

        gitignore_content = (tmp_path / ".gitignore").read_text()
        assert "/code-review-*.md" in gitignore_content
        assert "/.env" in gitignore_content
        assert "/.gemini-cache/" in gitignore_content

    def test_sample_task_list_content(self, tmp_path):
        """Test that sample task list has correct structure."""
        init_project(project_path=tmp_path, verbose=False)

        task_content = (tmp_path / "tasks" / "tasks-example.md").read_text()
        assert "## Relevant Files" in task_content
        assert "## Tasks" in task_content
        assert "- [ ] 1.0" in task_content
        assert "- [ ] 2.0" in task_content
        assert "- [ ] 3.0" in task_content
