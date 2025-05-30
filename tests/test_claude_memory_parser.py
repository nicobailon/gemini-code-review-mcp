"""
Test-driven development tests for Claude memory file parser functionality.

This module tests the parsing of CLAUDE.md files with import resolution,
recursion protection, and circular reference detection.

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


class TestClaudeMemoryParser(unittest.TestCase):
    """Test CLAUDE.md file parsing functionality."""
    
    def setUp(self):
        """Set up test environment with temporary directories."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name
        
    def tearDown(self):
        """Clean up temporary directories."""
        self.temp_dir.cleanup()
    
    def test_parse_claude_md_file_extracts_content(self):
        """Test basic CLAUDE.md file parsing extracts content correctly."""
        from claude_memory_parser import parse_claude_md_file
        
        # Create test CLAUDE.md file
        claude_file = os.path.join(self.project_root, "CLAUDE.md")
        content = """# Project Claude Memory

## Guidelines
- Use TypeScript for new files
- Follow TDD principles
- Write comprehensive tests

## Code Style
Use functional programming patterns where possible.
"""
        with open(claude_file, 'w') as f:
            f.write(content)
        
        result = parse_claude_md_file(claude_file)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['file_path'], claude_file)
        self.assertEqual(result['content'], content)
        self.assertIn('imports', result)
        self.assertIn('resolved_content', result)
        self.assertEqual(result['imports'], [])  # No imports in this test
        self.assertEqual(result['resolved_content'], content)  # No imports to resolve
    
    def test_parse_claude_md_file_handles_missing_file(self):
        """Test parsing handles missing CLAUDE.md files gracefully."""
        from claude_memory_parser import parse_claude_md_file
        
        nonexistent_file = os.path.join(self.project_root, "nonexistent.md")
        
        with self.assertRaises(FileNotFoundError):
            parse_claude_md_file(nonexistent_file)
    
    def test_parse_claude_md_file_handles_binary_files(self):
        """Test parsing handles binary files gracefully."""
        from claude_memory_parser import parse_claude_md_file
        
        # Create binary file with .md extension
        binary_file = os.path.join(self.project_root, "binary.md")
        with open(binary_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\xff\xfe')  # Binary content
        
        with self.assertRaises(UnicodeDecodeError):
            parse_claude_md_file(binary_file)
    
    def test_detect_import_syntax_in_content(self):
        """Test detection of @path/to/import syntax in content."""
        from claude_memory_parser import detect_imports
        
        content = """# Main Memory

Some content here.

@path/to/shared.md

More content.

@../parent/config.md

Final content.

@~/.claude/global.md
"""
        
        imports = detect_imports(content)
        
        self.assertIsInstance(imports, list)
        self.assertEqual(len(imports), 3)
        self.assertIn("path/to/shared.md", imports)
        self.assertIn("../parent/config.md", imports)
        self.assertIn("~/.claude/global.md", imports)
    
    def test_detect_import_syntax_with_whitespace(self):
        """Test detection handles whitespace around import statements."""
        from claude_memory_parser import detect_imports
        
        content = """
        @  path/to/file1.md  
        
        @ path/to/file2.md
        
        @path/to/file3.md
        """
        
        imports = detect_imports(content)
        
        self.assertEqual(len(imports), 3)
        self.assertIn("path/to/file1.md", imports)
        self.assertIn("path/to/file2.md", imports)
        self.assertIn("path/to/file3.md", imports)
    
    def test_detect_import_syntax_ignores_false_positives(self):
        """Test detection ignores false positives like email addresses."""
        from claude_memory_parser import detect_imports
        
        content = """# Memory File

Contact: user@example.com
Email: test@domain.org

@path/to/real/import.md

Twitter: @username
"""
        
        imports = detect_imports(content)
        
        # Should only find the real import, not emails or social handles
        self.assertEqual(len(imports), 1)
        self.assertIn("path/to/real/import.md", imports)
    
    def test_resolve_relative_path_imports(self):
        """Test resolution of relative path imports."""
        from claude_memory_parser import resolve_import_path
        
        base_file = os.path.join(self.project_root, "sub", "current.md")
        
        # Test relative imports
        test_cases = [
            ("../parent.md", os.path.join(self.project_root, "parent.md")),
            ("./sibling.md", os.path.join(self.project_root, "sub", "sibling.md")),
            ("deeper/nested.md", os.path.join(self.project_root, "sub", "deeper", "nested.md")),
        ]
        
        for import_path, expected in test_cases:
            with self.subTest(import_path=import_path):
                resolved = resolve_import_path(import_path, base_file)
                self.assertEqual(resolved, expected)
    
    def test_resolve_absolute_path_imports(self):
        """Test resolution of absolute path imports."""
        from claude_memory_parser import resolve_import_path
        
        base_file = os.path.join(self.project_root, "current.md")
        
        # Test absolute imports (relative to project root)
        test_cases = [
            ("config/settings.md", os.path.join(self.project_root, "config", "settings.md")),
            ("docs/readme.md", os.path.join(self.project_root, "docs", "readme.md")),
        ]
        
        for import_path, expected in test_cases:
            with self.subTest(import_path=import_path):
                resolved = resolve_import_path(import_path, base_file, project_root=self.project_root)
                self.assertEqual(resolved, expected)
    
    def test_resolve_home_directory_imports(self):
        """Test resolution of home directory imports (~/.claude/)."""
        from claude_memory_parser import resolve_import_path
        
        base_file = os.path.join(self.project_root, "current.md")
        fake_home = "/fake/home"
        
        import_path = "~/.claude/global.md"
        expected = os.path.join(fake_home, ".claude", "global.md")
        
        resolved = resolve_import_path(import_path, base_file, user_home_override=fake_home)
        self.assertEqual(resolved, expected)
    
    def test_resolve_import_with_full_parsing(self):
        """Test full import resolution with file parsing."""
        from claude_memory_parser import resolve_imports
        
        # Create main file with imports
        main_file = os.path.join(self.project_root, "main.md")
        main_content = """# Main Memory

@shared/common.md

Main content here.

@config/settings.md
"""
        with open(main_file, 'w') as f:
            f.write(main_content)
        
        # Create imported files
        shared_dir = os.path.join(self.project_root, "shared")
        os.makedirs(shared_dir)
        shared_file = os.path.join(shared_dir, "common.md")
        with open(shared_file, 'w') as f:
            f.write("# Shared Guidelines\nUse consistent naming.")
        
        config_dir = os.path.join(self.project_root, "config")
        os.makedirs(config_dir)
        config_file = os.path.join(config_dir, "settings.md")
        with open(config_file, 'w') as f:
            f.write("# Configuration\nProject settings here.")
        
        result = resolve_imports(main_file, project_root=self.project_root)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['file_path'], main_file)
        self.assertEqual(len(result['imports']), 2)
        
        # Check import details
        imports = result['imports']
        shared_import = next(imp for imp in imports if 'common.md' in imp['resolved_path'])
        config_import = next(imp for imp in imports if 'settings.md' in imp['resolved_path'])
        
        self.assertEqual(shared_import['import_path'], 'shared/common.md')
        self.assertEqual(config_import['import_path'], 'config/settings.md')
        self.assertIn('Use consistent naming', shared_import['content'])
        self.assertIn('Project settings here', config_import['content'])


