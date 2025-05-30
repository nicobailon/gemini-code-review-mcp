"""
Behavior tests for CLI user feedback - focus on what users see
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
from io import StringIO

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestCLIUserFeedback:
    """Test CLI provides proper user feedback"""
    
    @patch('generate_code_review_context.find_project_files')
    @patch('generate_code_review_context.get_changed_files')
    @patch('generate_code_review_context.generate_file_tree')
    @patch('builtins.print')
    def test_cli_shows_project_analysis_feedback(self, mock_print, mock_tree, mock_files, mock_find):
        """Test that CLI shows project analysis feedback to user"""
        from generate_code_review_context import main
        
        # Mock basic setup
        mock_find.return_value = (None, None)  # No PRD/task files
        mock_files.return_value = []
        mock_tree.return_value = "mock tree"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file, gemini_file = main(
                project_path=temp_dir,
                enable_gemini_review=False
            )
            
            # Check that print was called with user feedback
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            
            # Should show project analysis
            assert any("🔍 Analyzing project:" in call for call in print_calls)
            assert any("📊 Review scope:" in call for call in print_calls)
            
            # Should show completion
            assert any("📝 Generated review context:" in call for call in print_calls)
    
    @patch('generate_code_review_context.find_project_files')
    @patch('generate_code_review_context.get_changed_files')
    @patch('generate_code_review_context.generate_file_tree')
    @patch('generate_code_review_context.send_to_gemini_for_review')
    @patch('builtins.print')
    def test_cli_shows_gemini_feedback_when_enabled(self, mock_print, mock_gemini, mock_tree, mock_files, mock_find):
        """Test that CLI shows Gemini-related feedback when AI review is enabled"""
        from generate_code_review_context import main
        
        # Mock setup
        mock_find.return_value = (None, None)
        mock_files.return_value = []
        mock_tree.return_value = "mock tree"
        mock_gemini.return_value = "/path/to/gemini_review.md"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file, gemini_file = main(
                project_path=temp_dir,
                enable_gemini_review=True,
                temperature=0.7
            )
            
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            
            # Should show temperature setting
            assert any("🌡️" in call and "0.7" in call for call in print_calls)
            
            # Should show Gemini processing
            assert any("🔄 Sending to Gemini" in call for call in print_calls)
            
            # Should show completion
            assert any("✅ AI code review completed:" in call for call in print_calls)
    
    @patch('generate_code_review_context.find_project_files')
    @patch('generate_code_review_context.get_changed_files')
    @patch('generate_code_review_context.generate_file_tree')
    @patch('generate_code_review_context.send_to_gemini_for_review')
    @patch('builtins.print')
    def test_cli_shows_failure_feedback_when_gemini_fails(self, mock_print, mock_gemini, mock_tree, mock_files, mock_find):
        """Test that CLI shows appropriate feedback when AI review fails"""
        from generate_code_review_context import main
        
        # Mock setup with Gemini failure
        mock_find.return_value = (None, None)
        mock_files.return_value = []
        mock_tree.return_value = "mock tree"
        mock_gemini.return_value = None  # Failure
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file, gemini_file = main(
                project_path=temp_dir,
                enable_gemini_review=True
            )
            
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            
            # Should show failure feedback
            assert any("⚠️" in call and "failed or was skipped" in call for call in print_calls)
    
    def test_cli_main_shows_final_summary(self):
        """Test that CLI main function shows final file summary"""
        from generate_code_review_context import cli_main
        
        # Test with invalid path to trigger early exit
        with patch('sys.argv', ['generate-code-review', '/nonexistent/path']):
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print') as mock_print:
                    cli_main()
                    
                    # Should have called print (even for errors)
                    assert mock_print.called
    
    @patch('generate_code_review_context.send_to_gemini_for_review')
    @patch('builtins.print')
    def test_gemini_feedback_shows_model_capabilities(self, mock_print, mock_gemini):
        """Test that Gemini feedback shows model capabilities to user"""
        from generate_code_review_context import send_to_gemini_for_review
        
        # Mock successful Gemini call
        mock_gemini.return_value = "/path/to/review.md"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = send_to_gemini_for_review(
                context_content="mock content",
                project_path=temp_dir,
                temperature=0.5
            )
            
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            
            # Should show model information
            assert any("🤖 Using Gemini model:" in call for call in print_calls)
            
            # Should show either enhanced or standard features
            enhanced_shown = any("✨ Enhanced features enabled:" in call for call in print_calls)
            standard_shown = any("⚡ Standard features:" in call for call in print_calls)
            assert enhanced_shown or standard_shown


class TestCLIBehaviorRequirements:
    """Test CLI meets business requirements for user experience"""
    
    def test_cli_handles_missing_project_gracefully(self):
        """Test that CLI provides helpful error for missing projects"""
        from generate_code_review_context import cli_main
        
        with patch('sys.argv', ['generate-code-review', '/completely/nonexistent/path']):
            with patch('sys.exit') as mock_exit:
                with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                    cli_main()
                    
                    # Should exit with error
                    mock_exit.assert_called_with(1)
                    
                    # Should provide helpful error message
                    stderr_output = mock_stderr.getvalue()
                    assert "does not exist" in stderr_output
                    # Should suggest corrections
                    assert "SUGGESTIONS" in stderr_output or "EXAMPLES" in stderr_output
    
    def test_cli_validates_temperature_range(self):
        """Test that CLI validates temperature parameter range"""
        from generate_code_review_context import cli_main
        
        with patch('sys.argv', ['generate-code-review', '.', '--temperature', '3.0']):
            with patch('sys.exit') as mock_exit:
                with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                    cli_main()
                    
                    # Should exit with error for invalid temperature
                    mock_exit.assert_called_with(1)
                    
                    # Should explain valid range
                    stderr_output = mock_stderr.getvalue()
                    assert "Temperature must be between 0.0 and 2.0" in stderr_output
    
    def test_cli_validates_scope_parameters(self):
        """Test that CLI validates scope-specific parameters"""
        from generate_code_review_context import cli_main
        
        # Test specific_phase without phase_number
        with patch('sys.argv', ['generate-code-review', '.', '--scope', 'specific_phase']):
            with patch('sys.exit') as mock_exit:
                with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                    cli_main()
                    
                    # Should exit with error
                    mock_exit.assert_called_with(1)
                    
                    # Should explain what's missing
                    stderr_output = mock_stderr.getvalue()
                    assert "phase_number is required" in stderr_output
                    assert "Working examples:" in stderr_output
    
    @patch('generate_code_review_context.find_project_files')
    @patch('generate_code_review_context.get_changed_files')
    @patch('generate_code_review_context.generate_file_tree')
    @patch('builtins.print')
    def test_cli_shows_scope_in_feedback(self, mock_print, mock_tree, mock_files, mock_find):
        """Test that CLI shows selected scope in user feedback"""
        from generate_code_review_context import main
        
        mock_find.return_value = (None, None)
        mock_files.return_value = []
        mock_tree.return_value = "mock tree"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file, gemini_file = main(
                project_path=temp_dir,
                scope="full_project",
                enable_gemini_review=False
            )
            
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            
            # Should show the scope that was selected
            assert any("📊 Review scope: full_project" in call for call in print_calls)
    
    @patch('generate_code_review_context.find_project_files')
    @patch('generate_code_review_context.get_changed_files') 
    @patch('generate_code_review_context.generate_file_tree')
    @patch('builtins.print')
    def test_cli_shows_recognizable_project_name(self, mock_print, mock_tree, mock_files, mock_find):
        """Test that CLI shows recognizable project name to user"""
        from generate_code_review_context import main
        
        mock_find.return_value = (None, None)
        mock_files.return_value = []
        mock_tree.return_value = "mock tree"
        
        project_path = "/users/alice/projects/my-awesome-web-app"
        with patch('os.path.abspath', return_value=project_path):
            with tempfile.TemporaryDirectory() as temp_dir:
                context_file, gemini_file = main(
                    project_path=temp_dir,
                    enable_gemini_review=False
                )
                
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                
                # Should show project name user can recognize
                assert any("my-awesome-web-app" in call for call in print_calls)


class TestModelCapabilityFeedback:
    """Test that model capability detection provides user feedback"""
    
    @patch('generate_code_review_context.load_model_config')
    @patch('builtins.print')
    def test_model_capability_detection_shows_features(self, mock_print, mock_config):
        """Test that model capability detection shows enabled features"""
        from generate_code_review_context import send_to_gemini_for_review
        
        # Mock config with capabilities
        mock_config.return_value = {
            'model_aliases': {'gemini-2.5-pro': 'gemini-2.5-pro-preview-05-06'},
            'model_capabilities': {
                'url_context_supported': ['gemini-2.5-pro-preview-05-06'],
                'thinking_mode_supported': ['gemini-2.5-pro-preview-05-06']
            },
            'defaults': {'model': 'gemini-2.5-pro'}
        }
        
        with patch.dict(os.environ, {'GEMINI_MODEL': 'gemini-2.5-pro'}):
            with patch('generate_code_review_context.require_api_key', return_value='fake-key'):
                with patch('generate_code_review_context.genai.Client') as mock_client:
                    # Mock successful Gemini response
                    mock_response = mock_client.return_value.models.generate_content.return_value
                    mock_response.text = "Mock review content"
                    
                    with tempfile.TemporaryDirectory() as temp_dir:
                        result = send_to_gemini_for_review(
                            context_content="mock content",
                            project_path=temp_dir
                        )
                        
                        print_calls = [call[0][0] for call in mock_print.call_args_list]
                        
                        # Should show model name
                        assert any("🤖 Using Gemini model:" in call for call in print_calls)
                        
                        # Should show enhanced features
                        assert any("✨ Enhanced features enabled:" in call for call in print_calls)
                        
                        # Should show specific capability descriptions
                        assert any("💭 Thinking mode:" in call for call in print_calls)
                        assert any("🔗 URL context:" in call for call in print_calls)
    
    @patch('generate_code_review_context.load_model_config')
    @patch('builtins.print')
    def test_basic_model_shows_standard_features(self, mock_print, mock_config):
        """Test that basic models show standard features message"""
        from generate_code_review_context import send_to_gemini_for_review
        
        # Mock config with basic model (no special capabilities)
        mock_config.return_value = {
            'model_aliases': {},
            'model_capabilities': {
                'url_context_supported': [],
                'thinking_mode_supported': []
            },
            'defaults': {'model': 'gemini-1.0-basic'}
        }
        
        with patch.dict(os.environ, {'GEMINI_MODEL': 'gemini-1.0-basic'}):
            with patch('generate_code_review_context.require_api_key', return_value='fake-key'):
                with patch('generate_code_review_context.genai.Client') as mock_client:
                    mock_response = mock_client.return_value.models.generate_content.return_value
                    mock_response.text = "Mock review content"
                    
                    with tempfile.TemporaryDirectory() as temp_dir:
                        result = send_to_gemini_for_review(
                            context_content="mock content",
                            project_path=temp_dir
                        )
                        
                        print_calls = [call[0][0] for call in mock_print.call_args_list]
                        
                        # Should show standard features for basic model
                        assert any("⚡ Standard features: Basic text generation" in call for call in print_calls)