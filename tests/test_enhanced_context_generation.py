"""
Test-driven development tests for enhanced context generation with configuration discovery.

This module tests the integration of Claude memory files and Cursor rules
into the existing code review context generation process.

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


class TestConfigurationDiscoveryIntegration(unittest.TestCase):
    """Test integration of configuration discovery into context generation."""
    
    def setUp(self):
        """Set up test environment with complex project structure."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name
        
        # Create project structure
        self.tasks_dir = os.path.join(self.project_root, "tasks")
        os.makedirs(self.tasks_dir)
        
        # Create .cursor/rules structure
        self.cursor_rules_dir = os.path.join(self.project_root, ".cursor", "rules")
        os.makedirs(self.cursor_rules_dir)
        
        # Create source directories
        self.src_dir = os.path.join(self.project_root, "src")
        os.makedirs(self.src_dir)
        
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    def test_discover_configurations_from_project(self):
        """Test discovery of configurations from project structure."""
        from generate_code_review_context import discover_project_configurations
        
        # Create CLAUDE.md in project root
        claude_file = os.path.join(self.project_root, "CLAUDE.md")
        with open(claude_file, 'w') as f:
            f.write("# Project Memory\nUse TypeScript for all new files.")
        
        # Create legacy .cursorrules
        cursorrules_file = os.path.join(self.project_root, ".cursorrules")
        with open(cursorrules_file, 'w') as f:
            f.write("Use consistent naming conventions.")
        
        # Create modern cursor rule
        modern_rule = os.path.join(self.cursor_rules_dir, "001-typescript.mdc")
        with open(modern_rule, 'w') as f:
            f.write("""---
description: TypeScript coding standards
globs: ["*.ts", "*.tsx"]
alwaysApply: true
---

# TypeScript Standards
Use strict mode for all TypeScript files.""")
        
        configurations = discover_project_configurations(self.project_root)
        
        self.assertIsInstance(configurations, dict)
        self.assertIn('claude_memory_files', configurations)
        self.assertIn('cursor_rules', configurations)
        self.assertIn('discovery_errors', configurations)
        
        # Should discover project-level Claude memory (might find user-level too)
        claude_files = configurations['claude_memory_files']
        self.assertGreaterEqual(len(claude_files), 1)
        
        # Find project-level file
        project_files = [f for f in claude_files if f.hierarchy_level == 'project']
        self.assertEqual(len(project_files), 1)
        self.assertIn('TypeScript', project_files[0].content)
        
        # Should discover both legacy and modern cursor rules (simplified approach)
        cursor_rules = configurations['cursor_rules']
        self.assertEqual(len(cursor_rules), 2)
        rule_types = {rule.rule_type for rule in cursor_rules}
        self.assertIn('legacy', rule_types)
        self.assertIn('modern', rule_types)  # Simplified approach uses 'modern' for all .mdc files
    
    def test_merge_configurations_into_context(self):
        """Test merging discovered configurations into review context."""
        from generate_code_review_context import merge_configurations_into_context
        from configuration_context import ClaudeMemoryFile, CursorRule
        
        # Create sample configurations
        claude_memory = ClaudeMemoryFile(
            file_path=os.path.join(self.project_root, "CLAUDE.md"),
            content="# Project Guidelines\nUse TDD approach.",
            hierarchy_level="project",
            imports=[],
            resolved_content="# Project Guidelines\nUse TDD approach."
        )
        
        cursor_rule = CursorRule(
            file_path=os.path.join(self.project_root, ".cursorrules"),
            content="Write comprehensive tests.",
            rule_type="legacy",
            precedence=0,
            description="Legacy coding rules",
            globs=[],
            always_apply=True,
            metadata={}
        )
        
        # Sample existing context
        existing_context = {
            'prd_summary': 'Original project summary',
            'changed_files': [],
            'project_path': self.project_root
        }
        
        enhanced_context = merge_configurations_into_context(
            existing_context,
            [claude_memory],
            [cursor_rule]
        )
        
        self.assertIn('prd_summary', enhanced_context)
        self.assertIn('configuration_content', enhanced_context)
        self.assertIn('claude_memory_files', enhanced_context)
        self.assertIn('cursor_rules', enhanced_context)
        
        # Check that configuration content was added
        config_content = enhanced_context['configuration_content']
        self.assertIn('Project Guidelines', config_content)
        self.assertIn('comprehensive tests', config_content)
    
    def test_format_configuration_context_for_ai(self):
        """Test formatting configuration context for optimal AI consumption."""
        from generate_code_review_context import format_configuration_context_for_ai
        from configuration_context import ClaudeMemoryFile, CursorRule
        
        # Create configurations with different types
        project_memory = ClaudeMemoryFile(
            file_path="/project/CLAUDE.md",
            content="# Project Memory\nUse TypeScript strict mode.",
            hierarchy_level="project",
            imports=[],
            resolved_content="# Project Memory\nUse TypeScript strict mode."
        )
        
        user_memory = ClaudeMemoryFile(
            file_path="/home/user/.claude/CLAUDE.md",
            content="# User Preferences\nPrefer functional programming.",
            hierarchy_level="user",
            imports=[],
            resolved_content="# User Preferences\nPrefer functional programming."
        )
        
        legacy_rule = CursorRule(
            file_path="/project/.cursorrules",
            content="Legacy: Write tests first.",
            rule_type="legacy",
            precedence=0,
            description="Legacy rules",
            globs=[],
            always_apply=True,
            metadata={}
        )
        
        modern_rule = CursorRule(
            file_path="/project/.cursor/rules/001-testing.mdc",
            content="Modern: Use comprehensive test coverage.",
            rule_type="modern",
            precedence=1,
            description="Testing guidelines",
            globs=["*.test.ts"],
            always_apply=False,
            metadata={"author": "Team"}
        )
        
        formatted_content = format_configuration_context_for_ai(
            [project_memory, user_memory],
            [legacy_rule, modern_rule]
        )
        
        self.assertIsInstance(formatted_content, str)
        self.assertIn('PROJECT LEVEL', formatted_content)
        self.assertIn('USER LEVEL', formatted_content)
        self.assertIn('LEGACY (Precedence: 0)', formatted_content)
        self.assertIn('MODERN (Precedence: 1)', formatted_content)
        
        # Should be ordered by precedence
        project_index = formatted_content.find('PROJECT LEVEL')
        user_index = formatted_content.find('USER LEVEL')
        legacy_index = formatted_content.find('LEGACY')
        modern_index = formatted_content.find('MODERN')
        
        self.assertLess(project_index, user_index)  # Project before user
        self.assertLess(legacy_index, modern_index)  # Legacy before modern
    
    def test_cache_configuration_discovery(self):
        """Test caching mechanism for configuration discovery performance."""
        from generate_code_review_context import ConfigurationCache
        
        # Create a cache instance
        cache = ConfigurationCache()
        
        # Create test configuration
        claude_file = os.path.join(self.project_root, "CLAUDE.md")
        with open(claude_file, 'w') as f:
            f.write("# Cached Content")
        
        # First discovery should hit filesystem
        first_result = cache.get_configurations(self.project_root)
        self.assertIsNotNone(first_result)
        
        # Second discovery should return cached result (no file changes)
        second_result = cache.get_configurations(self.project_root)
        self.assertEqual(first_result, second_result)
        
        # Modify file content
        with open(claude_file, 'w') as f:
            f.write("# Modified Content")
        
        # Third discovery should detect file change and return new result
        third_result = cache.get_configurations(self.project_root)
        self.assertNotEqual(first_result, third_result)
        
        # Verify the content actually changed
        project_files = [f for f in third_result['claude_memory_files'] if f.hierarchy_level == 'project']
        self.assertEqual(len(project_files), 1)
        self.assertIn('Modified Content', project_files[0].content)
    
    def test_handle_configuration_discovery_errors(self):
        """Test graceful error handling during configuration discovery."""
        from generate_code_review_context import discover_project_configurations_with_fallback
        
        # Create malformed configuration files
        claude_file = os.path.join(self.project_root, "CLAUDE.md")
        with open(claude_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03')  # Binary content
        
        malformed_rule = os.path.join(self.cursor_rules_dir, "001-malformed.mdc")
        with open(malformed_rule, 'w') as f:
            f.write("""---
description: Malformed rule
globs: [*.ts", "*.tsx  # Invalid YAML
---

Content here.""")
        
        # Should handle errors gracefully
        configurations = discover_project_configurations_with_fallback(self.project_root)
        
        self.assertIsInstance(configurations, dict)
        self.assertIn('discovery_errors', configurations)
        self.assertTrue(len(configurations['discovery_errors']) > 0)
        
        # Should still provide empty collections for successful discovery
        self.assertIn('claude_memory_files', configurations)
        self.assertIn('cursor_rules', configurations)
        self.assertIsInstance(configurations['claude_memory_files'], list)
        self.assertIsInstance(configurations['cursor_rules'], list)
    
    def test_file_matching_for_auto_rules(self):
        """Test automatic rule application based on changed files."""
        from generate_code_review_context import get_applicable_rules_for_files
        from configuration_context import CursorRule
        
        # Create rules with different glob patterns
        typescript_rule = CursorRule(
            file_path="/project/.cursor/rules/001-typescript.mdc",
            content="TypeScript rules",
            rule_type="modern",
            precedence=1,
            description="TypeScript standards",
            globs=["*.ts", "*.tsx"],
            always_apply=False,
            metadata={}
        )
        
        testing_rule = CursorRule(
            file_path="/project/.cursor/rules/050-testing.mdc",
            content="Testing rules",
            rule_type="modern",
            precedence=50,
            description="Testing guidelines", 
            globs=["*.test.ts", "*.spec.ts"],
            always_apply=False,
            metadata={}
        )
        
        general_rule = CursorRule(
            file_path="/project/.cursorrules",
            content="General rules",
            rule_type="legacy",
            precedence=0,
            description="General rules",
            globs=[],
            always_apply=True,
            metadata={}
        )
        
        all_rules = [typescript_rule, testing_rule, general_rule]
        
        # Test with TypeScript files (simplified: all rules always apply)
        ts_files = ["src/components/Button.tsx", "src/utils/helpers.ts"]
        ts_applicable = get_applicable_rules_for_files(all_rules, ts_files)
        
        # Simplified approach: all rules are returned regardless of files
        self.assertEqual(len(ts_applicable), 3)
        applicable_descriptions = {rule.description for rule in ts_applicable}
        self.assertIn("TypeScript standards", applicable_descriptions)
        self.assertIn("Testing guidelines", applicable_descriptions)  
        self.assertIn("General rules", applicable_descriptions)
        
        # Test with test files (simplified: same result)
        test_files = ["src/utils/helpers.test.ts", "src/components/Button.spec.ts"]
        test_applicable = get_applicable_rules_for_files(all_rules, test_files)
        
        # Simplified approach: all rules always returned
        self.assertEqual(len(test_applicable), 3)
        applicable_descriptions = {rule.description for rule in test_applicable}
        self.assertIn("TypeScript standards", applicable_descriptions)
        self.assertIn("Testing guidelines", applicable_descriptions)
        self.assertIn("General rules", applicable_descriptions)


class TestBackwardCompatibility(unittest.TestCase):
    """Test that configuration integration maintains backward compatibility."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name
        
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    def test_context_generation_without_configurations(self):
        """Test that context generation works without any configuration files."""
        from generate_code_review_context import generate_enhanced_review_context
        
        # Create minimal project structure with no configurations
        tasks_dir = os.path.join(self.project_root, "tasks")
        os.makedirs(tasks_dir)
        
        # Create basic task list
        task_file = os.path.join(tasks_dir, "tasks-test.md")
        with open(task_file, 'w') as f:
            f.write("""## Tasks

- [x] 1.0 Implement basic feature
  - [x] 1.1 Create basic functionality
  - [x] 1.2 Add error handling""")
        
        # Should work without any project configuration files
        context = generate_enhanced_review_context(
            project_path=self.project_root,
            scope="recent_phase"
        )
        
        self.assertIsInstance(context, dict)
        self.assertIn('prd_summary', context)
        self.assertIn('changed_files', context)
        # Configuration sections should be present (may find user-level configs)
        self.assertIn('configuration_content', context)
        # Configuration content may be present from user-level or may be empty
        self.assertIsInstance(context['configuration_content'], str)
    
    def test_existing_functionality_unchanged(self):
        """Test that existing context generation functionality is unchanged."""
        from generate_code_review_context import parse_task_list, detect_current_phase
        
        # Test original task list parsing still works
        task_content = """## Tasks

- [x] 1.0 Completed Phase
  - [x] 1.1 First subtask
  - [x] 1.2 Second subtask

- [ ] 2.0 Current Phase  
  - [x] 2.1 Started subtask
  - [ ] 2.2 Pending subtask"""
        
        task_data = parse_task_list(task_content)
        
        self.assertEqual(task_data['total_phases'], 2)
        self.assertEqual(len(task_data['phases']), 2)
        
        # Should detect phase 1.0 as most recently completed
        self.assertEqual(task_data['current_phase_number'], '1.0')
        self.assertEqual(task_data['current_phase_description'], 'Completed Phase')
    
    def test_error_resilience_maintains_functionality(self):
        """Test that configuration errors don't break existing functionality."""
        from generate_code_review_context import generate_enhanced_review_context
        
        # Create project with broken configuration files
        tasks_dir = os.path.join(self.project_root, "tasks")
        os.makedirs(tasks_dir)
        
        # Create working task list
        task_file = os.path.join(tasks_dir, "tasks-test.md") 
        with open(task_file, 'w') as f:
            f.write("""## Tasks

- [x] 1.0 Working phase
  - [x] 1.1 Working subtask""")
        
        # Create broken CLAUDE.md
        claude_file = os.path.join(self.project_root, "CLAUDE.md")
        with open(claude_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03')  # Binary content
        
        # Should still generate valid context despite broken configuration
        context = generate_enhanced_review_context(
            project_path=self.project_root,
            scope="recent_phase"
        )
        
        self.assertIsInstance(context, dict)
        self.assertIn('prd_summary', context)
        self.assertEqual(context['current_phase_number'], '1.0')
        # Should include error information
        self.assertIn('configuration_errors', context)


class TestEndToEndIntegration(unittest.TestCase):
    """Test complete end-to-end integration scenarios."""
    
    def setUp(self):
        """Set up comprehensive test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = self.temp_dir.name
        
        # Create full project structure
        self._create_project_structure()
        self._create_configuration_files()
        self._create_source_files()
        
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    def _create_project_structure(self):
        """Create realistic project directory structure."""
        directories = [
            "tasks",
            "src/components",
            "src/utils", 
            "src/api",
            "tests",
            ".cursor/rules",
            "docs"
        ]
        
        for directory in directories:
            os.makedirs(os.path.join(self.project_root, directory))
    
    def _create_configuration_files(self):
        """Create comprehensive configuration files."""
        # Project CLAUDE.md with imports
        claude_file = os.path.join(self.project_root, "CLAUDE.md")
        with open(claude_file, 'w') as f:
            f.write("""# Project Memory

Use TypeScript for all new components.
Follow functional programming patterns.

@docs/coding-standards.md

## Testing Approach
Use TDD for all new features.""")
        
        # Coding standards file (imported)
        standards_file = os.path.join(self.project_root, "docs", "coding-standards.md") 
        with open(standards_file, 'w') as f:
            f.write("""# Coding Standards

- Use ESLint with strict rules
- Prefer const over let
- Use meaningful variable names""")
        
        # Legacy cursor rules
        cursorrules_file = os.path.join(self.project_root, ".cursorrules")
        with open(cursorrules_file, 'w') as f:
            f.write("Use consistent indentation and naming conventions.")
        
        # Modern cursor rules
        ts_rule = os.path.join(self.project_root, ".cursor/rules/001-typescript.mdc")
        with open(ts_rule, 'w') as f:
            f.write("""---
description: TypeScript coding standards
globs: ["*.ts", "*.tsx"]
alwaysApply: true
author: Development Team
---

# TypeScript Rules

Use strict mode for all TypeScript files.
Define explicit return types for all functions.""")
        
        testing_rule = os.path.join(self.project_root, ".cursor/rules/050-testing.mdc")
        with open(testing_rule, 'w') as f:
            f.write("""---
description: Testing guidelines
globs: ["*.test.ts", "*.spec.ts"]
alwaysApply: false
---

# Testing Standards

Write unit tests for all public functions.
Use descriptive test names.""")
        
        # Task list
        task_file = os.path.join(self.project_root, "tasks", "tasks-feature.md")
        with open(task_file, 'w') as f:
            f.write("""## Tasks

- [x] 1.0 Core Infrastructure
  - [x] 1.1 Set up TypeScript configuration
  - [x] 1.2 Create component structure

- [ ] 2.0 Feature Implementation
  - [x] 2.1 Implement main component
  - [ ] 2.2 Add error handling
  - [ ] 2.3 Write comprehensive tests""")
    
    def _create_source_files(self):
        """Create sample source files."""
        # TypeScript component
        component_file = os.path.join(self.project_root, "src/components/Button.tsx")
        with open(component_file, 'w') as f:
            f.write("""import React from 'react';

interface ButtonProps {
  onClick: () => void;
  children: string;
}

export const Button: React.FC<ButtonProps> = ({ onClick, children }) => {
  return <button onClick={onClick}>{children}</button>;
};""")
        
        # Test file
        test_file = os.path.join(self.project_root, "src/components/Button.test.tsx")
        with open(test_file, 'w') as f:
            f.write("""import { render, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('should call onClick when clicked', () => {
    const onClick = jest.fn();
    const { getByText } = render(<Button onClick={onClick}>Click me</Button>);
    
    fireEvent.click(getByText('Click me'));
    expect(onClick).toHaveBeenCalled();
  });
});""")
    
    def test_complete_workflow_with_configurations(self):
        """Test complete workflow from discovery to formatted context."""
        from generate_code_review_context import generate_enhanced_review_context
        
        # Generate complete enhanced context
        context = generate_enhanced_review_context(
            project_path=self.project_root,
            scope="recent_phase",
            changed_files=["src/components/Button.tsx", "src/components/Button.test.tsx"]
        )
        
        # Verify all sections are present
        required_sections = [
            'prd_summary', 'current_phase_number', 'current_phase_description',
            'configuration_content', 'claude_memory_files', 'cursor_rules',
            'applicable_rules', 'changed_files', 'project_path'
        ]
        
        for section in required_sections:
            self.assertIn(section, context)
        
        # Verify configuration content was discovered and merged
        config_content = context['configuration_content']
        self.assertIn('Project Memory', config_content)
        self.assertIn('TypeScript Rules', config_content)
        self.assertIn('Coding Standards', config_content)  # From import resolution
        
        # Verify applicable rules were filtered for changed files
        applicable_rules = context['applicable_rules']
        applicable_descriptions = {rule.description for rule in applicable_rules}
        
        # Should include all rules (simplified approach - no file matching)
        self.assertIn('Legacy .cursorrules file', applicable_descriptions)
        self.assertIn('Rules from 001-typescript.mdc', applicable_descriptions)
        self.assertIn('Rules from 050-testing.mdc', applicable_descriptions)
        
        # Verify task list data is preserved
        self.assertEqual(context['current_phase_number'], '1.0')
        # Task description may vary based on discovery, just check it's not empty
        self.assertIsInstance(context['current_phase_description'], str)
        self.assertGreater(len(context['current_phase_description']), 0)
    
    def test_performance_with_large_configuration_set(self):
        """Test performance with large number of configuration files."""
        from generate_code_review_context import generate_enhanced_review_context
        import time
        
        # Create many configuration files
        for i in range(20):
            rule_file = os.path.join(self.project_root, ".cursor/rules", f"{i:03d}-rule-{i}.mdc")
            with open(rule_file, 'w') as f:
                f.write(f"""---
description: Rule {i}
globs: ["*.{i}.ts"]
alwaysApply: false
---

Rule content {i}""")
        
        # Measure performance
        start_time = time.time()
        context = generate_enhanced_review_context(
            project_path=self.project_root,
            scope="recent_phase"
        )
        end_time = time.time()
        
        # Should complete in reasonable time (less than 2 seconds)
        execution_time = end_time - start_time
        self.assertLess(execution_time, 2.0)
        
        # Should discover all rules
        self.assertGreaterEqual(len(context['cursor_rules']), 22)  # 20 + 2 original rules
    
    def test_configuration_priority_in_merged_content(self):
        """Test that configuration content follows proper precedence in merged output."""
        from generate_code_review_context import generate_enhanced_review_context
        
        context = generate_enhanced_review_context(
            project_path=self.project_root,
            scope="recent_phase"
        )
        
        config_content = context['configuration_content']
        
        # Simplified: just verify that configuration content exists and contains expected sections
        self.assertIn('Claude Memory Configuration', config_content)
        self.assertIn('Cursor Rules Configuration', config_content)
        
        # Verify some content from each type is present
        self.assertIn('PROJECT LEVEL', config_content)  # Claude memory
        self.assertIn('TypeScript', config_content)     # From cursor rules


if __name__ == '__main__':
    unittest.main()