"""
TDD Tests for Git Branch Comparison Module

Following test-driven development approach - write tests first,
then implement functionality to make tests pass.

DO NOT create mock implementations.
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestBranchDetectionAndValidation:
    """Test branch detection and validation functionality."""
    
    def test_detect_primary_branch_finds_main(self):
        """Test detecting 'main' as primary branch when it exists."""
        # Import will fail initially - that's expected in TDD
        from git_branch_comparison import detect_primary_branch
        
        with patch('subprocess.run') as mock_run:
            # Mock git branch output showing 'main' exists
            mock_run.return_value.stdout = "  feature/test\n* main\n  develop\n"
            mock_run.return_value.returncode = 0
            
            result = detect_primary_branch("/test/repo")
            
            assert result == "main"
            # Verify git command was called correctly
            mock_run.assert_called_with(
                ['git', 'branch', '-a'],
                cwd="/test/repo",
                capture_output=True,
                text=True,
                check=True
            )
    
    def test_detect_primary_branch_finds_master_when_no_main(self):
        """Test detecting 'master' as primary branch when 'main' doesn't exist."""
        from git_branch_comparison import detect_primary_branch
        
        with patch('subprocess.run') as mock_run:
            # Mock git branch output showing 'master' but no 'main'
            mock_run.return_value.stdout = "  feature/test\n* master\n  develop\n"
            mock_run.return_value.returncode = 0
            
            result = detect_primary_branch("/test/repo")
            
            assert result == "master"
    
    def test_detect_primary_branch_prefers_main_over_master(self):
        """Test that 'main' is preferred when both 'main' and 'master' exist."""
        from git_branch_comparison import detect_primary_branch
        
        with patch('subprocess.run') as mock_run:
            # Mock git branch output showing both main and master
            mock_run.return_value.stdout = "  feature/test\n  main\n* master\n  develop\n"
            mock_run.return_value.returncode = 0
            
            result = detect_primary_branch("/test/repo")
            
            assert result == "main"
    
    def test_detect_primary_branch_handles_git_failure(self):
        """Test handling when git command fails."""
        from git_branch_comparison import detect_primary_branch
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'git')
            
            with pytest.raises(ValueError, match="Failed to detect primary branch"):
                detect_primary_branch("/invalid/repo")
    
    def test_detect_primary_branch_handles_no_main_or_master(self):
        """Test handling when neither main nor master branches exist."""
        from git_branch_comparison import detect_primary_branch
        
        with patch('subprocess.run') as mock_run:
            # Mock git branch output with no main or master
            mock_run.return_value.stdout = "  feature/test\n* develop\n  staging\n"
            mock_run.return_value.returncode = 0
            
            with pytest.raises(ValueError, match="No primary branch found"):
                detect_primary_branch("/test/repo")
    
    def test_validate_branch_exists_for_valid_branch(self):
        """Test validating that a branch exists in the repository."""
        from git_branch_comparison import validate_branch_exists
        
        with patch('subprocess.run') as mock_run:
            # Mock git show-ref output for existing branch
            mock_run.return_value.stdout = "abc123def456 refs/heads/feature/test\n"
            mock_run.return_value.returncode = 0
            
            result = validate_branch_exists("/test/repo", "feature/test")
            
            assert result is True
            mock_run.assert_called_with(
                ['git', 'show-ref', '--verify', '--quiet', 'refs/heads/feature/test'],
                cwd="/test/repo",
                capture_output=True,
                text=True
            )
    
    def test_validate_branch_exists_for_invalid_branch(self):
        """Test validating that a non-existent branch returns False."""
        from git_branch_comparison import validate_branch_exists
        
        with patch('subprocess.run') as mock_run:
            # Mock git show-ref failure for non-existent branch
            mock_run.return_value.returncode = 1
            
            result = validate_branch_exists("/test/repo", "nonexistent/branch")
            
            assert result is False
    
    def test_validate_branch_exists_handles_git_errors(self):
        """Test handling git errors during branch validation."""
        from git_branch_comparison import validate_branch_exists
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(128, 'git')
            
            with pytest.raises(ValueError, match="Git error validating branch"):
                validate_branch_exists("/invalid/repo", "any/branch")
    
    def test_validate_repository_for_valid_git_repo(self):
        """Test validating that a directory is a valid git repository."""
        from git_branch_comparison import validate_repository
        
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.run') as mock_run:
                # Mock successful git rev-parse
                mock_run.return_value.stdout = "/test/repo/.git\n"
                mock_run.return_value.returncode = 0
                
                result = validate_repository("/test/repo")
                
                assert result is True
                mock_run.assert_called_with(
                    ['git', 'rev-parse', '--git-dir'],
                    cwd="/test/repo",
                    capture_output=True,
                    text=True
                )
    
    def test_validate_repository_for_non_git_directory(self):
        """Test validating a directory that is not a git repository."""
        from git_branch_comparison import validate_repository
        
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.run') as mock_run:
                # Mock git rev-parse failure
                mock_run.return_value.returncode = 128
                
                result = validate_repository("/not/a/git/repo")
                
                assert result is False
    
    def test_validate_repository_handles_missing_directory(self):
        """Test handling when repository directory doesn't exist."""
        from git_branch_comparison import validate_repository
        
        with patch('os.path.exists', return_value=False):
            with pytest.raises(ValueError, match="Repository path does not exist"):
                validate_repository("/nonexistent/path")


