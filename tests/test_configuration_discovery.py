"""
Test-driven development tests for configuration discovery functionality.

This module tests the discovery of CLAUDE.md files across project hierarchy,
user-level configurations, and enterprise policies.

Following TDD protocol: Tests written FIRST to define expected behavior.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestClaudeMemoryFileDiscovery(unittest.TestCase):
    """Test CLAUDE.md file discovery functionality."""

    def setUp(self):
        """Set up test environment with temporary directories."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name

    def tearDown(self):
        """Clean up temporary directories."""
        self.temp_dir.cleanup()

    def test_discover_claude_md_files_returns_empty_list_when_no_files_exist(self):
        """Test that discovery returns empty list when no CLAUDE.md files exist."""
        from configuration_discovery import discover_claude_md_files

        result = discover_claude_md_files(self.project_root)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_discover_claude_md_files_finds_project_root_file(self):
        """Test discovery of CLAUDE.md in project root directory."""
        from configuration_discovery import discover_claude_md_files

        # Create CLAUDE.md in project root
        claude_file = os.path.join(self.project_root, "CLAUDE.md")
        with open(claude_file, "w") as f:
            f.write("# Project-level Claude memory\nTest content")

        result = discover_claude_md_files(self.project_root)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["file_path"], claude_file)
        self.assertEqual(result[0]["scope"], "project")
        self.assertIn("content", result[0])
        self.assertEqual(
            result[0]["content"], "# Project-level Claude memory\nTest content"
        )

    def test_discover_claude_md_files_finds_nested_directory_files(self):
        """Test discovery of CLAUDE.md files in nested project directories."""
        from configuration_discovery import discover_claude_md_files

        # Create nested directories with CLAUDE.md files
        subdir1 = os.path.join(self.project_root, "subproject1")
        os.makedirs(subdir1)
        claude_file1 = os.path.join(subdir1, "CLAUDE.md")
        with open(claude_file1, "w") as f:
            f.write("# Subproject 1 memory")

        subdir2 = os.path.join(self.project_root, "packages", "module")
        os.makedirs(subdir2)
        claude_file2 = os.path.join(subdir2, "CLAUDE.md")
        with open(claude_file2, "w") as f:
            f.write("# Module-specific memory")

        result = discover_claude_md_files(self.project_root)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        # Should find both files
        file_paths = [item["file_path"] for item in result]
        self.assertIn(claude_file1, file_paths)
        self.assertIn(claude_file2, file_paths)

        # All should be project scope
        for item in result:
            self.assertEqual(item["scope"], "project")

    def test_discover_claude_md_files_hierarchical_traversal_from_subdirectory(self):
        """Test hierarchical traversal when starting from a subdirectory."""
        from configuration_discovery import discover_claude_md_files

        # Create hierarchy: root/CLAUDE.md, root/sub/CLAUDE.md, root/sub/subsub/
        root_claude = os.path.join(self.project_root, "CLAUDE.md")
        with open(root_claude, "w") as f:
            f.write("# Root memory")

        subdir = os.path.join(self.project_root, "sub")
        os.makedirs(subdir)
        sub_claude = os.path.join(subdir, "CLAUDE.md")
        with open(sub_claude, "w") as f:
            f.write("# Sub memory")

        subsubdir = os.path.join(subdir, "subsub")
        os.makedirs(subsubdir)

        # Start discovery from deepest directory
        result = discover_claude_md_files(subsubdir)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        # Should find files in hierarchical order (closest first)
        file_paths = [item["file_path"] for item in result]
        self.assertIn(sub_claude, file_paths)
        self.assertIn(root_claude, file_paths)

        # First result should be the closest (sub directory)
        self.assertEqual(result[0]["file_path"], sub_claude)
        self.assertEqual(result[1]["file_path"], root_claude)

    def test_discover_claude_md_files_handles_invalid_directory_path(self):
        """Test discovery handles invalid directory paths gracefully."""
        from configuration_discovery import discover_claude_md_files

        with self.assertRaises(ValueError) as context:
            discover_claude_md_files("/nonexistent/directory/path")

        self.assertIn("Directory does not exist", str(context.exception))

    def test_discover_claude_md_files_handles_file_permission_errors(self):
        """Test discovery handles file permission errors gracefully."""
        from configuration_discovery import discover_claude_md_files

        # Create CLAUDE.md with restricted permissions (Unix-like systems)
        claude_file = os.path.join(self.project_root, "CLAUDE.md")
        with open(claude_file, "w") as f:
            f.write("# Restricted file")

        # Make file unreadable (skip on Windows)
        if os.name != "nt":
            os.chmod(claude_file, 0o000)

        try:
            result = discover_claude_md_files(self.project_root)

            # Should return empty list or handle gracefully
            self.assertIsInstance(result, list)
            # File should either be skipped or error logged but not crash

        finally:
            # Restore permissions for cleanup
            if os.name != "nt":
                os.chmod(claude_file, 0o644)

    def test_discover_claude_md_files_returns_content_with_file_info(self):
        """Test that discovery returns complete file information."""
        from configuration_discovery import discover_claude_md_files

        claude_file = os.path.join(self.project_root, "CLAUDE.md")
        test_content = "# Test Memory\n\nSome test content\nwith multiple lines"
        with open(claude_file, "w") as f:
            f.write(test_content)

        result = discover_claude_md_files(self.project_root)

        self.assertEqual(len(result), 1)
        file_info = result[0]

        # Should contain required fields
        required_fields = ["file_path", "scope", "content"]
        for field in required_fields:
            self.assertIn(field, file_info)

        # Verify content matches
        self.assertEqual(file_info["content"], test_content)
        self.assertEqual(file_info["file_path"], claude_file)
        self.assertEqual(file_info["scope"], "project")

    def test_discover_claude_md_files_skips_malformed_files(self):
        """Test that discovery handles malformed CLAUDE.md files gracefully."""
        from configuration_discovery import discover_claude_md_files

        # Create a valid file
        valid_file = os.path.join(self.project_root, "CLAUDE.md")
        with open(valid_file, "w") as f:
            f.write("# Valid content")

        # Create a binary file with .md extension (malformed)
        malformed_subdir = os.path.join(self.project_root, "subdir")
        os.makedirs(malformed_subdir)
        malformed_file = os.path.join(malformed_subdir, "CLAUDE.md")
        with open(malformed_file, "wb") as f:
            f.write(b"\x00\x01\x02\x03\xff\xfe")  # Binary content

        result = discover_claude_md_files(self.project_root)

        # Should find the valid file and skip the malformed one
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["file_path"], valid_file)


