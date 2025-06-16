#!/usr/bin/env python3
"""
Unit tests for file_context_generator module.
"""

import os
import tempfile
from pathlib import Path
from typing import List, Tuple
from unittest.mock import Mock, patch

import pytest

from gemini_code_review_mcp.file_context_generator import (
    build_file_selection_summary,
    format_file_context_template,
    generate_file_context_data,
    read_selected_files,
    save_file_context,
)
from gemini_code_review_mcp.file_context_types import (
    FileContentData,
    FileContextConfig,
    FileContextResult,
    FileSelection,
)


class TestGenerateFileContextData:
    """Tests for generate_file_context_data function."""

    def test_generate_simple_context(self):
        """Test generating context from simple file selection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello():\n    print('Hello')\n")

            config = FileContextConfig(
                file_selections=[
                    FileSelection(
                        path=str(test_file), line_ranges=None, include_full=True
                    )
                ],
                project_path=tmpdir,
                include_claude_memory=False,
                include_cursor_rules=False,
                auto_meta_prompt=False,
            )

            result = generate_file_context_data(config)

            assert isinstance(result, FileContextResult)
            assert len(result.included_files) == 1
            assert len(result.excluded_files) == 0
            assert result.total_tokens > 0
            assert "def hello():" in result.content
            assert "<selected_files>" in result.content

    def test_generate_with_line_ranges(self):
        """Test generating context with line ranges."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file with multiple lines
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("line1\nline2\nline3\nline4\nline5\n")

            config = FileContextConfig(
                file_selections=[
                    FileSelection(
                        path=str(test_file), line_ranges=[(2, 4)], include_full=True
                    )
                ],
                project_path=tmpdir,
                include_claude_memory=False,
                include_cursor_rules=False,
                auto_meta_prompt=False,
            )

            result = generate_file_context_data(config)

            assert len(result.included_files) == 1
            assert "line2" in result.content
            assert "line3" in result.content
            assert "line4" in result.content
            assert "line1" not in result.content
            assert "line5" not in result.content

    def test_generate_with_token_limit(self):
        """Test token limit enforcement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create large file that exceeds token limit
            large_file = Path(tmpdir) / "large.py"
            large_content = "x" * 10000  # ~2500 tokens
            large_file.write_text(large_content)

            small_file = Path(tmpdir) / "small.py"
            small_file.write_text("small content")

            config = FileContextConfig(
                file_selections=[
                    FileSelection(
                        path=str(small_file), line_ranges=None, include_full=True
                    ),
                    FileSelection(
                        path=str(large_file), line_ranges=None, include_full=True
                    ),
                ],
                project_path=tmpdir,
                token_limit=1000,  # Low limit
                include_claude_memory=False,
                include_cursor_rules=False,
                auto_meta_prompt=False,
            )

            result = generate_file_context_data(config)

            # Small file should be included
            assert len(result.included_files) == 1
            assert result.included_files[0].path == str(small_file)

            # Large file should be excluded
            assert len(result.excluded_files) == 1
            assert "large.py" in result.excluded_files[0][0]
            assert "token limit" in result.excluded_files[0][1]

    @patch("gemini_code_review_mcp.services.file_context_generator.discover_project_configurations_with_flags")
    @patch("gemini_code_review_mcp.services.file_context_generator.format_configuration_context_for_ai")
    def test_generate_with_configurations(
        self, mock_format: Mock, mock_discover: Mock
    ) -> None:
        """Test including Claude memory and Cursor rules."""
        # Mock configuration discovery
        mock_discover.return_value = {
            "claude_memory_files": [{"content": "claude rules"}],
            "cursor_rules": [{"content": "cursor rules"}],
            "discovery_errors": [],
        }
        mock_format.return_value = "Formatted configuration content"

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("code")

            config = FileContextConfig(
                file_selections=[
                    FileSelection(
                        path=str(test_file), line_ranges=None, include_full=True
                    )
                ],
                project_path=tmpdir,
                include_claude_memory=True,
                include_cursor_rules=True,
                auto_meta_prompt=False,
            )

            result = generate_file_context_data(config)

            assert mock_discover.called
            assert mock_format.called
            assert result.configuration_content == "Formatted configuration content"
            assert "<configuration_context>" in result.content

    @patch("gemini_code_review_mcp.services.file_context_generator.generate_optimized_meta_prompt")
    def test_generate_with_auto_meta_prompt(self, mock_meta_prompt: Mock) -> None:
        """Test auto meta-prompt generation."""
        mock_meta_prompt.return_value = {
            "generated_prompt": "Generated meta-prompt",
            "analysis_completed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("code")

            config = FileContextConfig(
                file_selections=[
                    FileSelection(
                        path=str(test_file), line_ranges=None, include_full=True
                    )
                ],
                project_path=tmpdir,
                auto_meta_prompt=True,
                user_instructions=None,  # No custom instructions
                include_claude_memory=False,
                include_cursor_rules=False,
            )

            result = generate_file_context_data(config)

            assert mock_meta_prompt.called
            assert result.meta_prompt == "Generated meta-prompt"
            assert "Generated meta-prompt" in result.content


class TestReadSelectedFiles:
    """Tests for read_selected_files function."""

    def test_read_multiple_files(self):
        """Test reading multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = Path(tmpdir) / "file1.py"
            file2 = Path(tmpdir) / "file2.py"
            file1.write_text("content1")
            file2.write_text("content2")

            selections = [
                FileSelection(path=str(file1), line_ranges=None, include_full=True),
                FileSelection(path=str(file2), line_ranges=None, include_full=True),
            ]

            results = read_selected_files(selections, tmpdir)

            assert len(results) == 2
            assert all(isinstance(r, FileContentData) for r in results)
            assert "content1" in results[0].content
            assert "content2" in results[1].content

    def test_read_with_error_propagation(self):
        """Test that errors are propagated."""
        selections = [
            FileSelection(
                path="/does/not/exist.py", line_ranges=None, include_full=True
            )
        ]

        with pytest.raises(Exception):
            read_selected_files(selections)


