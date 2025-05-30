"""
Test-driven development tests for Cursor rules parser functionality.

This module tests the parsing of both legacy .cursorrules files and modern
.cursor/rules/*.mdc files with metadata extraction and precedence handling.

Following TDD protocol: Tests written FIRST to define expected behavior.
"""

import os
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestLegacyCursorRulesParser(unittest.TestCase):
    """Test legacy .cursorrules file parsing functionality."""
    
    def setUp(self):
        """Set up test environment with temporary directories."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name
        
    def tearDown(self):
        """Clean up temporary directories."""
        self.temp_dir.cleanup()
    
    def test_parse_legacy_cursorrules_file_extracts_content(self):
        """Test basic .cursorrules file parsing extracts content correctly."""
        from cursor_rules_parser import parse_legacy_cursorrules
        
        # Create test .cursorrules file
        cursorrules_file = os.path.join(self.project_root, ".cursorrules")
        content = """Use TypeScript for all new files.
Follow functional programming patterns.
Write comprehensive tests for all functions.
Use consistent naming conventions.
"""
        with open(cursorrules_file, 'w') as f:
            f.write(content)
        
        result = parse_legacy_cursorrules(cursorrules_file)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['file_path'], cursorrules_file)
        self.assertEqual(result['type'], 'legacy')
        self.assertEqual(result['content'], content)
        self.assertEqual(result['description'], 'Legacy .cursorrules file')
        self.assertEqual(result['precedence'], 0)  # Highest precedence
        self.assertEqual(result['globs'], [])  # No glob patterns
        self.assertEqual(result['always_apply'], True)  # Legacy rules always apply
    
    def test_parse_legacy_cursorrules_handles_missing_file(self):
        """Test parsing handles missing .cursorrules files gracefully."""
        from cursor_rules_parser import parse_legacy_cursorrules
        
        nonexistent_file = os.path.join(self.project_root, ".cursorrules")
        
        with self.assertRaises(FileNotFoundError):
            parse_legacy_cursorrules(nonexistent_file)
    
    def test_parse_legacy_cursorrules_handles_empty_file(self):
        """Test parsing handles empty .cursorrules files."""
        from cursor_rules_parser import parse_legacy_cursorrules
        
        cursorrules_file = os.path.join(self.project_root, ".cursorrules")
        with open(cursorrules_file, 'w') as f:
            f.write("")
        
        result = parse_legacy_cursorrules(cursorrules_file)
        
        self.assertEqual(result['content'], "")
        self.assertEqual(result['type'], 'legacy')
    
    def test_parse_legacy_cursorrules_handles_multiline_content(self):
        """Test parsing handles multiline content with various formatting."""
        from cursor_rules_parser import parse_legacy_cursorrules
        
        cursorrules_file = os.path.join(self.project_root, ".cursorrules")
        content = """# Project Coding Standards

## TypeScript Rules
- Use strict mode
- Define explicit return types
- Prefer const over let

## Testing Guidelines
1. Write unit tests for all functions
2. Use descriptive test names
3. Test edge cases

