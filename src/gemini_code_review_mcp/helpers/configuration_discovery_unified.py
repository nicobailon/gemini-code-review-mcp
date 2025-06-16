"""
Unified configuration discovery module with both sync and async support.

This module consolidates the functionality from configuration_discovery.py and
async_configuration_discovery.py to eliminate code duplication while maintaining
both synchronous and asynchronous operation modes.

Key features:
- Single source of truth for configuration discovery logic
- Support for both sync and async operations
- Automatic fallback strategies for reliability
- Performance optimizations for concurrent file operations
"""

import asyncio
import glob
import logging
import os
import platform
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple, Union

from ..config_types import DEFAULT_INCLUDE_CLAUDE_MEMORY, DEFAULT_INCLUDE_CURSOR_RULES

logger = logging.getLogger(__name__)

# Try to import yaml, fallback if not available
yaml = None  # type: ignore

try:
    import yaml  # type: ignore
except ImportError:
    logger.warning("PyYAML not available. MDC frontmatter parsing will be limited.")

HAS_YAML = yaml is not None


class ConfigurationDiscovery:
    """
    Unified configuration discovery with sync and async support.
    
    This class provides methods for discovering configuration files
    (CLAUDE.md, Cursor rules) with both synchronous and asynchronous
    execution modes.
    """
    
    def __init__(self, use_async: bool = True, max_workers: int = 10):
        """
        Initialize configuration discovery.
        
        Args:
            use_async: Whether to use async operations by default
            max_workers: Maximum concurrent workers for async operations
        """
        self.use_async = use_async
        self.max_workers = max_workers
    
    # ========== Shared Utility Methods ==========
    
    @staticmethod
    def get_platform_specific_enterprise_directories() -> List[str]:
        """
        Get platform-specific enterprise-level configuration directories.
        
        Returns:
            List of platform-appropriate directory paths for enterprise configurations.
        """
        directories: List[str] = []
        system_name = platform.system().lower()
        
        if system_name == "windows":
            # Windows enterprise directories
            program_data = os.environ.get("PROGRAMDATA", "C:\\ProgramData")
            directories.extend([
                os.path.join(program_data, "Claude"),
                os.path.join(program_data, "Anthropic", "Claude"),
                "C:\\Program Files\\Claude",
                "C:\\Program Files\\Anthropic\\Claude",
            ])
        elif system_name == "darwin":  # macOS
            # macOS enterprise directories
            directories.extend([
                "/Library/Application Support/Claude",
                "/Library/Application Support/Anthropic/Claude",
                "/usr/local/etc/claude",
                "/opt/claude",
            ])
        else:  # Linux and other Unix-like systems
            # Linux/Unix enterprise directories
            directories.extend([
                "/etc/claude",
                "/etc/anthropic/claude",
                "/usr/local/etc/claude",
                "/opt/claude/etc",
                "/usr/share/claude",
            ])
        
        return directories
    
    @staticmethod
    def parse_mdc_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
        """
        Parse MDC file frontmatter and content.
        
        Args:
            content: Full MDC file content including frontmatter
            
        Returns:
            Tuple of (metadata_dict, content_without_frontmatter)
        """
        # Check if content starts with frontmatter delimiter
        if not content.strip().startswith("---"):
            return {}, content
        
        # Find the end of frontmatter
        lines = content.split("\n")
        if len(lines) < 3:  # Need at least ---, content, ---
            return {}, content
        
        # Find closing --- delimiter
        end_index = None
        for i, line in enumerate(lines[1:], 1):  # Start from line 1 (skip opening ---)
            if line.strip() == "---":
                end_index = i
                break
        
        if end_index is None:
            # No closing delimiter found, treat as regular content
            return {}, content
        
        # Extract frontmatter and content
        frontmatter_lines = lines[1:end_index]  # Skip opening --- and closing ---
        content_lines = lines[end_index + 1:]  # Content after closing ---
        
        frontmatter_yaml = "\n".join(frontmatter_lines)
        remaining_content = "\n".join(content_lines)
        
        # Parse YAML frontmatter
        metadata: Dict[str, Any] = {}
        if HAS_YAML and yaml is not None and frontmatter_yaml.strip():
            try:
                metadata = yaml.safe_load(frontmatter_yaml) or {}
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse MDC frontmatter: {e}")
                metadata = {}
        elif frontmatter_yaml.strip():
            # Basic fallback parsing without YAML
            logger.warning("PyYAML not available, using basic frontmatter parsing")
            metadata = ConfigurationDiscovery._basic_frontmatter_parse(frontmatter_yaml)
        
        return metadata, remaining_content
    
    @staticmethod
    def _basic_frontmatter_parse(frontmatter: str) -> Dict[str, Any]:
        """Basic frontmatter parsing fallback when PyYAML is not available."""
        metadata: Dict[str, Any] = {}
        
        # Check for complex YAML syntax that basic parser can't handle
        if any(indicator in frontmatter for indicator in ["- ", "  -", ": |", ": >", ": &", ": *"]):
            logger.warning(
                "Complex YAML syntax detected in frontmatter. "
                "Install PyYAML for proper parsing: pip install pyyaml"
            )
        
        for line in frontmatter.split("\n"):
            line = line.strip()
            if ":" in line and not line.startswith("#"):  # Skip comments
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                
                # Validate key format
                if not key or not key.replace("_", "").replace("-", "").isalnum():
                    logger.warning(f"Skipping potentially malformed key: {key}")
                    continue
                
                # Handle boolean values
                if value.lower() in ("true", "false"):
                    metadata[key] = value.lower() == "true"
                # Handle simple arrays [item1, item2]
                elif value.startswith("[") and value.endswith("]"):
                    # Basic array parsing
                    array_content = value[1:-1]  # Remove brackets
                    items = [item.strip().strip("\"'") for item in array_content.split(",")]
                    metadata[key] = [item for item in items if item]
                # Handle strings
                else:
                    # Remove quotes if present
                    metadata[key] = value.strip("\"'")
        
        return metadata
    
    @staticmethod
    def determine_rule_type_from_metadata(metadata: Dict[str, Any]) -> str:
        """Determine rule type from MDC metadata."""
        always_apply = metadata.get("alwaysApply", False)
        return "auto" if always_apply else "agent"
    
    @staticmethod
    def extract_precedence_from_filename(filename: str) -> int:
        """Extract numerical precedence from filename."""
        match = re.match(r"^(\d+)", os.path.basename(filename))
        if match:
            return int(match.group(1))
        return 999  # Default precedence
    
    def _read_file_safe(self, file_path: str) -> Optional[str]:
        """Safely read a file with error handling."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except (IOError, OSError, PermissionError, UnicodeDecodeError) as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return None
    
    # ========== Synchronous Methods ==========
    
    def discover_claude_md_files_sync(self, project_path: str) -> List[Dict[str, Any]]:
        """
        Synchronous discovery of CLAUDE.md files in project hierarchy.
        
        Args:
            project_path: Starting directory path for discovery
            
        Returns:
            List of dictionaries containing file information
        """
        if not os.path.exists(project_path):
            raise ValueError(f"Directory does not exist: {project_path}")
        
        if not os.path.isdir(project_path):
            raise ValueError(f"Path is not a directory: {project_path}")
        
        discovered_files: List[Dict[str, Any]] = []
        visited_paths: set[str] = set()
        
        # Hierarchical traversal up the directory tree
        current_path = os.path.abspath(project_path)
        
        while current_path not in visited_paths:
            visited_paths.add(current_path)
            
            # Check for CLAUDE.md in current directory
            claude_file = os.path.join(current_path, "CLAUDE.md")
            if os.path.isfile(claude_file):
                content = self._read_file_safe(claude_file)
                if content is not None:
                    discovered_files.append({
                        "file_path": claude_file,
                        "scope": "project",
                        "content": content,
                    })
            
            # Move up one directory
            parent_path = os.path.dirname(current_path)
            if parent_path == current_path:  # Reached filesystem root
                break
            current_path = parent_path
        
        # Discover nested CLAUDE.md files
        self._discover_nested_claude_files_sync(project_path, discovered_files, visited_paths)
        
        return discovered_files
    
    def _discover_nested_claude_files_sync(
        self, project_path: str, discovered_files: List[Dict[str, Any]], visited_paths: set[str]
    ) -> None:
        """Discover CLAUDE.md files in nested directories (sync)."""
        try:
            for root, _dirs, files in os.walk(project_path, followlinks=False):
                # Skip if already processed
                if os.path.abspath(root) in visited_paths:
                    continue
                
                if "CLAUDE.md" in files:
                    claude_file = os.path.join(root, "CLAUDE.md")
                    
                    # Skip if already found
                    if any(item["file_path"] == claude_file for item in discovered_files):
                        continue
                    
                    content = self._read_file_safe(claude_file)
                    if content is not None:
                        discovered_files.append({
                            "file_path": claude_file,
                            "scope": "project",
                            "content": content,
                        })
        
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not traverse directory {project_path}: {e}")
    
    def discover_user_level_claude_md_sync(
        self, user_home_override: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Synchronous discovery of user-level CLAUDE.md file."""
        try:
            user_home = user_home_override if user_home_override else os.path.expanduser("~")
            user_claude_file = os.path.join(user_home, ".claude", "CLAUDE.md")
            
            if not os.path.isfile(user_claude_file):
                return None
            
            content = self._read_file_safe(user_claude_file)
            if content is not None:
                return {
                    "file_path": user_claude_file,
                    "scope": "user",
                    "content": content
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Unexpected error discovering user-level CLAUDE.md: {e}")
            return None
    
    def discover_enterprise_level_claude_md_sync(
        self, enterprise_dir_override: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Synchronous discovery of enterprise-level CLAUDE.md file."""
        try:
            if enterprise_dir_override:
                enterprise_directories = [enterprise_dir_override]
            else:
                enterprise_directories = self.get_platform_specific_enterprise_directories()
            
            # Check each enterprise directory
            for enterprise_dir in enterprise_directories:
                enterprise_claude_file = os.path.join(enterprise_dir, "CLAUDE.md")
                
                if not os.path.isfile(enterprise_claude_file):
                    continue
                
                content = self._read_file_safe(enterprise_claude_file)
                if content is not None:
                    return {
                        "file_path": enterprise_claude_file,
                        "scope": "enterprise",
                        "content": content
                    }
            
            return None
            
        except Exception as e:
            logger.warning(f"Unexpected error discovering enterprise-level CLAUDE.md: {e}")
            return None
    
    def discover_legacy_cursorrules_sync(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Synchronous discovery of legacy .cursorrules file."""
        try:
            cursorrules_file = os.path.join(project_path, ".cursorrules")
            
            if not os.path.isfile(cursorrules_file):
                return None
            
            content = self._read_file_safe(cursorrules_file)
            if content is not None:
                return {
                    "file_path": cursorrules_file,
                    "type": "legacy",
                    "description": "Legacy .cursorrules file",
                    "content": content,
                    "globs": [],
                    "precedence": 0,
                    "referenced_files": [],
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Unexpected error discovering legacy .cursorrules: {e}")
            return None
    
    def discover_modern_cursor_rules_sync(self, project_path: str) -> List[Dict[str, Any]]:
        """Synchronous discovery of modern .cursor/rules/*.mdc files."""
        rules: List[Dict[str, Any]] = []
        
        try:
            cursor_rules_dir = os.path.join(project_path, ".cursor", "rules")
            
            if not os.path.isdir(cursor_rules_dir):
                return rules
            
            # Find all .mdc files
            mdc_pattern = os.path.join(cursor_rules_dir, "**", "*.mdc")
            mdc_files = glob.glob(mdc_pattern, recursive=True)
            
            for mdc_file in mdc_files:
                content = self._read_file_safe(mdc_file)
                if content is None:
                    continue
                
                # Parse frontmatter
                metadata, rule_content = self.parse_mdc_frontmatter(content)
                
                # Skip files without valid frontmatter
                if not metadata or "description" not in metadata:
                    logger.warning(
                        f"Skipping malformed MDC file {mdc_file}: no description in frontmatter"
                    )
                    continue
                
                # Build rule information
                rule_info: Dict[str, Any] = {
                    "file_path": mdc_file,
                    "type": self.determine_rule_type_from_metadata(metadata),
                    "description": metadata.get("description", ""),
                    "content": rule_content,
                    "globs": metadata.get("globs", []),
                    "precedence": self.extract_precedence_from_filename(mdc_file),
                    "referenced_files": [],
                }
                
                rules.append(rule_info)
            
            # Sort by precedence
            rules.sort(key=lambda r: r["precedence"])
            
        except Exception as e:
            logger.warning(f"Unexpected error discovering modern cursor rules: {e}")
        
        return rules
    
    def discover_all_configurations_sync(
        self,
        project_path: str,
        include_claude_memory: bool = DEFAULT_INCLUDE_CLAUDE_MEMORY,
        include_cursor_rules: bool = DEFAULT_INCLUDE_CURSOR_RULES,
        user_home_override: Optional[str] = None,
        enterprise_dir_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synchronous discovery of all configuration files.
        
        Args:
            project_path: Starting directory path for discovery
            include_claude_memory: Whether to discover CLAUDE.md files
            include_cursor_rules: Whether to discover Cursor rules
            user_home_override: Optional override for user home directory
            enterprise_dir_override: Optional override for enterprise directory
            
        Returns:
            Dictionary containing all discovered configurations
        """
        start_time = time.time()
        
        result: Dict[str, Any] = {
            "claude_memory_files": [],
            "cursor_rules": [],
            "performance_stats": {
                "total_files_read": 0,
                "discovery_time_ms": 0,
                "method": "sync"
            }
        }
        
        # Discover Claude memory files
        if include_claude_memory:
            try:
                # Project-level files
                project_files = self.discover_claude_md_files_sync(project_path)
                result["claude_memory_files"].extend(project_files)
                
                # User-level file
                user_file = self.discover_user_level_claude_md_sync(user_home_override)
                if user_file:
                    result["claude_memory_files"].append(user_file)
                
                # Enterprise-level file
                enterprise_file = self.discover_enterprise_level_claude_md_sync(enterprise_dir_override)
                if enterprise_file:
                    result["claude_memory_files"].append(enterprise_file)
                    
            except Exception as e:
                logger.error(f"Failed to discover Claude memory files: {e}")
        
        # Discover Cursor rules
        if include_cursor_rules:
            try:
                # Legacy rules
                legacy_rule = self.discover_legacy_cursorrules_sync(project_path)
                if legacy_rule:
                    legacy_rule["hierarchy_level"] = "project"
                    result["cursor_rules"].append(legacy_rule)
                
                # Modern rules
                modern_rules = self.discover_modern_cursor_rules_sync(project_path)
                for rule in modern_rules:
                    rule["hierarchy_level"] = "project"
                    result["cursor_rules"].append(rule)
                    
            except Exception as e:
                logger.error(f"Failed to discover Cursor rules: {e}")
        
        # Calculate stats
        end_time = time.time()
        result["performance_stats"]["discovery_time_ms"] = int((end_time - start_time) * 1000)
        result["performance_stats"]["total_files_read"] = (
            len(result["claude_memory_files"]) + len(result["cursor_rules"])
        )
        
        return result
    
    # ========== Asynchronous Methods ==========
    
    async def _async_read_files(self, file_paths: List[str]) -> Dict[str, str]:
        """Asynchronously read multiple files using thread pool."""
        file_contents: Dict[str, str] = {}
        
        def _read_sync(path: str) -> Optional[Tuple[str, str]]:
            content = self._read_file_safe(path)
            return (path, content) if content is not None else None
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(_read_sync, path): path
                for path in file_paths
            }
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    path, content = result
                    file_contents[path] = content
        
        return file_contents
    
    async def discover_claude_md_files_async(self, project_path: str) -> List[Dict[str, Any]]:
        """Asynchronous discovery of CLAUDE.md files."""
        if not os.path.exists(project_path):
            raise ValueError(f"Project path does not exist: {project_path}")
        
        if not os.path.isdir(project_path):
            raise ValueError(f"Project path must be a directory: {project_path}")
        
        claude_files: List[str] = []
        visited_paths: set[str] = set()
        
        # Hierarchical traversal
        current_path = os.path.abspath(project_path)
        while True:
            visited_paths.add(current_path)
            claude_file = os.path.join(current_path, "CLAUDE.md")
            if os.path.isfile(claude_file):
                claude_files.append(claude_file)
            
            parent_path = os.path.dirname(current_path)
            if parent_path == current_path:
                break
            current_path = parent_path
        
        # Subdirectory traversal
        subdirectory_files = await self._discover_claude_md_subdirectories_async(
            project_path, visited_paths
        )
        claude_files.extend(subdirectory_files)
        
        # Read all files concurrently
        if claude_files:
            file_contents = await self._async_read_files(claude_files)
            
            result: List[Dict[str, Any]] = []
            for file_path in claude_files:
                if file_path in file_contents:
                    result.append({
                        "file_path": file_path,
                        "scope": "project",
                        "content": file_contents[file_path],
                    })
            
            return result
        
        return []
    
    async def _discover_claude_md_subdirectories_async(
        self, project_path: str, visited_paths: set[str]
    ) -> List[str]:
        """Async discovery of CLAUDE.md files in subdirectories."""
        def _walk_dirs() -> List[str]:
            found_files: List[str] = []
            for root, _dirs, files in os.walk(project_path, followlinks=False):
                if os.path.abspath(root) in visited_paths:
                    continue
                if "CLAUDE.md" in files:
                    claude_file = os.path.join(root, "CLAUDE.md")
                    if os.path.isfile(claude_file):
                        found_files.append(claude_file)
            return found_files
        
        # Run in thread to avoid blocking
        return await asyncio.to_thread(_walk_dirs)
    
    async def discover_all_configurations_async(
        self,
        project_path: str,
        include_claude_memory: bool = DEFAULT_INCLUDE_CLAUDE_MEMORY,
        include_cursor_rules: bool = DEFAULT_INCLUDE_CURSOR_RULES,
        user_home_override: Optional[str] = None,
        enterprise_dir_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Asynchronous discovery of all configuration files.
        
        Args:
            project_path: Starting directory path for discovery
            include_claude_memory: Whether to discover CLAUDE.md files
            include_cursor_rules: Whether to discover Cursor rules
            user_home_override: Optional override for user home directory
            enterprise_dir_override: Optional override for enterprise directory
            
        Returns:
            Dictionary containing all discovered configurations
        """
        start_time = time.time()
        
        result: Dict[str, Any] = {
            "claude_memory_files": [],
            "cursor_rules": [],
            "performance_stats": {
                "total_files_read": 0,
                "discovery_time_ms": 0,
                "method": "async"
            }
        }
        
        tasks: List[Tuple[str, asyncio.Task]] = []
        
        if include_claude_memory:
            # Create async tasks for Claude memory discovery
            tasks.append((
                "claude_project",
                asyncio.create_task(self.discover_claude_md_files_async(project_path))
            ))
            
            # User and enterprise discovery can be done in parallel
            async def _async_user():
                return await asyncio.to_thread(
                    self.discover_user_level_claude_md_sync, user_home_override
                )
            
            async def _async_enterprise():
                return await asyncio.to_thread(
                    self.discover_enterprise_level_claude_md_sync, enterprise_dir_override
                )
            
            tasks.append(("claude_user", asyncio.create_task(_async_user())))
            tasks.append(("claude_enterprise", asyncio.create_task(_async_enterprise())))
        
        if include_cursor_rules:
            # Cursor rules discovery
            async def _async_cursor():
                legacy = await asyncio.to_thread(
                    self.discover_legacy_cursorrules_sync, project_path
                )
                modern = await asyncio.to_thread(
                    self.discover_modern_cursor_rules_sync, project_path
                )
                return {"legacy": legacy, "modern": modern}
            
            tasks.append(("cursor", asyncio.create_task(_async_cursor())))
        
        # Execute all tasks concurrently
        for task_name, task in tasks:
            try:
                task_result = await task
                
                if task_name == "claude_project":
                    result["claude_memory_files"].extend(task_result)
                elif task_name == "claude_user" and task_result:
                    result["claude_memory_files"].append(task_result)
                elif task_name == "claude_enterprise" and task_result:
                    result["claude_memory_files"].append(task_result)
                elif task_name == "cursor":
                    if task_result["legacy"]:
                        task_result["legacy"]["hierarchy_level"] = "project"
                        result["cursor_rules"].append(task_result["legacy"])
                    for rule in task_result["modern"]:
                        rule["hierarchy_level"] = "project"
                        result["cursor_rules"].append(rule)
                        
            except Exception as e:
                logger.warning(f"Task {task_name} failed: {e}")
        
        # Calculate stats
        end_time = time.time()
        result["performance_stats"]["discovery_time_ms"] = int((end_time - start_time) * 1000)
        result["performance_stats"]["total_files_read"] = (
            len(result["claude_memory_files"]) + len(result["cursor_rules"])
        )
        
        return result
    
    # ========== Unified Interface ==========
    
    def discover_all_configurations(
        self,
        project_path: str,
        include_claude_memory: bool = DEFAULT_INCLUDE_CLAUDE_MEMORY,
        include_cursor_rules: bool = DEFAULT_INCLUDE_CURSOR_RULES,
        user_home_override: Optional[str] = None,
        enterprise_dir_override: Optional[str] = None,
        force_sync: bool = False,
    ) -> Dict[str, Any]:
        """
        Unified configuration discovery with automatic sync/async selection.
        
        Args:
            project_path: Starting directory path for discovery
            include_claude_memory: Whether to discover CLAUDE.md files
            include_cursor_rules: Whether to discover Cursor rules
            user_home_override: Optional override for user home directory
            enterprise_dir_override: Optional override for enterprise directory
            force_sync: Force synchronous execution even if async is enabled
            
        Returns:
            Dictionary containing all discovered configurations
        """
        if force_sync or not self.use_async:
            return self.discover_all_configurations_sync(
                project_path,
                include_claude_memory,
                include_cursor_rules,
                user_home_override,
                enterprise_dir_override,
            )
        
        # Try async with fallback
        try:
            # Check for existing event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an existing loop - run in thread
                import concurrent.futures
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        self._run_async_in_new_loop,
                        project_path,
                        include_claude_memory,
                        include_cursor_rules,
                        user_home_override,
                        enterprise_dir_override,
                    )
                    return future.result(timeout=30)
                    
            except RuntimeError:
                # No event loop - create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        self.discover_all_configurations_async(
                            project_path,
                            include_claude_memory,
                            include_cursor_rules,
                            user_home_override,
                            enterprise_dir_override,
                        )
                    )
                finally:
                    loop.close()
                    
        except Exception as e:
            logger.warning(f"Async discovery failed: {e}, falling back to sync")
            return self.discover_all_configurations_sync(
                project_path,
                include_claude_memory,
                include_cursor_rules,
                user_home_override,
                enterprise_dir_override,
            )
    
    def _run_async_in_new_loop(
        self,
        project_path: str,
        include_claude_memory: bool,
        include_cursor_rules: bool,
        user_home_override: Optional[str],
        enterprise_dir_override: Optional[str],
    ) -> Dict[str, Any]:
        """Run async discovery in a new event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.discover_all_configurations_async(
                    project_path,
                    include_claude_memory,
                    include_cursor_rules,
                    user_home_override,
                    enterprise_dir_override,
                )
            )
        finally:
            loop.close()


# ========== Backward Compatibility Functions ==========
# These maintain the same signatures as the original modules

_default_discovery = ConfigurationDiscovery(use_async=True)


def discover_claude_md_files(project_path: str) -> List[Dict[str, Any]]:
    """Backward compatible wrapper for discover_claude_md_files."""
    return _default_discovery.discover_claude_md_files_sync(project_path)


def discover_user_level_claude_md(
    user_home_override: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Backward compatible wrapper for discover_user_level_claude_md."""
    return _default_discovery.discover_user_level_claude_md_sync(user_home_override)


def discover_enterprise_level_claude_md(
    enterprise_dir_override: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Backward compatible wrapper for discover_enterprise_level_claude_md."""
    return _default_discovery.discover_enterprise_level_claude_md_sync(enterprise_dir_override)


def discover_all_claude_md_files(
    project_path: str,
    user_home_override: Optional[str] = None,
    enterprise_dir_override: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Backward compatible wrapper for discover_all_claude_md_files."""
    result = _default_discovery.discover_all_configurations_sync(
        project_path,
        include_claude_memory=True,
        include_cursor_rules=False,
        user_home_override=user_home_override,
        enterprise_dir_override=enterprise_dir_override,
    )
    return result["claude_memory_files"]


def discover_legacy_cursorrules(project_path: str) -> Optional[Dict[str, Any]]:
    """Backward compatible wrapper for discover_legacy_cursorrules."""
    return _default_discovery.discover_legacy_cursorrules_sync(project_path)


def discover_modern_cursor_rules(project_path: str) -> List[Dict[str, Any]]:
    """Backward compatible wrapper for discover_modern_cursor_rules."""
    return _default_discovery.discover_modern_cursor_rules_sync(project_path)


def discover_cursor_rules(project_path: str) -> Dict[str, Any]:
    """Backward compatible wrapper for discover_cursor_rules."""
    result: Dict[str, Any] = {"legacy_cursorrules": None, "modern_rules": []}
    
    legacy_rule = _default_discovery.discover_legacy_cursorrules_sync(project_path)
    result["legacy_cursorrules"] = legacy_rule
    
    modern_rules = _default_discovery.discover_modern_cursor_rules_sync(project_path)
    result["modern_rules"] = modern_rules
    
    return result


def discover_all_cursor_rules(project_path: str) -> List[Dict[str, Any]]:
    """Backward compatible wrapper for discover_all_cursor_rules."""
    result = _default_discovery.discover_all_configurations_sync(
        project_path,
        include_claude_memory=False,
        include_cursor_rules=True,
    )
    return result["cursor_rules"]


def discover_configuration_files(
    project_path: str,
    user_home_override: Optional[str] = None,
    enterprise_dir_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Backward compatible wrapper for discover_configuration_files."""
    config_result = _default_discovery.discover_all_configurations_sync(
        project_path,
        include_claude_memory=True,
        include_cursor_rules=True,
        user_home_override=user_home_override,
        enterprise_dir_override=enterprise_dir_override,
    )
    
    # Transform to match original format
    cursor_data = discover_cursor_rules(project_path)
    
    return {
        "claude_memory_files": config_result["claude_memory_files"],
        "cursor_rules": cursor_data["modern_rules"],
        "legacy_cursorrules": cursor_data["legacy_cursorrules"],
    }


def discover_all_configurations(
    project_path: str,
    include_claude_memory: bool = DEFAULT_INCLUDE_CLAUDE_MEMORY,
    include_cursor_rules: bool = DEFAULT_INCLUDE_CURSOR_RULES,
) -> Dict[str, Any]:
    """High-performance configuration discovery with async by default."""
    return _default_discovery.discover_all_configurations(
        project_path,
        include_claude_memory=include_claude_memory,
        include_cursor_rules=include_cursor_rules,
    )


# Additional backward compatibility exports
def get_platform_specific_enterprise_directories() -> List[str]:
    """Backward compatible wrapper."""
    return ConfigurationDiscovery.get_platform_specific_enterprise_directories()


def parse_mdc_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Backward compatible wrapper."""
    return ConfigurationDiscovery.parse_mdc_frontmatter(content)


def determine_rule_type_from_metadata(metadata: Dict[str, Any]) -> str:
    """Backward compatible wrapper."""
    return ConfigurationDiscovery.determine_rule_type_from_metadata(metadata)


def extract_precedence_from_filename(filename: str) -> int:
    """Backward compatible wrapper."""
    return ConfigurationDiscovery.extract_precedence_from_filename(filename)


# Export all for compatibility
__all__ = [
    "ConfigurationDiscovery",
    "discover_claude_md_files",
    "discover_user_level_claude_md",
    "discover_enterprise_level_claude_md",
    "discover_all_claude_md_files",
    "discover_legacy_cursorrules",
    "discover_modern_cursor_rules",
    "discover_cursor_rules",
    "discover_all_cursor_rules",
    "discover_configuration_files",
    "discover_all_configurations",
    "get_platform_specific_enterprise_directories",
    "parse_mdc_frontmatter",
    "determine_rule_type_from_metadata",
    "extract_precedence_from_filename",
]