"""
Tests for CLI argument parsing and validation for auto-prompt generation features.
Following TDD Protocol: Writing tests FIRST before any implementation.
"""

import pytest
import argparse
import sys
import os
from unittest.mock import Mock, patch
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def setup_import_path():
    """Fixture to ensure src module can be imported in tests."""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)


class TestCLIArgumentParsing:
    """Test CLI argument parsing for auto-prompt generation features."""
    
    def test_argument_parser_creation_function_exists(self):
        """Test that create_argument_parser function exists and returns ArgumentParser."""
        try:
            from src.generate_code_review_context import create_argument_parser
            parser = create_argument_parser()
            assert isinstance(parser, argparse.ArgumentParser)
            
        except ImportError as e:
            pytest.skip(f"create_argument_parser function not found - {e}")
    
    def test_all_expected_arguments_exist(self):
        """Test that all required CLI arguments exist in the parser."""
        try:
            from src.generate_code_review_context import create_argument_parser
            parser = create_argument_parser()
            
            # Get all argument names
            arg_names = set()
            for action in parser._actions:
                arg_names.update(action.option_strings)
                if action.dest != 'help':
                    arg_names.add(action.dest)
            
            # Check new auto-prompt arguments exist
            assert '--auto-prompt' in arg_names
            assert '--generate-prompt-only' in arg_names
            assert 'auto_prompt' in arg_names
            assert 'generate_prompt_only' in arg_names
            
            # Check existing arguments still exist (backward compatibility)
            assert '--context-only' in arg_names
            assert '--temperature' in arg_names
            assert '--scope' in arg_names
            assert 'project_path' in arg_names
            
        except ImportError:
            pytest.skip("create_argument_parser function not found - implementation pending")
    
    def test_auto_prompt_argument_properties(self):
        """Test specific properties of --auto-prompt argument."""
        try:
            from src.generate_code_review_context import create_argument_parser
            parser = create_argument_parser()
            
            # Find the auto-prompt action
            auto_prompt_action = None
            for action in parser._actions:
                if '--auto-prompt' in action.option_strings:
                    auto_prompt_action = action
                    break
            
            assert auto_prompt_action is not None
            assert auto_prompt_action.dest == 'auto_prompt'
            assert auto_prompt_action.default is False
            assert isinstance(auto_prompt_action, argparse._StoreTrueAction)
            assert auto_prompt_action.help is not None
            assert len(auto_prompt_action.help) > 10  # Should have meaningful help text
            
        except ImportError:
            pytest.skip("create_argument_parser function not found - implementation pending")
    
    def test_generate_prompt_only_argument_properties(self):
        """Test specific properties of --generate-prompt-only argument."""
        try:
            from src.generate_code_review_context import create_argument_parser
            parser = create_argument_parser()
            
            # Find the generate-prompt-only action
            prompt_only_action = None
            for action in parser._actions:
                if '--generate-prompt-only' in action.option_strings:
                    prompt_only_action = action
                    break
            
            assert prompt_only_action is not None
            assert prompt_only_action.dest == 'generate_prompt_only'
            assert prompt_only_action.default is False
            assert isinstance(prompt_only_action, argparse._StoreTrueAction)
            assert prompt_only_action.help is not None
            assert len(prompt_only_action.help) > 10  # Should have meaningful help text
            
        except ImportError:
            pytest.skip("create_argument_parser function not found - implementation pending")
    
    def test_argument_parsing_combinations(self):
        """Test various combinations of CLI arguments."""
        try:
            from src.generate_code_review_context import create_argument_parser
            parser = create_argument_parser()
            
            # Test basic auto-prompt usage
            args1 = parser.parse_args(['--auto-prompt', '.'])
            assert args1.auto_prompt is True
            assert args1.generate_prompt_only is False
            assert args1.project_path == '.'
            
            # Test basic generate-prompt-only usage
            args2 = parser.parse_args(['--generate-prompt-only', '/path/to/project'])
            assert args2.auto_prompt is False
            assert args2.generate_prompt_only is True
            assert args2.project_path == '/path/to/project'
            
            # Test with additional arguments
            args3 = parser.parse_args(['--auto-prompt', '--temperature', '0.3', '--scope', 'full_project', '.'])
            assert args3.auto_prompt is True
            assert args3.temperature == 0.3
            assert args3.scope == 'full_project'
            
            # Test that both flags can be parsed (validation happens later)
            args4 = parser.parse_args(['--auto-prompt', '--generate-prompt-only', '.'])
            assert args4.auto_prompt is True
            assert args4.generate_prompt_only is True
            
        except ImportError:
            pytest.skip("create_argument_parser function not found - implementation pending")
    
    def test_help_text_content(self):
        """Test that help text contains appropriate content and examples."""
        try:
            from src.generate_code_review_context import create_argument_parser
            parser = create_argument_parser()
            
            # Get help text
            help_text = parser.format_help()
            
            # Check that new flags appear in help
            assert '--auto-prompt' in help_text
            assert '--generate-prompt-only' in help_text
            
            # Check that help text mentions key concepts
            assert 'prompt' in help_text.lower()
            assert 'generate' in help_text.lower()
            
            # Check that existing help content is preserved
            assert '--context-only' in help_text
            assert '--temperature' in help_text
            assert 'project_path' in help_text
            
        except ImportError:
            pytest.skip("create_argument_parser function not found - implementation pending")


