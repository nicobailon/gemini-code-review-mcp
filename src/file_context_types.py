#!/usr/bin/env python3
"""
Type definitions for file-based context generation.

This module defines the types and data structures used for selecting files,
specifying line ranges, and configuring the file-based context generation feature.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict, Union, cast, TypeGuard

# Type alias for line ranges
LineRange = Tuple[int, int]  # (start_line, end_line) - both inclusive


class FileSelection(TypedDict):
    """Type definition for a file selection with optional line ranges."""
    path: str  # File path (absolute or relative to project_path)
    line_ranges: Optional[List[LineRange]]  # List of (start, end) tuples, None means full file
    include_full: bool  # Include full file if no ranges specified (default True)


class FileSelectionInput(TypedDict, total=False):
    """Flexible input type for file selection that allows partial specification."""
    path: str  # Required
    line_ranges: Optional[List[LineRange]]  # Optional
    include_full: Optional[bool]  # Optional, defaults to True


@dataclass
class FileContextConfig:
    """Configuration for file-based context generation."""
    file_selections: List[FileSelection]
    project_path: Optional[str] = None
    user_instructions: Optional[str] = None
    include_claude_memory: bool = False
    include_cursor_rules: bool = False
    auto_meta_prompt: bool = True
    temperature: float = 0.5
    text_output: bool = True
    output_path: Optional[str] = None
    model: Optional[str] = None  # Optional specific model override
    token_limit: int = 200000  # 200k LLM tokens


@dataclass
class FileContentData:
    """Structured data for file content with metadata."""
    path: str
    absolute_path: str
    content: str
    line_ranges: Optional[List[LineRange]]
    total_lines: int
    included_lines: int
    estimated_tokens: int


@dataclass
class FileContextResult:
    """Result of file context generation."""
    content: str  # The generated context content
    total_tokens: int  # Total estimated tokens
    included_files: List[FileContentData]  # Files that were included
    excluded_files: List[Tuple[str, str]]  # List of (path, reason) for excluded files
    configuration_content: Optional[str] = None  # Claude/Cursor configuration if included
    meta_prompt: Optional[str] = None  # Generated meta-prompt if enabled


# Type for output mode
OutputMode = Literal["text", "file"]


# Error types
class FileSelectionError(Exception):
    """Base exception for file selection errors."""
    pass


class FileNotFoundError(FileSelectionError):
    """File path does not exist."""
    pass


class InvalidLineRangeError(FileSelectionError):
    """Line range is invalid (e.g., start > end, out of bounds)."""
    pass


class TokenLimitExceededError(FileSelectionError):
    """Total content exceeds token limit."""
    pass


# Type guard functions
def is_valid_line_range(obj: object) -> TypeGuard[LineRange]:
    """Type guard to check if object is a valid LineRange (2-tuple of ints)."""
    if not isinstance(obj, (list, tuple)):
        return False
    # After isinstance check, we know obj is list or tuple
    obj_seq = cast(Union[List[Any], Tuple[Any, ...]], obj)
    return (len(obj_seq) == 2 and 
            isinstance(obj_seq[0], int) and 
            isinstance(obj_seq[1], int))


def is_file_selection(obj: object) -> bool:
    """Type guard to check if object is a valid FileSelection."""
    # Type validation with runtime checks
    try:
        if not isinstance(obj, dict):
            return False
        
        obj_dict = cast(Dict[str, Any], obj)
        
        # Check required path field
        if "path" not in obj_dict or not isinstance(obj_dict["path"], str):
            return False
        
        # Check optional line_ranges
        if "line_ranges" in obj_dict:
            line_ranges_value = obj_dict.get("line_ranges")
            
            if line_ranges_value is not None:
                if not isinstance(line_ranges_value, list):
                    return False
                    
                # Validate each range is a 2-tuple of ints
                # Cast to List[Any] after isinstance check
                ranges_list = cast(List[Any], line_ranges_value)
                for item in ranges_list:
                    if not is_valid_line_range(item):
                        return False
        
        # Check optional include_full
        if "include_full" in obj_dict and not isinstance(obj_dict["include_full"], bool):
            return False
        
        return True
    except (KeyError, TypeError):
        return False


def normalize_file_selection(selection: Union[FileSelection, FileSelectionInput, Dict[str, Any]]) -> FileSelection:
    """Normalize various input formats to FileSelection."""
    # TypedDicts are dicts at runtime, so we check if it's already the right structure
    if hasattr(selection, "__annotations__") and "path" in selection:
        # It's already a FileSelection TypedDict
        return cast(FileSelection, selection)
    
    # Otherwise, it's a regular dict or FileSelectionInput
    if "path" not in selection:
        raise ValueError("Selection must have a 'path' field")
    
    # Cast to dict for type safety
    selection_dict = cast(Dict[str, Any], selection)
    
    # Extract and validate line_ranges
    line_ranges_raw = selection_dict.get("line_ranges", None)
    line_ranges: Optional[List[LineRange]] = None
    
    if line_ranges_raw is not None:
        if isinstance(line_ranges_raw, list):
            # Validate and cast each range
            validated_ranges: List[LineRange] = []
            # Cast to List[Any] after isinstance check
            ranges_list = cast(List[Any], line_ranges_raw)
            for item in ranges_list:
                if is_valid_line_range(item):
                    # Type guard ensures item is LineRange, no cast needed
                    validated_ranges.append(item)
                else:
                    raise ValueError(f"Invalid line range: {item}")
            line_ranges = validated_ranges
    
    return FileSelection(
        path=selection_dict["path"],
        line_ranges=line_ranges,
        include_full=bool(selection_dict.get("include_full", True))
    )