#!/usr/bin/env python3
"""
Context builder module for configuration discovery and merging.

This module orchestrates the discovery, parsing, and merging of various configuration
contexts (Claude memory files, Cursor rules) into a structured format suitable for
AI consumption. It also manages a caching mechanism for configurations.
"""

import glob
import logging
import os
from typing import Any, Dict, List, Optional, TypedDict

try:
    from ..config_types import DEFAULT_INCLUDE_CLAUDE_MEMORY, DEFAULT_INCLUDE_CURSOR_RULES
except ImportError:
    from config_types import DEFAULT_INCLUDE_CLAUDE_MEMORY, DEFAULT_INCLUDE_CURSOR_RULES

logger = logging.getLogger(__name__)


class DiscoveredConfigurations(TypedDict):
    """Type definition for discovered configurations."""

    claude_memory_files: List[Any]
    cursor_rules: List[Any]
    discovery_errors: List[Dict[str, Any]]
    performance_stats: Dict[str, Any]


class ConfigurationCache:
    """Cache for configuration discovery to improve performance."""

    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.mtimes: Dict[str, float] = {}

    def get_configurations(
        self,
        project_path: str,
        include_claude_memory: bool = DEFAULT_INCLUDE_CLAUDE_MEMORY,
        include_cursor_rules: bool = DEFAULT_INCLUDE_CURSOR_RULES,
    ) -> Optional[Dict[str, Any]]:
        """Get cached configurations if they exist and are up to date, otherwise discover and cache.
    
    Args:
        project_path: Project directory path
        include_claude_memory: Whether to discover CLAUDE.md files (default: False)
        include_cursor_rules: Whether to discover Cursor rules (default: False)
    
    Returns:
        Dictionary with discovered configurations or None if failed
    """
        # Create cache key based on path and flags
        cache_key = f"{project_path}:{include_claude_memory}:{include_cursor_rules}"
        
        # Check if we have cached data
        if cache_key not in self.cache:
            # No cached data, discover configurations
            configurations = _discover_project_configurations_uncached(
                project_path, include_claude_memory, include_cursor_rules
            )
            self.set_configurations(cache_key, project_path, configurations)
            return configurations

        # Check if any configuration files have been modified
        current_mtime = self._get_max_config_mtime(project_path)
        cached_mtime = self.mtimes.get(cache_key, 0)

        if current_mtime > cached_mtime:
            # Configuration files have been modified, invalidate cache and rediscover
            self.invalidate(cache_key)
            configurations = _discover_project_configurations_uncached(
                project_path, include_claude_memory, include_cursor_rules
            )
            self.set_configurations(cache_key, project_path, configurations)
            return configurations

        return self.cache[cache_key]

    def set_configurations(self, cache_key: str, project_path: str, configurations: Dict[str, Any]):
        """Cache configurations for a project."""
        self.cache[cache_key] = configurations
        self.mtimes[cache_key] = self._get_max_config_mtime(project_path)

    def invalidate(self, cache_key: str):
        """Invalidate cache for a cache key."""
        if cache_key in self.cache:
            del self.cache[cache_key]
        if cache_key in self.mtimes:
            del self.mtimes[cache_key]

    def _get_max_config_mtime(self, project_path: str) -> float:
        """Get the maximum modification time of configuration files."""
        max_mtime = 0

        # Check CLAUDE.md files
        for claude_pattern in ["CLAUDE.md", "*/CLAUDE.md", "**/CLAUDE.md"]:
            # Enable recursive search for ** patterns
            recursive = "**" in claude_pattern
            claude_files = glob.glob(
                os.path.join(project_path, claude_pattern), recursive=recursive
            )
            for claude_file in claude_files:
                if os.path.isfile(claude_file):
                    max_mtime = max(max_mtime, os.path.getmtime(claude_file))

        # Check cursor rules
        cursorrules_file = os.path.join(project_path, ".cursorrules")
        if os.path.isfile(cursorrules_file):
            max_mtime = max(max_mtime, os.path.getmtime(cursorrules_file))

        cursor_rules_dir = os.path.join(project_path, ".cursor", "rules")
        if os.path.isdir(cursor_rules_dir):
            for root, _, files in os.walk(cursor_rules_dir):
                for file in files:
                    if file.endswith(".mdc"):
                        file_path = os.path.join(root, file)
                        max_mtime = max(max_mtime, os.path.getmtime(file_path))

        return max_mtime