class TestUserLevelConfigurationDiscovery(unittest.TestCase):
    """Test user-level CLAUDE.md configuration discovery."""

    def setUp(self):
        """Set up test environment with temporary user directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name

        # Create temporary user directory
        self.user_temp_dir = tempfile.TemporaryDirectory()
        self.fake_user_home = self.user_temp_dir.name

    def tearDown(self):
        """Clean up temporary directories."""
        self.temp_dir.cleanup()
        self.user_temp_dir.cleanup()

    def test_discover_user_level_claude_md_when_exists(self):
        """Test discovery of user-level CLAUDE.md file when it exists."""
        from configuration_discovery import discover_user_level_claude_md

        # Create ~/.claude/CLAUDE.md in fake home directory
        claude_dir = os.path.join(self.fake_user_home, ".claude")
        os.makedirs(claude_dir)
        user_claude_file = os.path.join(claude_dir, "CLAUDE.md")
        user_content = "# User-level Claude memory\nUser preferences and settings"
        with open(user_claude_file, "w") as f:
            f.write(user_content)

        result = discover_user_level_claude_md(user_home_override=self.fake_user_home)

        self.assertIsNotNone(result)
        assert result is not None  # Type guard for pyright
        self.assertEqual(result["file_path"], user_claude_file)
        self.assertEqual(result["scope"], "user")
        self.assertEqual(result["content"], user_content)

    def test_discover_user_level_claude_md_when_not_exists(self):
        """Test discovery returns None when user-level CLAUDE.md doesn't exist."""
        from configuration_discovery import discover_user_level_claude_md

        result = discover_user_level_claude_md(user_home_override=self.fake_user_home)

        self.assertIsNone(result)

    def test_discover_user_level_claude_md_handles_permission_errors(self):
        """Test discovery handles permission errors gracefully."""
        from configuration_discovery import discover_user_level_claude_md

        # Create ~/.claude/CLAUDE.md with restricted permissions
        claude_dir = os.path.join(self.fake_user_home, ".claude")
        os.makedirs(claude_dir)
        user_claude_file = os.path.join(claude_dir, "CLAUDE.md")
        with open(user_claude_file, "w") as f:
            f.write("# Restricted user config")

        # Make file unreadable (skip on Windows)
        if os.name != "nt":
            os.chmod(user_claude_file, 0o000)

        try:
            result = discover_user_level_claude_md(
                user_home_override=self.fake_user_home
            )

            # Should return None when file is unreadable
            self.assertIsNone(result)

        finally:
            # Restore permissions for cleanup
            if os.name != "nt":
                os.chmod(user_claude_file, 0o644)

    def test_discover_user_level_claude_md_handles_malformed_content(self):
        """Test discovery handles malformed user-level CLAUDE.md files."""
        from configuration_discovery import discover_user_level_claude_md

        # Create ~/.claude/CLAUDE.md with binary content
        claude_dir = os.path.join(self.fake_user_home, ".claude")
        os.makedirs(claude_dir)
        user_claude_file = os.path.join(claude_dir, "CLAUDE.md")
        with open(user_claude_file, "wb") as f:
            f.write(b"\x00\x01\x02\x03\xff\xfe")  # Binary content

        result = discover_user_level_claude_md(user_home_override=self.fake_user_home)

        # Should return None when content is malformed
        self.assertIsNone(result)

    def test_discover_user_level_claude_md_with_real_home_directory(self):
        """Test discovery uses real home directory when no override provided."""
        from configuration_discovery import discover_user_level_claude_md

        # This test should not crash even if real ~/.claude/CLAUDE.md doesn't exist
        result = discover_user_level_claude_md()

        # Result should be None or a valid dict, but not crash
        # Result should be None or a valid dict, but not crash
        # (result is typed as Dict[str, Any] | None, so dict check is redundant)

        if result is not None:
            # If found, should have correct structure
            required_fields = ["file_path", "scope", "content"]
            for field in required_fields:
                self.assertIn(field, result)
            self.assertEqual(result["scope"], "user")


