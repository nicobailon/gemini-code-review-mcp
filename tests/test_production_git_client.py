"""
Test ProductionGitClient implementation with parametric tests.
Focuses on the async branch of get_changed_files.
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gemini_code_review_mcp.interfaces import GitFileChange, ProductionGitClient
from gemini_code_review_mcp.progress import progress


class TestProductionGitClientGetChangedFiles:
    """Test the get_changed_files method with different parameters."""

    def setup_method(self):
        self.client = ProductionGitClient()
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.parametrize(
        "base_ref,head_ref,expected_cmd_parts,test_name",
        [
            # Test case 1: Compare specific branches
            (
                "main",
                "feature/test",
                ["diff", "--numstat", "main...feature/test"],
                "compare_specific_branches",
            ),
            # Test case 2: Compare with different base
            (
                "develop",
                "HEAD",
                ["diff", "--numstat", "develop...HEAD"],
                "compare_develop_to_head",
            ),
            # Test case 3: Compare tags
            (
                "v1.0.0",
                "v2.0.0",
                ["diff", "--numstat", "v1.0.0...v2.0.0"],
                "compare_tags",
            ),
            # Test case 4: No refs - working directory changes
            (
                None,
                None,
                ["diff", "--cached", "--numstat"],  # First command for staged
                "working_directory_changes",
            ),
        ],
    )
    def test_get_changed_files_async_branch(
        self, base_ref, head_ref, expected_cmd_parts, test_name
    ):
        """Test the async branch of get_changed_files with different ref combinations."""
        # Mock subprocess.run
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        if base_ref and head_ref:
            # Mock output for branch comparison
            mock_result.stdout = "10\t5\tsrc/main.py\n20\t0\tsrc/new_feature.py\n0\t15\tsrc/old_file.py"
        else:
            # Mock output for working directory changes
            mock_result.stdout = "5\t3\tsrc/modified.py"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            # Call the method
            with progress(f"Testing {test_name}"):
                changes = self.client.get_changed_files(
                    self.repo_path,
                    base_ref=base_ref,
                    head_ref=head_ref,
                    include_untracked=False,
                )

            # Verify the correct command was called
            if base_ref and head_ref:
                # For branch comparison, verify the exact command
                mock_run.assert_any_call(
                    ["git"] + expected_cmd_parts,
                    cwd=str(self.repo_path),  # ProductionGitClient converts to string
                    capture_output=True,
                    text=True,
                    check=True,
                )
                
                # Verify results
                assert len(changes) == 3
                assert changes[0].file_path == "src/main.py"
                assert changes[0].additions == 10
                assert changes[0].deletions == 5
                assert changes[1].file_path == "src/new_feature.py"
                assert changes[1].additions == 20
                assert changes[1].deletions == 0
            else:
                # For working directory, verify staged changes command
                mock_run.assert_any_call(
                    ["git", "diff", "--cached", "--numstat"],
                    cwd=str(self.repo_path),  # ProductionGitClient converts to string
                    capture_output=True,
                    text=True,
                    check=True,
                )

    @pytest.mark.parametrize(
        "include_untracked,expected_calls",
        [
            (True, 3),  # staged + unstaged + untracked
            (False, 2),  # staged + unstaged only
        ],
    )
    def test_get_changed_files_untracked_parameter(self, include_untracked, expected_calls):
        """Test include_untracked parameter behavior."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            with progress("Testing untracked files"):
                self.client.get_changed_files(
                    self.repo_path,
                    include_untracked=include_untracked,
                )

            # Verify number of git commands called
            assert mock_run.call_count == expected_calls

            if include_untracked:
                # Verify untracked files command was called
                mock_run.assert_any_call(
                    ["git", "ls-files", "--others", "--exclude-standard"],
                    cwd=str(self.repo_path),  # ProductionGitClient converts to string
                    capture_output=True,
                    text=True,
                    check=True,
                )

    def test_get_changed_files_with_progress_updates(self):
        """Test that progress indicators are properly updated during execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "10\t5\tsrc/file.py"

        # Track progress calls
        progress_updates = []
        
        class MockProgressIndicator:
            def update(self, msg):
                progress_updates.append(msg)
            
            def __enter__(self):
                return self
            
            def __exit__(self, *args):
                pass

        with patch("subprocess.run", return_value=mock_result):
            with patch("gemini_code_review_mcp.interfaces.git_client_impl.progress") as mock_progress:
                # Configure mock to return our tracking indicator
                mock_indicator = MockProgressIndicator()
                mock_progress.return_value.__enter__.return_value = mock_indicator
                
                self.client.get_changed_files(
                    self.repo_path,
                    base_ref="main",
                    head_ref="feature",
                )

            # Verify progress was called
            mock_progress.assert_called_once_with("Analyzing Git changes")
            
            # Verify updates were made
            assert len(progress_updates) > 0
            assert any("Comparing main...feature" in update for update in progress_updates)

    def test_get_changed_files_error_handling(self):
        """Test error handling when git commands fail."""
        mock_result = MagicMock()
        mock_result.returncode = 128
        mock_result.stderr = "fatal: not a git repository"

        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(128, ["git"], stderr="fatal: not a git repository")):
            with pytest.raises(RuntimeError, match="Git command failed"):
                self.client.get_changed_files(self.repo_path)

    @pytest.mark.parametrize(
        "numstat_output,expected_changes",
        [
            # Normal files with additions and deletions
            ("10\t5\tsrc/file.py\n20\t0\tsrc/new.py", 2),
            # Binary files (shown as -)
            ("-\t-\timage.png\n5\t3\ttext.txt", 2),
            # Empty output
            ("", 0),
            # Files with spaces in names
            ("10\t5\tsrc/my file.py", 1),
        ],
    )
    def test_get_changed_files_output_parsing(self, numstat_output, expected_changes):
        """Test parsing of different git diff numstat outputs."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = numstat_output

        with patch("subprocess.run", return_value=mock_result):
            changes = self.client.get_changed_files(
                self.repo_path,
                base_ref="main",
                head_ref="feature",
            )

            assert len(changes) == expected_changes
            
            # Verify binary files are handled correctly
            if "-\t-\t" in numstat_output:
                binary_change = next((c for c in changes if "image.png" in c.file_path), None)
                if binary_change:
                    assert binary_change.additions == 0
                    assert binary_change.deletions == 0