# Global cache instance
_config_cache = ConfigurationCache()


def _discover_project_configurations_uncached(
    project_path: str,
    include_claude_memory: bool = DEFAULT_INCLUDE_CLAUDE_MEMORY,
    include_cursor_rules: bool = DEFAULT_INCLUDE_CURSOR_RULES,
) -> Dict[str, Any]:
    """
    High-performance discovery of Claude memory files and Cursor rules from project.

    Uses async/concurrent operations by default with bulletproof fallbacks.

    Args:
        project_path: Path to project root
        include_claude_memory: Whether to discover CLAUDE.md files (default: False)
        include_cursor_rules: Whether to discover Cursor rules (default: False)

    Returns:
        Dictionary with discovered configurations, performance stats, and any errors
    """

    try:
        # Import configuration modules (relative imports for same package)
        # Use relative imports since we're in the same package
        from .configuration_discovery_unified import discover_all_configurations
        from .claude_memory_parser import parse_claude_memory_with_imports
        from .configuration_context import ClaudeMemoryFile, CursorRule
        from .cursor_rules_parser import parse_cursor_rules_directory

        claude_memory_files: List[Any] = []
        cursor_rules: List[Any] = []
        discovery_errors: List[Dict[str, Any]] = []

        # Use high-performance discovery (includes performance stats)
        discovery_result = discover_all_configurations(
            project_path,
            include_claude_memory=include_claude_memory,
            include_cursor_rules=include_cursor_rules,
        )

        # Log performance stats
        perf_stats = discovery_result.get("performance_stats", {})
        discovery_time = perf_stats.get("discovery_time_ms", 0)
        files_count = perf_stats.get("total_files_read", 0)
        fallback_method = perf_stats.get("fallback_method", "async")

        if discovery_time > 0:
            logger.info(
                f"🚀 Configuration discovery completed in {discovery_time}ms "
                f"({files_count} files) using {fallback_method} method"
            )

        # Process Claude memory files with improved error handling
        try:
            claude_files_data = discovery_result.get("claude_memory_files", [])

            for claude_file_data in claude_files_data:
                try:
                    # Validate file content before parsing
                    content = claude_file_data.get("content", "")

                    # Check for binary content (null bytes indicate binary)
                    if "\x00" in content:
                        raise ValueError(
                            f"Binary content detected in CLAUDE.md file: {claude_file_data['file_path']}"
                        )

                    # Parse with import resolution
                    parsed_data = parse_claude_memory_with_imports(
                        claude_file_data["file_path"], project_root=project_path
                    )

                    # Determine hierarchy level
                    hierarchy_level = claude_file_data.get("scope", "project")

                    # Create ClaudeMemoryFile object
                    memory_file = ClaudeMemoryFile(
                        file_path=claude_file_data["file_path"],
                        content=parsed_data["content"],
                        hierarchy_level=hierarchy_level,
                        imports=parsed_data.get("successful_imports", []),
                        resolved_content=parsed_data.get(
                            "resolved_content", parsed_data["content"]
                        ),
                    )

                    claude_memory_files.append(memory_file)

                    # Add any import errors to discovery errors
                    discovery_errors.extend(parsed_data.get("import_errors", []))

                except Exception as e:
                    discovery_errors.append(
                        {
                            "file_path": claude_file_data["file_path"],
                            "error_type": "claude_parsing_error",
                            "error_message": str(e),
                        }
                    )

        except Exception as e:
            discovery_errors.append(
                {"error_type": "claude_discovery_error", "error_message": str(e)}
            )

        # Process Cursor rules from high-performance discovery
        try:
            cursor_files_data = discovery_result.get("cursor_rules", [])

            for cursor_file_data in cursor_files_data:
                try:
                    # Handle both legacy and modern formats
                    if cursor_file_data.get("format") == "cursorrules":
                        # Legacy .cursorrules file
                        legacy_rule = CursorRule(
                            file_path=cursor_file_data["file_path"],
                            content=cursor_file_data["content"],
                            rule_type="legacy",
                            precedence=1000,  # Lower precedence than modern rules
                            description="Legacy cursorrules file",
                            globs=["**/*"],  # Apply to all files by default
                            always_apply=True,
                            metadata={"source": "legacy_cursorrules"},
                        )
                        cursor_rules.append(legacy_rule)

                    elif cursor_file_data.get("format") == "mdc":
                        # Modern .mdc file
                        parsed_data = cursor_file_data.get("parsed_data", {})

                        modern_rule = CursorRule(
                            file_path=cursor_file_data["file_path"],
                            content=cursor_file_data["content"],
                            rule_type="modern",
                            precedence=parsed_data.get("precedence", 500),
                            description=parsed_data.get(
                                "description", "Modern MDC rule"
                            ),
                            globs=parsed_data.get("globs", ["**/*"]),
                            always_apply=parsed_data.get("alwaysApply", False),
                            metadata=parsed_data.get("metadata", {}),
                        )
                        cursor_rules.append(modern_rule)

                except Exception as e:
                    discovery_errors.append(
                        {
                            "file_path": cursor_file_data.get("file_path", "unknown"),
                            "error_type": "cursor_parsing_error",
                            "error_message": str(e),
                        }
                    )

            # Legacy fallback: use original parser if new format doesn't work
            if not cursor_files_data:
                cursor_data = parse_cursor_rules_directory(project_path)

                # Add any parsing errors to discovery errors
                discovery_errors.extend(cursor_data.get("parse_errors", []))

                # Convert legacy rules
                if cursor_data.get("legacy_rules"):
                    legacy_data = cursor_data["legacy_rules"]
                    legacy_rule = CursorRule(
                        file_path=legacy_data["file_path"],
                        content=legacy_data["content"],
                        rule_type=legacy_data["type"],
                        precedence=legacy_data["precedence"],
                        description=legacy_data["description"],
                        globs=legacy_data["globs"],
                        always_apply=legacy_data["always_apply"],
                        metadata=legacy_data["metadata"],
                    )
                    cursor_rules.append(legacy_rule)

                # Convert modern rules
                for modern_data in cursor_data.get("modern_rules", []):
                    modern_rule = CursorRule(
                        file_path=modern_data["file_path"],
                        content=modern_data["content"],
                        rule_type=modern_data["type"],
                        precedence=modern_data["precedence"],
                        description=modern_data["description"],
                        globs=modern_data["globs"],
                        always_apply=modern_data["always_apply"],
                        metadata=modern_data["metadata"],
                    )
                    cursor_rules.append(modern_rule)

        except Exception as e:
            discovery_errors.append(
                {"error_type": "cursor_discovery_error", "error_message": str(e)}
            )

        result = {
            "claude_memory_files": claude_memory_files,
            "cursor_rules": cursor_rules,
            "discovery_errors": discovery_errors,
            "performance_stats": perf_stats,  # Include performance metrics
        }

        return result

    except ImportError as e:
        # Configuration modules not available - return empty result
        logger.warning(f"Configuration discovery modules not available: {e}")
        return {
            "claude_memory_files": [],
            "cursor_rules": [],
            "discovery_errors": [
                {"error_type": "module_import_error", "error_message": str(e)}
            ],
        }


