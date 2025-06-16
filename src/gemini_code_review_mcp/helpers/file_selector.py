#!/usr/bin/env python3
"""
File selection utilities for file-based context generation.

This module provides functions for parsing file selections, validating paths,
extracting line ranges, and formatting file content with line numbers.

Main functions:
- parse_file_selection: Parse string format like "file.py:10-50"
- parse_file_selections: Parse multiple selections from various formats
- normalize_file_selections_from_dicts: Convert dict selections to FileSelection objects
- validate_file_paths: Check file existence and readability
- extract_line_ranges: Read specific line ranges from files
- format_file_content: Format content with line numbers
- read_file_with_line_ranges: Read file with metadata
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from .file_context_types import (
        FileContentData,
        FileNotFoundError,
        FileSelection,
        FileSelectionInput,
        InvalidLineRangeError,
        LineRange,
        normalize_file_selection,
    )
except ImportError:
    # Fall back to absolute imports for testing
    from ..file_context_types import (
        FileContentData,
        FileNotFoundError,
        FileSelection,
        FileSelectionInput,
        InvalidLineRangeError,
        LineRange,
        normalize_file_selection,
    )


def parse_file_selection(selection_str: str) -> FileSelection:
    """
    Parse a file selection string into a FileSelection object.

    Supports formats:
    - "file.py" - Full file
    - "file.py:10-50" - Single line range
    - "file.py:10-50,100-150" - Multiple line ranges

    Args:
        selection_str: String representation of file selection

    Returns:
        FileSelection object

    Raises:
        ValueError: If the format is invalid
    """
    # Match pattern: path followed by optional :ranges
    match = re.match(r"^(.+?)(?::(.+))?$", selection_str)
    if not match:
        raise ValueError(f"Invalid file selection format: {selection_str}")

    path = match.group(1)
    ranges_str = match.group(2)

    line_ranges: Optional[List[LineRange]] = None

    if ranges_str:
        line_ranges = []
        # Split by comma and parse each range
        for range_str in ranges_str.split(","):
            range_match = re.match(r"^(\d+)-(\d+)$", range_str.strip())
            if not range_match:
                raise ValueError(f"Invalid line range format: {range_str}")

            start = int(range_match.group(1))
            end = int(range_match.group(2))

            if start > end:
                raise ValueError(f"Invalid line range: start ({start}) > end ({end})")

            line_ranges.append((start, end))

    return FileSelection(path=path, line_ranges=line_ranges, include_full=True)


def parse_file_selections(
    selections: Union[List[str], List[Dict[str, Any]], List[FileSelectionInput]],
) -> List[FileSelection]:
    """
    Parse multiple file selections from various input formats.

    Args:
        selections: List of file selections in string or dict format

    Returns:
        List of normalized FileSelection objects
    """
    result: List[FileSelection] = []

    for selection in selections:
        if isinstance(selection, str):
            result.append(parse_file_selection(selection))
        else:
            # Must be a dict type (FileSelectionInput or Dict[str, Any])
            result.append(normalize_file_selection(selection))

    return result


def normalize_file_selections_from_dicts(
    selections: Optional[List[Dict[str, Any]]],
) -> List[FileSelection]:
    """
    Normalize a list of file selection dictionaries to FileSelection objects.

    This is a convenience function for MCP tools that accept file selections
    as dictionaries and need to convert them to the proper TypedDict format.

    Args:
        selections: Optional list of file selection dictionaries

    Returns:
        List of normalized FileSelection objects (empty list if selections is None)

    Raises:
        ValueError: If any selection is missing the required 'path' field
    """
    if not selections:
        return []

    normalized: List[FileSelection] = []
    for selection in selections:
        if "path" not in selection:
            raise ValueError("Each file selection must have a 'path' field")

        normalized.append(
            FileSelection(
                path=selection["path"],
                line_ranges=selection.get("line_ranges"),
                include_full=selection.get("include_full", True),
            )
        )

    return normalized


def validate_file_paths(
    file_selections: List[FileSelection], project_path: Optional[str] = None
) -> Tuple[List[FileSelection], List[Tuple[str, str]]]:
    """
    Validate that file paths exist and are readable.

    Args:
        file_selections: List of file selections to validate
        project_path: Optional base path for relative paths

    Returns:
        Tuple of (valid_selections, errors)
        where errors is a list of (path, error_message) tuples
    """
    valid_selections: List[FileSelection] = []
    errors: List[Tuple[str, str]] = []

    base_path = Path(project_path) if project_path else Path.cwd()

    for selection in file_selections:
        file_path = Path(selection["path"])

        # Make absolute if relative
        if not file_path.is_absolute():
            file_path = base_path / file_path

        # Check existence
        if not file_path.exists():
            errors.append((selection["path"], f"File not found: {file_path}"))
            continue

        # Check if it's a file (not directory)
        if not file_path.is_file():
            errors.append((selection["path"], f"Not a file: {file_path}"))
            continue

        # Check readability
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                # Just try to read first byte to check access
                f.read(1)
        except PermissionError:
            errors.append((selection["path"], f"Permission denied: {file_path}"))
            continue
        except Exception as e:
            errors.append((selection["path"], f"Cannot read file: {str(e)}"))
            continue

        # Update selection with absolute path for consistency
        validated_selection = FileSelection(
            path=str(file_path),
            line_ranges=selection.get("line_ranges"),
            include_full=selection.get("include_full", True),
        )
        valid_selections.append(validated_selection)

    return valid_selections, errors


def extract_line_ranges(
    file_path: str, line_ranges: Optional[List[LineRange]] = None
) -> Tuple[str, int, int]:
    """
    Read specific line ranges from a file.

    Args:
        file_path: Path to the file
        line_ranges: Optional list of (start, end) tuples (1-indexed, inclusive)
                    If None, returns the entire file

    Returns:
        Tuple of (content, total_lines, included_lines)

    Raises:
        FileNotFoundError: If file doesn't exist
        InvalidLineRangeError: If line ranges are out of bounds
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise FileNotFoundError(f"Cannot read file {file_path}: {str(e)}")

    total_lines = len(all_lines)

    # If no ranges specified, return entire file
    if not line_ranges:
        return "".join(all_lines), total_lines, total_lines

    # Validate and extract line ranges
    selected_lines: List[str] = []
    included_line_numbers: set[int] = set()

    for start, end in line_ranges:
        # Validate range
        if start < 1 or end < 1:
            raise InvalidLineRangeError(
                f"Line numbers must be positive (got {start}-{end})"
            )
        if start > total_lines or end > total_lines:
            raise InvalidLineRangeError(
                f"Line range {start}-{end} out of bounds (file has {total_lines} lines)"
            )

        # Extract lines (convert to 0-indexed)
        for line_num in range(start - 1, end):
            if line_num not in included_line_numbers:
                selected_lines.append(all_lines[line_num])
                included_line_numbers.add(line_num)

    return "".join(selected_lines), total_lines, len(included_line_numbers)