class TestBranchComparison:
    """Test branch comparison functionality."""
    
    def test_get_branch_diff_basic_comparison(self):
        """Test basic branch comparison with modified files."""
        from git_branch_comparison import get_branch_diff
        
        with patch('subprocess.run') as mock_run:
            def side_effect(*args, **kwargs):
                if '--name-status' in args[0]:
                    # Mock git diff output
                    mock_run.return_value.stdout = """M\tsrc/file1.py
A\tsrc/new_file.py
D\told_file.py"""
                    mock_run.return_value.returncode = 0
                elif 'show' in args[0]:
                    # Mock file content
                    mock_run.return_value.stdout = "file content"
                    mock_run.return_value.returncode = 0
                elif '--oneline' in args[0]:
                    # Mock commit log
                    mock_run.return_value.stdout = ""
                    mock_run.return_value.returncode = 0
                return mock_run.return_value
            
            mock_run.side_effect = side_effect
            
            result = get_branch_diff("/test/repo", "feature/branch", "main")
            
            assert result['source_branch'] == "feature/branch"
            assert result['target_branch'] == "main"
            assert len(result['changed_files']) == 3
            
            # Check file details
            modified_file = next(f for f in result['changed_files'] if f['status'] == 'M')
            assert modified_file['path'] == 'src/file1.py'
            
            added_file = next(f for f in result['changed_files'] if f['status'] == 'A')
            assert added_file['path'] == 'src/new_file.py'
            
            deleted_file = next(f for f in result['changed_files'] if f['status'] == 'D')
            assert deleted_file['path'] == 'old_file.py'
            
            # Verify git diff command was called (check first call)
            assert mock_run.call_args_list[0][0][0] == ['git', 'diff', '--name-status', 'main...feature/branch']
    
    def test_get_branch_diff_with_file_content(self):
        """Test branch comparison includes file content for changed files."""
        from git_branch_comparison import get_branch_diff
        
        with patch('subprocess.run') as mock_run:
            def side_effect(*args, **kwargs):
                if '--name-status' in args[0]:
                    # Mock file list
                    mock_run.return_value.stdout = "M\tsrc/test.py"
                    mock_run.return_value.returncode = 0
                elif 'show' in args[0] and 'src/test.py' in args[0]:
                    # Mock file content from source branch
                    mock_run.return_value.stdout = "def test_function():\n    return 'updated'"
                    mock_run.return_value.returncode = 0
                return mock_run.return_value
            
            mock_run.side_effect = side_effect
            
            result = get_branch_diff("/test/repo", "feature/branch", "main")
            
            modified_file = result['changed_files'][0]
            assert modified_file['status'] == 'M'
            assert modified_file['path'] == 'src/test.py'
            assert 'def test_function' in modified_file['content']
    
    def test_get_branch_diff_handles_binary_files(self):
        """Test handling binary files in branch comparison."""
        from git_branch_comparison import get_branch_diff
        
        with patch('subprocess.run') as mock_run:
            def side_effect(*args, **kwargs):
                if '--name-status' in args[0]:
                    mock_run.return_value.stdout = "M\timage.png"
                    mock_run.return_value.returncode = 0
                elif 'show' in args[0]:
                    # Mock binary file error
                    mock_run.side_effect = subprocess.CalledProcessError(1, 'git')
                return mock_run.return_value
            
            mock_run.side_effect = side_effect
            
            result = get_branch_diff("/test/repo", "feature/branch", "main")
            
            binary_file = result['changed_files'][0]
            assert binary_file['content'] == "[Binary file or content not available]"
    
    def test_get_branch_diff_with_commit_info(self):
        """Test that branch comparison includes commit information."""
        from git_branch_comparison import get_branch_diff
        
        with patch('subprocess.run') as mock_run:
            def side_effect(*args, **kwargs):
                if '--name-status' in args[0]:
                    mock_run.return_value.stdout = "M\tsrc/test.py"
                    mock_run.return_value.returncode = 0
                elif 'log' in args[0] and '--oneline' in args[0]:
                    # Mock commit log
                    mock_run.return_value.stdout = """abc123d Fix authentication bug
def456e Add new feature
789ghij Update documentation"""
                    mock_run.return_value.returncode = 0
                elif 'show' in args[0]:
                    mock_run.return_value.stdout = "file content"
                    mock_run.return_value.returncode = 0
                return mock_run.return_value
            
            mock_run.side_effect = side_effect
            
            result = get_branch_diff("/test/repo", "feature/branch", "main")
            
            assert 'commits' in result
            assert len(result['commits']) == 3
            assert result['commits'][0]['hash'] == 'abc123d'
            assert result['commits'][0]['message'] == 'Fix authentication bug'
    
    def test_get_branch_diff_handles_no_differences(self):
        """Test handling when branches have no differences."""
        from git_branch_comparison import get_branch_diff
        
        with patch('subprocess.run') as mock_run:
            # Mock empty git diff output
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0
            
            result = get_branch_diff("/test/repo", "feature/branch", "main")
            
            assert result['source_branch'] == "feature/branch"
            assert result['target_branch'] == "main"
            assert len(result['changed_files']) == 0
            assert result['summary']['files_changed'] == 0
    
    def test_get_branch_diff_includes_statistics(self):
        """Test that branch comparison includes file change statistics."""
        from git_branch_comparison import get_branch_diff
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = """M\tsrc/file1.py
A\tsrc/file2.py
A\tsrc/file3.py
D\told_file.py"""
            mock_run.return_value.returncode = 0
            
            result = get_branch_diff("/test/repo", "feature/branch", "main")
            
            summary = result['summary']
            assert summary['files_changed'] == 4
            assert summary['files_added'] == 2
            assert summary['files_modified'] == 1
            assert summary['files_deleted'] == 1