def discover_project_configurations(
    project_path: str,
    include_claude_memory: bool = DEFAULT_INCLUDE_CLAUDE_MEMORY,
    include_cursor_rules: bool = DEFAULT_INCLUDE_CURSOR_RULES,
) -> Dict[str, Any]:
    """
    Discover Claude memory files and Cursor rules from project (cached version).

    Args:
        project_path: Path to project root
        include_claude_memory: Whether to discover CLAUDE.md files (default: False)
        include_cursor_rules: Whether to discover Cursor rules (default: False)

    Returns:
        Dictionary with discovered configurations and any errors
    """
    # Use cache for performance
    configurations = _config_cache.get_configurations(
        project_path, include_claude_memory, include_cursor_rules
    )
    if configurations is None:
        # Fallback if cache returns None
        return {
            "claude_memory": [],
            "cursor_rules": [],
            "discovery_errors": [
                {
                    "error_type": "cache_error",
                    "error_message": "Failed to get configurations from cache",
                }
            ],
        }
    return configurations


def discover_project_configurations_with_fallback(
    project_path: str,
    include_claude_memory: bool = DEFAULT_INCLUDE_CLAUDE_MEMORY,
    include_cursor_rules: bool = DEFAULT_INCLUDE_CURSOR_RULES,
) -> Dict[str, Any]:
    """
    Discover configurations with comprehensive error handling and fallback.

    Args:
        project_path: Path to project root
        include_claude_memory: Whether to discover CLAUDE.md files (default: False)
        include_cursor_rules: Whether to discover Cursor rules (default: False)

    Returns:
        Dictionary with discovered configurations, always includes empty lists on failure
    """
    try:
        return discover_project_configurations(
            project_path, include_claude_memory, include_cursor_rules
        )
    except Exception as e:
        logger.warning(f"Configuration discovery failed: {e}")
        return {
            "claude_memory_files": [],
            "cursor_rules": [],
            "discovery_errors": [
                {"error_type": "discovery_failure", "error_message": str(e)}
            ],
        }