def format_file_content(
    file_path: str,
    content: str,
    line_ranges: Optional[List[LineRange]] = None,
    show_line_numbers: bool = True,
) -> str:
    """
    Format file content with optional line numbers and range indicators.

    Args:
        file_path: Path to the file (for header)
        content: File content to format
        line_ranges: Optional line ranges that were extracted
        show_line_numbers: Whether to show line numbers

    Returns:
        Formatted content string
    """
    lines = content.splitlines(keepends=True)

    if not show_line_numbers:
        return content

    # If we have line ranges, we need to determine the starting line number
    # for each line in the content
    if line_ranges:
        # Build a map of which lines are included
        line_map: List[int] = []
        for start, end in sorted(line_ranges):
            for line_num in range(start, end + 1):
                if line_num not in line_map:
                    line_map.append(line_num)

        # Format with actual line numbers
        formatted_lines: List[str] = []
        for i, line in enumerate(lines):
            if i < len(line_map):
                actual_line_num = line_map[i]
                # Preserve existing line ending if present
                if line.endswith("\n"):
                    formatted_lines.append(f"{actual_line_num:6d} | {line}")
                else:
                    formatted_lines.append(f"{actual_line_num:6d} | {line}\n")
            else:
                # Shouldn't happen, but handle gracefully
                formatted_lines.append(f"     ? | {line}")

        # Remove trailing newline if original didn't have one
        result = "".join(formatted_lines)
        if not content.endswith("\n") and result.endswith("\n"):
            result = result[:-1]
        return result
    else:
        # Full file - simple sequential numbering
        formatted_lines: List[str] = []
        for i, line in enumerate(lines, 1):
            # Preserve existing line ending if present
            if line.endswith("\n"):
                formatted_lines.append(f"{i:6d} | {line}")
            else:
                formatted_lines.append(f"{i:6d} | {line}\n")

        # Remove trailing newline if original didn't have one
        result = "".join(formatted_lines)
        if not content.endswith("\n") and result.endswith("\n"):
            result = result[:-1]
        return result


def estimate_tokens(content: str) -> int:
    """
    Estimate the number of tokens in content.

    This is a rough approximation based on character count.
    More accurate token counting would require the actual tokenizer.

    Args:
        content: Text content

    Returns:
        Estimated token count
    """
    # Rough approximation: ~4 characters per token on average
    # This varies by content type and tokenizer, but is reasonable for code
    return len(content) // 4


def read_file_with_line_ranges(
    file_path: str,
    line_ranges: Optional[List[LineRange]] = None,
    project_path: Optional[str] = None,
) -> FileContentData:
    """
    Read a file with optional line ranges and return structured data.

    Args:
        file_path: Path to the file (absolute or relative)
        line_ranges: Optional line ranges to extract
        project_path: Optional project path for relative paths

    Returns:
        FileContentData with content and metadata

    Raises:
        FileNotFoundError: If file doesn't exist
        InvalidLineRangeError: If line ranges are invalid
    """
    # Resolve path
    path = Path(file_path)
    if not path.is_absolute() and project_path:
        path = Path(project_path) / path

    absolute_path = str(path.resolve())

    # Extract content
    content, total_lines, included_lines = extract_line_ranges(
        absolute_path, line_ranges
    )

    # Format content with line numbers
    formatted_content = format_file_content(
        file_path, content, line_ranges, show_line_numbers=True
    )

    # Estimate tokens
    estimated_tokens = estimate_tokens(formatted_content)

    return FileContentData(
        path=file_path,
        absolute_path=absolute_path,
        content=formatted_content,
        line_ranges=line_ranges,
        total_lines=total_lines,
        included_lines=included_lines,
        estimated_tokens=estimated_tokens,
    )
