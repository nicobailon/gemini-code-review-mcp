#!/usr/bin/env python3
"""
Tests for context_builder module to ensure proper flag handling.
"""

import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest

from src.context_builder import (
    discover_project_configurations_with_flags,
    generate_enhanced_review_context,
    discover_project_configurations,
)


def test_discover_configurations_respects_default_flags() -> None:
    """Test that discovery respects the default False flags for CLAUDE.md and cursor rules."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create CLAUDE.md and .cursorrules files
        claude_file = os.path.join(tmpdir, "CLAUDE.md")
        with open(claude_file, "w") as f:
            f.write("# Project guidelines\nTest content")
        
        cursor_file = os.path.join(tmpdir, ".cursorrules")
        with open(cursor_file, "w") as f:
            f.write("# Cursor rules\nTest rules")
        
        # Test with defaults (should not include files)
        result = discover_project_configurations(tmpdir)
        assert len(result["claude_memory_files"]) == 0
        assert len(result["cursor_rules"]) == 0
        
        # Test with explicit False (same behavior)
        result = discover_project_configurations(tmpdir, include_claude_memory=False, include_cursor_rules=False)
        assert len(result["claude_memory_files"]) == 0
        assert len(result["cursor_rules"]) == 0
        
        # Test with explicit True (should include files)
        result = discover_project_configurations(tmpdir, include_claude_memory=True, include_cursor_rules=True)
        assert len(result["claude_memory_files"]) > 0
        assert len(result["cursor_rules"]) > 0


def test_discover_configurations_with_flags_respects_defaults() -> None:
    """Test that discover_project_configurations_with_flags respects default False flags."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create CLAUDE.md file
        claude_file = os.path.join(tmpdir, "CLAUDE.md")
        with open(claude_file, "w") as f:
            f.write("# Test content")
        
        # Test with defaults
        result = discover_project_configurations_with_flags(tmpdir)
        assert len(result["claude_memory_files"]) == 0
        assert len(result["cursor_rules"]) == 0
        
        # Test with explicit True
        result = discover_project_configurations_with_flags(
            tmpdir, 
            include_claude_memory=True,
            include_cursor_rules=True
        )
        assert len(result["claude_memory_files"]) > 0


def test_generate_enhanced_review_context_respects_flags() -> None:
    """Test that generate_enhanced_review_context respects the include flags."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        claude_file = os.path.join(tmpdir, "CLAUDE.md")
        with open(claude_file, "w") as f:
            f.write("# Claude memory content")
        
        # Mock git_utils to avoid git dependency
        with patch("src.git_utils.get_changed_files") as mock_git:
            mock_git: MagicMock
            mock_git.return_value = []
            
            # Test with defaults (should not include configuration)
            context = generate_enhanced_review_context(tmpdir)
            assert len(context.get("claude_memory_files", [])) == 0
            assert context.get("configuration_content", "") == ""
            
            # Test with explicit True
            context = generate_enhanced_review_context(
                tmpdir,
                include_claude_memory=True
            )
            assert len(context.get("claude_memory_files", [])) > 0
            assert "Claude Memory Configuration" in context.get("configuration_content", "")


def test_cache_respects_different_flag_combinations() -> None:
    """Test that the cache correctly handles different flag combinations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        claude_file = os.path.join(tmpdir, "CLAUDE.md")
        with open(claude_file, "w") as f:
            f.write("# Claude content")
        
        cursor_file = os.path.join(tmpdir, ".cursorrules")
        with open(cursor_file, "w") as f:
            f.write("# Cursor rules")
        
        # Test different flag combinations
        result1 = discover_project_configurations(tmpdir, False, False)
        assert len(result1["claude_memory_files"]) == 0
        assert len(result1["cursor_rules"]) == 0
        
        result2 = discover_project_configurations(tmpdir, True, False)
        assert len(result2["claude_memory_files"]) > 0
        assert len(result2["cursor_rules"]) == 0
        
        result3 = discover_project_configurations(tmpdir, False, True)
        assert len(result3["claude_memory_files"]) == 0
        assert len(result3["cursor_rules"]) > 0
        
        result4 = discover_project_configurations(tmpdir, True, True)
        assert len(result4["claude_memory_files"]) > 0
        assert len(result4["cursor_rules"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])