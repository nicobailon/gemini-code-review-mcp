#!/usr/bin/env python3
"""
Unit tests for file_selector module.
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.file_context_types import (
    FileNotFoundError,
    FileSelection,
    InvalidLineRangeError,
)
from src.file_selector import (
    estimate_tokens,
    extract_line_ranges,
    format_file_content,
    parse_file_selection,
    parse_file_selections,
    read_file_with_line_ranges,
    validate_file_paths,
)


class TestParseFileSelection:
    """Tests for parse_file_selection function."""

    def test_parse_full_file(self):
        """Test parsing file path without line ranges."""
        result = parse_file_selection("src/main.py")
        assert result["path"] == "src/main.py"
        assert result["line_ranges"] is None
        assert result["include_full"] is True

    def test_parse_single_range(self):
        """Test parsing file with single line range."""
        result = parse_file_selection("src/main.py:10-50")
        assert result["path"] == "src/main.py"
        assert result["line_ranges"] == [(10, 50)]

    def test_parse_multiple_ranges(self):
        """Test parsing file with multiple line ranges."""
        result = parse_file_selection("src/main.py:10-50,100-150,200-250")
        assert result["path"] == "src/main.py"
        assert result["line_ranges"] == [(10, 50), (100, 150), (200, 250)]

    def test_parse_with_spaces(self):
        """Test parsing handles spaces in ranges."""
        result = parse_file_selection("src/main.py:10-50, 100-150")
        assert result["line_ranges"] == [(10, 50), (100, 150)]

    def test_parse_invalid_format(self):
        """Test parsing raises error for invalid format."""
        with pytest.raises(ValueError, match="Invalid file selection format"):
            parse_file_selection("")

    def test_parse_invalid_range_format(self):
        """Test parsing raises error for invalid range format."""
        with pytest.raises(ValueError, match="Invalid line range format"):
            parse_file_selection("src/main.py:10")

        with pytest.raises(ValueError, match="Invalid line range format"):
            parse_file_selection("src/main.py:10-")

        with pytest.raises(ValueError, match="Invalid line range format"):
            parse_file_selection("src/main.py:abc-def")

    def test_parse_invalid_range_order(self):
        """Test parsing raises error when start > end."""
        with pytest.raises(ValueError, match="Invalid line range: start .* > end"):
            parse_file_selection("src/main.py:50-10")


class TestParseFileSelections:
    """Tests for parse_file_selections function."""

    def test_parse_string_list(self):
        """Test parsing list of string selections."""
        selections = ["file1.py", "file2.py:10-20", "file3.py:5-10,20-30"]
        result = parse_file_selections(selections)

        assert len(result) == 3
        assert result[0]["path"] == "file1.py"
        assert result[0]["line_ranges"] is None
        assert result[1]["path"] == "file2.py"
        assert result[1]["line_ranges"] == [(10, 20)]
        assert result[2]["path"] == "file3.py"
        assert result[2]["line_ranges"] == [(5, 10), (20, 30)]

    def test_parse_dict_list(self):
        """Test parsing list of dict selections."""
        selections = [
            {"path": "file1.py"},
            {"path": "file2.py", "line_ranges": [(10, 20)]},
            {"path": "file3.py", "line_ranges": None, "include_full": False},
        ]
        result = parse_file_selections(selections)

        assert len(result) == 3
        assert result[0]["path"] == "file1.py"
        assert result[0]["include_full"] is True
        assert result[1]["line_ranges"] == [(10, 20)]
        assert result[2]["include_full"] is False

    def test_parse_mixed_list(self):
        """Test parsing mixed string and dict selections."""
        # Test string list first
        string_selections = ["file1.py"]
        result1 = parse_file_selections(string_selections)
        assert len(result1) == 1
        assert result1[0]["path"] == "file1.py"

        # Test dict list separately
        dict_selections = [{"path": "file2.py", "line_ranges": [(10, 20)]}]
        result2 = parse_file_selections(dict_selections)
        assert len(result2) == 1
        assert result2[0]["path"] == "file2.py"
        assert result2[0]["line_ranges"] == [(10, 20)]

        # Combine results to verify both work
        combined = result1 + result2
        assert len(combined) == 2


class TestValidateFilePaths:
    """Tests for validate_file_paths function."""

    def test_validate_existing_files(self):
        """Test validation of existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = Path(tmpdir) / "file1.py"
            file2 = Path(tmpdir) / "subdir" / "file2.py"
            file2.parent.mkdir()

            file1.write_text("content1")
            file2.write_text("content2")

            selections = [
                FileSelection(path=str(file1), line_ranges=None, include_full=True),
                FileSelection(path=str(file2), line_ranges=None, include_full=True),
            ]

            valid, errors = validate_file_paths(selections)

            assert len(valid) == 2
            assert len(errors) == 0
            assert all(Path(s["path"]).is_absolute() for s in valid)

    def test_validate_relative_paths(self):
        """Test validation with relative paths and project_path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            file_path = Path(tmpdir) / "src" / "main.py"
            file_path.parent.mkdir()
            file_path.write_text("content")

            selections = [
                FileSelection(path="src/main.py", line_ranges=None, include_full=True)
            ]

            valid, errors = validate_file_paths(selections, project_path=tmpdir)

            assert len(valid) == 1
            assert len(errors) == 0
            assert Path(valid[0]["path"]).is_absolute()

    def test_validate_missing_files(self):
        """Test validation of missing files."""
        selections = [
            FileSelection(
                path="/does/not/exist.py", line_ranges=None, include_full=True
            )
        ]

        valid, errors = validate_file_paths(selections)

        assert len(valid) == 0
        assert len(errors) == 1
        assert "File not found" in errors[0][1]

    def test_validate_directory(self):
        """Test validation rejects directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            selections = [
                FileSelection(path=tmpdir, line_ranges=None, include_full=True)
            ]

            valid, errors = validate_file_paths(selections)

            assert len(valid) == 0
            assert len(errors) == 1
            assert "Not a file" in errors[0][1]


