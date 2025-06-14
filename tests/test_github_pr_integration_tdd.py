"""
TDD Tests for GitHub PR Integration Module

Following test-driven development approach - write tests first,
then implement functionality to make tests pass.

DO NOT create mock implementations.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestGitHubPRUrlParsing:
    """Test GitHub PR URL parsing and validation functionality."""

    def test_parse_github_pr_url_valid_standard_format(self):
        """Test parsing standard GitHub PR URL format."""
        # Import will fail initially - that's expected in TDD
        from github_pr_integration import parse_github_pr_url

        url = "https://github.com/owner/repo/pull/123"
        result = parse_github_pr_url(url)

        assert result["owner"] == "owner"
        assert result["repo"] == "repo"
        assert result["pr_number"] == 123
        assert result["base_url"] == "https://github.com"

    def test_parse_github_pr_url_with_trailing_slash(self):
        """Test parsing GitHub PR URL with trailing slash."""
        from github_pr_integration import parse_github_pr_url

        url = "https://github.com/microsoft/vscode/pull/456/"
        result = parse_github_pr_url(url)

        assert result["owner"] == "microsoft"
        assert result["repo"] == "vscode"
        assert result["pr_number"] == 456

    def test_parse_github_pr_url_with_query_params(self):
        """Test parsing GitHub PR URL with query parameters."""
        from github_pr_integration import parse_github_pr_url

        url = "https://github.com/facebook/react/pull/789?tab=files"
        result = parse_github_pr_url(url)

        assert result["owner"] == "facebook"
        assert result["repo"] == "react"
        assert result["pr_number"] == 789

    def test_parse_github_pr_url_github_enterprise(self):
        """Test parsing GitHub Enterprise URL."""
        from github_pr_integration import parse_github_pr_url

        url = "https://github.company.com/team/project/pull/42"
        result = parse_github_pr_url(url)

        assert result["owner"] == "team"
        assert result["repo"] == "project"
        assert result["pr_number"] == 42
        assert result["base_url"] == "https://github.company.com"

    def test_parse_github_pr_url_invalid_format_raises_error(self):
        """Test that invalid URL format raises ValueError."""
        from github_pr_integration import parse_github_pr_url

        invalid_urls = [
            "https://github.com/owner/repo/issues/123",  # Issue, not PR
            "https://github.com/owner/repo",  # No PR path
            "https://gitlab.com/owner/repo/merge_requests/123",  # Different host
            "not-a-url",  # Invalid URL
            "https://github.com/owner/pull/123",  # Missing repo
            "https://github.com/owner/repo/pull/abc",  # Non-numeric PR
        ]

        for url in invalid_urls:
            with pytest.raises(ValueError, match="Invalid GitHub PR URL"):
                parse_github_pr_url(url)

    def test_parse_github_pr_url_empty_or_none_raises_error(self):
        """Test that empty or None URL raises ValueError."""
        from github_pr_integration import parse_github_pr_url

        with pytest.raises(ValueError, match="URL cannot be empty"):
            parse_github_pr_url("")

        with pytest.raises(ValueError, match="URL cannot be empty"):
            parse_github_pr_url(None)  # type: ignore


class TestGitHubAPIIntegration:
    """Test GitHub API integration functionality."""

    def test_fetch_pr_data_success(self):
        """Test successful PR data retrieval from GitHub API."""
        from github_pr_integration import fetch_pr_data

        # Mock data based on real GitHub API response structure
        # (based on https://github.com/nicobailon/gemini-code-review-mcp/pull/3)
        mock_response_data = {
            "url": "https://api.github.com/repos/testowner/testrepo/pulls/123",
            "id": 2553516570,
            "html_url": "https://github.com/testowner/testrepo/pull/123",
            "number": 123,
            "state": "open",
            "title": "Add new feature implementation",
            "user": {"login": "testuser"},
            "body": "This PR adds a new feature to improve functionality",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "head": {"ref": "feature/new-feature", "sha": "abc123def456789"},
            "base": {"ref": "master", "sha": "def456ghi789abc"},
        }

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response

            result = fetch_pr_data("testowner", "testrepo", 123, "test_token")

            assert result["pr_number"] == 123
            assert result["title"] == "Add new feature implementation"
            assert result["author"] == "testuser"
            assert result["source_branch"] == "feature/new-feature"
            assert result["target_branch"] == "master"
            assert result["state"] == "open"
            assert result["created_at"] == "2024-01-01T00:00:00Z"
            assert result["updated_at"] == "2024-01-02T00:00:00Z"
            assert result["url"] == "https://github.com/testowner/testrepo/pull/123"

    def test_fetch_pr_data_with_authentication_header(self):
        """Test that authentication token is properly included in request."""
        from github_pr_integration import fetch_pr_data

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "url": "https://api.github.com/repos/owner/repo/pulls/123",
                "id": 2553516570,
                "html_url": "https://github.com/owner/repo/pull/123",
                "number": 123,
                "state": "open",
                "title": "Test authentication",
                "user": {"login": "test_user"},
                "body": "Test description",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
                "head": {"ref": "feature/test", "sha": "abc123def"},
                "base": {"ref": "main", "sha": "def456ghi"},
            }
            mock_get.return_value = mock_response

            fetch_pr_data("owner", "repo", 123, "test_token_123")

            # Verify request was made with correct authentication
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == "token test_token_123"
            assert headers["Accept"] == "application/vnd.github.v3+json"

    def test_fetch_pr_data_handles_404_not_found(self):
        """Test handling when PR is not found (404 error)."""
        from github_pr_integration import fetch_pr_data

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            mock_get.return_value = mock_response

            with pytest.raises(ValueError, match="PR not found"):
                fetch_pr_data("owner", "repo", 999, "token")

    def test_fetch_pr_data_handles_403_forbidden(self):
        """Test handling when access is forbidden (403 error)."""
        from github_pr_integration import fetch_pr_data

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.text = "Forbidden"
            mock_get.return_value = mock_response

            with pytest.raises(ValueError, match="Access forbidden"):
                fetch_pr_data("owner", "repo", 123, "invalid_token")

    def test_fetch_pr_data_handles_rate_limiting(self):
        """Test handling of GitHub API rate limiting."""
        from github_pr_integration import fetch_pr_data

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.headers = {"X-RateLimit-Remaining": "0"}
            mock_response.text = "Rate limit exceeded"
            mock_get.return_value = mock_response

            with pytest.raises(ValueError, match="Rate limit exceeded"):
                fetch_pr_data("owner", "repo", 123, "token")

    def test_fetch_pr_data_handles_network_timeout(self):
        """Test handling of network timeout errors."""
        from github_pr_integration import fetch_pr_data

        with patch("requests.get") as mock_get:
            import requests

            mock_get.side_effect = requests.Timeout("Request timed out")

            with pytest.raises(ValueError, match="Network timeout"):
                fetch_pr_data("owner", "repo", 123, "token")

    def test_fetch_pr_data_handles_connection_error(self):
        """Test handling of network connection errors."""
        from github_pr_integration import fetch_pr_data

        with patch("requests.get") as mock_get:
            import requests

            mock_get.side_effect = requests.ConnectionError("Connection failed")

            with pytest.raises(ValueError, match="Network connection failed"):
                fetch_pr_data("owner", "repo", 123, "token")


class TestPRFileChanges:
    """Test PR file changes retrieval functionality."""

    def test_get_pr_file_changes_success(self):
        """Test successful retrieval of PR file changes."""
        from github_pr_integration import get_pr_file_changes

        # Mock API response for PR files
        mock_files_data = [
            {
                "filename": "src/main.py",
                "status": "modified",
                "additions": 10,
                "deletions": 5,
                "changes": 15,
                "patch": "@@ -1,3 +1,4 @@\n+import os\n import sys\n def main():\n-    pass\n+    print('Hello')",
            },
            {
                "filename": "tests/test_main.py",
                "status": "added",
                "additions": 20,
                "deletions": 0,
                "changes": 20,
                "patch": "@@ -0,0 +1,20 @@\n+import pytest\n+def test_main():\n+    assert True",
            },
            {
                "filename": "old_file.py",
                "status": "removed",
                "additions": 0,
                "deletions": 30,
                "changes": 30,
                "patch": "@@ -1,30 +0,0 @@\n-# This file is being deleted\n-def old_function():\n-    pass\n-# ... (30 lines deleted)",
            },
        ]

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_files_data
            mock_get.return_value = mock_response

            result = get_pr_file_changes("owner", "repo", 123, "token")

            assert len(result["changed_files"]) == 3

            # Check modified file
            modified_file = next(
                f for f in result["changed_files"] if f["status"] == "modified"
            )
            assert modified_file["path"] == "src/main.py"
            assert modified_file["additions"] == 10
            assert modified_file["deletions"] == 5
            assert "import os" in modified_file["patch"]

            # Check added file
            added_file = next(
                f for f in result["changed_files"] if f["status"] == "added"
            )
            assert added_file["path"] == "tests/test_main.py"
            assert added_file["additions"] == 20

            # Check deleted file
            deleted_file = next(
                f for f in result["changed_files"] if f["status"] == "removed"
            )
            assert deleted_file["path"] == "old_file.py"
            # Real GitHub API returns patch data for deleted files, not None
            assert deleted_file["patch"] is not None

    def test_get_pr_file_changes_includes_statistics(self):
        """Test that file changes include summary statistics."""
        from github_pr_integration import get_pr_file_changes

        mock_files_data = [
            {
                "filename": "file1.py",
                "status": "modified",
                "additions": 5,
                "deletions": 2,
                "changes": 7,
            },
            {
                "filename": "file2.py",
                "status": "added",
                "additions": 15,
                "deletions": 0,
                "changes": 15,
            },
            {
                "filename": "file3.py",
                "status": "removed",
                "additions": 0,
                "deletions": 10,
                "changes": 10,
            },
        ]

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_files_data
            mock_get.return_value = mock_response

            result = get_pr_file_changes("owner", "repo", 123, "token")

            summary = result["summary"]
            assert summary["files_changed"] == 3
            assert summary["files_added"] == 1
            assert summary["files_modified"] == 1
            assert summary["files_deleted"] == 1
            assert summary["total_additions"] == 20
            assert summary["total_deletions"] == 12

    def test_get_pr_file_changes_handles_binary_files(self):
        """Test handling of binary files in PR changes."""
        from github_pr_integration import get_pr_file_changes

        mock_files_data = [
            {
                "filename": "image.png",
                "status": "added",
                "additions": 0,
                "deletions": 0,
                "changes": 0,
                "patch": None,  # Binary files don't have patches
            }
        ]

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_files_data
            mock_get.return_value = mock_response

            result = get_pr_file_changes("owner", "repo", 123, "token")

            binary_file = result["changed_files"][0]
            assert binary_file["path"] == "image.png"
            assert binary_file["patch"] == "[Binary file]"

    def test_get_pr_file_changes_handles_api_errors(self):
        """Test error handling for PR files API failures."""
        from github_pr_integration import get_pr_file_changes

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_get.return_value = mock_response

            with pytest.raises(ValueError, match="Failed to fetch PR file changes"):
                get_pr_file_changes("owner", "repo", 123, "token")


class TestAuthenticationHandling:
    """Test GitHub authentication handling."""

    def test_validate_github_token_valid_token(self):
        """Test validation of valid GitHub token."""
        from github_pr_integration import validate_github_token

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"login": "username"}
            mock_get.return_value = mock_response

            result = validate_github_token("valid_token")

            assert result is True
            # Verify correct API endpoint was called
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "user" in call_args[0][0]  # /user endpoint

    def test_validate_github_token_invalid_token(self):
        """Test validation of invalid GitHub token."""
        from github_pr_integration import validate_github_token

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response

            result = validate_github_token("invalid_token")

            assert result is False

    def test_get_github_token_from_environment(self):
        """Test retrieving GitHub token from environment variables."""
        from github_pr_integration import get_github_token

        with patch.dict(os.environ, {"GITHUB_TOKEN": "env_token_123"}):
            token = get_github_token()
            assert token == "env_token_123"

    def test_get_github_token_from_git_config(self):
        """Test retrieving GitHub token from git config."""
        from github_pr_integration import get_github_token

        with patch.dict(os.environ, {}, clear=True):  # Clear env vars
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.stdout = "git_config_token_456\n"
                mock_run.return_value.returncode = 0

                token = get_github_token()
                assert token == "git_config_token_456"

    def test_get_github_token_no_token_found(self):
        """Test behavior when no GitHub token is found."""
        from github_pr_integration import get_github_token

        with patch.dict(os.environ, {}, clear=True):  # Clear env vars
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, "git")

                token = get_github_token()
                assert token is None


class TestErrorHandlingAndEdgeCases:
    """Test comprehensive error handling and edge cases."""

    def test_github_enterprise_url_handling(self):
        """Test proper handling of GitHub Enterprise URLs."""
        from github_pr_integration import fetch_pr_data, parse_github_pr_url

        enterprise_url = "https://github.mycompany.com/team/project/pull/42"
        parsed = parse_github_pr_url(enterprise_url)

        assert parsed["base_url"] == "https://github.mycompany.com"

        # Verify API calls use correct base URL
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "url": "https://github.mycompany.com/api/v3/repos/team/project/pulls/42",
                "id": 2553516570,
                "html_url": "https://github.mycompany.com/team/project/pull/42",
                "number": 42,
                "state": "open",
                "title": "Enterprise feature implementation",
                "user": {"login": "enterprise_user"},
                "body": "Enterprise PR description",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
                "head": {"ref": "feature/enterprise", "sha": "abc123def"},
                "base": {"ref": "main", "sha": "def456ghi"},
            }
            mock_get.return_value = mock_response

            fetch_pr_data(
                "team", "project", 42, "token", base_url="https://github.mycompany.com"
            )

            # Verify enterprise API endpoint was called
            call_args = mock_get.call_args
            assert "github.mycompany.com" in call_args[0][0]

    def test_large_pr_handling(self):
        """Test handling of PRs with many file changes."""
        from github_pr_integration import get_pr_file_changes

        # Mock large PR with 100+ files
        mock_files: List[Dict[str, Any]] = []
        for i in range(150):
            mock_files.append(
                {
                    "filename": f"file_{i}.py",
                    "status": "modified",
                    "additions": 1,
                    "deletions": 1,
                    "changes": 2,
                    "patch": f"@@ -1,1 +1,1 @@\n-old_line_{i}\n+new_line_{i}",
                }
            )

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_files
            mock_get.return_value = mock_response

            result = get_pr_file_changes("owner", "repo", 123, "token")

            assert len(result["changed_files"]) == 150
            assert result["summary"]["files_changed"] == 150

    def test_special_characters_in_filenames(self):
        """Test handling of files with special characters in names."""
        from github_pr_integration import get_pr_file_changes

        mock_files_data = [
            {
                "filename": "files/测试.py",  # Chinese characters
                "status": "added",
                "additions": 1,
                "deletions": 0,
                "changes": 1,
                "patch": "@@ -0,0 +1,1 @@\n+# Test file",
            },
            {
                "filename": "files/file with spaces.js",  # Spaces
                "status": "modified",
                "additions": 1,
                "deletions": 1,
                "changes": 2,
                "patch": "@@ -1,1 +1,1 @@\n-old\n+new",
            },
            {
                "filename": "files/file-with-émojis-🚀.md",  # Emojis and accents
                "status": "modified",
                "additions": 1,
                "deletions": 0,
                "changes": 1,
                "patch": "@@ -1,1 +1,2 @@\n# Header\n+🚀 New content",
            },
        ]

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_files_data
            mock_get.return_value = mock_response

            result = get_pr_file_changes("owner", "repo", 123, "token")

            file_paths = [f["path"] for f in result["changed_files"]]
            assert "files/测试.py" in file_paths
            assert "files/file with spaces.js" in file_paths
            assert "files/file-with-émojis-🚀.md" in file_paths


class TestIntegrationScenarios:
    """Test realistic end-to-end integration scenarios."""

    def test_complete_pr_analysis_workflow(self):
        """Test complete workflow of analyzing a GitHub PR."""
        from github_pr_integration import (
            fetch_pr_data,
            get_pr_file_changes,
            parse_github_pr_url,
        )

        # Test complete workflow
        pr_url = "https://github.com/microsoft/vscode/pull/42"

        # Step 1: Parse URL
        parsed = parse_github_pr_url(pr_url)
        assert parsed["owner"] == "microsoft"
        assert parsed["repo"] == "vscode"
        assert parsed["pr_number"] == 42

        # Step 2: Fetch PR data
        with patch("requests.get") as mock_get:

            def mock_response_side_effect(url: str, **kwargs: Any) -> MagicMock:
                mock_response = MagicMock()
                mock_response.status_code = 200

                if "/pulls/42" in url and "/files" not in url:
                    # PR metadata endpoint - based on real GitHub API structure
                    mock_response.json.return_value = {
                        "url": "https://api.github.com/repos/microsoft/vscode/pulls/42",
                        "id": 2553516570,
                        "html_url": "https://github.com/microsoft/vscode/pull/42",
                        "number": 42,
                        "state": "open",
                        "title": "Add new feature",
                        "user": {"login": "contributor"},
                        "body": "Description of changes",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-02T00:00:00Z",
                        "head": {"ref": "feature/new-feature", "sha": "abc123def"},
                        "base": {"ref": "main", "sha": "def456ghi"},
                    }
                elif "/pulls/42/files" in url:
                    # PR files endpoint
                    mock_response.json.return_value = [
                        {
                            "filename": "src/feature.py",
                            "status": "added",
                            "additions": 50,
                            "deletions": 0,
                            "changes": 50,
                            "patch": "@@ -0,0 +1,50 @@\n+def new_feature():\n+    return True",
                        }
                    ]

                return mock_response

            mock_get.side_effect = mock_response_side_effect

            # Fetch PR metadata
            pr_data = fetch_pr_data("microsoft", "vscode", 42, "token")
            assert pr_data["title"] == "Add new feature"
            assert pr_data["source_branch"] == "feature/new-feature"

            # Fetch PR file changes
            file_changes = get_pr_file_changes("microsoft", "vscode", 42, "token")
            assert len(file_changes["changed_files"]) == 1
            assert file_changes["changed_files"][0]["path"] == "src/feature.py"


# Import subprocess for use in tests
import subprocess


class TestThinkingBudgetIntegration:
    """Test thinking budget parameter integration with GitHub PR context."""

    def test_pr_context_with_thinking_budget_param(self):
        """Test that PR context generation can accept thinking_budget parameter."""
        from src.config_types import CodeReviewConfig

        # Create config with thinking_budget
        config = CodeReviewConfig(
            project_path="/tmp/test",
            github_pr_url="https://github.com/owner/repo/pull/123",
            thinking_budget=15000,
            temperature=0.7,
        )

        # Verify config accepts thinking_budget
        assert config.thinking_budget == 15000
        assert hasattr(config, "url_context")


if __name__ == "__main__":
    pytest.main([__file__])