class TestEnterpriseLevelConfigurationDiscovery(unittest.TestCase):
    """Test enterprise-level CLAUDE.md configuration discovery."""

    def setUp(self):
        """Set up test environment with temporary enterprise directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name

        # Create temporary enterprise directory
        self.enterprise_temp_dir = tempfile.TemporaryDirectory()
        self.fake_enterprise_dir = self.enterprise_temp_dir.name

    def tearDown(self):
        """Clean up temporary directories."""
        self.temp_dir.cleanup()
        self.enterprise_temp_dir.cleanup()

    def test_discover_enterprise_level_claude_md_when_exists(self):
        """Test discovery of enterprise-level CLAUDE.md file when it exists."""
        from configuration_discovery import discover_enterprise_level_claude_md

        # Create enterprise CLAUDE.md file
        enterprise_claude_file = os.path.join(self.fake_enterprise_dir, "CLAUDE.md")
        enterprise_content = (
            "# Enterprise-level Claude memory\nCompany policies and standards"
        )
        with open(enterprise_claude_file, "w") as f:
            f.write(enterprise_content)

        result = discover_enterprise_level_claude_md(
            enterprise_dir_override=self.fake_enterprise_dir
        )

        self.assertIsNotNone(result)
        assert result is not None  # Type guard for pyright
        self.assertEqual(result["file_path"], enterprise_claude_file)
        self.assertEqual(result["scope"], "enterprise")
        self.assertEqual(result["content"], enterprise_content)

    def test_discover_enterprise_level_claude_md_when_not_exists(self):
        """Test discovery returns None when enterprise-level CLAUDE.md doesn't exist."""
        from configuration_discovery import discover_enterprise_level_claude_md

        result = discover_enterprise_level_claude_md(
            enterprise_dir_override=self.fake_enterprise_dir
        )

        self.assertIsNone(result)

    def test_discover_enterprise_level_claude_md_handles_permission_errors(self):
        """Test discovery handles permission errors gracefully."""
        from configuration_discovery import discover_enterprise_level_claude_md

        # Create enterprise CLAUDE.md with restricted permissions
        enterprise_claude_file = os.path.join(self.fake_enterprise_dir, "CLAUDE.md")
        with open(enterprise_claude_file, "w") as f:
            f.write("# Restricted enterprise config")

        # Make file unreadable (skip on Windows)
        if os.name != "nt":
            os.chmod(enterprise_claude_file, 0o000)

        try:
            result = discover_enterprise_level_claude_md(
                enterprise_dir_override=self.fake_enterprise_dir
            )

            # Should return None when file is unreadable
            self.assertIsNone(result)

        finally:
            # Restore permissions for cleanup
            if os.name != "nt":
                os.chmod(enterprise_claude_file, 0o644)

    def test_discover_enterprise_level_claude_md_handles_malformed_content(self):
        """Test discovery handles malformed enterprise-level CLAUDE.md files."""
        from configuration_discovery import discover_enterprise_level_claude_md

        # Create enterprise CLAUDE.md with binary content
        enterprise_claude_file = os.path.join(self.fake_enterprise_dir, "CLAUDE.md")
        with open(enterprise_claude_file, "wb") as f:
            f.write(b"\x00\x01\x02\x03\xff\xfe")  # Binary content

        result = discover_enterprise_level_claude_md(
            enterprise_dir_override=self.fake_enterprise_dir
        )

        # Should return None when content is malformed
        self.assertIsNone(result)

    def test_get_platform_specific_enterprise_directories_returns_correct_paths(self):
        """Test that platform-specific enterprise directories are returned correctly."""
        from configuration_discovery import get_platform_specific_enterprise_directories

        directories = get_platform_specific_enterprise_directories()

        self.assertIsInstance(directories, list)
        self.assertGreater(len(directories), 0)

        # Should contain platform-appropriate paths
        if os.name == "nt":  # Windows
            # Should contain Windows-style paths
            windows_paths = [
                d for d in directories if "ProgramData" in d or "Program Files" in d
            ]
            self.assertGreater(len(windows_paths), 0)
        else:  # Unix-like (Linux, macOS)
            # Should contain Unix-style paths
            unix_paths = [d for d in directories if d.startswith("/")]
            self.assertGreater(len(unix_paths), 0)

    def test_discover_enterprise_level_claude_md_with_real_platform_directories(self):
        """Test discovery uses real platform directories when no override provided."""
        from configuration_discovery import discover_enterprise_level_claude_md

        # This test should not crash even if real enterprise directories don't exist
        result = discover_enterprise_level_claude_md()

        # Result should be None or a valid dict, but not crash
        # Result should be None or a valid dict, but not crash
        # (result is typed as Dict[str, Any] | None, so dict check is redundant)

        if result is not None:
            # If found, should have correct structure
            required_fields = ["file_path", "scope", "content"]
            for field in required_fields:
                self.assertIn(field, result)
            self.assertEqual(result["scope"], "enterprise")