## Code Style
Follow Prettier configuration.
Use ESLint rules consistently.
"""
        with open(cursorrules_file, 'w') as f:
            f.write(content)
        
        result = parse_legacy_cursorrules(cursorrules_file)
        
        self.assertEqual(result['content'], content)
        self.assertIn('TypeScript Rules', result['content'])
        self.assertIn('Testing Guidelines', result['content'])
        self.assertIn('Code Style', result['content'])


class TestModernMDCParser(unittest.TestCase):
    """Test modern .mdc file parsing functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name
        
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    def test_parse_mdc_file_with_frontmatter(self):
        """Test parsing MDC file with YAML frontmatter."""
        from cursor_rules_parser import parse_mdc_file
        
        mdc_file = os.path.join(self.project_root, "001-typescript.mdc")
        content = """---
description: TypeScript coding standards
globs: ["*.ts", "*.tsx"]
alwaysApply: true
author: Development Team
version: 1.2
---

# TypeScript Rules

Use TypeScript for all new files.
Always define explicit return types.
Use strict mode configuration.

## Best Practices
- Prefer interfaces over types for object shapes
- Use proper error handling with try-catch
- Document complex functions with JSDoc
"""
        with open(mdc_file, 'w') as f:
            f.write(content)
        
        result = parse_mdc_file(mdc_file)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['file_path'], mdc_file)
        self.assertEqual(result['type'], 'modern')
        self.assertEqual(result['description'], 'TypeScript coding standards')
        self.assertEqual(result['globs'], ["*.ts", "*.tsx"])
        self.assertEqual(result['always_apply'], True)
        self.assertEqual(result['precedence'], 1)  # From filename 001-
        self.assertIn('Use TypeScript for all new files', result['content'])
        self.assertIn('Best Practices', result['content'])
        
        # Check metadata extraction
        self.assertIn('metadata', result)
        self.assertEqual(result['metadata']['author'], 'Development Team')
        self.assertEqual(result['metadata']['version'], 1.2)
    
    def test_parse_mdc_file_without_frontmatter(self):
        """Test parsing MDC file without YAML frontmatter."""
        from cursor_rules_parser import parse_mdc_file
        
        mdc_file = os.path.join(self.project_root, "plain.mdc")
        content = """# Plain Content

This is a rule file without frontmatter.
It should still be parsed correctly.
"""
        with open(mdc_file, 'w') as f:
            f.write(content)
        
        result = parse_mdc_file(mdc_file)
        
        self.assertEqual(result['content'], content)
        self.assertEqual(result['description'], '')  # No description without frontmatter
        self.assertEqual(result['globs'], [])
        self.assertEqual(result['always_apply'], False)  # Default to false
        self.assertEqual(result['precedence'], 999)  # Default precedence for no number
        self.assertEqual(result['metadata'], {})
    
    def test_parse_mdc_file_with_malformed_frontmatter(self):
        """Test parsing MDC file with malformed YAML frontmatter."""
        from cursor_rules_parser import parse_mdc_file
        
        mdc_file = os.path.join(self.project_root, "malformed.mdc")
        content = """---
description: Test rule
globs: [*.ts", "*.tsx  # Malformed YAML
alwaysApply: true
---

# Content

Valid content here.
"""
        with open(mdc_file, 'w') as f:
            f.write(content)
        
        result = parse_mdc_file(mdc_file)
        
        # Should handle malformed YAML gracefully
        self.assertEqual(result['description'], '')  # Failed to parse
        self.assertEqual(result['globs'], [])
        self.assertEqual(result['content'], '# Content\n\nValid content here.\n')


class TestGlobPatternMatching(unittest.TestCase):
    """Test glob pattern matching and validation."""
    
    def test_validate_glob_patterns(self):
        """Test validation of glob patterns."""
        from cursor_rules_parser import validate_glob_patterns
        
        valid_patterns = ["*.ts", "*.tsx", "src/**/*.js", "tests/*.test.ts"]
        invalid_patterns = ["", "   ", "invalid[pattern", "**/"]
        
        for pattern in valid_patterns:
            with self.subTest(pattern=pattern):
                self.assertTrue(validate_glob_patterns([pattern]))
        
        self.assertFalse(validate_glob_patterns(invalid_patterns))
    
    def test_match_files_against_globs(self):
        """Test matching files against glob patterns."""
        from cursor_rules_parser import match_files_against_globs
        
        globs = ["*.ts", "*.tsx", "src/**/*.js"]
        test_files = [
            "component.tsx",
            "utils.ts", 
            "config.js",
            "src/api/client.js",
            "src/components/Button.tsx",
            "test.py",
            "README.md"
        ]
        
        matches = match_files_against_globs(test_files, globs)
        
        expected_matches = [
            "component.tsx",
            "utils.ts",
            "src/api/client.js",
            "src/components/Button.tsx"
        ]
        
        self.assertEqual(set(matches), set(expected_matches))
    
    def test_match_files_with_directory_patterns(self):
        """Test matching files with directory-specific patterns."""
        from cursor_rules_parser import match_files_against_globs
        
        globs = ["tests/**/*.test.ts", "src/components/*.tsx", "docs/*.md"]
        test_files = [
            "tests/unit/parser.test.ts",
            "tests/integration/api.test.ts",
            "src/components/Button.tsx",
            "src/utils/helpers.ts",
            "docs/README.md",
            "docs/API.md",
            "other/file.md"
        ]
        
        matches = match_files_against_globs(test_files, globs)
        
        expected_matches = [
            "tests/unit/parser.test.ts",
            "tests/integration/api.test.ts",
            "src/components/Button.tsx",
            "docs/README.md",
            "docs/API.md"
        ]
        
        self.assertEqual(set(matches), set(expected_matches))