def discover_project_configurations_with_flags(
    project_path: str,
    include_claude_memory: bool = DEFAULT_INCLUDE_CLAUDE_MEMORY,
    include_cursor_rules: bool = DEFAULT_INCLUDE_CURSOR_RULES,
) -> DiscoveredConfigurations:
    """
    Discover configurations with flag-based inclusion control.

    Args:
        project_path: Path to project root
        include_claude_memory: Whether to include CLAUDE.md files (default: False)
        include_cursor_rules: Whether to include Cursor rules files (default: False)

    Returns:
        Dictionary with discovered configurations based on flags
    """
    # Use the cache with the provided flags
    configurations = _config_cache.get_configurations(
        project_path, include_claude_memory, include_cursor_rules
    )
    
    if configurations is None:
        # Fallback if cache returns None
        return DiscoveredConfigurations(
            claude_memory_files=[],
            cursor_rules=[],
            discovery_errors=[
                {
                    "error_type": "cache_error",
                    "error_message": "Failed to get configurations from cache",
                }
            ],
            performance_stats={},
        )
    
    return DiscoveredConfigurations(**configurations)
def merge_configurations_into_context(
    existing_context: Dict[str, Any],
    claude_memory_files: List[Any],
    cursor_rules: List[Any],
) -> Dict[str, Any]:
    """
    Merge discovered configurations into existing review context.

    Args:
        existing_context: Existing context dictionary
        claude_memory_files: List of ClaudeMemoryFile objects
        cursor_rules: List of CursorRule objects

    Returns:
        Enhanced context dictionary with configuration content
    """
    try:
        from ..configuration_context import create_configuration_context

        # Create configuration context
        config_context = create_configuration_context(claude_memory_files, cursor_rules)

        # Enhanced context with configuration data
        enhanced_context = existing_context.copy()
        enhanced_context.update(
            {
                "configuration_content": config_context["merged_content"],
                "claude_memory_files": claude_memory_files,
                "cursor_rules": cursor_rules,
                "auto_apply_rules": config_context["auto_apply_rules"],
                "configuration_errors": config_context["error_summary"],
            }
        )

        return enhanced_context

    except Exception as e:
        logger.warning(f"Failed to merge configurations: {e}")
        # Return original context with empty configuration sections
        enhanced_context = existing_context.copy()
        enhanced_context.update(
            {
                "configuration_content": "",
                "claude_memory_files": claude_memory_files,
                "cursor_rules": cursor_rules,
                "auto_apply_rules": [],
                "configuration_errors": [
                    {"error_type": "merge_error", "error_message": str(e)}
                ],
            }
        )
        return enhanced_context