class TestCLIArgumentValidation:
    """Test CLI argument validation for auto-prompt features."""
    
    def test_validate_cli_arguments_function_exists(self):
        """Test that validate_cli_arguments function exists."""
        try:
            from src.generate_code_review_context import validate_cli_arguments
            assert callable(validate_cli_arguments)
            
        except ImportError:
            pytest.skip("validate_cli_arguments function not found - implementation pending")
    
    def test_mutually_exclusive_flags_validation(self):
        """Test validation of mutually exclusive flag combinations."""
        try:
            from src.generate_code_review_context import create_argument_parser, validate_cli_arguments
            parser = create_argument_parser()
            
            # Test that auto-prompt and generate-prompt-only are mutually exclusive
            args_invalid = parser.parse_args(['--auto-prompt', '--generate-prompt-only', '.'])
            
            with pytest.raises(ValueError) as exc_info:
                validate_cli_arguments(args_invalid)
            
            error_message = str(exc_info.value).lower()
            assert 'mutually exclusive' in error_message or 'cannot be used together' in error_message
            assert 'auto-prompt' in error_message
            assert 'generate-prompt-only' in error_message
            
        except ImportError:
            pytest.skip("CLI validation functions not found - implementation pending")
    
    def test_context_only_conflicts_validation(self):
        """Test validation of conflicts with --context-only flag."""
        try:
            from src.generate_code_review_context import create_argument_parser, validate_cli_arguments
            parser = create_argument_parser()
            
            # Test that generate-prompt-only conflicts with context-only
            args_invalid = parser.parse_args(['--generate-prompt-only', '--context-only', '.'])
            
            with pytest.raises(ValueError) as exc_info:
                validate_cli_arguments(args_invalid)
            
            error_message = str(exc_info.value).lower()
            assert 'mutually exclusive' in error_message or 'cannot be used together' in error_message
            assert 'generate-prompt-only' in error_message
            assert 'context-only' in error_message
            
        except ImportError:
            pytest.skip("CLI validation functions not found - implementation pending")
    
    def test_valid_argument_combinations_pass_validation(self):
        """Test that valid argument combinations pass validation."""
        try:
            from src.generate_code_review_context import create_argument_parser, validate_cli_arguments
            parser = create_argument_parser()
            
            # Test valid combinations
            valid_combinations = [
                ['--auto-prompt', '.'],
                ['--generate-prompt-only', '.'],
                ['--context-only', '.'],
                ['--auto-prompt', '--temperature', '0.5', '.'],
                ['--generate-prompt-only', '--scope', 'full_project', '.'],
                ['.'],  # No flags (default behavior)
            ]
            
            for args_list in valid_combinations:
                args = parser.parse_args(args_list)
                # Should not raise an exception
                validate_cli_arguments(args)
            
        except ImportError:
            pytest.skip("CLI validation functions not found - implementation pending")
    
    def test_project_path_validation(self):
        """Test project path validation with auto-prompt flags."""
        try:
            from src.generate_code_review_context import validate_cli_arguments
            
            # Mock args object for testing
            class MockArgs:
                def __init__(self, **kwargs):
                    self.auto_prompt = kwargs.get('auto_prompt', False)
                    self.generate_prompt_only = kwargs.get('generate_prompt_only', False)
                    self.context_only = kwargs.get('context_only', False)
                    self.project_path = kwargs.get('project_path', '.')
            
            # Test that missing project path is caught
            args_no_path = MockArgs(auto_prompt=True, project_path=None)
            
            with pytest.raises(ValueError) as exc_info:
                validate_cli_arguments(args_no_path)
            
            assert 'project_path' in str(exc_info.value).lower()
            
        except ImportError:
            pytest.skip("validate_cli_arguments function not found - implementation pending")
    
    def test_custom_validation_error_messages(self):
        """Test that validation error messages are helpful and specific."""
        try:
            from src.generate_code_review_context import create_argument_parser, validate_cli_arguments
            parser = create_argument_parser()
            
            # Test error message for conflicting flags
            args = parser.parse_args(['--auto-prompt', '--generate-prompt-only', '.'])
            
            with pytest.raises(ValueError) as exc_info:
                validate_cli_arguments(args)
            
            error_msg = str(exc_info.value)
            
            # Error message should be helpful
            assert len(error_msg) > 20  # Should be detailed
            assert '--auto-prompt' in error_msg
            assert '--generate-prompt-only' in error_msg
            
            # Should suggest alternative usage
            assert 'use' in error_msg.lower() or 'instead' in error_msg.lower() or 'choose' in error_msg.lower()
            
        except ImportError:
            pytest.skip("CLI validation functions not found - implementation pending")