class TestPrecedenceExtraction(unittest.TestCase):
    """Test numerical precedence extraction from filenames."""
    
    def test_extract_precedence_from_numbered_files(self):
        """Test precedence extraction from numbered filenames."""
        from cursor_rules_parser import extract_precedence_from_filename
        
        test_cases = [
            ("001-typescript.mdc", 1),
            ("050-testing.mdc", 50),
            ("100-deployment.mdc", 100),
            ("005-style.mdc", 5),
            ("000-base.mdc", 0),
        ]
        
        for filename, expected_precedence in test_cases:
            with self.subTest(filename=filename):
                precedence = extract_precedence_from_filename(filename)
                self.assertEqual(precedence, expected_precedence)
    
    def test_extract_precedence_from_unnumbered_files(self):
        """Test precedence extraction from files without numbers."""
        from cursor_rules_parser import extract_precedence_from_filename
        
        test_cases = [
            ("typescript.mdc", 999),
            ("general-rules.mdc", 999),
            ("README.mdc", 999),
            ("config.mdc", 999),
        ]
        
        for filename, expected_precedence in test_cases:
            with self.subTest(filename=filename):
                precedence = extract_precedence_from_filename(filename)
                self.assertEqual(precedence, expected_precedence)
    
    def test_extract_precedence_with_path(self):
        """Test precedence extraction from full file paths."""
        from cursor_rules_parser import extract_precedence_from_filename
        
        test_cases = [
            ("/project/.cursor/rules/010-api.mdc", 10),
            ("C:\\project\\.cursor\\rules\\025-database.mdc", 25),
            ("./rules/nested/075-security.mdc", 75),
        ]
        
        for filepath, expected_precedence in test_cases:
            with self.subTest(filepath=filepath):
                precedence = extract_precedence_from_filename(filepath)
                self.assertEqual(precedence, expected_precedence)


class TestFileReferenceDetection(unittest.TestCase):
    """Test @filename.ts reference detection and resolution."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name
        
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    def test_detect_file_references_in_content(self):
        """Test detection of @filename.ts references in rule content."""
        from cursor_rules_parser import detect_file_references
        
        content = """# Component Rules

When working with @Button.tsx, ensure proper prop validation.
For @api/client.ts, use proper error handling.
Check @utils/helpers.js for utility functions.