class TestBuildFileSelectionSummary:
    """Tests for build_file_selection_summary function."""

    def test_build_summary_included_only(self):
        """Test building summary with only included files."""
        included = [
            FileContentData(
                path="file1.py",
                absolute_path="/path/to/file1.py",
                content="content",
                line_ranges=None,
                total_lines=10,
                included_lines=10,
                estimated_tokens=50,
            ),
            FileContentData(
                path="file2.py",
                absolute_path="/path/to/file2.py",
                content="content",
                line_ranges=[(5, 15)],
                total_lines=20,
                included_lines=11,
                estimated_tokens=30,
            ),
        ]
        excluded: List[Tuple[str, str]] = []

        summary = build_file_selection_summary(included, excluded)

        assert "Selected 2 of 2 files" in summary
        assert "Total lines: 21" in summary
        assert "Estimated tokens: 80" in summary
        assert "file1.py: 10 lines" in summary
        assert "file2.py (lines 5-15): 11 lines" in summary

    def test_build_summary_with_excluded(self):
        """Test building summary with excluded files."""
        included = [
            FileContentData(
                path="file1.py",
                absolute_path="/path/to/file1.py",
                content="content",
                line_ranges=None,
                total_lines=10,
                included_lines=10,
                estimated_tokens=50,
            )
        ]
        excluded = [("file2.py", "File not found"), ("file3.py", "Permission denied")]

        summary = build_file_selection_summary(included, excluded)

        assert "Selected 1 of 3 files" in summary
        assert "Excluded files:" in summary
        assert "file2.py: File not found" in summary
        assert "file3.py: Permission denied" in summary


class TestFormatFileContextTemplate:
    """Tests for format_file_context_template function."""

    def test_format_basic_template(self):
        """Test formatting basic template."""
        included = [
            FileContentData(
                path="test.py",
                absolute_path="/path/to/test.py",
                content="def hello():\n    pass",
                line_ranges=None,
                total_lines=2,
                included_lines=2,
                estimated_tokens=10,
            )
        ]

        result = format_file_context_template(
            summary="Test summary",
            project_path="/project",
            configuration_content="",
            included_files=included,
            excluded_files=[],
            user_instructions="Review this code",
            auto_meta_prompt=False,
            raw_context_only=False,
        )

        assert "# File-Based Code Review Context" in result
        assert "<file_selection_summary>" in result
        assert "Test summary" in result
        assert "<project_path>" in result
        assert "/project" in result
        assert "<selected_files>" in result
        assert "test.py (full file)" in result
        assert "def hello():" in result
        assert "<user_instructions>" in result
        assert "Review this code" in result

    def test_format_with_configuration(self):
        """Test formatting with configuration content."""
        included: List[FileContentData] = []

        result = format_file_context_template(
            summary="Summary",
            project_path="/project",
            configuration_content="Configuration rules",
            included_files=included,
            excluded_files=[],
            raw_context_only=False,
        )

        assert "<configuration_context>" in result
        assert "Configuration rules" in result

    def test_format_raw_context_only(self):
        """Test formatting without user instructions."""
        included: List[FileContentData] = []

        result = format_file_context_template(
            summary="Summary",
            project_path="/project",
            configuration_content="",
            included_files=included,
            excluded_files=[],
            raw_context_only=True,
        )

        assert "<user_instructions>" not in result

    def test_format_with_auto_meta_prompt_placeholder(self):
        """Test formatting with auto meta-prompt placeholder."""
        included: List[FileContentData] = []

        result = format_file_context_template(
            summary="Summary",
            project_path="/project",
            configuration_content="",
            included_files=included,
            excluded_files=[],
            user_instructions=None,
            auto_meta_prompt=True,
            raw_context_only=False,
        )

        assert "<user_instructions>" in result
        assert "[Auto-generated meta-prompt will be inserted here" in result


class TestSaveFileContext:
    """Tests for save_file_context function."""

    def test_save_with_custom_path(self):
        """Test saving with custom output path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "custom-output.md")

            result = FileContextResult(
                content="Test content",
                total_tokens=10,
                included_files=[],
                excluded_files=[],
            )

            saved_path = save_file_context(result, output_path)

            assert saved_path == output_path
            assert os.path.exists(output_path)

            with open(output_path, "r") as f:
                assert f.read() == "Test content"

    def test_save_with_default_path(self):
        """Test saving with auto-generated path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = FileContextResult(
                content="Test content",
                total_tokens=10,
                included_files=[],
                excluded_files=[],
            )

            saved_path = save_file_context(result, project_path=tmpdir)

            assert os.path.dirname(saved_path) == tmpdir
            assert saved_path.endswith(".md")
            assert "file-context-" in os.path.basename(saved_path)
            assert os.path.exists(saved_path)