class TestCLIBackwardCompatibility:
    """Test that new CLI features don't break existing functionality."""
    
    def test_existing_cli_commands_unchanged(self):
        """Test that existing CLI commands work exactly as before."""
        try:
            from src.generate_code_review_context import create_argument_parser
            parser = create_argument_parser()
            
            # Test existing command patterns
            existing_patterns = [
                ['.'],
                ['--context-only', '.'],
                ['--temperature', '0.3', '.'],
                ['--scope', 'full_project', '.'],
                ['--scope', 'specific_phase', '--phase-number', '2.0', '.'],
                ['--compare-branch', 'feature/test', '.'],
                ['--github-pr-url', 'https://github.com/owner/repo/pull/123'],
            ]
            
            for pattern in existing_patterns:
                args = parser.parse_args(pattern)
                
                # New flags should default to False
                assert args.auto_prompt is False
                assert args.generate_prompt_only is False
                
                # Existing functionality should be preserved
                if '--context-only' in pattern:
                    assert args.context_only is True
                if '--temperature' in pattern:
                    assert args.temperature == 0.3
                if '--scope' in pattern:
                    scope_index = pattern.index('--scope') + 1
                    assert args.scope == pattern[scope_index]
            
        except ImportError:
            pytest.skip("create_argument_parser function not found - implementation pending")
    
    def test_help_output_includes_new_and_existing_options(self):
        """Test that help output includes both new and existing options."""
        try:
            from src.generate_code_review_context import create_argument_parser
            parser = create_argument_parser()
            
            help_output = parser.format_help()
            
            # New options should be present
            assert '--auto-prompt' in help_output
            assert '--generate-prompt-only' in help_output
            
            # Existing options should still be present
            assert '--context-only' in help_output
            assert '--temperature' in help_output
            assert '--scope' in help_output
            assert '--compare-branch' in help_output
            assert '--github-pr-url' in help_output
            
            # Help structure should be maintained
            assert 'usage:' in help_output.lower()
            assert 'positional arguments:' in help_output.lower() or 'arguments:' in help_output.lower()
            assert 'optional arguments:' in help_output.lower() or 'options:' in help_output.lower()
            
        except ImportError:
            pytest.skip("create_argument_parser function not found - implementation pending")
    
    def test_argument_defaults_preserved(self):
        """Test that default values for existing arguments are preserved."""
        try:
            from src.generate_code_review_context import create_argument_parser
            parser = create_argument_parser()
            
            # Parse minimal arguments
            args = parser.parse_args(['.'])
            
            # Check that existing defaults are preserved
            assert args.scope == 'recent_phase'  # Should remain default
            assert args.temperature == 0.5  # Should remain default
            assert args.context_only is False  # Should remain default
            assert args.no_claude_memory is False  # Should remain default
            assert args.include_cursor_rules is False  # Should remain default
            
            # New arguments should have appropriate defaults
            assert args.auto_prompt is False
            assert args.generate_prompt_only is False
            
        except ImportError:
            pytest.skip("create_argument_parser function not found - implementation pending")
    
    def test_existing_argument_types_preserved(self):
        """Test that existing argument types and validation are preserved."""
        try:
            from src.generate_code_review_context import create_argument_parser
            parser = create_argument_parser()
            
            # Test that temperature still validates as float
            args = parser.parse_args(['--temperature', '0.7', '.'])
            assert isinstance(args.temperature, float)
            assert args.temperature == 0.7
            
            # Test that scope still validates choices
            valid_scopes = ['recent_phase', 'full_project', 'specific_phase', 'specific_task']
            for scope in valid_scopes:
                args = parser.parse_args(['--scope', scope, '.'])
                assert args.scope == scope
            
            # Test that invalid scope still raises error
            with pytest.raises(SystemExit):
                parser.parse_args(['--scope', 'invalid_scope', '.'])
            
        except ImportError:
            pytest.skip("create_argument_parser function not found - implementation pending")