Regular @mentions should be ignored.
Email addresses like user@example.com should be ignored.
"""
        
        references = detect_file_references(content)
        
        expected_references = ["Button.tsx", "api/client.ts", "utils/helpers.js"]
        self.assertEqual(set(references), set(expected_references))
    
    def test_resolve_file_references_to_paths(self):
        """Test resolution of file references to actual file paths."""
        from cursor_rules_parser import resolve_file_references
        
        # Create test files
        test_files = [
            "src/components/Button.tsx",
            "src/api/client.ts", 
            "src/utils/helpers.js",
            "src/pages/Home.tsx"
        ]
        
        for file_path in test_files:
            full_path = os.path.join(self.project_root, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(f"// {file_path}")
        
        references = ["Button.tsx", "api/client.ts", "NonExistent.ts"]
        
        resolved = resolve_file_references(references, self.project_root)
        
        self.assertIsInstance(resolved, dict)
        self.assertIn("Button.tsx", resolved)
        self.assertIn("api/client.ts", resolved)
        self.assertNotIn("NonExistent.ts", resolved)
        
        # Check resolved paths
        self.assertEqual(resolved["Button.tsx"], os.path.join(self.project_root, "src/components/Button.tsx"))
        self.assertEqual(resolved["api/client.ts"], os.path.join(self.project_root, "src/api/client.ts"))


class TestRuleTypeClassification(unittest.TestCase):
    """Test rule type classification based on metadata."""
    
    def test_classify_rule_type_from_metadata(self):
        """Test classification of rule types based on metadata."""
        from cursor_rules_parser import classify_rule_type
        
        test_cases = [
            ({"alwaysApply": True}, "auto"),
            ({"alwaysApply": False}, "agent"),
            ({"alwaysApply": True, "globs": ["*.ts"]}, "auto"),
            ({}, "agent"),  # Default when no alwaysApply
            ({"description": "Test rule"}, "agent"),  # No alwaysApply field
        ]
        
        for metadata, expected_type in test_cases:
            with self.subTest(metadata=metadata):
                rule_type = classify_rule_type(metadata)
                self.assertEqual(rule_type, expected_type)
    
    def test_classify_rule_type_with_manual_override(self):
        """Test classification with manual type override."""
        from cursor_rules_parser import classify_rule_type
        
        # Test manual override in metadata
        metadata_manual = {"alwaysApply": True, "type": "manual"}
        rule_type = classify_rule_type(metadata_manual)
        self.assertEqual(rule_type, "manual")
        
        # Test agent override
        metadata_agent = {"alwaysApply": True, "type": "agent"}
        rule_type = classify_rule_type(metadata_agent)
        self.assertEqual(rule_type, "agent")


class TestIntegratedCursorRulesParser(unittest.TestCase):
    """Test integrated Cursor rules parsing with all features."""
    
    def setUp(self):
        """Set up comprehensive test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name
        
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    def test_parse_cursor_rules_directory_structure(self):
        """Test parsing complete Cursor rules directory structure."""
        from cursor_rules_parser import parse_cursor_rules_directory
        
        # Create .cursor/rules directory structure
        cursor_rules_dir = os.path.join(self.project_root, ".cursor", "rules")
        os.makedirs(cursor_rules_dir)
        
        # Create legacy .cursorrules
        legacy_file = os.path.join(self.project_root, ".cursorrules")
        with open(legacy_file, 'w') as f:
            f.write("Legacy cursor rules content.")
        
        # Create modern MDC files
        mdc_files = [
            ("001-typescript.mdc", """---
description: TypeScript standards
globs: ["*.ts", "*.tsx"]
alwaysApply: true
---

# TypeScript Rules
Use strict mode."""),
            ("050-testing.mdc", """---
description: Testing guidelines
globs: ["*.test.ts", "*.spec.ts"]
alwaysApply: false
---

# Testing Rules
Write comprehensive tests."""),
        ]
        
        for filename, content in mdc_files:
            file_path = os.path.join(cursor_rules_dir, filename)
            with open(file_path, 'w') as f:
                f.write(content)
        
        result = parse_cursor_rules_directory(self.project_root)
        
        self.assertIsInstance(result, dict)
        self.assertIn('legacy_rules', result)
        self.assertIn('modern_rules', result)
        
        # Check legacy rules
        legacy_rules = result['legacy_rules']
        self.assertIsNotNone(legacy_rules)
        self.assertEqual(legacy_rules['type'], 'legacy')
        self.assertEqual(legacy_rules['precedence'], 0)
        
        # Check modern rules
        modern_rules = result['modern_rules']
        self.assertEqual(len(modern_rules), 2)
        
        # Verify sorting by precedence
        precedences = [rule['precedence'] for rule in modern_rules]
        self.assertEqual(precedences, sorted(precedences))
        
        # Check specific rule details
        ts_rule = next(rule for rule in modern_rules if 'typescript' in rule['file_path'])
        self.assertEqual(ts_rule['description'], 'TypeScript standards')
        self.assertEqual(ts_rule['precedence'], 1)
        self.assertEqual(ts_rule['type'], 'auto')  # alwaysApply: true
        
        testing_rule = next(rule for rule in modern_rules if 'testing' in rule['file_path'])
        self.assertEqual(testing_rule['description'], 'Testing guidelines')
        self.assertEqual(testing_rule['precedence'], 50)
        self.assertEqual(testing_rule['type'], 'agent')  # alwaysApply: false
    
    def test_parse_nested_cursor_rules_directories(self):
        """Test parsing nested .cursor/rules directories (monorepo support)."""
        from cursor_rules_parser import parse_cursor_rules_directory
        
        # Create nested directory structure
        nested_dirs = [
            ".cursor/rules/backend",
            ".cursor/rules/frontend", 
            ".cursor/rules/shared"
        ]
        
        for nested_dir in nested_dirs:
            full_dir = os.path.join(self.project_root, nested_dir)
            os.makedirs(full_dir)
            
            # Create rule file in each directory
            rule_name = os.path.basename(nested_dir)
            rule_file = os.path.join(full_dir, f"010-{rule_name}.mdc")
            with open(rule_file, 'w') as f:
                f.write(f"""---
description: {rule_name.title()} specific rules
globs: ["{rule_name}/**/*.ts"]
alwaysApply: true
---

# {rule_name.title()} Rules
Specific guidelines for {rule_name}.""")
        
        result = parse_cursor_rules_directory(self.project_root)
        
        modern_rules = result['modern_rules']
        self.assertEqual(len(modern_rules), 3)
        
        # Check that all nested rules were found
        rule_descriptions = [rule['description'] for rule in modern_rules]
        self.assertIn('Backend specific rules', rule_descriptions)
        self.assertIn('Frontend specific rules', rule_descriptions)
        self.assertIn('Shared specific rules', rule_descriptions)
    
    def test_parse_cursor_rules_with_file_references(self):
        """Test parsing rules with @filename.ts references."""
        from cursor_rules_parser import parse_cursor_rules_directory
        
        # Create source files to reference
        src_files = [
            "src/components/Button.tsx",
            "src/api/client.ts",
            "src/utils/helpers.js"
        ]
        
        for src_file in src_files:
            full_path = os.path.join(self.project_root, src_file)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(f"// {src_file}")
        
        # Create rule with file references
        cursor_rules_dir = os.path.join(self.project_root, ".cursor", "rules")
        os.makedirs(cursor_rules_dir)
        
        rule_file = os.path.join(cursor_rules_dir, "020-references.mdc")
        with open(rule_file, 'w') as f:
            f.write("""---
description: Rules with file references
globs: ["src/**/*.ts", "src/**/*.tsx"]
alwaysApply: false
---

# Component Rules

When working with @Button.tsx, ensure proper prop validation.
For @api/client.ts, use comprehensive error handling.
Refer to @utils/helpers.js for shared utilities.
""")
        
        result = parse_cursor_rules_directory(self.project_root)
        
        modern_rules = result['modern_rules']
        rule_with_refs = modern_rules[0]
        
        self.assertIn('file_references', rule_with_refs)
        self.assertIsInstance(rule_with_refs['file_references'], dict)
        
        # Check that file references were resolved
        file_refs = rule_with_refs['file_references']
        self.assertIn('Button.tsx', file_refs)
        self.assertIn('api/client.ts', file_refs)
        self.assertIn('utils/helpers.js', file_refs)
        
        # Verify resolved paths
        self.assertTrue(file_refs['Button.tsx'].endswith('src/components/Button.tsx'))
        self.assertTrue(file_refs['api/client.ts'].endswith('src/api/client.ts'))