class TestComprehensiveConfigurationDiscovery(unittest.TestCase):
    """Test comprehensive discovery that combines project, user, and enterprise configurations."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name

        self.user_temp_dir = tempfile.TemporaryDirectory()
        self.fake_user_home = self.user_temp_dir.name

        self.enterprise_temp_dir = tempfile.TemporaryDirectory()
        self.fake_enterprise_dir = self.enterprise_temp_dir.name

    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
        self.user_temp_dir.cleanup()
        self.enterprise_temp_dir.cleanup()

    def test_discover_all_claude_md_files_combines_all_levels(self):
        """Test that discovery combines project, user, and enterprise CLAUDE.md files."""
        from configuration_discovery import discover_all_claude_md_files

        # Create project-level CLAUDE.md
        project_claude = os.path.join(self.project_root, "CLAUDE.md")
        with open(project_claude, "w") as f:
            f.write("# Project configuration")

        # Create user-level CLAUDE.md
        claude_dir = os.path.join(self.fake_user_home, ".claude")
        os.makedirs(claude_dir)
        user_claude = os.path.join(claude_dir, "CLAUDE.md")
        with open(user_claude, "w") as f:
            f.write("# User configuration")

        # Create enterprise-level CLAUDE.md
        enterprise_claude = os.path.join(self.fake_enterprise_dir, "CLAUDE.md")
        with open(enterprise_claude, "w") as f:
            f.write("# Enterprise configuration")

        result = discover_all_claude_md_files(
            self.project_root,
            user_home_override=self.fake_user_home,
            enterprise_dir_override=self.fake_enterprise_dir,
        )

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

        # Should contain all three levels
        file_paths = [item["file_path"] for item in result]
        self.assertIn(project_claude, file_paths)
        self.assertIn(user_claude, file_paths)
        self.assertIn(enterprise_claude, file_paths)

        # Check scopes are correct
        scopes = [item["scope"] for item in result]
        self.assertIn("project", scopes)
        self.assertIn("user", scopes)
        self.assertIn("enterprise", scopes)

    def test_discover_all_claude_md_files_handles_missing_enterprise_config(self):
        """Test discovery works when enterprise-level config doesn't exist."""
        from configuration_discovery import discover_all_claude_md_files

        # Create only project and user configs
        project_claude = os.path.join(self.project_root, "CLAUDE.md")
        with open(project_claude, "w") as f:
            f.write("# Project configuration")

        claude_dir = os.path.join(self.fake_user_home, ".claude")
        os.makedirs(claude_dir)
        user_claude = os.path.join(claude_dir, "CLAUDE.md")
        with open(user_claude, "w") as f:
            f.write("# User configuration")

        result = discover_all_claude_md_files(
            self.project_root,
            user_home_override=self.fake_user_home,
            enterprise_dir_override=self.fake_enterprise_dir,
        )

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        scopes = [item["scope"] for item in result]
        self.assertIn("project", scopes)
        self.assertIn("user", scopes)
        self.assertNotIn("enterprise", scopes)


class TestIntegratedConfigurationDiscovery(unittest.TestCase):
    """Test integrated discovery that combines project and user-level configurations."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name

        self.user_temp_dir = tempfile.TemporaryDirectory()
        self.fake_user_home = self.user_temp_dir.name

    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
        self.user_temp_dir.cleanup()

    def test_discover_all_claude_md_files_combines_project_and_user(self):
        """Test that discovery combines both project and user-level CLAUDE.md files."""
        from configuration_discovery import discover_all_claude_md_files

        # Create project-level CLAUDE.md
        project_claude = os.path.join(self.project_root, "CLAUDE.md")
        with open(project_claude, "w") as f:
            f.write("# Project configuration")

        # Create user-level CLAUDE.md
        claude_dir = os.path.join(self.fake_user_home, ".claude")
        os.makedirs(claude_dir)
        user_claude = os.path.join(claude_dir, "CLAUDE.md")
        with open(user_claude, "w") as f:
            f.write("# User configuration")

        result = discover_all_claude_md_files(
            self.project_root, user_home_override=self.fake_user_home
        )

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        # Should contain both project and user files
        file_paths = [item["file_path"] for item in result]
        self.assertIn(project_claude, file_paths)
        self.assertIn(user_claude, file_paths)

        # Check scopes are correct
        scopes = [item["scope"] for item in result]
        self.assertIn("project", scopes)
        self.assertIn("user", scopes)

    def test_discover_all_claude_md_files_handles_missing_user_config(self):
        """Test discovery works when user-level config doesn't exist."""
        from configuration_discovery import discover_all_claude_md_files

        # Create only project-level CLAUDE.md
        project_claude = os.path.join(self.project_root, "CLAUDE.md")
        with open(project_claude, "w") as f:
            f.write("# Project configuration")

        result = discover_all_claude_md_files(
            self.project_root, user_home_override=self.fake_user_home
        )

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["file_path"], project_claude)
        self.assertEqual(result[0]["scope"], "project")

    def test_discover_all_claude_md_files_handles_missing_project_config(self):
        """Test discovery works when project-level config doesn't exist."""
        from configuration_discovery import discover_all_claude_md_files

        # Create only user-level CLAUDE.md
        claude_dir = os.path.join(self.fake_user_home, ".claude")
        os.makedirs(claude_dir)
        user_claude = os.path.join(claude_dir, "CLAUDE.md")
        with open(user_claude, "w") as f:
            f.write("# User configuration")

        result = discover_all_claude_md_files(
            self.project_root, user_home_override=self.fake_user_home
        )

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["file_path"], user_claude)
        self.assertEqual(result[0]["scope"], "user")


