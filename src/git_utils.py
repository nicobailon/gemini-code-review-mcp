#!/usr/bin/env python3
"""
Git utilities and file tree generation module.

This module provides utility functions for interacting with Git (e.g., getting changed files)
and generating ASCII file trees.
"""

import fnmatch
import logging
import os
import subprocess
from typing import Dict, List, Optional

from .progress import progress

logger = logging.getLogger(__name__)


def get_changed_files(project_path: str) -> List[Dict[str, str]]:
    """
    Get changed files from git with their content.

    Args:
        project_path: Path to project root

    Returns:
        List of changed file dictionaries
    """
    try:
        changed_files: List[Dict[str, str]] = []
        max_lines_env = os.getenv("MAX_FILE_CONTENT_LINES", "500")
        try:
            max_lines = int(max_lines_env) if max_lines_env else 500
            # Ensure max_lines is reasonable (10-10000)
            if max_lines < 10:
                logger.warning(
                    f"MAX_FILE_CONTENT_LINES={max_lines} too small, using 10"
                )
                max_lines = 10
            elif max_lines > 10000:
                logger.warning(
                    f"MAX_FILE_CONTENT_LINES={max_lines} too large, using 10000"
                )
                max_lines = 10000
        except ValueError:
            logger.warning(
                f"Invalid MAX_FILE_CONTENT_LINES='{max_lines_env}', using default 500"
            )
            max_lines = 500
        debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

        if debug_mode:
            logger.info(
                f"Debug mode enabled. Processing max {max_lines} lines per file."
            )

        # Get all types of changes: staged, unstaged, and untracked
        all_files: Dict[str, List[str]] = {}

        # 1. Staged changes (index vs HEAD)
        result = subprocess.run(
            ["git", "diff", "--name-status", "--cached"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("\t", 1)
                if len(parts) == 2:
                    status, file_path = parts
                    if file_path not in all_files:
                        all_files[file_path] = []
                    all_files[file_path].append(f"staged-{status}")

        # 2. Unstaged changes (working tree vs index)
        result = subprocess.run(
            ["git", "diff", "--name-status"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("\t", 1)
                if len(parts) == 2:
                    status, file_path = parts
                    if file_path not in all_files:
                        all_files[file_path] = []
                    all_files[file_path].append(f"unstaged-{status}")

        # 3. Untracked files
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.strip().split("\n"):
            if line:
                if line not in all_files:
                    all_files[line] = []
                all_files[line].append("untracked")

        # Process all collected files
        with progress("Reading file contents") as p:
            for file_path, statuses in all_files.items():
                p.update(f"Processing {file_path}")
                absolute_path = os.path.abspath(os.path.join(project_path, file_path))

                # Check if this is a deleted file
                is_deleted = any("D" in status for status in statuses)

                if is_deleted:
                    content = "[File deleted]"
                else:
                    # Get file content from working directory
                    try:
                        if os.path.exists(absolute_path):
                            # Check file size to avoid memory issues with very large files
                            file_size = os.path.getsize(absolute_path)
                            max_file_size = (
                                int(os.getenv("MAX_FILE_SIZE_MB", "10")) * 1024 * 1024
                            )  # Default 10MB

                            if file_size > max_file_size:
                                content = f"[File too large: {file_size / (1024 * 1024):.1f}MB, limit is {max_file_size / (1024 * 1024)}MB]"
                            else:
                                with open(absolute_path, "r", encoding="utf-8") as f:
                                    content_lines = f.readlines()

                                if len(content_lines) > max_lines:
                                    content = "".join(content_lines[:max_lines])
                                    content += f"\n... (truncated, showing first {max_lines} lines)"
                                else:
                                    content = "".join(content_lines).rstrip("\n")
                        else:
                            content = "[File not found in working directory]"

                    except (UnicodeDecodeError, PermissionError, OSError):
                        # Handle binary files or other errors
                        content = "[Binary file or content not available]"

                changed_files.append(
                    {
                        "path": absolute_path,
                        "status": ", ".join(statuses),
                        "content": content,
                    }
                )

        return changed_files

    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not a git repository or git not available
        logger.warning("Git not available or not in a git repository")
        return []


def generate_file_tree(project_path: str, max_depth: Optional[int] = None) -> str:
    """
    Generate ASCII file tree representation.

    Args:
        project_path: Path to project root
        max_depth: Maximum depth to traverse

    Returns:
        ASCII file tree string
    """
    if max_depth is None:
        max_depth = int(os.getenv("MAX_FILE_TREE_DEPTH", "5"))

    # Default ignore patterns
    ignore_patterns = {
        ".git",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        "*.pyc",
        ".DS_Store",
        ".vscode",
        ".idea",
    }

    # Read .gitignore if it exists
    gitignore_path = os.path.join(project_path, ".gitignore")
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        ignore_patterns.add(line)
        except Exception as e:
            logger.warning(f"Failed to read .gitignore: {e}")

    def should_ignore(name: str, path: str) -> bool:
        """Check if file/directory should be ignored."""
        for pattern in ignore_patterns:
            if pattern == name or pattern in path:
                return True
            # Simple glob pattern matching
            if "*" in pattern:
                if fnmatch.fnmatch(name, pattern):
                    return True
        return False

    def build_tree(current_path: str, prefix: str = "", depth: int = 0) -> List[str]:
        """Recursively build tree structure."""
        if depth >= max_depth:
            return []

        try:
            items = os.listdir(current_path)
        except PermissionError:
            return []

        # Filter out ignored items
        items = [
            item
            for item in items
            if not should_ignore(item, os.path.join(current_path, item))
        ]

        # Sort: directories first, then files, both alphabetically
        dirs = sorted(
            [item for item in items if os.path.isdir(os.path.join(current_path, item))]
        )
        files = sorted(
            [item for item in items if os.path.isfile(os.path.join(current_path, item))]
        )

        tree_lines: List[str] = []
        all_items = dirs + files

        for i, item in enumerate(all_items):
            is_last = i == len(all_items) - 1
            item_path = os.path.join(current_path, item)

            if os.path.isdir(item_path):
                connector = "└── " if is_last else "├── "
                tree_lines.append(f"{prefix}{connector}{item}/")

                extension = "    " if is_last else "│   "
                subtree = build_tree(item_path, prefix + extension, depth + 1)
                tree_lines.extend(subtree)
            else:
                connector = "└── " if is_last else "├── "
                tree_lines.append(f"{prefix}{connector}{item}")

        return tree_lines

    tree_lines = [project_path]
    tree_lines.extend(build_tree(project_path))
    return "\n".join(tree_lines)
