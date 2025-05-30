"""
Git Branch Comparison Module

Provides functionality for comparing git branches and detecting branch information.
"""

import subprocess
import os
import re
from typing import Dict, List, Optional, Any


def detect_primary_branch(repo_path: str) -> str:
    """
    Detect the primary branch (main or master) in a git repository.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        Name of primary branch ('main' or 'master')
        
    Raises:
        ValueError: If primary branch cannot be detected or git fails
    """
    try:
        result = subprocess.run(
            ['git', 'branch', '-a'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        branches = result.stdout.strip().split('\n')
        branch_names = [branch.strip().lstrip('* ').strip() for branch in branches]
        
        # Prefer 'main' over 'master'
        if 'main' in branch_names:
            return 'main'
        elif 'master' in branch_names:
            return 'master'
        else:
            raise ValueError("No primary branch found (neither 'main' nor 'master' exists)")
            
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Failed to detect primary branch: {e}")


def validate_branch_exists(repo_path: str, branch_name: str) -> bool:
    """
    Validate that a branch exists in the repository.
    
    Args:
        repo_path: Path to the git repository
        branch_name: Name of the branch to validate
        
    Returns:
        True if branch exists, False otherwise
        
    Raises:
        ValueError: If git command fails with unexpected error
    """
    try:
        result = subprocess.run(
            ['git', 'show-ref', '--verify', '--quiet', f'refs/heads/{branch_name}'],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        return result.returncode == 0
        
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            # Branch doesn't exist - this is expected
            return False
        else:
            # Other git error
            raise ValueError(f"Git error validating branch '{branch_name}': {e}")


def validate_repository(repo_path: str) -> bool:
    """
    Validate that a directory is a valid git repository.
    
    Args:
        repo_path: Path to validate
        
    Returns:
        True if valid git repository, False otherwise
        
    Raises:
        ValueError: If path doesn't exist
    """
    if not os.path.exists(repo_path):
        raise ValueError(f"Repository path does not exist: {repo_path}")
    
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        return result.returncode == 0
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_branch_diff(repo_path: str, source_branch: str, target_branch: str) -> Dict[str, Any]:
    """
    Get diff information between two branches.
    
    Args:
        repo_path: Path to the git repository
        source_branch: Source branch to compare from
        target_branch: Target branch to compare against
        
    Returns:
        Dictionary containing diff information, file changes, and statistics
        
    Raises:
        ValueError: If git commands fail or branches are invalid
    """
    try:
        # Get file changes
        diff_result = subprocess.run(
            ['git', 'diff', '--name-status', f'{target_branch}...{source_branch}'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        changed_files = []
        files_added = 0
        files_modified = 0 
        files_deleted = 0
        
        if diff_result.stdout.strip():
            for line in diff_result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t', 1)
                    if len(parts) == 2:
                        status, file_path = parts
                        
                        # Get file content for non-deleted files
                        content = "[Binary file or content not available]"
                        if status != 'D':
                            try:
                                content_result = subprocess.run(
                                    ['git', 'show', f'{source_branch}:{file_path}'],
                                    cwd=repo_path,
                                    capture_output=True,
                                    text=True,
                                    check=True
                                )
                                content = content_result.stdout
                            except (subprocess.CalledProcessError, UnicodeDecodeError):
                                content = "[Binary file or content not available]"
                        else:
                            content = "[File deleted]"
                        
                        changed_files.append({
                            'status': status,
                            'path': file_path,
                            'content': content
                        })
                        
                        # Update statistics
                        if status == 'A':
                            files_added += 1
                        elif status == 'M':
                            files_modified += 1
                        elif status == 'D':
                            files_deleted += 1
        
        # Get commit information - try detailed format first, fallback to simple
        commits = []
        
        # Try detailed commit log first
        try:
            log_result = subprocess.run(
                ['git', 'log', '--pretty=format:%H|%h|%s|%an|%ad|%ar', '--date=iso', f'{target_branch}..{source_branch}'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            if log_result.stdout.strip():
                for line in log_result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('|')
                        if len(parts) >= 6:
                            commits.append({
                                'hash': parts[1],  # Short hash
                                'full_hash': parts[0],  # Full hash
                                'message': parts[2],
                                'author': parts[3],
                                'date': parts[4],
                                'date_relative': parts[5]
                            })
        except subprocess.CalledProcessError:
            # Fallback to simple log format
            try:
                log_result = subprocess.run(
                    ['git', 'log', '--oneline', f'{target_branch}..{source_branch}'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                if log_result.stdout.strip():
                    for line in log_result.stdout.strip().split('\n'):
                        if line:
                            parts = line.split(' ', 1)
                            if len(parts) == 2:
                                commits.append({
                                    'hash': parts[0],
                                    'message': parts[1]
                                })
            except subprocess.CalledProcessError:
                # No commits or git log failed - that's OK, leave commits empty
                pass
        
        return {
            'source_branch': source_branch,
            'target_branch': target_branch,
            'changed_files': changed_files,
            'commits': commits,
            'summary': {
                'files_changed': len(changed_files),
                'files_added': files_added,
                'files_modified': files_modified,
                'files_deleted': files_deleted
            }
        }
        
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Failed to compare branches '{source_branch}' and '{target_branch}': {e}")
    except FileNotFoundError:
        raise ValueError("Git is not available on this system")