class TestConfigurationDiscoveryInterface(unittest.TestCase):
    """Test the main configuration discovery interface."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name

    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()

    def test_discover_configuration_files_returns_structured_data(self):
        """Test that main discovery function returns properly structured data."""
        from configuration_discovery import discover_configuration_files

        result = discover_configuration_files(self.project_root)

        self.assertIsInstance(result, dict)
        self.assertIn("claude_memory_files", result)
        self.assertIsInstance(result["claude_memory_files"], list)

    def test_discover_configuration_files_integrates_claude_md_discovery(self):
        """Test that main function integrates CLAUDE.md file discovery."""
        from configuration_discovery import discover_configuration_files

        # Create test CLAUDE.md file
        claude_file = os.path.join(self.project_root, "CLAUDE.md")
        with open(claude_file, "w") as f:
            f.write("# Test configuration")

        # Use empty user and enterprise overrides to ensure clean test
        result = discover_configuration_files(
            self.project_root,
            user_home_override="/nonexistent/user/home",
            enterprise_dir_override="/nonexistent/enterprise",
        )

        self.assertEqual(len(result["claude_memory_files"]), 1)
        self.assertEqual(result["claude_memory_files"][0]["file_path"], claude_file)
        self.assertEqual(result["claude_memory_files"][0]["scope"], "project")

    def test_discover_configuration_files_integrates_user_level_discovery(self):
        """Test that main function integrates user-level configuration discovery."""
        from configuration_discovery import discover_configuration_files

        # Create temporary user directory with CLAUDE.md
        user_temp_dir = tempfile.TemporaryDirectory()
        fake_user_home = user_temp_dir.name

        try:
            claude_dir = os.path.join(fake_user_home, ".claude")
            os.makedirs(claude_dir)
            user_claude_file = os.path.join(claude_dir, "CLAUDE.md")
            with open(user_claude_file, "w") as f:
                f.write("# User configuration")

            result = discover_configuration_files(
                self.project_root,
                user_home_override=fake_user_home,
                enterprise_dir_override="/nonexistent/enterprise",
            )

            # Should find user-level configuration
            user_files = [
                f for f in result["claude_memory_files"] if f["scope"] == "user"
            ]
            self.assertEqual(len(user_files), 1)
            self.assertEqual(user_files[0]["file_path"], user_claude_file)

        finally:
            user_temp_dir.cleanup()

    def test_discover_configuration_files_integrates_enterprise_level_discovery(self):
        """Test that main function integrates enterprise-level configuration discovery."""
        from configuration_discovery import discover_configuration_files

        # Create temporary enterprise directory with CLAUDE.md
        enterprise_temp_dir = tempfile.TemporaryDirectory()
        fake_enterprise_dir = enterprise_temp_dir.name

        try:
            enterprise_claude_file = os.path.join(fake_enterprise_dir, "CLAUDE.md")
            with open(enterprise_claude_file, "w") as f:
                f.write("# Enterprise configuration")

            result = discover_configuration_files(
                self.project_root,
                user_home_override="/nonexistent/user",
                enterprise_dir_override=fake_enterprise_dir,
            )

            # Should find enterprise-level configuration
            enterprise_files = [
                f for f in result["claude_memory_files"] if f["scope"] == "enterprise"
            ]
            self.assertEqual(len(enterprise_files), 1)
            self.assertEqual(enterprise_files[0]["file_path"], enterprise_claude_file)

        finally:
            enterprise_temp_dir.cleanup()


class TestCursorRulesDiscovery(unittest.TestCase):
    """Test Cursor rules file discovery functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name

    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()

    def test_discover_legacy_cursorrules_file_when_exists(self):
        """Test discovery of legacy .cursorrules file when it exists."""
        from configuration_discovery import discover_legacy_cursorrules

        # Create legacy .cursorrules file
        cursorrules_file = os.path.join(self.project_root, ".cursorrules")
        legacy_content = "Use TypeScript for all new files\nPrefer functional programming patterns\nWrite tests for all functions"
        with open(cursorrules_file, "w") as f:
            f.write(legacy_content)

        result = discover_legacy_cursorrules(self.project_root)

        self.assertIsNotNone(result)
        assert result is not None  # Type guard for pyright
        self.assertEqual(result["file_path"], cursorrules_file)
        self.assertEqual(result["type"], "legacy")
        self.assertEqual(result["content"], legacy_content)
        self.assertEqual(result["description"], "Legacy .cursorrules file")

    def test_discover_legacy_cursorrules_file_when_not_exists(self):
        """Test discovery returns None when legacy .cursorrules doesn't exist."""
        from configuration_discovery import discover_legacy_cursorrules

        result = discover_legacy_cursorrules(self.project_root)

        self.assertIsNone(result)

    def test_discover_modern_cursor_rules_finds_mdc_files(self):
        """Test discovery of modern .cursor/rules/*.mdc files."""
        from configuration_discovery import discover_modern_cursor_rules

        # Create .cursor/rules directory with MDC files
        cursor_rules_dir = os.path.join(self.project_root, ".cursor", "rules")
        os.makedirs(cursor_rules_dir)

        # Create numbered MDC file
        mdc_file1 = os.path.join(cursor_rules_dir, "001-typescript.mdc")
        mdc_content1 = """---
description: TypeScript coding standards
globs: ["*.ts", "*.tsx"]
alwaysApply: true
---

# TypeScript Rules
Use TypeScript for all new files.
Always define explicit return types."""
        with open(mdc_file1, "w") as f:
            f.write(mdc_content1)

        # Create another MDC file
        mdc_file2 = os.path.join(cursor_rules_dir, "050-testing.mdc")
        mdc_content2 = """---
description: Testing guidelines
globs: ["*.test.ts", "*.spec.ts"]
alwaysApply: false
---

# Testing Rules
Write comprehensive tests.
Use describe and it blocks."""
        with open(mdc_file2, "w") as f:
            f.write(mdc_content2)

        result = discover_modern_cursor_rules(self.project_root)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        # Check first file
        rule1 = next(r for r in result if "001-typescript" in r["file_path"])
        self.assertEqual(rule1["type"], "auto")  # alwaysApply: true -> auto
        self.assertEqual(rule1["description"], "TypeScript coding standards")
        self.assertEqual(rule1["globs"], ["*.ts", "*.tsx"])
        self.assertEqual(rule1["precedence"], 1)
        self.assertIn("TypeScript Rules", rule1["content"])

        # Check second file
        rule2 = next(r for r in result if "050-testing" in r["file_path"])
        self.assertEqual(rule2["type"], "agent")  # alwaysApply: false -> agent
        self.assertEqual(rule2["description"], "Testing guidelines")
        self.assertEqual(rule2["globs"], ["*.test.ts", "*.spec.ts"])
        self.assertEqual(rule2["precedence"], 50)

    def test_discover_modern_cursor_rules_handles_malformed_mdc(self):
        """Test discovery handles malformed MDC files gracefully."""
        from configuration_discovery import discover_modern_cursor_rules

        cursor_rules_dir = os.path.join(self.project_root, ".cursor", "rules")
        os.makedirs(cursor_rules_dir)

        # Create valid MDC file
        valid_file = os.path.join(cursor_rules_dir, "001-valid.mdc")
        with open(valid_file, "w") as f:
            f.write(
                """---
description: Valid rule
---

Valid content"""
            )

        # Create malformed MDC file (no frontmatter)
        malformed_file = os.path.join(cursor_rules_dir, "002-malformed.mdc")
        with open(malformed_file, "w") as f:
            f.write("Just plain content without frontmatter")

        result = discover_modern_cursor_rules(self.project_root)

        # Should find the valid file and skip the malformed one
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["description"], "Valid rule")

    def test_discover_modern_cursor_rules_extracts_precedence_from_filename(self):
        """Test precedence extraction from numbered filenames."""
        from configuration_discovery import discover_modern_cursor_rules

        cursor_rules_dir = os.path.join(self.project_root, ".cursor", "rules")
        os.makedirs(cursor_rules_dir)

        # Create files with different precedence numbers
        test_cases = [
            ("005-low.mdc", 5),
            ("100-high.mdc", 100),
            ("001-first.mdc", 1),
            ("no-number.mdc", 999),  # Default precedence for no number
        ]

        for filename, expected_precedence in test_cases:
            file_path = os.path.join(cursor_rules_dir, filename)
            with open(file_path, "w") as f:
                f.write(
                    f"""---
description: Test rule {expected_precedence}
---

Content"""
                )

        result = discover_modern_cursor_rules(self.project_root)

        self.assertEqual(len(result), 4)

        # Check precedence values
        for rule in result:
            if "005-low" in rule["file_path"]:
                self.assertEqual(rule["precedence"], 5)
            elif "100-high" in rule["file_path"]:
                self.assertEqual(rule["precedence"], 100)
            elif "001-first" in rule["file_path"]:
                self.assertEqual(rule["precedence"], 1)
            elif "no-number" in rule["file_path"]:
                self.assertEqual(rule["precedence"], 999)

    def test_discover_modern_cursor_rules_handles_no_cursor_directory(self):
        """Test discovery when .cursor directory doesn't exist."""
        from configuration_discovery import discover_modern_cursor_rules

        result = discover_modern_cursor_rules(self.project_root)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_discover_cursor_rules_combines_legacy_and_modern(self):
        """Test that discovery combines both legacy and modern Cursor rules."""
        from configuration_discovery import discover_cursor_rules

        # Create legacy .cursorrules file
        cursorrules_file = os.path.join(self.project_root, ".cursorrules")
        with open(cursorrules_file, "w") as f:
            f.write("Legacy cursor rules")

        # Create modern rules
        cursor_rules_dir = os.path.join(self.project_root, ".cursor", "rules")
        os.makedirs(cursor_rules_dir)
        mdc_file = os.path.join(cursor_rules_dir, "001-modern.mdc")
        with open(mdc_file, "w") as f:
            f.write(
                """---
description: Modern rule
---

Modern content"""
            )

        result = discover_cursor_rules(self.project_root)

        self.assertIsInstance(result, dict)
        self.assertIn("legacy_cursorrules", result)
        self.assertIn("modern_rules", result)

        # Check legacy rule
        self.assertIsNotNone(result["legacy_cursorrules"])
        self.assertEqual(result["legacy_cursorrules"]["content"], "Legacy cursor rules")

        # Check modern rules
        self.assertEqual(len(result["modern_rules"]), 1)
        self.assertEqual(result["modern_rules"][0]["description"], "Modern rule")

    def test_parse_mdc_frontmatter_extracts_metadata_correctly(self):
        """Test MDC frontmatter parsing extracts metadata correctly."""
        from configuration_discovery import parse_mdc_frontmatter

        mdc_content = """---
description: Test rule
globs: ["*.ts", "*.js"]
alwaysApply: true
customField: custom value
---

# Main Content
This is the main rule content.
Multiple lines of content."""

        metadata, content = parse_mdc_frontmatter(mdc_content)

        self.assertEqual(metadata["description"], "Test rule")
        self.assertEqual(metadata["globs"], ["*.ts", "*.js"])
        self.assertEqual(metadata["alwaysApply"], True)
        self.assertEqual(metadata["customField"], "custom value")
        self.assertEqual(
            content.strip(),
            "# Main Content\nThis is the main rule content.\nMultiple lines of content.",
        )

    def test_parse_mdc_frontmatter_handles_missing_frontmatter(self):
        """Test MDC parsing handles content without frontmatter."""
        from configuration_discovery import parse_mdc_frontmatter

        content_without_frontmatter = """# Just Content
No frontmatter here.
Just plain content."""

        metadata, content = parse_mdc_frontmatter(content_without_frontmatter)

        self.assertEqual(metadata, {})
        self.assertEqual(content, content_without_frontmatter)

    def test_determine_rule_type_from_metadata(self):
        """Test rule type determination from metadata."""
        from configuration_discovery import determine_rule_type_from_metadata

        # Test always apply rules
        metadata_always = {"alwaysApply": True}
        self.assertEqual(determine_rule_type_from_metadata(metadata_always), "auto")

        # Test non-always apply rules
        metadata_not_always = {"alwaysApply": False}
        self.assertEqual(
            determine_rule_type_from_metadata(metadata_not_always), "agent"
        )

        # Test missing alwaysApply field (default to agent)
        metadata_missing = {"description": "Some rule"}
        self.assertEqual(determine_rule_type_from_metadata(metadata_missing), "agent")

    def test_discover_modern_cursor_rules_finds_nested_directories(self):
        """Test discovery of MDC files in nested subdirectories (monorepo support)."""
        from configuration_discovery import discover_modern_cursor_rules

        # Create nested directory structure
        cursor_rules_dir = os.path.join(self.project_root, ".cursor", "rules")
        backend_dir = os.path.join(cursor_rules_dir, "backend")
        frontend_dir = os.path.join(cursor_rules_dir, "frontend")
        shared_dir = os.path.join(cursor_rules_dir, "shared")

        os.makedirs(backend_dir)
        os.makedirs(frontend_dir)
        os.makedirs(shared_dir)

        # Create MDC files in nested directories
        backend_file = os.path.join(backend_dir, "001-api.mdc")
        with open(backend_file, "w") as f:
            f.write(
                """---
description: Backend API rules
globs: ["src/api/*.ts", "src/models/*.ts"]
alwaysApply: true
---

# Backend API Rules
Use Express.js patterns."""
            )

        frontend_file = os.path.join(frontend_dir, "002-react.mdc")
        with open(frontend_file, "w") as f:
            f.write(
                """---
description: React component rules
globs: ["src/components/*.tsx", "src/pages/*.tsx"]
alwaysApply: false
---

# React Rules
Use functional components."""
            )

        shared_file = os.path.join(shared_dir, "010-common.mdc")
        with open(shared_file, "w") as f:
            f.write(
                """---
description: Shared utilities
globs: ["src/utils/*.ts", "lib/*.ts"]
alwaysApply: true
---

# Shared Rules
Use TypeScript strict mode."""
            )

        result = discover_modern_cursor_rules(self.project_root)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

        # Check that all nested files were found
        file_paths = [rule["file_path"] for rule in result]
        self.assertIn(backend_file, file_paths)
        self.assertIn(frontend_file, file_paths)
        self.assertIn(shared_file, file_paths)

        # Check precedence ordering
        backend_rule = next(r for r in result if "001-api" in r["file_path"])
        frontend_rule = next(r for r in result if "002-react" in r["file_path"])
        shared_rule = next(r for r in result if "010-common" in r["file_path"])

        self.assertEqual(backend_rule["precedence"], 1)
        self.assertEqual(frontend_rule["precedence"], 2)
        self.assertEqual(shared_rule["precedence"], 10)

        # Verify rules are sorted by precedence
        precedences = [rule["precedence"] for rule in result]
        self.assertEqual(precedences, sorted(precedences))

    def test_discover_modern_cursor_rules_handles_deeply_nested_directories(self):
        """Test discovery in deeply nested directory structures."""
        from configuration_discovery import discover_modern_cursor_rules

        # Create deeply nested structure
        deep_dir = os.path.join(
            self.project_root, ".cursor", "rules", "services", "auth", "middleware"
        )
        os.makedirs(deep_dir)

        deep_file = os.path.join(deep_dir, "005-auth.mdc")
        with open(deep_file, "w") as f:
            f.write(
                """---
description: Authentication middleware rules
globs: ["src/middleware/auth*.ts"]
alwaysApply: true
---

# Auth Middleware Rules
Implement proper JWT validation."""
            )

        result = discover_modern_cursor_rules(self.project_root)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["file_path"], deep_file)
        self.assertEqual(result[0]["description"], "Authentication middleware rules")
        self.assertEqual(result[0]["precedence"], 5)

    def test_discover_modern_cursor_rules_ignores_non_mdc_files_in_subdirs(self):
        """Test that non-MDC files in subdirectories are ignored."""
        from configuration_discovery import discover_modern_cursor_rules

        # Create subdirectory with mixed file types
        subdir = os.path.join(self.project_root, ".cursor", "rules", "config")
        os.makedirs(subdir)

        # Create valid MDC file
        mdc_file = os.path.join(subdir, "001-config.mdc")
        with open(mdc_file, "w") as f:
            f.write(
                """---
description: Config rules
---

Config content"""
            )

        # Create non-MDC files that should be ignored
        txt_file = os.path.join(subdir, "readme.txt")
        with open(txt_file, "w") as f:
            f.write("This is not an MDC file")

        json_file = os.path.join(subdir, "config.json")
        with open(json_file, "w") as f:
            f.write('{"key": "value"}')

        result = discover_modern_cursor_rules(self.project_root)

        # Should only find the MDC file
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["file_path"], mdc_file)

    def test_discover_modern_cursor_rules_handles_empty_subdirectories(self):
        """Test discovery handles empty subdirectories gracefully."""
        from configuration_discovery import discover_modern_cursor_rules

        # Create empty subdirectories
        empty_dirs = [
            os.path.join(self.project_root, ".cursor", "rules", "empty1"),
            os.path.join(self.project_root, ".cursor", "rules", "empty2", "nested"),
        ]

        for empty_dir in empty_dirs:
            os.makedirs(empty_dir)

        # Create one valid file in the main rules directory
        main_file = os.path.join(self.project_root, ".cursor", "rules", "001-main.mdc")
        with open(main_file, "w") as f:
            f.write(
                """---
description: Main rule
---

Main content"""
            )

        result = discover_modern_cursor_rules(self.project_root)

        # Should find the one valid file, empty directories should not cause issues
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["file_path"], main_file)