def format_configuration_context_for_ai(
    claude_memory_files: List[Any], cursor_rules: List[Any]
) -> str:
    """
    Format configuration context for optimal AI consumption.

    Args:
        claude_memory_files: List of ClaudeMemoryFile objects
        cursor_rules: List of CursorRule objects

    Returns:
        Formatted configuration content string
    """
    try:
        from ..configuration_context import (
            merge_claude_memory_content,
            merge_cursor_rules_content,
        )

        # Format Claude memory content
        claude_content = merge_claude_memory_content(claude_memory_files)

        # Format Cursor rules content
        cursor_content = merge_cursor_rules_content(cursor_rules)

        # Combine with clear sections
        sections: List[str] = []

        if claude_content:
            sections.append("# Claude Memory Configuration\n\n" + claude_content)

        if cursor_content:
            sections.append("# Cursor Rules Configuration\n\n" + cursor_content)

        return "\n\n".join(sections)

    except Exception as e:
        logger.warning(f"Failed to format configuration context: {e}")
        return ""


def get_applicable_rules_for_files(
    cursor_rules: List[Any], changed_files: List[str]
) -> List[Any]:
    """
    Get Cursor rules applicable to changed files.

    Args:
        cursor_rules: List of CursorRule objects
        changed_files: List of changed file paths

    Returns:
        List of applicable CursorRule objects

    Note:
        Currently returns all cursor rules regardless of changed files.
        This is intentional as rules may have broader applicability than
        specific file patterns. Future enhancement could filter based on
        file patterns if performance becomes an issue.
    """
    try:
        from ..configuration_context import get_all_cursor_rules

        # Return all cursor rules - file filtering not implemented yet
        # as rules often apply project-wide regardless of specific files
        return get_all_cursor_rules(cursor_rules)

    except Exception as e:
        logger.warning(f"Failed to get applicable rules: {e}")
        return []


def generate_enhanced_review_context(
    project_path: str,
    scope: str = "recent_phase",
    changed_files: Optional[List[str]] = None,
    include_claude_memory: bool = DEFAULT_INCLUDE_CLAUDE_MEMORY,
    include_cursor_rules: bool = DEFAULT_INCLUDE_CURSOR_RULES,
) -> Dict[str, Any]:
    """
    Generate enhanced review context with configuration discovery.

    Args:
        project_path: Path to project root
        scope: Review scope
        changed_files: Optional list of changed file paths
        include_claude_memory: Whether to include CLAUDE.md files
        include_cursor_rules: Whether to include Cursor rules files

    Returns:
        Enhanced context dictionary with configuration data
    """
    # Import git utils
    try:
        from ..helpers.git_utils import get_changed_files
    except ImportError:
        from helpers.git_utils import get_changed_files

    # Discover configurations
    configurations = discover_project_configurations_with_fallback(
        project_path, include_claude_memory, include_cursor_rules
    )

    # Get changed files if not provided
    if changed_files is None:
        git_changed_files = get_changed_files(project_path)
        changed_files = [f["path"] for f in git_changed_files]

    # Ensure we have valid data for rule processing
    cursor_rules: List[Any] = configurations.get("cursor_rules", []) or []
    changed_files = changed_files or []

    # Get applicable rules for changed files
    applicable_rules = get_applicable_rules_for_files(cursor_rules, changed_files)

    # Create basic context structure
    basic_context = {
        "prd_summary": "Enhanced code review with configuration context",
        "current_phase_number": "1.0",
        "current_phase_description": "Configuration-enhanced review",
        "changed_files": changed_files,
        "project_path": project_path,
    }

    # Merge configurations
    enhanced_context = merge_configurations_into_context(
        basic_context,
        configurations["claude_memory_files"],
        configurations["cursor_rules"],
    )

    # Add applicable rules
    enhanced_context["applicable_rules"] = applicable_rules

    return enhanced_context
