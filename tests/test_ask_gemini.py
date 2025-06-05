#!/usr/bin/env python3
"""
Tests for the ask_gemini module and MCP tool.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.ask_gemini import ask_gemini, ask_gemini_direct
from src.file_context_types import FileContextResult, FileContentData


class TestAskGemini:
    """Test the main ask_gemini function."""
    
    def test_ask_gemini_simple_question(self):
        """Test asking a simple question without file context."""
        with patch('src.ask_gemini.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = "Python decorators are functions that modify other functions."
            
            result = ask_gemini("What are Python decorators?")
            
            assert result == "Python decorators are functions that modify other functions."
            mock_gemini.assert_called_once()
            args = mock_gemini.call_args[1]
            assert "What are Python decorators?" in args['context_content']
            assert args['return_text'] is True
            assert args['include_formatting'] is False
    
    def test_ask_gemini_with_file_context(self):
        """Test asking a question with file context."""
        mock_file_data = FileContentData(
            path="src/utils.py",
            absolute_path="/project/src/utils.py",
            content="def slow_function():\n    time.sleep(1)\n    return 42",
            line_ranges=[(1, 3)],
            included_lines=3,
            total_lines=3,
            estimated_tokens=20
        )
        
        mock_result = FileContextResult(
            content="File: src/utils.py\n```python\ndef slow_function():\n    time.sleep(1)\n    return 42\n```",
            total_tokens=20,
            included_files=[mock_file_data],
            excluded_files=[],
            configuration_content="",
            meta_prompt=None
        )
        
        with patch('src.ask_gemini.generate_file_context_data') as mock_context:
            with patch('src.ask_gemini.send_to_gemini_for_review') as mock_gemini:
                mock_context.return_value = mock_result
                mock_gemini.return_value = "You can optimize by removing the sleep call."
                
                result = ask_gemini(
                    "How can I optimize this function?",
                    file_selections=[{"path": "src/utils.py"}]
                )
                
                assert result == "You can optimize by removing the sleep call."
                mock_context.assert_called_once()
                mock_gemini.assert_called_once()
                
                # Check that file context was included in prompt
                gemini_args = mock_gemini.call_args[1]
                assert "File: src/utils.py" in gemini_args['context_content']
                assert "How can I optimize this function?" in gemini_args['context_content']
    
    def test_ask_gemini_with_user_instructions(self):
        """Test asking with additional user instructions."""
        with patch('src.ask_gemini.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = "Here's a performance-focused answer."
            
            result = ask_gemini(
                "What is a list comprehension?",
                user_instructions="Focus on performance benefits"
            )
            
            assert result == "Here's a performance-focused answer."
            args = mock_gemini.call_args[1]
            assert "Focus on performance benefits" in args['context_content']
            assert "What is a list comprehension?" in args['context_content']
    
    def test_ask_gemini_empty_question(self):
        """Test that empty question raises ValueError."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            ask_gemini("")
        
        with pytest.raises(ValueError, match="Question cannot be empty"):
            ask_gemini("   ")
    
    def test_ask_gemini_save_to_file(self):
        """Test saving response to file."""
        with patch('src.ask_gemini.send_to_gemini_for_review') as mock_gemini:
            with patch('builtins.open', create=True) as mock_open:
                with patch('os.makedirs') as mock_makedirs:
                    mock_gemini.return_value = "Test response"
                    mock_file = MagicMock()
                    mock_open.return_value.__enter__.return_value = mock_file
                    
                    result = ask_gemini(
                        "Test question",
                        text_output=False,
                        output_path="/tmp/test-response.md"
                    )
                    
                    assert "Gemini response saved to: test-response.md" in result
                    mock_makedirs.assert_called_once()
                    mock_file.write.assert_called_once()
                    written_content = mock_file.write.call_args[0][0]
                    assert "Test question" in written_content
                    assert "Test response" in written_content
    
    def test_ask_gemini_with_line_ranges(self):
        """Test asking with specific line ranges."""
        mock_file_data = FileContentData(
            path="src/main.py",
            absolute_path="/project/src/main.py",
            content="# Lines 10-20 content",
            line_ranges=[(10, 20)],
            included_lines=11,
            total_lines=100,
            estimated_tokens=50
        )
        
        mock_result = FileContextResult(
            content="File: src/main.py (lines 10-20)\n```python\n# Lines 10-20 content\n```",
            total_tokens=50,
            included_files=[mock_file_data],
            excluded_files=[],
            configuration_content="",
            meta_prompt=None
        )
        
        with patch('src.ask_gemini.generate_file_context_data') as mock_context:
            with patch('src.ask_gemini.send_to_gemini_for_review') as mock_gemini:
                mock_context.return_value = mock_result
                mock_gemini.return_value = "The code looks good."
                
                result = ask_gemini(
                    "Review this code section",
                    file_selections=[{
                        "path": "src/main.py",
                        "line_ranges": [(10, 20)]
                    }]
                )
                
                assert result == "The code looks good."
                # Verify FileContextConfig was created with line ranges
                config = mock_context.call_args[0][0]
                assert len(config.file_selections) == 1
                assert config.file_selections[0]["path"] == "src/main.py"
                assert config.file_selections[0]["line_ranges"] == [(10, 20)]
    
    def test_ask_gemini_file_context_error_continues(self):
        """Test that file context errors don't stop the question."""
        with patch('src.ask_gemini.generate_file_context_data') as mock_context:
            with patch('src.ask_gemini.send_to_gemini_for_review') as mock_gemini:
                mock_context.side_effect = Exception("File not found")
                mock_gemini.return_value = "General Python answer"
                
                result = ask_gemini(
                    "What is Python?",
                    file_selections=[{"path": "missing.py"}]
                )
                
                assert result == "General Python answer"
                # Check error was included in prompt
                args = mock_gemini.call_args[1]
                assert "Failed to load file context" in args['context_content']
    
    def test_ask_gemini_api_failure(self):
        """Test handling of Gemini API failures."""
        with patch('src.ask_gemini.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = None
            
            with pytest.raises(Exception, match="Gemini API returned empty response"):
                ask_gemini("Test question")


class TestAskGeminiDirect:
    """Test the ask_gemini_direct convenience function."""
    
    def test_direct_question_only(self):
        """Test direct question without context."""
        with patch('src.ask_gemini.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = "Direct answer"
            
            result = ask_gemini_direct("What is Python?")
            
            assert result == "Direct answer"
            mock_gemini.assert_called_once_with(
                context_content="What is Python?",
                temperature=0.5,
                model=None,
                return_text=True,
                include_formatting=False,
            )
    
    def test_direct_with_context(self):
        """Test direct question with context."""
        with patch('src.ask_gemini.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = "Contextual answer"
            
            result = ask_gemini_direct(
                "What does this do?",
                context="def add(a, b): return a + b"
            )
            
            assert result == "Contextual answer"
            args = mock_gemini.call_args[1]
            assert "def add(a, b): return a + b" in args['context_content']
            assert "What does this do?" in args['context_content']
    
    def test_direct_empty_response_handling(self):
        """Test handling of empty responses."""
        with patch('src.ask_gemini.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = None
            
            result = ask_gemini_direct("Test")
            
            assert result == ""  # Should return empty string, not None


class TestAskGeminiIntegration:
    """Integration tests with mocked dependencies."""
    
    def test_full_workflow_with_claude_memory(self):
        """Test complete workflow including CLAUDE.md inclusion."""
        mock_file_data = FileContentData(
            path="src/test.py",
            absolute_path="/project/src/test.py",
            content="# Test file",
            line_ranges=None,
            included_lines=1,
            total_lines=1,
            estimated_tokens=5
        )
        
        mock_result = FileContextResult(
            content="File: src/test.py\n# Test file\n\nCLAUDE.md: Follow type safety",
            total_tokens=25,
            included_files=[mock_file_data],
            excluded_files=[],
            configuration_content="CLAUDE.md content",
            meta_prompt=None
        )
        
        with patch('src.ask_gemini.generate_file_context_data') as mock_context:
            with patch('src.ask_gemini.send_to_gemini_for_review') as mock_gemini:
                mock_context.return_value = mock_result
                mock_gemini.return_value = "Type-safe answer following CLAUDE.md"
                
                result = ask_gemini(
                    "How should I type this?",
                    file_selections=[{"path": "src/test.py"}],
                    include_claude_memory=True
                )
                
                assert "Type-safe answer" in result
                
                # Verify config had CLAUDE.md enabled
                config = mock_context.call_args[0][0]
                assert config.include_claude_memory is True
    
    def test_temperature_override(self):
        """Test temperature parameter is passed correctly."""
        with patch('src.ask_gemini.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = "Creative answer"
            
            ask_gemini("Be creative", temperature=1.5)
            
            assert mock_gemini.call_args[1]['temperature'] == 1.5
    
    def test_model_override(self):
        """Test model parameter is passed correctly."""
        with patch('src.ask_gemini.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = "Pro model answer"
            
            ask_gemini("Complex question", model="gemini-1.5-pro")
            
            assert mock_gemini.call_args[1]['model'] == "gemini-1.5-pro"