class TestCursorRulesErrorHandling(unittest.TestCase):
    """Test error handling in Cursor rules parsing."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name
        
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    def test_handle_missing_cursor_directory(self):
        """Test handling when .cursor directory doesn't exist."""
        from cursor_rules_parser import parse_cursor_rules_directory
        
        result = parse_cursor_rules_directory(self.project_root)
        
        self.assertEqual(result['legacy_rules'], None)
        self.assertEqual(result['modern_rules'], [])
    
    def test_handle_malformed_mdc_files(self):
        """Test handling of malformed MDC files."""
        from cursor_rules_parser import parse_cursor_rules_directory
        
        cursor_rules_dir = os.path.join(self.project_root, ".cursor", "rules")
        os.makedirs(cursor_rules_dir)
        
        # Create valid MDC file
        valid_file = os.path.join(cursor_rules_dir, "001-valid.mdc")
        with open(valid_file, 'w') as f:
            f.write("""---
description: Valid rule
---

Valid content""")
        
        # Create malformed MDC file (no description)
        malformed_file = os.path.join(cursor_rules_dir, "002-malformed.mdc")
        with open(malformed_file, 'w') as f:
            f.write("""---
globs: ["*.ts"]
---

Content without description""")
        
        # Create binary file with .mdc extension
        binary_file = os.path.join(cursor_rules_dir, "003-binary.mdc")
        with open(binary_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03')
        
        result = parse_cursor_rules_directory(self.project_root)
        
        # Should only find the valid file
        modern_rules = result['modern_rules']
        self.assertEqual(len(modern_rules), 1)
        self.assertEqual(modern_rules[0]['description'], 'Valid rule')
    
    def test_handle_permission_errors(self):
        """Test handling of permission errors."""
        from cursor_rules_parser import parse_cursor_rules_directory
        
        cursor_rules_dir = os.path.join(self.project_root, ".cursor", "rules")
        os.makedirs(cursor_rules_dir)
        
        # Create file and make it unreadable (skip on Windows)
        restricted_file = os.path.join(cursor_rules_dir, "001-restricted.mdc")
        with open(restricted_file, 'w') as f:
            f.write("""---
description: Restricted rule
---

Content""")
        
        if os.name != 'nt':
            os.chmod(restricted_file, 0o000)
        
        try:
            result = parse_cursor_rules_directory(self.project_root)
            
            # Should handle gracefully and return empty results
            if os.name != 'nt':
                self.assertEqual(len(result['modern_rules']), 0)
        
        finally:
            # Restore permissions for cleanup
            if os.name != 'nt':
                os.chmod(restricted_file, 0o644)


if __name__ == '__main__':
    unittest.main()