import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..progress import progress
from .git_client import GitClient, GitCommit, GitFileChange


class ProductionGitClient(GitClient):
    """Production implementation of GitClient using actual git commands."""

    def _run_git_command(self, cmd: List[str], cwd: Union[str, Path]) -> str:
        """Run a git command and return output."""
        try:
            result = subprocess.run(
                ["git"] + cmd, cwd=str(cwd), capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git command failed: {e.stderr}")

    def is_git_repo(self, path: Union[str, Path]) -> bool:
        try:
            self._run_git_command(["rev-parse", "--git-dir"], path)
            return True
        except RuntimeError:
            return False

    def get_repo_root(self, path: Union[str, Path]) -> Optional[Path]:
        try:
            root = self._run_git_command(["rev-parse", "--show-toplevel"], path)
            return Path(root)
        except RuntimeError:
            return None

    def get_current_branch(self, repo_path: Union[str, Path]) -> str:
        return self._run_git_command(["branch", "--show-current"], repo_path)

    def get_changed_files(
        self,
        repo_path: Union[str, Path],
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
        include_untracked: bool = True,
    ) -> List[GitFileChange]:
        changes: List[GitFileChange] = []
        
        # Use progress indicator for long-running git operations
        with progress("Analyzing Git changes") as p:

            if base_ref and head_ref:
                # Compare two refs
                p.update(f"Comparing {base_ref}...{head_ref}")
                output = self._run_git_command(
                    ["diff", "--numstat", f"{base_ref}...{head_ref}"], repo_path
                )
                for line in output.splitlines():
                    if line:
                        parts = line.split("\t")
                        if len(parts) >= 3:
                            additions = int(parts[0]) if parts[0] != "-" else 0
                            deletions = int(parts[1]) if parts[1] != "-" else 0
                            file_path = parts[2]
                            changes.append(
                                GitFileChange(
                                    file_path=file_path,
                                    status="Modified",
                                    additions=additions,
                                    deletions=deletions,
                                )
                            )
            else:
                # Get staged changes
                p.update("Checking staged changes")
                output = self._run_git_command(["diff", "--cached", "--numstat"], repo_path)
                for line in output.splitlines():
                    if line:
                        parts = line.split("\t")
                        if len(parts) >= 3:
                            additions = int(parts[0]) if parts[0] != "-" else 0
                            deletions = int(parts[1]) if parts[1] != "-" else 0
                            file_path = parts[2]
                            changes.append(
                                GitFileChange(
                                    file_path=file_path,
                                    status="Modified",
                                    additions=additions,
                                    deletions=deletions,
                                )
                            )

                # Get unstaged changes
                p.update("Checking unstaged changes")
                output = self._run_git_command(["diff", "--numstat"], repo_path)
                for line in output.splitlines():
                    if line:
                        parts = line.split("\t")
                        if len(parts) >= 3:
                            file_path = parts[2]
                            # Check if already in staged changes
                            if not any(c.file_path == file_path for c in changes):
                                additions = int(parts[0]) if parts[0] != "-" else 0
                                deletions = int(parts[1]) if parts[1] != "-" else 0
                                changes.append(
                                    GitFileChange(
                                    file_path=file_path,
                                    status="Modified",
                                    additions=additions,
                                    deletions=deletions,
                                )
                            )

                # Get untracked files if requested
                if include_untracked:
                    p.update("Checking untracked files")
                    output = self._run_git_command(
                        ["ls-files", "--others", "--exclude-standard"], repo_path
                    )
                    for line in output.splitlines():
                        if line:
                            changes.append(
                                GitFileChange(
                                    file_path=line, status="Added", additions=0, deletions=0
                                )
                            )

        return changes

    def get_file_diff(
        self,
        repo_path: Union[str, Path],
        file_path: str,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
    ) -> str:
        if base_ref and head_ref:
            return self._run_git_command(
                ["diff", f"{base_ref}...{head_ref}", "--", file_path], repo_path
            )
        else:
            # Get both staged and unstaged changes
            staged = self._run_git_command(
                ["diff", "--cached", "--", file_path], repo_path
            )
            unstaged = self._run_git_command(["diff", "--", file_path], repo_path)
            return f"{staged}\n{unstaged}".strip()

    def get_commits(
        self, repo_path: Union[str, Path], branch: Optional[str] = None, limit: int = 10
    ) -> List[GitCommit]:
        cmd = ["log", f"-{limit}", "--pretty=format:%H|%an|%ad|%s", "--date=iso"]
        if branch:
            cmd.append(branch)

        output = self._run_git_command(cmd, repo_path)
        commits: List[GitCommit] = []

        for line in output.splitlines():
            if line:
                parts = line.split("|", 3)
                if len(parts) == 4:
                    commits.append(
                        GitCommit(
                            sha=parts[0],
                            author=parts[1],
                            date=parts[2],
                            message=parts[3],
                        )
                    )

        return commits

    def get_remote_url(
        self, repo_path: Union[str, Path], remote: str = "origin"
    ) -> Optional[str]:
        try:
            return self._run_git_command(["remote", "get-url", remote], repo_path)
        except RuntimeError:
            return None

    def get_file_content(
        self, repo_path: Union[str, Path], file_path: str, ref: Optional[str] = None
    ) -> Optional[str]:
        try:
            if ref:
                return self._run_git_command(["show", f"{ref}:{file_path}"], repo_path)
            else:
                # Read from working tree
                full_path = Path(repo_path) / file_path
                if full_path.exists():
                    return full_path.read_text()
                return None
        except RuntimeError:
            return None


class InMemoryGitClient(GitClient):
    """In-memory implementation of GitClient for testing."""

    def __init__(self):
        self._repos: Dict[str, Dict[str, Any]] = {}

    def setup_repo(
        self,
        repo_path: str,
        current_branch: str = "main",
        files: Optional[Dict[str, str]] = None,
        changes: Optional[List[GitFileChange]] = None,
        commits: Optional[List[GitCommit]] = None,
    ):
        """Set up a fake repository for testing."""
        self._repos[repo_path] = {
            "current_branch": current_branch,
            "files": files or {},
            "changes": changes or [],
            "commits": commits or [],
            "remotes": {"origin": "https://github.com/test/repo.git"},
        }

    def is_git_repo(self, path: Union[str, Path]) -> bool:
        path_str = str(Path(path).resolve())
        return any(path_str.startswith(repo_path) for repo_path in self._repos)

    def get_repo_root(self, path: Union[str, Path]) -> Optional[Path]:
        path_str = str(Path(path).resolve())
        for repo_path in self._repos:
            if path_str.startswith(repo_path):
                return Path(repo_path)
        return None

    def get_current_branch(self, repo_path: Union[str, Path]) -> str:
        repo_path_str = str(Path(repo_path).resolve())
        if repo_path_str in self._repos:
            return self._repos[repo_path_str]["current_branch"]
        raise RuntimeError(f"Not a git repository: {repo_path}")

    def get_changed_files(
        self,
        repo_path: Union[str, Path],
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
        include_untracked: bool = True,
    ) -> List[GitFileChange]:
        repo_path_str = str(Path(repo_path).resolve())
        if repo_path_str in self._repos:
            return self._repos[repo_path_str]["changes"]
        return []

    def get_file_diff(
        self,
        repo_path: Union[str, Path],
        file_path: str,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
    ) -> str:
        return (
            f"diff --git a/{file_path} b/{file_path}\n+++ Added line\n--- Removed line"
        )

    def get_commits(
        self, repo_path: Union[str, Path], branch: Optional[str] = None, limit: int = 10
    ) -> List[GitCommit]:
        repo_path_str = str(Path(repo_path).resolve())
        if repo_path_str in self._repos:
            commits = self._repos[repo_path_str]["commits"]
            return commits[:limit]
        return []

    def get_remote_url(
        self, repo_path: Union[str, Path], remote: str = "origin"
    ) -> Optional[str]:
        repo_path_str = str(Path(repo_path).resolve())
        if repo_path_str in self._repos:
            return self._repos[repo_path_str]["remotes"].get(remote)
        return None

    def get_file_content(
        self, repo_path: Union[str, Path], file_path: str, ref: Optional[str] = None
    ) -> Optional[str]:
        repo_path_str = str(Path(repo_path).resolve())
        if repo_path_str in self._repos:
            return self._repos[repo_path_str]["files"].get(file_path)
        return None