class TestErrorHandling:
    """Test error handling for git operations."""
    
    def test_get_branch_diff_handles_invalid_branches(self):
        """Test error handling for invalid branch names."""
        from git_branch_comparison import get_branch_diff
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(128, 'git')
            
            with pytest.raises(ValueError, match="Failed to compare branches"):
                get_branch_diff("/test/repo", "invalid/branch", "main")
    
    def test_get_branch_diff_handles_git_not_available(self):
        """Test error handling when git is not available."""
        from git_branch_comparison import get_branch_diff
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("git command not found")
            
            with pytest.raises(ValueError, match="Git is not available"):
                get_branch_diff("/test/repo", "feature/branch", "main")


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    def test_typical_feature_branch_comparison(self):
        """Test typical scenario of comparing feature branch to main."""
        from git_branch_comparison import get_branch_diff, detect_primary_branch, validate_branch_exists
        
        with patch('subprocess.run') as mock_run:
            def side_effect(*args, **kwargs):
                if 'branch' in args[0] and '-a' in args[0]:
                    # Primary branch detection
                    mock_run.return_value.stdout = "* feature/auth\n  main\n  develop\n"
                    mock_run.return_value.returncode = 0
                elif 'show-ref' in args[0]:
                    # Branch validation
                    mock_run.return_value.returncode = 0
                elif '--name-status' in args[0]:
                    # File changes
                    mock_run.return_value.stdout = "M\tsrc/auth.py\nA\ttests/test_auth.py"
                    mock_run.return_value.returncode = 0
                elif 'show' in args[0]:
                    mock_run.return_value.stdout = "file content"
                    mock_run.return_value.returncode = 0
                return mock_run.return_value
            
            mock_run.side_effect = side_effect
            
            # Test the workflow
            primary = detect_primary_branch("/test/repo")
            assert primary == "main"
            
            branch_valid = validate_branch_exists("/test/repo", "feature/auth")
            assert branch_valid is True
            
            diff_result = get_branch_diff("/test/repo", "feature/auth", "main")
            assert len(diff_result['changed_files']) == 2
            assert diff_result['summary']['files_changed'] == 2


# Import subprocess for use in tests
import subprocess


if __name__ == "__main__":
    pytest.main([__file__])