class TestExtractLineRanges:
    """Tests for extract_line_ranges function."""

    def test_extract_full_file(self):
        """Test extracting full file content."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("line1\nline2\nline3\nline4\nline5\n")
            f.flush()

            try:
                content, total, included = extract_line_ranges(f.name)
                assert content == "line1\nline2\nline3\nline4\nline5\n"
                assert total == 5
                assert included == 5
            finally:
                os.unlink(f.name)

    def test_extract_single_range(self):
        """Test extracting single line range."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("line1\nline2\nline3\nline4\nline5\n")
            f.flush()

            try:
                content, total, included = extract_line_ranges(f.name, [(2, 4)])
                assert content == "line2\nline3\nline4\n"
                assert total == 5
                assert included == 3
            finally:
                os.unlink(f.name)

    def test_extract_multiple_ranges(self):
        """Test extracting multiple line ranges."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("line1\nline2\nline3\nline4\nline5\n")
            f.flush()

            try:
                content, total, included = extract_line_ranges(f.name, [(1, 2), (4, 5)])
                assert content == "line1\nline2\nline4\nline5\n"
                assert total == 5
                assert included == 4
            finally:
                os.unlink(f.name)

    def test_extract_overlapping_ranges(self):
        """Test extracting overlapping ranges (should not duplicate lines)."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("line1\nline2\nline3\nline4\nline5\n")
            f.flush()

            try:
                content, total, included = extract_line_ranges(f.name, [(1, 3), (2, 4)])
                assert content == "line1\nline2\nline3\nline4\n"
                assert total == 5
                assert included == 4
            finally:
                os.unlink(f.name)

    def test_extract_invalid_range(self):
        """Test extracting with invalid line ranges."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("line1\nline2\nline3\n")
            f.flush()

            try:
                # Line numbers must be positive
                with pytest.raises(InvalidLineRangeError, match="must be positive"):
                    extract_line_ranges(f.name, [(0, 2)])

                # Out of bounds
                with pytest.raises(InvalidLineRangeError, match="out of bounds"):
                    extract_line_ranges(f.name, [(1, 10)])
            finally:
                os.unlink(f.name)

    def test_extract_missing_file(self):
        """Test extracting from missing file."""
        with pytest.raises(FileNotFoundError):
            extract_line_ranges("/does/not/exist.py")


class TestFormatFileContent:
    """Tests for format_file_content function."""

    def test_format_without_line_numbers(self):
        """Test formatting without line numbers."""
        content = "line1\nline2\nline3\n"
        result = format_file_content("test.py", content, show_line_numbers=False)
        assert result == content

    def test_format_with_line_numbers_full_file(self):
        """Test formatting with line numbers for full file."""
        content = "line1\nline2\nline3\n"
        result = format_file_content("test.py", content, show_line_numbers=True)

        # Check that all lines are formatted correctly
        lines = result.strip().split("\n")
        assert len(lines) == 3

        # Verify each line contains the expected content
        assert lines[0].endswith("1 | line1")
        assert lines[1].endswith("2 | line2")
        assert lines[2].endswith("3 | line3")

        # Verify line numbers are properly padded
        assert "     1 |" in result or "1 |" in lines[0]
        assert "     2 |" in result
        assert "     3 |" in result

    def test_format_with_line_numbers_ranges(self):
        """Test formatting with line numbers for specific ranges."""
        content = "line2\nline3\nline5\n"
        result = format_file_content(
            "test.py", content, line_ranges=[(2, 3), (5, 5)], show_line_numbers=True
        )

        # Check that all lines are formatted correctly
        lines = result.strip().split("\n")
        assert len(lines) == 3

        # Verify each line contains the expected content
        assert lines[0].endswith("2 | line2")
        assert lines[1].endswith("3 | line3")
        assert lines[2].endswith("5 | line5")

        # Verify line numbers are properly padded
        assert "     2 |" in result or "2 |" in lines[0]
        assert "     3 |" in result
        assert "     5 |" in result


class TestEstimateTokens:
    """Tests for estimate_tokens function."""

    def test_estimate_empty(self):
        """Test token estimation for empty string."""
        assert estimate_tokens("") == 0

    def test_estimate_short_text(self):
        """Test token estimation for short text."""
        # ~4 chars per token
        assert estimate_tokens("hello world") == 2  # 11 chars / 4

    def test_estimate_code(self):
        """Test token estimation for code."""
        code = "def hello():\n    print('Hello, world!')\n"
        # 40 chars / 4 = 10 tokens
        assert estimate_tokens(code) == 10


class TestReadFileWithLineRanges:
    """Tests for read_file_with_line_ranges function."""

    def test_read_full_file(self):
        """Test reading full file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("def hello():\n    print('Hello')\n")
            f.flush()

            try:
                result = read_file_with_line_ranges(f.name)

                assert result.path == f.name
                assert result.total_lines == 2
                assert result.included_lines == 2
                assert result.line_ranges is None
                assert "def hello():" in result.content
                assert result.estimated_tokens > 0
            finally:
                os.unlink(f.name)

    def test_read_with_ranges(self):
        """Test reading file with line ranges."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("line1\nline2\nline3\nline4\nline5\n")
            f.flush()

            try:
                result = read_file_with_line_ranges(f.name, [(2, 3)])

                assert result.total_lines == 5
                assert result.included_lines == 2
                assert result.line_ranges == [(2, 3)]
                assert "line2" in result.content
                assert "line3" in result.content
                assert "line1" not in result.content
            finally:
                os.unlink(f.name)

    def test_read_relative_path(self):
        """Test reading file with relative path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("content")

            result = read_file_with_line_ranges("test.py", project_path=tmpdir)

            assert result.absolute_path == str(file_path.resolve())
            assert result.content.strip().endswith("content")
