"""
Test-driven development tests for configuration context data models and merging.

This module tests the data models and merging logic for Claude memory files,
Cursor rules, and configuration context management with precedence handling.

Following TDD protocol: Tests written FIRST to define expected behavior.
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestConfigurationDataModels(unittest.TestCase):
    """Test configuration context data models."""

    def test_claude_memory_file_model_creation(self):
        """Test ClaudeMemoryFile data model creation and validation."""
        from configuration_context import ClaudeMemoryFile

        # Test basic model creation
        memory_file = ClaudeMemoryFile(
            file_path="/project/CLAUDE.md",
            content="# Project Memory\nUse TypeScript.",
            hierarchy_level="project",
            imports=[],
            resolved_content="# Project Memory\nUse TypeScript.",
        )

        self.assertEqual(memory_file.file_path, "/project/CLAUDE.md")
        self.assertEqual(memory_file.content, "# Project Memory\nUse TypeScript.")
        self.assertEqual(memory_file.hierarchy_level, "project")
        self.assertEqual(memory_file.imports, [])
        self.assertEqual(
            memory_file.resolved_content, "# Project Memory\nUse TypeScript."
        )

    def test_claude_memory_file_with_imports(self):
        """Test ClaudeMemoryFile with import data."""
        from configuration_context import ClaudeMemoryFile, ImportInfo

        import_info = ImportInfo(
            import_path="shared/common.md",
            resolved_path="/project/shared/common.md",
            content="# Common Guidelines\nShared standards.",
            depth=1,
        )

        memory_file = ClaudeMemoryFile(
            file_path="/project/CLAUDE.md",
            content="# Project Memory\n@shared/common.md",
            hierarchy_level="project",
            imports=[import_info],
            resolved_content="# Project Memory\n# Common Guidelines\nShared standards.",
        )

        self.assertEqual(len(memory_file.imports), 1)
        self.assertEqual(memory_file.imports[0].import_path, "shared/common.md")
        self.assertEqual(memory_file.imports[0].depth, 1)
        self.assertIn("Shared standards", memory_file.resolved_content)

    def test_cursor_rule_model_creation(self):
        """Test CursorRule data model creation and validation."""
        from configuration_context import CursorRule

        # Test legacy rule creation
        legacy_rule = CursorRule(
            file_path="/project/.cursorrules",
            content="Use TypeScript for all files.",
            rule_type="legacy",
            precedence=0,
            description="Legacy .cursorrules file",
            globs=[],
            always_apply=True,
            metadata={},
        )

        self.assertEqual(legacy_rule.file_path, "/project/.cursorrules")
        self.assertEqual(legacy_rule.rule_type, "legacy")
        self.assertEqual(legacy_rule.precedence, 0)
        self.assertTrue(legacy_rule.always_apply)

        # Test modern rule creation
        modern_rule = CursorRule(
            file_path="/project/.cursor/rules/001-typescript.mdc",
            content="# TypeScript Rules\nUse strict mode.",
            rule_type="modern",
            precedence=1,
            description="TypeScript coding standards",
            globs=["*.ts", "*.tsx"],
            always_apply=True,
            metadata={"author": "Team", "version": 1.0},
        )

        self.assertEqual(modern_rule.rule_type, "modern")
        self.assertEqual(modern_rule.precedence, 1)
        self.assertEqual(modern_rule.globs, ["*.ts", "*.tsx"])
        self.assertEqual(modern_rule.metadata["author"], "Team")

    def test_configuration_context_model_creation(self):
        """Test ConfigurationContext data model creation and validation."""
        from configuration_context import (
            ClaudeMemoryFile,
            ConfigurationContext,
            CursorRule,
        )

        # Create sample memory files
        project_memory = ClaudeMemoryFile(
            file_path="/project/CLAUDE.md",
            content="# Project Memory",
            hierarchy_level="project",
            imports=[],
            resolved_content="# Project Memory",
        )

        user_memory = ClaudeMemoryFile(
            file_path="/home/user/.claude/CLAUDE.md",
            content="# User Memory",
            hierarchy_level="user",
            imports=[],
            resolved_content="# User Memory",
        )

        # Create sample rules
        legacy_rule = CursorRule(
            file_path="/project/.cursorrules",
            content="Legacy rules",
            rule_type="legacy",
            precedence=0,
            description="Legacy rules",
            globs=[],
            always_apply=True,
            metadata={},
        )

        modern_rule = CursorRule(
            file_path="/project/.cursor/rules/001-typescript.mdc",
            content="Modern rules",
            rule_type="modern",
            precedence=1,
            description="TypeScript rules",
            globs=["*.ts"],
            always_apply=True,
            metadata={},
        )

        context = ConfigurationContext(
            claude_memory_files=[project_memory, user_memory],
            cursor_rules=[legacy_rule, modern_rule],
            merged_content="Combined configuration content",
            auto_apply_rules=[modern_rule],
            error_summary=[],
        )

        self.assertEqual(len(context.claude_memory_files), 2)
        self.assertEqual(len(context.cursor_rules), 2)
        self.assertEqual(len(context.auto_apply_rules), 1)
        self.assertEqual(context.merged_content, "Combined configuration content")
        self.assertEqual(context.error_summary, [])

    def test_import_info_model_creation(self):
        """Test ImportInfo data model creation and validation."""
        from configuration_context import ImportInfo

        import_info = ImportInfo(
            import_path="config/settings.md",
            resolved_path="/project/config/settings.md",
            content="# Configuration Settings\nProject config here.",
            depth=2,
        )

        self.assertEqual(import_info.import_path, "config/settings.md")
        self.assertEqual(import_info.resolved_path, "/project/config/settings.md")
        self.assertEqual(import_info.depth, 2)
        self.assertIn("Project config here", import_info.content)


class TestPrecedenceLogic(unittest.TestCase):
    """Test precedence logic for Claude memory files and Cursor rules."""

    def test_claude_memory_precedence_hierarchy(self):
        """Test Claude memory precedence: project > user > enterprise."""
        from configuration_context import (
            ClaudeMemoryFile,
            sort_claude_memory_by_precedence,
        )

        enterprise_memory = ClaudeMemoryFile(
            file_path="/etc/claude/CLAUDE.md",
            content="# Enterprise Memory",
            hierarchy_level="enterprise",
            imports=[],
            resolved_content="# Enterprise Memory",
        )

        user_memory = ClaudeMemoryFile(
            file_path="/home/user/.claude/CLAUDE.md",
            content="# User Memory",
            hierarchy_level="user",
            imports=[],
            resolved_content="# User Memory",
        )

        project_memory = ClaudeMemoryFile(
            file_path="/project/CLAUDE.md",
            content="# Project Memory",
            hierarchy_level="project",
            imports=[],
            resolved_content="# Project Memory",
        )

        # Test sorting (should be project, user, enterprise)
        unsorted_files = [enterprise_memory, user_memory, project_memory]
        sorted_files = sort_claude_memory_by_precedence(unsorted_files)

        self.assertEqual(len(sorted_files), 3)
        self.assertEqual(sorted_files[0].hierarchy_level, "project")
        self.assertEqual(sorted_files[1].hierarchy_level, "user")
        self.assertEqual(sorted_files[2].hierarchy_level, "enterprise")

    def test_cursor_rules_numerical_precedence(self):
        """Test Cursor rules numerical precedence sorting."""
        from configuration_context import CursorRule, sort_cursor_rules_by_precedence

        rule_100 = CursorRule(
            file_path="/project/.cursor/rules/100-deployment.mdc",
            content="Deployment rules",
            rule_type="modern",
            precedence=100,
            description="Deployment guidelines",
            globs=["*.yml"],
            always_apply=False,
            metadata={},
        )

        rule_001 = CursorRule(
            file_path="/project/.cursor/rules/001-typescript.mdc",
            content="TypeScript rules",
            rule_type="modern",
            precedence=1,
            description="TypeScript standards",
            globs=["*.ts"],
            always_apply=True,
            metadata={},
        )

        rule_050 = CursorRule(
            file_path="/project/.cursor/rules/050-testing.mdc",
            content="Testing rules",
            rule_type="modern",
            precedence=50,
            description="Testing guidelines",
            globs=["*.test.ts"],
            always_apply=False,
            metadata={},
        )

        legacy_rule = CursorRule(
            file_path="/project/.cursorrules",
            content="Legacy rules",
            rule_type="legacy",
            precedence=0,
            description="Legacy cursor rules",
            globs=[],
            always_apply=True,
            metadata={},
        )

        # Test sorting (should be legacy=0, modern=1, modern=50, modern=100)
        unsorted_rules = [rule_100, rule_001, rule_050, legacy_rule]
        sorted_rules = sort_cursor_rules_by_precedence(unsorted_rules)

        self.assertEqual(len(sorted_rules), 4)
        self.assertEqual(sorted_rules[0].precedence, 0)  # Legacy
        self.assertEqual(sorted_rules[1].precedence, 1)  # 001-typescript
        self.assertEqual(sorted_rules[2].precedence, 50)  # 050-testing
        self.assertEqual(sorted_rules[3].precedence, 100)  # 100-deployment

    def test_mixed_precedence_handling(self):
        """Test precedence handling with mixed rule types."""
        from configuration_context import CursorRule, sort_cursor_rules_by_precedence

        # Create rules with same numerical precedence but different types
        modern_rule_1 = CursorRule(
            file_path="/project/.cursor/rules/010-api.mdc",
            content="API rules",
            rule_type="modern",
            precedence=10,
            description="API guidelines",
            globs=["src/api/*.ts"],
            always_apply=True,
            metadata={},
        )

        modern_rule_999 = CursorRule(
            file_path="/project/.cursor/rules/no-number.mdc",
            content="Unnumbered rules",
            rule_type="modern",
            precedence=999,  # Default for files without numbers
            description="Unnumbered guidelines",
            globs=["*.md"],
            always_apply=False,
            metadata={},
        )

        legacy_rule = CursorRule(
            file_path="/project/.cursorrules",
            content="Legacy rules",
            rule_type="legacy",
            precedence=0,
            description="Legacy rules",
            globs=[],
            always_apply=True,
            metadata={},
        )

        unsorted_rules = [modern_rule_999, modern_rule_1, legacy_rule]
        sorted_rules = sort_cursor_rules_by_precedence(unsorted_rules)

        self.assertEqual(sorted_rules[0].precedence, 0)  # Legacy
        self.assertEqual(sorted_rules[1].precedence, 10)  # Numbered modern
        self.assertEqual(sorted_rules[2].precedence, 999)  # Unnumbered modern


class TestContentMerging(unittest.TestCase):
    """Test content merging algorithms for configuration context."""

    def test_merge_claude_memory_content(self):
        """Test merging Claude memory content with hierarchy respect."""
        from configuration_context import ClaudeMemoryFile, merge_claude_memory_content

        project_memory = ClaudeMemoryFile(
            file_path="/project/CLAUDE.md",
            content="# Project Guidelines\nUse TypeScript.",
            hierarchy_level="project",
            imports=[],
            resolved_content="# Project Guidelines\nUse TypeScript.",
        )

        user_memory = ClaudeMemoryFile(
            file_path="/home/user/.claude/CLAUDE.md",
            content="# User Preferences\nPrefer functional patterns.",
            hierarchy_level="user",
            imports=[],
            resolved_content="# User Preferences\nPrefer functional patterns.",
        )

        memory_files = [project_memory, user_memory]
        merged_content = merge_claude_memory_content(memory_files)

        self.assertIsInstance(merged_content, str)
        self.assertIn("Project Guidelines", merged_content)
        self.assertIn("User Preferences", merged_content)
        # Project should come before user in merged content
        project_index = merged_content.find("Project Guidelines")
        user_index = merged_content.find("User Preferences")
        self.assertLess(project_index, user_index)

    def test_merge_cursor_rules_content(self):
        """Test merging Cursor rules content with precedence respect."""
        from configuration_context import CursorRule, merge_cursor_rules_content

        legacy_rule = CursorRule(
            file_path="/project/.cursorrules",
            content="Legacy: Use consistent naming.",
            rule_type="legacy",
            precedence=0,
            description="Legacy rules",
            globs=[],
            always_apply=True,
            metadata={},
        )

        typescript_rule = CursorRule(
            file_path="/project/.cursor/rules/001-typescript.mdc",
            content="Modern: Use TypeScript strict mode.",
            rule_type="modern",
            precedence=1,
            description="TypeScript standards",
            globs=["*.ts"],
            always_apply=True,
            metadata={},
        )

        cursor_rules = [typescript_rule, legacy_rule]  # Unsorted
        merged_content = merge_cursor_rules_content(cursor_rules)

        self.assertIsInstance(merged_content, str)
        self.assertIn("Legacy: Use consistent naming", merged_content)
        self.assertIn("Modern: Use TypeScript strict mode", merged_content)
        # Legacy (precedence 0) should come before modern (precedence 1)
        legacy_index = merged_content.find("Legacy:")
        modern_index = merged_content.find("Modern:")
        self.assertLess(legacy_index, modern_index)

    def test_content_deduplication(self):
        """Test content deduplication in merged configurations."""
        from configuration_context import merge_with_deduplication

        content_parts = [
            "# Common Guidelines\nUse TypeScript.",
            "# Project Rules\nFollow TDD principles.",
            "# Common Guidelines\nUse TypeScript.",  # Duplicate
            "# Additional Rules\nWrite tests first.",
        ]

        merged_content = merge_with_deduplication(content_parts)

        self.assertIsInstance(merged_content, str)
        # Should contain each unique content only once
        self.assertEqual(merged_content.count("# Common Guidelines"), 1)
        self.assertEqual(merged_content.count("Use TypeScript."), 1)
        self.assertIn("Follow TDD principles", merged_content)
        self.assertIn("Write tests first", merged_content)

    def test_conflict_resolution_strategy(self):
        """Test conflict resolution when multiple rules conflict."""
        from configuration_context import resolve_content_conflicts

        conflicting_contents = [
            "# Code Style\nUse 2 spaces for indentation.",
            "# Code Style\nUse 4 spaces for indentation.",
            "# Code Style\nUse tabs for indentation.",
        ]

        # Should resolve conflicts by taking the first (highest precedence) rule
        resolved_content = resolve_content_conflicts(conflicting_contents)

        self.assertIsInstance(resolved_content, str)
        self.assertIn("Use 2 spaces for indentation", resolved_content)
        self.assertNotIn("Use 4 spaces for indentation", resolved_content)
        self.assertNotIn("Use tabs for indentation", resolved_content)


class TestSimplifiedCursorRuleHandling(unittest.TestCase):
    """Test simplified cursor rule handling (no filtering, all rules included)."""

    def test_get_all_cursor_rules(self):
        """Test getting all cursor rules (simplified approach - no filtering)."""
        from configuration_context import CursorRule, get_all_cursor_rules

        auto_rule_1 = CursorRule(
            file_path="/project/.cursor/rules/001-typescript.mdc",
            content="TypeScript rules",
            rule_type="modern",
            precedence=1,
            description="TypeScript standards",
            globs=["*.ts", "*.tsx"],
            always_apply=True,  # Auto-apply
            metadata={},
        )

        manual_rule = CursorRule(
            file_path="/project/.cursor/rules/050-docs.mdc",
            content="Documentation rules",
            rule_type="modern",
            precedence=50,
            description="Documentation guidelines",
            globs=["*.md"],
            always_apply=False,  # Manual apply
            metadata={},
        )

        auto_rule_2 = CursorRule(
            file_path="/project/.cursorrules",
            content="Legacy rules",
            rule_type="legacy",
            precedence=0,
            description="Legacy rules",
            globs=[],
            always_apply=True,  # Auto-apply (legacy always auto)
            metadata={},
        )

        all_rules = [auto_rule_1, manual_rule, auto_rule_2]
        all_rules_result = get_all_cursor_rules(all_rules)

        # Simplified approach: all rules are returned
        self.assertEqual(len(all_rules_result), 3)
        self.assertIn(auto_rule_1, all_rules_result)
        self.assertIn(auto_rule_2, all_rules_result)
        self.assertIn(
            manual_rule, all_rules_result
        )  # Now included in simplified approach

    def test_get_applicable_cursor_rules_for_files(self):
        """Test getting applicable cursor rules for files (simplified approach - no file matching)."""
        from configuration_context import (
            CursorRule,
            get_applicable_cursor_rules_for_files,
        )

        typescript_rule = CursorRule(
            file_path="/project/.cursor/rules/001-typescript.mdc",
            content="TypeScript rules",
            rule_type="modern",
            precedence=1,
            description="TypeScript standards",
            globs=["*.ts", "*.tsx"],
            always_apply=False,  # Not always apply, but should auto-attach for matching files
            metadata={},
        )

        markdown_rule = CursorRule(
            file_path="/project/.cursor/rules/050-docs.mdc",
            content="Documentation rules",
            rule_type="modern",
            precedence=50,
            description="Documentation guidelines",
            globs=["*.md", "docs/**/*.md"],
            always_apply=False,
            metadata={},
        )

        general_rule = CursorRule(
            file_path="/project/.cursorrules",
            content="General rules",
            rule_type="legacy",
            precedence=0,
            description="General coding rules",
            globs=[],  # No globs - won't auto-attach based on files
            always_apply=False,
            metadata={},
        )

        all_rules = [typescript_rule, markdown_rule, general_rule]
        changed_files = [
            "src/components/Button.tsx",
            "src/utils/helpers.ts",
            "docs/README.md",
            "package.json",
        ]

        applicable_rules = get_applicable_cursor_rules_for_files(
            all_rules, changed_files
        )

        # Simplified approach: all rules are returned regardless of file matching
        self.assertEqual(len(applicable_rules), 3)
        self.assertIn(typescript_rule, applicable_rules)
        self.assertIn(markdown_rule, applicable_rules)
        self.assertIn(
            general_rule, applicable_rules
        )  # Now included in simplified approach


class TestConfigurationContextMerger(unittest.TestCase):
    """Test complete configuration context merger functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name

    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()

    def test_create_configuration_context_from_discoveries(self):
        """Test creating ConfigurationContext from discovered files."""
        from configuration_context import (
            ClaudeMemoryFile,
            CursorRule,
            create_configuration_context,
        )

        # Sample discovered Claude memory files
        claude_files = [
            ClaudeMemoryFile(
                file_path="/project/CLAUDE.md",
                content="# Project Memory\nUse TypeScript.",
                hierarchy_level="project",
                imports=[],
                resolved_content="# Project Memory\nUse TypeScript.",
            ),
            ClaudeMemoryFile(
                file_path="/home/user/.claude/CLAUDE.md",
                content="# User Memory\nPrefer functional patterns.",
                hierarchy_level="user",
                imports=[],
                resolved_content="# User Memory\nPrefer functional patterns.",
            ),
        ]

        # Sample discovered Cursor rules
        cursor_rules = [
            CursorRule(
                file_path="/project/.cursorrules",
                content="Legacy rules content",
                rule_type="legacy",
                precedence=0,
                description="Legacy rules",
                globs=[],
                always_apply=True,
                metadata={},
            ),
            CursorRule(
                file_path="/project/.cursor/rules/001-typescript.mdc",
                content="# TypeScript Standards\nUse strict mode.",
                rule_type="modern",
                precedence=1,
                description="TypeScript guidelines",
                globs=["*.ts", "*.tsx"],
                always_apply=True,
                metadata={},
            ),
        ]

        context = create_configuration_context(claude_files, cursor_rules)

        self.assertIsInstance(context, dict)
        self.assertIn("claude_memory_files", context)
        self.assertIn("cursor_rules", context)
        self.assertIn("merged_content", context)
        self.assertIn("auto_apply_rules", context)
        self.assertIn("error_summary", context)

        # Check that content was merged properly
        merged_content = context["merged_content"]
        self.assertIn("Project Memory", merged_content)
        self.assertIn("TypeScript Standards", merged_content)

        # Check auto-apply rules filtering
        auto_rules = context["auto_apply_rules"]
        self.assertEqual(len(auto_rules), 2)  # Both rules have always_apply=True

    def test_configuration_context_with_file_matching(self):
        """Test configuration context with file-based rule matching."""
        from configuration_context import (
            CursorRule,
            create_configuration_context_for_files,
        )

        # Rules with different glob patterns
        cursor_rules = [
            CursorRule(
                file_path="/project/.cursor/rules/001-typescript.mdc",
                content="TypeScript rules content",
                rule_type="modern",
                precedence=1,
                description="TypeScript guidelines",
                globs=["*.ts", "*.tsx"],
                always_apply=False,  # Not always apply
                metadata={},
            ),
            CursorRule(
                file_path="/project/.cursor/rules/050-testing.mdc",
                content="Testing rules content",
                rule_type="modern",
                precedence=50,
                description="Testing guidelines",
                globs=["*.test.ts", "*.spec.ts"],
                always_apply=False,
                metadata={},
            ),
            CursorRule(
                file_path="/project/.cursorrules",
                content="General rules",
                rule_type="legacy",
                precedence=0,
                description="General rules",
                globs=[],
                always_apply=True,  # Always apply
                metadata={},
            ),
        ]

        changed_files = [
            "src/components/Button.tsx",  # Matches TypeScript rule
            "src/utils/helpers.test.ts",  # Matches both TypeScript and testing rules
            "docs/README.md",  # Matches no specific rules
        ]

        context = create_configuration_context_for_files(
            [], cursor_rules, changed_files
        )

        # Should include:
        # - Legacy rule (always_apply=True)
        # - TypeScript rule (matches .tsx and .test.ts files)
        # - Testing rule (matches .test.ts files)
        applicable_rules = context["applicable_rules"]
        self.assertEqual(len(applicable_rules), 3)

        # Verify rule types are included
        rule_descriptions = [rule.description for rule in applicable_rules]
        self.assertIn("General rules", rule_descriptions)
        self.assertIn("TypeScript guidelines", rule_descriptions)
        self.assertIn("Testing guidelines", rule_descriptions)

    def test_error_handling_in_context_creation(self):
        """Test error handling during configuration context creation."""
        from configuration_context import (
            ClaudeMemoryFile,
            CursorRule,
            create_configuration_context_with_error_handling,
        )

        # Valid memory file
        valid_memory = ClaudeMemoryFile(
            file_path="/project/CLAUDE.md",
            content="# Valid Memory",
            hierarchy_level="project",
            imports=[],
            resolved_content="# Valid Memory",
        )

        # Valid rule
        valid_rule = CursorRule(
            file_path="/project/.cursorrules",
            content="Valid rules",
            rule_type="legacy",
            precedence=0,
            description="Valid rules",
            globs=[],
            always_apply=True,
            metadata={},
        )

        # Simulate some errors
        import_errors = [
            {
                "import_path": "missing.md",
                "error_type": "file_not_found",
                "error_message": "File not found: missing.md",
            }
        ]

        context = create_configuration_context_with_error_handling(
            [valid_memory], [valid_rule], import_errors
        )

        self.assertIn("error_summary", context)
        self.assertEqual(len(context["error_summary"]), 1)
        self.assertIn("file_not_found", context["error_summary"][0]["error_type"])

        # Should still successfully create context with valid data
        self.assertEqual(len(context["claude_memory_files"]), 1)
        self.assertEqual(len(context["cursor_rules"]), 1)
        self.assertIn("Valid Memory", context["merged_content"])


if __name__ == "__main__":
    unittest.main()