class TestImportRecursionProtection(unittest.TestCase):
    """Test recursion protection and circular reference detection."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name
        
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    def test_recursion_protection_max_5_hops(self):
        """Test that import resolution stops at maximum 5 hops."""
        from claude_memory_parser import resolve_imports_with_recursion_protection
        
        # Create chain of imports: file1 -> file2 -> file3 -> file4 -> file5 -> file6
        files = []
        for i in range(1, 7):
            file_path = os.path.join(self.project_root, f"file{i}.md")
            files.append(file_path)
            
            if i < 6:
                content = f"# File {i}\n\nContent for file {i}.\n\n@file{i+1}.md\n"
            else:
                content = f"# File {i}\n\nContent for file {i}.\n"
            
            with open(file_path, 'w') as f:
                f.write(content)
        
        result = resolve_imports_with_recursion_protection(files[0], project_root=self.project_root)
        
        # Should resolve up to 5 hops (files 1-5), but not file6
        self.assertEqual(result['max_depth_reached'], 5)
        self.assertTrue(result['recursion_limit_hit'])
        
        # Check that files 1-5 are resolved but file6 is not
        resolved_files = [imp['resolved_path'] for imp in result['all_imports']]
        self.assertIn(files[1], resolved_files)  # file2.md
        self.assertIn(files[4], resolved_files)  # file5.md
        self.assertNotIn(files[5], resolved_files)  # file6.md should not be resolved
    
    def test_circular_reference_detection(self):
        """Test detection and prevention of circular references."""
        from claude_memory_parser import resolve_imports_with_recursion_protection
        
        # Create circular imports: file1 -> file2 -> file3 -> file1
        file1 = os.path.join(self.project_root, "file1.md")
        file2 = os.path.join(self.project_root, "file2.md")
        file3 = os.path.join(self.project_root, "file3.md")
        
        with open(file1, 'w') as f:
            f.write("# File 1\n\nContent 1.\n\n@file2.md\n")
        
        with open(file2, 'w') as f:
            f.write("# File 2\n\nContent 2.\n\n@file3.md\n")
        
        with open(file3, 'w') as f:
            f.write("# File 3\n\nContent 3.\n\n@file1.md\n")
        
        result = resolve_imports_with_recursion_protection(file1, project_root=self.project_root)
        
        # Should detect circular reference
        self.assertTrue(result['circular_reference_detected'])
        self.assertIn('circular_references', result)
        
        # Should still resolve files before hitting the circular reference
        resolved_files = [imp['resolved_path'] for imp in result['all_imports']]
        self.assertIn(file2, resolved_files)
        self.assertIn(file3, resolved_files)
    
    def test_complex_import_graph_with_shared_dependencies(self):
        """Test complex import graph where multiple files import the same dependency."""
        from claude_memory_parser import resolve_imports_with_recursion_protection
        
        # Create structure:
        # main.md -> [config.md, utils.md]
        # config.md -> shared.md
        # utils.md -> shared.md (shared dependency)
        
        main_file = os.path.join(self.project_root, "main.md")
        config_file = os.path.join(self.project_root, "config.md")
        utils_file = os.path.join(self.project_root, "utils.md")
        shared_file = os.path.join(self.project_root, "shared.md")
        
        with open(main_file, 'w') as f:
            f.write("# Main\n\n@config.md\n\n@utils.md\n")
        
        with open(config_file, 'w') as f:
            f.write("# Config\n\n@shared.md\n")
        
        with open(utils_file, 'w') as f:
            f.write("# Utils\n\n@shared.md\n")
        
        with open(shared_file, 'w') as f:
            f.write("# Shared Guidelines\n\nShared content.")
        
        result = resolve_imports_with_recursion_protection(main_file, project_root=self.project_root)
        
        # Should resolve all files without issues
        self.assertFalse(result['circular_reference_detected'])
        self.assertFalse(result['recursion_limit_hit'])
        
        # Shared.md should appear only once despite being imported twice
        shared_imports = [imp for imp in result['all_imports'] if 'shared.md' in imp['resolved_path']]
        self.assertEqual(len(shared_imports), 1)  # Deduplicated
    
    def test_self_reference_detection(self):
        """Test detection of files that try to import themselves."""
        from claude_memory_parser import resolve_imports_with_recursion_protection
        
        # Create file that imports itself
        self_ref_file = os.path.join(self.project_root, "self_ref.md")
        with open(self_ref_file, 'w') as f:
            f.write("# Self Reference\n\nContent here.\n\n@self_ref.md\n")
        
        result = resolve_imports_with_recursion_protection(self_ref_file, project_root=self.project_root)
        
        # Should detect self-reference as circular reference
        self.assertTrue(result['circular_reference_detected'])
        self.assertIn('self_ref.md', str(result['circular_references']))


class TestImportErrorHandling(unittest.TestCase):
    """Test error handling for missing files and invalid imports."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name
        
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    def test_handle_missing_imported_files(self):
        """Test handling of missing imported files."""
        from claude_memory_parser import resolve_imports_with_error_handling
        
        # Create main file that imports nonexistent files
        main_file = os.path.join(self.project_root, "main.md")
        with open(main_file, 'w') as f:
            f.write("# Main\n\n@nonexistent.md\n\n@also/missing.md\n")
        
        result = resolve_imports_with_error_handling(main_file, project_root=self.project_root)
        
        self.assertIn('import_errors', result)
        self.assertEqual(len(result['import_errors']), 2)
        
        # Check error details
        errors = result['import_errors']
        self.assertTrue(any('nonexistent.md' in error['import_path'] for error in errors))
        self.assertTrue(any('missing.md' in error['import_path'] for error in errors))
        self.assertTrue(all(error['error_type'] == 'file_not_found' for error in errors))
    
    def test_handle_permission_denied_files(self):
        """Test handling of files with permission restrictions."""
        from claude_memory_parser import resolve_imports_with_error_handling
        
        # Create main file and restricted imported file
        main_file = os.path.join(self.project_root, "main.md")
        restricted_file = os.path.join(self.project_root, "restricted.md")
        
        with open(main_file, 'w') as f:
            f.write("# Main\n\n@restricted.md\n")
        
        with open(restricted_file, 'w') as f:
            f.write("# Restricted content")
        
        # Make file unreadable (skip on Windows)
        if os.name != 'nt':
            os.chmod(restricted_file, 0o000)
        
        try:
            result = resolve_imports_with_error_handling(main_file, project_root=self.project_root)
            
            if os.name != 'nt':  # Only test on Unix systems
                self.assertIn('import_errors', result)
                self.assertTrue(len(result['import_errors']) > 0)
                
                permission_errors = [e for e in result['import_errors'] if e['error_type'] == 'permission_denied']
                self.assertTrue(len(permission_errors) > 0)
        
        finally:
            # Restore permissions for cleanup
            if os.name != 'nt':
                os.chmod(restricted_file, 0o644)
    
    def test_handle_malformed_imported_files(self):
        """Test handling of malformed imported files."""
        from claude_memory_parser import resolve_imports_with_error_handling
        
        # Create main file and malformed imported file
        main_file = os.path.join(self.project_root, "main.md")
        malformed_file = os.path.join(self.project_root, "malformed.md")
        
        with open(main_file, 'w') as f:
            f.write("# Main\n\n@malformed.md\n")
        
        # Create malformed file (binary content with .md extension)
        with open(malformed_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\xff\xfe')
        
        result = resolve_imports_with_error_handling(main_file, project_root=self.project_root)
        
        self.assertIn('import_errors', result)
        self.assertTrue(len(result['import_errors']) > 0)
        
        encoding_errors = [e for e in result['import_errors'] if e['error_type'] == 'encoding_error']
        self.assertTrue(len(encoding_errors) > 0)
    
    def test_graceful_degradation_with_partial_imports(self):
        """Test that partial import resolution works even when some imports fail."""
        from claude_memory_parser import resolve_imports_with_error_handling
        
        # Create main file with mix of valid and invalid imports
        main_file = os.path.join(self.project_root, "main.md")
        valid_file = os.path.join(self.project_root, "valid.md")
        
        with open(main_file, 'w') as f:
            f.write("# Main\n\n@valid.md\n\n@nonexistent.md\n")
        
        with open(valid_file, 'w') as f:
            f.write("# Valid Content\n\nThis import should work.")
        
        result = resolve_imports_with_error_handling(main_file, project_root=self.project_root)
        
        # Should successfully resolve valid import
        self.assertEqual(len(result['successful_imports']), 1)
        self.assertIn('valid.md', result['successful_imports'][0]['resolved_path'])
        self.assertIn('This import should work', result['successful_imports'][0]['content'])
        
        # Should record error for invalid import
        self.assertEqual(len(result['import_errors']), 1)
        self.assertIn('nonexistent.md', result['import_errors'][0]['import_path'])


class TestHomeDirectoryImports(unittest.TestCase):
    """Test home directory import functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name
        
        self.home_temp_dir = tempfile.TemporaryDirectory()
        self.fake_home = self.home_temp_dir.name
        
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
        self.home_temp_dir.cleanup()
    
    def test_resolve_tilde_imports(self):
        """Test resolution of ~/ imports to user home directory."""
        from claude_memory_parser import resolve_imports_with_error_handling
        
        # Create project file with home directory import
        main_file = os.path.join(self.project_root, "main.md")
        with open(main_file, 'w') as f:
            f.write("# Main\n\n@~/.claude/global.md\n")
        
        # Create home directory structure
        claude_dir = os.path.join(self.fake_home, ".claude")
        os.makedirs(claude_dir)
        global_file = os.path.join(claude_dir, "global.md")
        with open(global_file, 'w') as f:
            f.write("# Global Configuration\n\nGlobal settings here.")
        
        result = resolve_imports_with_error_handling(
            main_file, 
            project_root=self.project_root,
            user_home_override=self.fake_home
        )
        
        self.assertEqual(len(result['successful_imports']), 1)
        global_import = result['successful_imports'][0]
        self.assertEqual(global_import['import_path'], '~/.claude/global.md')
        self.assertEqual(global_import['resolved_path'], global_file)
        self.assertIn('Global settings here', global_import['content'])
    
    def test_nested_home_directory_imports(self):
        """Test nested imports from home directory files."""
        from claude_memory_parser import resolve_imports_with_error_handling
        
        # Create project file importing from home
        main_file = os.path.join(self.project_root, "main.md")
        with open(main_file, 'w') as f:
            f.write("# Main\n\n@~/.claude/config.md\n")
        
        # Create home directory files with nested imports
        claude_dir = os.path.join(self.fake_home, ".claude")
        os.makedirs(claude_dir)
        
        config_file = os.path.join(claude_dir, "config.md")
        with open(config_file, 'w') as f:
            f.write("# Config\n\n@~/.claude/shared/common.md\n")
        
        shared_dir = os.path.join(claude_dir, "shared")
        os.makedirs(shared_dir)
        common_file = os.path.join(shared_dir, "common.md")
        with open(common_file, 'w') as f:
            f.write("# Common\n\nShared guidelines.")
        
        result = resolve_imports_with_error_handling(
            main_file,
            project_root=self.project_root,
            user_home_override=self.fake_home
        )
        
        # Should resolve both files
        self.assertEqual(len(result['successful_imports']), 2)
        
        # Check that both home directory files were resolved
        resolved_paths = [imp['resolved_path'] for imp in result['successful_imports']]
        self.assertIn(config_file, resolved_paths)
        self.assertIn(common_file, resolved_paths)


class TestIntegratedClaudeMemoryParser(unittest.TestCase):
    """Test integrated Claude memory parsing with all features."""
    
    def setUp(self):
        """Set up comprehensive test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name
        
        self.home_temp_dir = tempfile.TemporaryDirectory()
        self.fake_home = self.home_temp_dir.name
        
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
        self.home_temp_dir.cleanup()
    
    def test_full_claude_memory_parsing_pipeline(self):
        """Test complete Claude memory parsing with all features enabled."""
        from claude_memory_parser import parse_claude_memory_with_imports
        
        # Create complex project structure
        main_file = os.path.join(self.project_root, "CLAUDE.md")
        with open(main_file, 'w') as f:
            f.write("""# Project Memory

@config/typescript.md
@~/.claude/global.md

## Project Guidelines
Follow TDD principles.

@utils/testing.md
""")
        
        # Create config directory
        config_dir = os.path.join(self.project_root, "config")
        os.makedirs(config_dir)
        ts_file = os.path.join(config_dir, "typescript.md")
        with open(ts_file, 'w') as f:
            f.write("# TypeScript Rules\nUse strict mode.\n\n@../utils/common.md")
        
        # Create utils directory  
        utils_dir = os.path.join(self.project_root, "utils")
        os.makedirs(utils_dir)
        testing_file = os.path.join(utils_dir, "testing.md")
        with open(testing_file, 'w') as f:
            f.write("# Testing Guidelines\nWrite comprehensive tests.")
        
        common_file = os.path.join(utils_dir, "common.md")
        with open(common_file, 'w') as f:
            f.write("# Common Guidelines\nShared project standards.")
        
        # Create home directory structure
        claude_dir = os.path.join(self.fake_home, ".claude")
        os.makedirs(claude_dir)
        global_file = os.path.join(claude_dir, "global.md")
        with open(global_file, 'w') as f:
            f.write("# Global Configuration\nEnterprise standards.")
        
        result = parse_claude_memory_with_imports(
            main_file,
            project_root=self.project_root,
            user_home_override=self.fake_home
        )
        
        # Should successfully resolve all imports
        self.assertEqual(len(result['successful_imports']), 4)
        self.assertEqual(len(result['import_errors']), 0)
        self.assertFalse(result['circular_reference_detected'])
        self.assertFalse(result['recursion_limit_hit'])
        
        # Check resolved content contains all imports
        resolved_content = result['resolved_content']
        self.assertIn('Use strict mode', resolved_content)
        self.assertIn('Enterprise standards', resolved_content)
        self.assertIn('Write comprehensive tests', resolved_content)
        self.assertIn('Shared project standards', resolved_content)
        
        # Verify import hierarchy is tracked
        import_graph = result['import_graph']
        self.assertIn(main_file, import_graph)
        self.assertIn(ts_file, import_graph[main_file])
        self.assertIn(global_file, import_graph[main_file])


if __name__ == '__main__':
    unittest.main()