class TestFileSystemTraversal(unittest.TestCase):
    """Test file system traversal functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name

    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()

    def test_traverse_directories_stops_at_filesystem_root(self):
        """Test that directory traversal stops at filesystem root."""
        from configuration_discovery import discover_claude_md_files

        # Create a deep directory structure
        deep_dir = os.path.join(self.project_root, "a", "b", "c", "d", "e")
        os.makedirs(deep_dir)

        # Discovery should not traverse beyond the temp directory
        result = discover_claude_md_files(deep_dir)

        # Should handle this without errors (even if no files found)
        self.assertIsInstance(result, list)

    def test_traverse_directories_handles_symlinks_safely(self):
        """Test that directory traversal handles symlinks safely."""
        from configuration_discovery import discover_claude_md_files

        # Create a subdirectory and a symlink pointing to parent (potential infinite loop)
        subdir = os.path.join(self.project_root, "subdir")
        os.makedirs(subdir)

        # Create symlink (skip on Windows)
        if os.name != "nt":
            symlink_path = os.path.join(subdir, "parent_link")
            try:
                os.symlink(self.project_root, symlink_path)

                # Discovery should handle this safely
                result = discover_claude_md_files(subdir)
                self.assertIsInstance(result, list)

            except OSError:
                # Symlink creation failed, skip test
                pass


if __name__ == "__main__":
    unittest.main()
