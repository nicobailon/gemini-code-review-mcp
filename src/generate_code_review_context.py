#!/usr/bin/env python3
"""
Generate code review context by parsing PRD, task lists, and git changes.

The script should:
1. Read PRD files (prd-*.md) from /tasks/ directory
2. Read task list files (tasks-prd-*.md) from /tasks/ directory  
3. Parse current phase and progress from task list
4. Extract or generate PRD summary (2-3 sentences)
5. Get git diff for changed files
6. Generate ASCII file tree
7. Format everything into markdown template
8. Save to /tasks/review-context-{timestamp}.md
"""

import re
import os
import sys
import subprocess
import argparse
import glob
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
# Load environment variables from .env file (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, continue without it

# Optional Gemini import
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_model_config() -> Dict[str, Any]:
    """Load model configuration from JSON file with fallback defaults."""
    config_path = os.path.join(os.path.dirname(__file__), 'model_config.json')
    
    # Default configuration as fallback
    default_config = {
        "model_aliases": {
            "gemini-2.5-pro": "gemini-2.5-pro-preview-05-06",
            "gemini-2.5-flash": "gemini-2.5-flash-preview-05-20"
        },
        "model_capabilities": {
            "url_context_supported": [
                "gemini-2.5-pro-preview-05-06", "gemini-2.5-flash-preview-05-20",
                "gemini-2.0-flash", "gemini-2.0-flash-live-001", "gemini-2.5-flash"
            ],
            "thinking_mode_supported": [
                "gemini-2.5-pro-preview-05-06", "gemini-2.5-flash-preview-05-20"
            ]
        },
        "defaults": {
            "model": "gemini-2.0-flash",
            "summary_model": "gemini-2.0-flash-lite",
            "default_prompt": "Generate comprehensive code review for recent development changes focusing on code quality, security, performance, and best practices."
        }
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        else:
            logger.warning(f"Model config file not found at {config_path}, using defaults")
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load model config: {e}, using defaults")
    
    return default_config


def load_api_key() -> Optional[str]:
    """Load API key with multiple fallback strategies for uvx compatibility"""
    from pathlib import Path
    
    # Strategy 1: Direct environment variables
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if api_key:
        logger.debug("API key loaded from environment variable")
        return api_key
    
    # Strategy 2: .env file in current directory
    env_file = Path('.env')
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if api_key:
                logger.debug("API key loaded from .env file")
                return api_key
        except ImportError:
            logger.debug("python-dotenv not available, skipping .env file")
    
    # Strategy 3: User's home directory .env file
    home_env = Path.home() / '.task-list-code-review-mcp.env'
    if home_env.exists():
        try:
            api_key = home_env.read_text().strip()
            if api_key:
                logger.debug(f"API key loaded from {home_env}")
                return api_key
        except IOError:
            pass
    
    return None


def suggest_path_corrections(provided_path: str, expected_type: str = "project") -> str:
    """
    Generate helpful path correction suggestions based on common mistakes.
    
    Args:
        provided_path: The path the user provided
        expected_type: Type of path expected ("project", "file", "directory")
    
    Returns:
        String with suggestion messages
    """
    suggestions = []
    current_dir = os.getcwd()
    
    # Check if path exists but is wrong type
    if os.path.exists(provided_path):
        if expected_type == "project" and os.path.isfile(provided_path):
            parent_dir = os.path.dirname(provided_path)
            suggestions.append(f"  # You provided a file, try the parent directory instead:")
            suggestions.append(f"  generate-code-review {parent_dir if parent_dir else '.'}")
    else:
        # Path doesn't exist - suggest common corrections
        abs_path = os.path.abspath(provided_path)
        parent_dir = os.path.dirname(abs_path)
        
        # Check if parent exists
        if os.path.exists(parent_dir):
            suggestions.append(f"  # Parent directory exists. Maybe there's a typo?")
            similar_items = []
            try:
                for item in os.listdir(parent_dir):
                    if item.lower().startswith(os.path.basename(provided_path).lower()[:3]):
                        similar_items.append(item)
                if similar_items:
                    suggestions.append(f"  # Similar items found: {', '.join(similar_items[:3])}")
                    suggestions.append(f"  generate-code-review {os.path.join(parent_dir, similar_items[0])}")
            except PermissionError:
                suggestions.append(f"  # Permission denied accessing {parent_dir}")
        
        # Check if it's a relative path issue
        basename = os.path.basename(provided_path)
        for root, dirs, files in os.walk(current_dir):
            if basename in dirs:
                rel_path = os.path.relpath(os.path.join(root, basename), current_dir)
                suggestions.append(f"  # Found similar directory:")
                suggestions.append(f"  generate-code-review {rel_path}")
                break
            if len(suggestions) > 6:  # Limit suggestions
                break
        
        # Common path corrections
        if provided_path.startswith('/'):
            suggestions.append(f"  # Try relative path instead:")
            suggestions.append(f"  generate-code-review ./{os.path.basename(provided_path)}")
        else:
            suggestions.append(f"  # Try absolute path:")
            suggestions.append(f"  generate-code-review {abs_path}")
    
    # Check for common project structure issues
    if expected_type == "project":
        tasks_path = os.path.join(provided_path, 'tasks') if os.path.exists(provided_path) else None
        if tasks_path and not os.path.exists(tasks_path):
            suggestions.append(f"  # Directory exists but missing tasks/ folder:")
            suggestions.append(f"  mkdir {tasks_path}")
            suggestions.append(f"  # Then add PRD and task files to tasks/")
    
    return '\n'.join(suggestions) if suggestions else "  # Check the path and try again"


def require_api_key():
    """Ensure API key is available with uvx-specific guidance"""
    api_key = load_api_key()
    
    if not api_key:
        error_msg = """
🔑 GEMINI_API_KEY not found. Choose the setup method that works for your environment:

📋 QUICKSTART (Recommended):
   # 1. Get API key: https://ai.google.dev/gemini-api/docs/api-key
   # 2. Set environment variable:
   export GEMINI_API_KEY=your_key_here
   
   # 3. Run tool:
   generate-code-review .

🔧 FOR UVX USERS:
   # Method 1: Environment variable prefix (most reliable)
   GEMINI_API_KEY=your_key uvx task-list-code-review-mcp generate-code-review .
   
   # Method 2: Create project .env file
   echo "GEMINI_API_KEY=your_key_here" > .env
   uvx task-list-code-review-mcp generate-code-review .
   
   # Method 3: Global user config
   echo "GEMINI_API_KEY=your_key_here" > ~/.task-list-code-review-mcp.env
   uvx task-list-code-review-mcp generate-code-review .

📝 FOR MCP SERVER USERS:
   Add to your Claude Desktop configuration:
   {
     "mcpServers": {
       "task-list-reviewer": {
         "command": "uvx",
         "args": ["task-list-code-review-mcp"],
         "env": {
           "GEMINI_API_KEY": "your_key_here"
         }
       }
     }
   }

🚨 TROUBLESHOOTING:
   # Check if environment variable is set:
   echo $GEMINI_API_KEY
   
   # Test API key with minimal command:
   GEMINI_API_KEY=your_key uvx task-list-code-review-mcp generate-code-review . --no-gemini
   
   # Verify current directory structure:
   ls -la tasks/

🌐 Get your API key: https://ai.google.dev/gemini-api/docs/api-key
"""
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    return api_key


def parse_task_list(content: str) -> Dict[str, Any]:
    """
    Parse task list content and extract phase information.
    
    Args:
        content: Raw markdown content of task list
        
    Returns:
        Dictionary with phase information
    """
    lines = content.strip().split('\n')
    phases = []
    current_phase = None
    
    # Phase pattern: ^- \[([ x])\] (\d+\.\d+) (.+)$
    phase_pattern = r'^- \[([ x])\] (\d+\.\d+) (.+)$'
    # Subtask pattern: ^  - \[([ x])\] (\d+\.\d+) (.+)$
    subtask_pattern = r'^  - \[([ x])\] (\d+\.\d+) (.+)$'
    
    for line in lines:
        phase_match = re.match(phase_pattern, line)
        if phase_match:
            completed = phase_match.group(1) == 'x'
            number = phase_match.group(2)
            description = phase_match.group(3).strip()
            
            current_phase = {
                'number': number,
                'description': description,
                'completed': completed,
                'subtasks': [],
                'subtasks_completed': []
            }
            phases.append(current_phase)
            continue
            
        subtask_match = re.match(subtask_pattern, line)
        if subtask_match and current_phase:
            completed = subtask_match.group(1) == 'x'
            number = subtask_match.group(2)
            description = subtask_match.group(3).strip()
            
            current_phase['subtasks'].append({
                'number': number,
                'description': description,
                'completed': completed
            })
            
            if completed:
                current_phase['subtasks_completed'].append(f"{number} {description}")
    
    # Determine if each phase is complete (all subtasks complete)
    for phase in phases:
        if phase['subtasks']:
            phase['subtasks_complete'] = all(st['completed'] for st in phase['subtasks'])
        else:
            phase['subtasks_complete'] = phase['completed']
    
    return {
        'total_phases': len(phases),
        'phases': phases,
        **detect_current_phase(phases)
    }


def detect_current_phase(phases: List[Dict]) -> Dict[str, Any]:
    """
    Detect the most recently completed phase for code review.
    
    The logic prioritizes reviewing completed phases over in-progress ones:
    1. Find the most recently completed phase (all subtasks done)
    2. If no phases are complete, fall back to the current in-progress phase
    3. If all phases are complete, use the last phase
    
    Args:
        phases: List of phase dictionaries
        
    Returns:
        Dictionary with phase information for code review
    """
    if not phases:
        return {
            'current_phase_number': '',
            'current_phase_description': '',
            'previous_phase_completed': '',
            'next_phase': '',
            'subtasks_completed': []
        }
    
    # Find the most recently completed phase (all subtasks complete)
    review_phase = None
    for i in range(len(phases) - 1, -1, -1):  # Start from the end
        phase = phases[i]
        if phase['subtasks_complete'] and phase['subtasks']:
            review_phase = phase
            break
    
    # If no completed phases found, find first phase with incomplete subtasks
    if review_phase is None:
        for phase in phases:
            if not phase['subtasks_complete']:
                review_phase = phase
                break
    
    # If all phases complete or no phases found, use last phase
    if review_phase is None:
        review_phase = phases[-1]
    
    # Find the index of the review phase
    review_idx = None
    for i, phase in enumerate(phases):
        if phase['number'] == review_phase['number']:
            review_idx = i
            break
    
    # Find previous completed phase
    previous_phase_completed = ''
    if review_idx is not None and review_idx > 0:
        prev_phase = phases[review_idx - 1]
        previous_phase_completed = f"{prev_phase['number']} {prev_phase['description']}"
    
    # Find next phase
    next_phase = ''
    if review_idx is not None and review_idx < len(phases) - 1:
        next_phase_obj = phases[review_idx + 1]
        next_phase = f"{next_phase_obj['number']} {next_phase_obj['description']}"
    
    return {
        'current_phase_number': review_phase['number'],
        'current_phase_description': review_phase['description'],
        'previous_phase_completed': previous_phase_completed,
        'next_phase': next_phase,
        'subtasks_completed': review_phase['subtasks_completed']
    }


def generate_prd_summary_from_task_list(task_data: Dict[str, Any]) -> str:
    """
    Generate a PRD-style summary from task list content.
    
    Args:
        task_data: Parsed task list data
        
    Returns:
        Generated project summary string
    """
    phases = task_data.get('phases', [])
    if not phases:
        return "Development project focused on code quality and feature implementation."
    
    # Extract high-level goals from phase descriptions
    phase_descriptions = [p.get('description', '') for p in phases]
    
    # Create a coherent summary
    if len(phases) == 1:
        summary = f"Development project focused on {phase_descriptions[0].lower()}."
    elif len(phases) <= 3:
        summary = f"Development project covering: {', '.join(phase_descriptions[:-1]).lower()}, and {phase_descriptions[-1].lower()}."
    else:
        key_phases = phase_descriptions[:3]
        summary = f"Multi-phase development project including {', '.join(key_phases).lower()}, and {len(phases)-3} additional phases."
    
    return summary


def extract_prd_summary(content: str) -> str:
    """
    Extract PRD summary using multiple strategies.
    
    Args:
        content: Raw markdown content of PRD
        
    Returns:
        Extracted or generated summary
    """
    # Strategy 1: Look for explicit summary sections
    summary_patterns = [
        r'## Summary\n(.+?)(?=\n##|\Z)',
        r'## Overview\n(.+?)(?=\n##|\Z)',
        r'### Summary\n(.+?)(?=\n###|\Z)',
        r'## Executive Summary\n(.+?)(?=\n##|\Z)'
    ]
    
    for pattern in summary_patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            summary = match.group(1).strip()
            # Clean up the summary (remove extra whitespace, newlines)
            summary = re.sub(r'\s+', ' ', summary)
            return summary
    
    # Strategy 2: Use Gemini if available and API key provided
    if GEMINI_AVAILABLE:
        try:
            api_key = load_api_key()
        except Exception:
            api_key = None
    else:
        api_key = None
        
    if GEMINI_AVAILABLE and api_key:
        try:
            client = genai.Client(api_key=api_key)
            first_2000_chars = content[:2000]
            
            # Use configurable model for PRD summarization
            config = load_model_config()
            summary_model = os.getenv('GEMINI_SUMMARY_MODEL', config['defaults']['summary_model'])
            
            response = client.models.generate_content(
                model=summary_model,
                contents=[f"Summarize this PRD in 2-3 sentences focusing on the main goal and key deliverables:\\n\\n{first_2000_chars}"],
                config=types.GenerateContentConfig(
                    max_output_tokens=150,
                    temperature=0.1
                )
            )
            
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Failed to generate LLM summary: {e}")
    
    # Strategy 3: Fallback - use first paragraph or first 200 characters
    lines = content.split('\n')
    content_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
    
    if content_lines:
        first_paragraph = content_lines[0]
        if len(first_paragraph) > 200:
            first_paragraph = first_paragraph[:200] + "..."
        return first_paragraph
    
    # Ultimate fallback
    return "No summary available."


def get_changed_files(project_path: str) -> List[Dict[str, str]]:
    """
    Get changed files from git with their content.
    
    Args:
        project_path: Path to project root
        
    Returns:
        List of changed file dictionaries
    """
    try:
        changed_files = []
        max_lines = int(os.getenv('MAX_FILE_CONTENT_LINES', '500'))
        debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        
        if debug_mode:
            logger.info(f"Debug mode enabled. Processing max {max_lines} lines per file.")
        
        # Get all types of changes: staged, unstaged, and untracked
        all_files = {}
        
        # 1. Staged changes (index vs HEAD)
        result = subprocess.run(
            ['git', 'diff', '--name-status', '--cached'],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    status, file_path = parts
                    if file_path not in all_files:
                        all_files[file_path] = []
                    all_files[file_path].append(f"staged-{status}")
        
        # 2. Unstaged changes (working tree vs index)
        result = subprocess.run(
            ['git', 'diff', '--name-status'],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    status, file_path = parts
                    if file_path not in all_files:
                        all_files[file_path] = []
                    all_files[file_path].append(f"unstaged-{status}")
        
        # 3. Untracked files
        result = subprocess.run(
            ['git', 'ls-files', '--others', '--exclude-standard'],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.strip().split('\n'):
            if line:
                if line not in all_files:
                    all_files[line] = []
                all_files[line].append("untracked")
        
        # Process all collected files
        for file_path, statuses in all_files.items():
            absolute_path = os.path.abspath(os.path.join(project_path, file_path))
            
            # Check if this is a deleted file
            is_deleted = any('D' in status for status in statuses)
            
            if is_deleted:
                content = "[File deleted]"
            else:
                # Get file content from working directory
                try:
                    if os.path.exists(absolute_path):
                        # Check file size to avoid memory issues with very large files
                        file_size = os.path.getsize(absolute_path)
                        max_file_size = int(os.getenv('MAX_FILE_SIZE_MB', '10')) * 1024 * 1024  # Default 10MB
                        
                        if file_size > max_file_size:
                            content = f"[File too large: {file_size / (1024*1024):.1f}MB, limit is {max_file_size / (1024*1024)}MB]"
                        else:
                            with open(absolute_path, 'r', encoding='utf-8') as f:
                                content_lines = f.readlines()
                                
                            if len(content_lines) > max_lines:
                                content = ''.join(content_lines[:max_lines])
                                content += f'\n... (truncated, showing first {max_lines} lines)'
                            else:
                                content = ''.join(content_lines).rstrip('\n')
                    else:
                        content = "[File not found in working directory]"
                        
                except (UnicodeDecodeError, PermissionError, OSError):
                    # Handle binary files or other errors
                    content = "[Binary file or content not available]"
            
            changed_files.append({
                'path': absolute_path,
                'status': ', '.join(statuses),
                'content': content
            })
        
        return changed_files
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not a git repository or git not available
        logger.warning("Git not available or not in a git repository")
        return []


def generate_file_tree(project_path: str, max_depth: int = None) -> str:
    """
    Generate ASCII file tree representation.
    
    Args:
        project_path: Path to project root
        max_depth: Maximum depth to traverse
        
    Returns:
        ASCII file tree string
    """
    if max_depth is None:
        max_depth = int(os.getenv('MAX_FILE_TREE_DEPTH', '5'))
    
    # Default ignore patterns
    ignore_patterns = {
        '.git', 'node_modules', '__pycache__', '.pytest_cache',
        '*.pyc', '.DS_Store', '.vscode', '.idea'
    }
    
    # Read .gitignore if it exists
    gitignore_path = os.path.join(project_path, '.gitignore')
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        ignore_patterns.add(line)
        except Exception as e:
            logger.warning(f"Failed to read .gitignore: {e}")
    
    def should_ignore(name: str, path: str) -> bool:
        """Check if file/directory should be ignored."""
        for pattern in ignore_patterns:
            if pattern == name or pattern in path:
                return True
            # Simple glob pattern matching
            if '*' in pattern:
                import fnmatch
                if fnmatch.fnmatch(name, pattern):
                    return True
        return False
    
    def build_tree(current_path: str, prefix: str = "", depth: int = 0) -> List[str]:
        """Recursively build tree structure."""
        if depth >= max_depth:
            return []
        
        try:
            items = os.listdir(current_path)
        except PermissionError:
            return []
        
        # Filter out ignored items
        items = [item for item in items if not should_ignore(item, os.path.join(current_path, item))]
        
        # Sort: directories first, then files, both alphabetically
        dirs = sorted([item for item in items if os.path.isdir(os.path.join(current_path, item))])
        files = sorted([item for item in items if os.path.isfile(os.path.join(current_path, item))])
        
        tree_lines = []
        all_items = dirs + files
        
        for i, item in enumerate(all_items):
            is_last = i == len(all_items) - 1
            item_path = os.path.join(current_path, item)
            
            if os.path.isdir(item_path):
                connector = "└── " if is_last else "├── "
                tree_lines.append(f"{prefix}{connector}{item}/")
                
                extension = "    " if is_last else "│   "
                subtree = build_tree(item_path, prefix + extension, depth + 1)
                tree_lines.extend(subtree)
            else:
                connector = "└── " if is_last else "├── "
                tree_lines.append(f"{prefix}{connector}{item}")
        
        return tree_lines
    
    tree_lines = [project_path]
    tree_lines.extend(build_tree(project_path))
    return '\n'.join(tree_lines)


def format_review_template(data: Dict[str, Any]) -> str:
    """
    Format the final review template.
    
    Args:
        data: Dictionary containing all template data
        
    Returns:
        Formatted markdown template
    """
    # Add scope information to header
    review_mode = data.get('review_mode', 'task_list_based')
    if review_mode == 'github_pr':
        scope_info = f"Review Mode: GitHub PR Analysis"
    elif review_mode == 'branch_comparison':
        scope_info = f"Review Mode: Git Branch Comparison"
    else:
        scope_info = f"Review Scope: {data['scope']}"
        if data.get('phase_number'):
            scope_info += f" (Phase: {data['phase_number']})"
        elif data.get('task_number'):
            scope_info += f" (Task: {data['task_number']})"
    
    template = f"""# Code Review Context - {scope_info}

<overall_prd_summary>
{data['prd_summary']}
</overall_prd_summary>

<total_phases>
{data['total_phases']}
</total_phases>

<current_phase_number>
{data['current_phase_number']}
</current_phase_number>

<previous_phase_completed>
{data['previous_phase_completed']}
</previous_phase_completed>
"""
    
    # Only add next phase if it exists
    if data['next_phase']:
        template += f"""<next_phase>
{data['next_phase']}
</next_phase>

"""
    
    template += f"""<current_phase_description>
{data['current_phase_description']}
</current_phase_description>

<subtasks_completed>
{chr(10).join(f"- {subtask}" for subtask in data['subtasks_completed'])}
</subtasks_completed>"""
    
    # Add branch comparison metadata if available
    branch_data = data.get('branch_comparison_data')
    if branch_data:
        if branch_data['mode'] == 'github_pr':
            pr_data = branch_data['pr_data']
            summary = branch_data.get('summary', {})
            template += f"""
<github_pr_metadata>
Repository: {branch_data['repository']}
PR Number: {pr_data['pr_number']}
Title: {pr_data['title']}
Author: {pr_data['author']}
Source Branch: {pr_data['source_branch']}
Target Branch: {pr_data['target_branch']}
Source SHA: {pr_data.get('source_sha', 'N/A')[:8]}...
Target SHA: {pr_data.get('target_sha', 'N/A')[:8]}...
State: {pr_data['state']}
Created: {pr_data['created_at']}
Updated: {pr_data['updated_at']}
Files Changed: {summary.get('files_changed', 'N/A')}
Files Added: {summary.get('files_added', 'N/A')}
Files Modified: {summary.get('files_modified', 'N/A')}
Files Deleted: {summary.get('files_deleted', 'N/A')}"""
            if pr_data.get('body') and pr_data['body'].strip():
                # Show first 200 chars of PR description
                description = pr_data['body'].strip()[:200]
                if len(pr_data['body']) > 200:
                    description += "..."
                template += f"""
Description: {description}"""
            template += """
</github_pr_metadata>"""
        
        elif branch_data['mode'] == 'branch_comparison':
            template += f"""
<branch_comparison_metadata>
Source Branch: {branch_data['source_branch']}
Target Branch: {branch_data['target_branch']}
Files Changed: {branch_data['summary']['files_changed']}
Files Added: {branch_data['summary']['files_added']}
Files Modified: {branch_data['summary']['files_modified']}
Files Deleted: {branch_data['summary']['files_deleted']}"""
            if branch_data.get('commits'):
                template += f"""
Commits Ahead: {len(branch_data['commits'])}
Recent Commits:"""
                for commit in branch_data['commits'][:10]:  # Show up to 10 commits
                    if commit.get('author') and commit.get('date_relative'):
                        template += f"""
- {commit['hash']}: {commit['message']} (by {commit['author']}, {commit['date_relative']})"""
                    else:
                        template += f"""
- {commit['hash']}: {commit['message']}"""
            template += """
</branch_comparison_metadata>"""
            
            # Add detailed commit information section
            if branch_data.get('commits'):
                template += """

<commit_information>
Commit History (showing changes from target to source branch):"""
                for i, commit in enumerate(branch_data['commits'][:15], 1):  # Show up to 15 commits
                    if commit.get('author') and commit.get('date_relative'):
                        template += f"""

{i}. Commit: {commit['hash']}
   Message: {commit['message']}
   Author: {commit['author']}
   Date: {commit.get('date', 'N/A')} ({commit['date_relative']})"""
                    else:
                        template += f"""

{i}. Commit: {commit['hash']}
   Message: {commit['message']}"""
                template += """
</commit_information>"""
            
            # Add branch statistics section
            template += f"""

<branch_statistics>
Comparison Summary:
- Source Branch: {branch_data['source_branch']} ({len(branch_data.get('commits', []))} commits ahead)
- Target Branch: {branch_data['target_branch']}
- Total Files Changed: {branch_data['summary']['files_changed']}
- Files Added: {branch_data['summary']['files_added']}
- Files Modified: {branch_data['summary']['files_modified']}
- Files Deleted: {branch_data['summary']['files_deleted']}
</branch_statistics>"""
    
    template += f"""
<project_path>
{data['project_path']}
</project_path>
<file_tree>
{data['file_tree']}
</file_tree>

<files_changed>"""
    
    for file_info in data['changed_files']:
        file_ext = os.path.splitext(file_info['path'])[1].lstrip('.')
        if not file_ext:
            file_ext = 'txt'
            
        template += f"""
File: {file_info['path']} ({file_info['status']})
```{file_ext}
{file_info['content']}
```"""
    
    template += f"""
</files_changed>

<user_instructions>"""
    
    # Customize instructions based on review mode and scope
    review_mode = data.get('review_mode', 'task_list_based')
    branch_data = data.get('branch_comparison_data')
    
    if review_mode == 'github_pr' and branch_data:
        template += f"""You are reviewing a GitHub Pull Request that contains changes from branch '{branch_data['pr_data']['source_branch']}' to '{branch_data['pr_data']['target_branch']}'.

The PR "{branch_data['pr_data']['title']}" by {branch_data['pr_data']['author']} includes {branch_data['summary']['files_changed']} changed files with {branch_data['summary']['files_added']} additions, {branch_data['summary']['files_modified']} modifications, and {branch_data['summary']['files_deleted']} deletions.

Based on the PR metadata, commit history, and file changes shown above, conduct a comprehensive code review focusing on:
1. Code quality and best practices
2. Security implications of the changes
3. Performance considerations
4. Testing coverage and approach
5. Documentation completeness
6. Integration and compatibility issues

Identify specific lines, files, or patterns that are concerning and provide actionable feedback."""
    elif review_mode == 'branch_comparison' and branch_data:
        commits_count = len(branch_data.get('commits', []))
        template += f"""You are reviewing changes between git branches '{branch_data['source_branch']}' and '{branch_data['target_branch']}'.

The comparison shows {commits_count} commits ahead of the target branch, affecting {branch_data['summary']['files_changed']} files with {branch_data['summary']['files_added']} additions, {branch_data['summary']['files_modified']} modifications, and {branch_data['summary']['files_deleted']} deletions.

Based on the branch comparison metadata, commit history, and file changes shown above, conduct a comprehensive code review focusing on:
1. Changes introduced in this branch compared to the target
2. Code quality and architectural decisions
3. Security implications of the modifications
4. Performance impact of the changes
5. Testing strategy and coverage
6. Documentation updates needed

Review the commit progression to understand the development approach and identify specific lines, files, or patterns that need attention."""
    elif data['scope'] == 'full_project':
        template += f"""We have completed all phases (and subtasks within) of this project: {data['current_phase_description']}.

Based on the PRD, all completed phases, all subtasks that were finished across the entire project, and the files changed in the working directory, your job is to conduct a comprehensive code review and output your code review feedback for the entire project. Identify specific lines or files that are concerning when appropriate."""
    elif data['scope'] == 'specific_task':
        template += f"""We have just completed task #{data['current_phase_number']}: "{data['current_phase_description']}".

Based on the PRD, the completed task, and the files changed in the working directory, your job is to conduct a code review and output your code review feedback for this specific task. Identify specific lines or files that are concerning when appropriate."""
    else:
        template += f"""We have just completed phase #{data['current_phase_number']}: "{data['current_phase_description']}".

Based on the PRD, the completed phase, all subtasks that were finished in that phase, and the files changed in the working directory, your job is to conduct a code review and output your code review feedback for the completed phase. Identify specific lines or files that are concerning when appropriate."""
    
    template += """
</user_instructions>"""
    
    return template


def find_project_files(project_path: str, task_list_name: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
    """
    Find PRD and task list files in the project. PRD files are now optional.
    
    Args:
        project_path: Path to project root
        task_list_name: Optional specific task list file name (e.g., 'tasks-feature-x.md')
        
    Returns:
        Tuple of (prd_file_path, task_list_path). prd_file_path may be None.
    """
    tasks_dir = os.path.join(project_path, 'tasks')
    
    # Create tasks directory if it doesn't exist (for new projects)
    if not os.path.exists(tasks_dir):
        logger.info(f"Tasks directory not found: {tasks_dir}. This is OK - the tool can work without task lists.")
        return None, None
    
    # Find PRD files (optional)
    prd_file = None
    prd_files = glob.glob(os.path.join(tasks_dir, 'prd-*.md'))
    if not prd_files:
        # Also check root directory
        prd_files = glob.glob(os.path.join(project_path, 'prd.md'))
    
    if prd_files:
        # Use most recently modified if multiple
        prd_file = max(prd_files, key=os.path.getmtime)
        logger.info(f"Found PRD file: {os.path.basename(prd_file)}")
    else:
        logger.info("No PRD files found. Will generate project summary from task list or use default prompt.")
    
    # Find task list files
    task_file = None
    
    if task_list_name:
        # User specified exact task list file
        if not task_list_name.endswith('.md'):
            task_list_name += '.md'
        
        specified_path = os.path.join(tasks_dir, task_list_name)
        if os.path.exists(specified_path):
            task_file = specified_path
            logger.info(f"Using specified task list: {task_list_name}")
        else:
            # Try to find similar files
            available_files = [f for f in os.listdir(tasks_dir) if f.startswith('tasks-') and f.endswith('.md')]
            error_msg = f"""Specified task list not found: {task_list_name}

Available task lists in {tasks_dir}:
{chr(10).join(f'  - {f}' for f in available_files) if available_files else '  (no task list files found)'}

Working examples:
  # Use specific task list
  generate-code-review . --task-list tasks-feature-auth.md
  
  # Let tool auto-select most recent task list
  generate-code-review ."""
            raise FileNotFoundError(error_msg)
    else:
        # Auto-discover task list files
        task_files = glob.glob(os.path.join(tasks_dir, 'tasks-*.md'))
        
        if task_files:
            # Use most recently modified if multiple
            task_file = max(task_files, key=os.path.getmtime)
            if len(task_files) > 1:
                available_files = [os.path.basename(f) for f in task_files]
                logger.info(f"Multiple task lists found: {', '.join(available_files)}")
                logger.info(f"Auto-selected most recent: {os.path.basename(task_file)}")
            else:
                logger.info(f"Found task list: {os.path.basename(task_file)}")
        else:
            logger.info("No task list files found. Will use default prompt for code review.")
    
    return prd_file, task_file


def send_to_gemini_for_review(context_content: str, project_path: str, temperature: float = 0.5, model: Optional[str] = None) -> Optional[str]:
    """
    Send review context to Gemini for comprehensive code review with advanced features.
    
    Features enabled by default:
    - Thinking mode (for supported models)
    - URL context (for supported models) 
    - Google Search grounding (for supported models)
    
    Args:
        context_content: The formatted review context content
        project_path: Path to project root for saving output
        temperature: Temperature for AI model (default: 0.5)
        model: Optional model override (default: uses GEMINI_MODEL env var or config default)
        
    Returns:
        Path to saved Gemini response file, or None if failed
    """
    # Check if Gemini is available first
    if not GEMINI_AVAILABLE:
        logger.warning("Gemini API not available. Skipping Gemini review.")
        return None
    
    # Use enhanced API key loading with multiple strategies
    try:
        api_key = require_api_key()
    except ValueError as e:
        logger.warning(f"API key not found: {e}")
        return None
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Load model configuration from JSON file
        config = load_model_config()
        
        # Configure model selection with precedence: parameter > env var > config default
        model_config = model or os.getenv('GEMINI_MODEL', config['defaults']['model'])
        
        # Resolve model aliases to actual API model names
        model_config = config['model_aliases'].get(model_config, model_config)
        
        # Model capability detection using configuration
        supports_url_context = model_config in config['model_capabilities']['url_context_supported']
        supports_grounding = 'gemini-1.5' in model_config or 'gemini-2.0' in model_config or 'gemini-2.5' in model_config
        supports_thinking = model_config in config['model_capabilities']['thinking_mode_supported']
        
        # Determine what features will actually be enabled (considering disable flags)
        actual_capabilities = []
        disable_url_context = os.getenv('DISABLE_URL_CONTEXT', 'false').lower() == 'true'
        disable_grounding = os.getenv('DISABLE_GROUNDING', 'false').lower() == 'true'
        disable_thinking = os.getenv('DISABLE_THINKING', 'false').lower() == 'true'
        
        # Check what will actually be enabled
        url_context_enabled = supports_url_context and not disable_url_context
        grounding_enabled = supports_grounding and not disable_grounding
        thinking_enabled = supports_thinking and not disable_thinking
        
        # Build capabilities list for user feedback
        if url_context_enabled: actual_capabilities.append("URL context")
        if grounding_enabled: actual_capabilities.append("web grounding") 
        if thinking_enabled: actual_capabilities.append("thinking mode")
        
        # Enhanced user feedback for CLI
        print(f"🤖 Using Gemini model: {model_config}")
        if actual_capabilities:
            print(f"✨ Enhanced features enabled: {', '.join(actual_capabilities)}")
            if thinking_enabled:
                thinking_budget = os.getenv('THINKING_BUDGET')
                budget_info = f" (budget: {thinking_budget} tokens)" if thinking_budget else " (auto-budget)"
                print(f"   💭 Thinking mode: Deep reasoning{budget_info}")
            if grounding_enabled:
                print(f"   🌐 Web grounding: Real-time information lookup")
            if url_context_enabled:
                print(f"   🔗 URL context: Enhanced web content understanding")
        else:
            print(f"⚡ Standard features: Basic text generation")
        
        # Log for debugging (less verbose than user output)
        capabilities_text = f" (features: {', '.join(actual_capabilities)})" if actual_capabilities else " (basic)"
        logger.info(f"Gemini configuration: {model_config}{capabilities_text}")
        
        # Configure tools (enabled by default with opt-out)
        tools = []
        
        # URL Context - enabled by default for supported models
        if url_context_enabled:
            try:
                tools.append(types.Tool(url_context=types.UrlContext()))
            except (AttributeError, TypeError) as e:
                logger.warning(f"URL context configuration failed: {e}")
        
        # Google Search Grounding - enabled by default for supported models
        if grounding_enabled:
            try:
                # Use GoogleSearch for newer models (Gemini 2.0+, 2.5+)
                if 'gemini-2.0' in model_config or 'gemini-2.5' in model_config:
                    google_search_tool = types.Tool(google_search=types.GoogleSearch())
                    tools.append(google_search_tool)
                else:
                    # Fallback to GoogleSearchRetrieval for older models
                    grounding_config = types.GoogleSearchRetrieval()
                    tools.append(types.Tool(google_search_retrieval=grounding_config))
            except (AttributeError, TypeError) as e:
                logger.warning(f"Grounding configuration failed: {e}")
        
        # Configure thinking mode - enabled by default for supported models
        thinking_config = None
        thinking_budget = os.getenv('THINKING_BUDGET')  # Let model auto-adjust if not specified
        include_thoughts = os.getenv('INCLUDE_THOUGHTS', 'true').lower() == 'true'
        
        if thinking_enabled:
            try:
                if 'gemini-2.5-flash' in model_config:
                    # Full thinking support with optional budget control
                    config_params = {'include_thoughts': include_thoughts}
                    if thinking_budget is not None:
                        budget_val = int(thinking_budget)
                        config_params['thinking_budget'] = min(budget_val, 24576)  # Max 24,576 tokens
                        budget_msg = f"budget: {config_params['thinking_budget']}"
                    else:
                        budget_msg = "budget: auto-adjust"
                    thinking_config = types.ThinkingConfig(**config_params)
                elif 'gemini-2.5-pro' in model_config:
                    # Pro models support summaries only
                    thinking_config = types.ThinkingConfig(
                        include_thoughts=include_thoughts
                    )
                    budget_msg = "budget: N/A (Pro model)"
            except (AttributeError, TypeError) as e:
                logger.warning(f"Thinking configuration failed: {e}")
        
        # Use the provided temperature (from CLI arg or function parameter)
        # Environment variable is handled at the caller level
        
        # Build configuration parameters
        config_params = {
            'max_output_tokens': 8000,
            'temperature': temperature
        }
        
        if tools:
            config_params['tools'] = tools
            
        if thinking_config:
            config_params['thinking_config'] = thinking_config
        
        config = types.GenerateContentConfig(**config_params)
        
        # Create comprehensive review prompt
        review_prompt = f"""You are an expert code reviewer conducting a comprehensive code review. Based on the provided context, please provide detailed feedback.

{context_content}

Please provide a thorough code review that includes:
1. **Overall Assessment** - High-level evaluation of the implementation
2. **Code Quality & Best Practices** - Specific line-by-line feedback where applicable
3. **Architecture & Design** - Comments on system design and patterns
4. **Security Considerations** - Any security concerns or improvements
5. **Performance Implications** - Performance considerations and optimizations
6. **Testing & Maintainability** - Suggestions for testing and long-term maintenance
7. **Next Steps** - Recommendations for future work or improvements

Focus on being specific and actionable. When referencing files, include line numbers where relevant."""
        
        # Generate review
        logger.info("Sending context to Gemini for code review...")
        response = client.models.generate_content(
            model=model_config,
            contents=[review_prompt],
            config=config
        )
        
        # Format and save response
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_file = os.path.join(project_path, f'code-review-comprehensive-feedback-{timestamp}.md')
        
        # Format the response with metadata
        enabled_features = []
        if supports_url_context and not disable_url_context and tools:
            # Check if URL context tool was actually added
            if any(hasattr(tool, 'url_context') for tool in tools):
                enabled_features.append("URL context")
        if supports_grounding and not disable_grounding and tools:
            # Check if grounding tool was actually added
            if any(hasattr(tool, 'google_search') or hasattr(tool, 'google_search_retrieval') for tool in tools):
                enabled_features.append("web grounding")
        if thinking_config:
            enabled_features.append("thinking mode")
        
        features_text = ", ".join(enabled_features) if enabled_features else "basic capabilities"
        
        formatted_response = f"""# Comprehensive Code Review Feedback
*Generated on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S")} using {model_config}*

{response.text}

---
*Review conducted by Gemini AI with {features_text}*
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_response)
        
        logger.info(f"Gemini review saved to: {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"Failed to generate Gemini review: {e}")
        return None


def main(project_path: str = None, phase: str = None, output: str = None, enable_gemini_review: bool = True, 
         scope: str = "recent_phase", phase_number: str = None, task_number: str = None, temperature: float = 0.5,
         task_list: str = None, default_prompt: str = None, compare_branch: str = None, 
         target_branch: str = None, github_pr_url: str = None) -> tuple[str, Optional[str]]:
    """
    Main function to generate code review context with enhanced scope support.
    
    Args:
        project_path: Path to project root
        phase: Override current phase detection (legacy parameter)
        output: Custom output file path
        enable_gemini_review: Whether to generate AI review
        scope: Review scope - "recent_phase", "full_project", "specific_phase", "specific_task"
        phase_number: Phase number for specific_phase scope (e.g., "2.0")
        task_number: Task number for specific_task scope (e.g., "1.2")
        
    Returns:
        Tuple of (context_file_path, gemini_review_path). gemini_review_path is None if not generated.
    """
    if project_path is None:
        project_path = os.getcwd()
    
    # Detect and validate review mode
    review_modes = []
    if github_pr_url:
        review_modes.append("github_pr")
    if compare_branch or target_branch:
        review_modes.append("branch_comparison")
    if not review_modes:
        review_modes.append("task_list_based")
    
    # Validate mutually exclusive modes
    if len(review_modes) > 1:
        error_msg = """Multiple review modes detected. Please use only one:

Working examples:
  # Task list based review (default)
  generate-code-review .
  
  # Branch comparison review
  generate-code-review . --compare-branch feature/auth
  
  # GitHub PR review  
  generate-code-review --github-pr-url https://github.com/owner/repo/pull/123
  
  # NOT valid - conflicting modes
  generate-code-review . --compare-branch feature/auth --github-pr-url https://github.com/owner/repo/pull/123"""
        raise ValueError(error_msg)
    
    # Validate scope parameter
    valid_scopes = ["recent_phase", "full_project", "specific_phase", "specific_task"]
    if scope not in valid_scopes:
        raise ValueError(f"Invalid scope '{scope}'. Must be one of: {', '.join(valid_scopes)}")
    
    # Validate scope-specific parameters
    if scope == "specific_phase":
        if not phase_number:
            error_msg = """phase_number is required when scope is 'specific_phase'

Working examples:
  # Review a specific phase
  generate-code-review . --scope specific_phase --phase-number 2.0
  
  # Review first phase
  generate-code-review . --scope specific_phase --phase-number 1.0
  
  # Use environment variable for API key
  GEMINI_API_KEY=your_key generate-code-review . --scope specific_phase --phase-number 3.0"""
            raise ValueError(error_msg)
        if not re.match(r'^\d+\.0$', phase_number):
            error_msg = f"""Invalid phase_number format '{phase_number}'. Must be in format 'X.0'

Working examples:
  # Correct formats
  generate-code-review . --scope specific_phase --phase-number 1.0
  generate-code-review . --scope specific_phase --phase-number 2.0
  generate-code-review . --scope specific_phase --phase-number 10.0
  
  # Incorrect formats
  --phase-number 1    ❌ (missing .0)
  --phase-number 1.1  ❌ (phases end in .0)
  --phase-number v1.0 ❌ (no prefix allowed)"""
            raise ValueError(error_msg)
    
    if scope == "specific_task":
        if not task_number:
            error_msg = """task_number is required when scope is 'specific_task'

Working examples:
  # Review a specific task
  generate-code-review . --scope specific_task --task-number 1.2
  
  # Review first subtask of phase 2
  generate-code-review . --scope specific_task --task-number 2.1
  
  # Use with custom temperature
  generate-code-review . --scope specific_task --task-number 3.4 --temperature 0.3"""
            raise ValueError(error_msg)
        if not re.match(r'^\d+\.\d+$', task_number) or task_number.endswith('.0'):
            error_msg = f"""Invalid task_number format '{task_number}'. Must be in format 'X.Y'

Working examples:
  # Correct formats
  generate-code-review . --scope specific_task --task-number 1.1
  generate-code-review . --scope specific_task --task-number 2.3
  generate-code-review . --scope specific_task --task-number 10.15
  
  # Incorrect formats
  --task-number 1     ❌ (missing subtask number)
  --task-number 1.0   ❌ (use specific_phase for X.0)
  --task-number 1.a   ❌ (must be numeric)"""
            raise ValueError(error_msg)
    
    # Validate GitHub PR URL if provided
    if github_pr_url:
        try:
            # Import here to avoid circular imports
            from github_pr_integration import parse_github_pr_url
            parse_github_pr_url(github_pr_url)  # This will raise ValueError if invalid
        except ValueError as e:
            error_msg = f"""Invalid GitHub PR URL: {e}

Working examples:
  # Standard GitHub PR
  generate-code-review --github-pr-url https://github.com/microsoft/vscode/pull/123
  
  # GitHub Enterprise
  generate-code-review --github-pr-url https://github.company.com/team/project/pull/456
  
  # With additional parameters
  generate-code-review --github-pr-url https://github.com/owner/repo/pull/789 --temperature 0.3"""
            raise ValueError(error_msg)
    
    try:
        # Initial user feedback
        print(f"🔍 Analyzing project: {os.path.basename(os.path.abspath(project_path))}")
        
        # Display review mode
        current_mode = review_modes[0]
        if current_mode == "github_pr":
            print(f"🔗 Review mode: GitHub PR analysis")
            print(f"🌐 PR URL: {github_pr_url}")
        elif current_mode == "branch_comparison":
            print(f"🔀 Review mode: Git branch comparison")
            if compare_branch:
                print(f"📦 Source branch: {compare_branch}")
            if target_branch:
                print(f"🎯 Target branch: {target_branch}")
        else:
            print(f"📊 Review mode: Task list based ({scope})")
        
        if enable_gemini_review:
            print(f"🌡️  AI temperature: {temperature}")
        
        # Load model config for default prompt
        config = load_model_config()
        
        # Find project files (PRD is now optional)
        prd_file, task_file = find_project_files(project_path, task_list)
        
        # Handle different scenarios
        prd_summary = None
        task_data = None
        
        if task_file:
            # We have a task list - read and parse it
            with open(task_file, 'r', encoding='utf-8') as f:
                task_content = f.read()
            task_data = parse_task_list(task_content)
            
            if prd_file:
                # We have both PRD and task list - use PRD summary
                with open(prd_file, 'r', encoding='utf-8') as f:
                    prd_content = f.read()
                prd_summary = extract_prd_summary(prd_content)
            else:
                # Generate summary from task list
                prd_summary = generate_prd_summary_from_task_list(task_data)
        else:
            # No task list - use default prompt
            if default_prompt:
                prd_summary = default_prompt
            else:
                prd_summary = config['defaults']['default_prompt']
            
            # Create minimal task data for template
            task_data = {
                'total_phases': 0,
                'current_phase_number': 'General Review',
                'current_phase_description': 'Code review without specific task context',
                'previous_phase_completed': '',
                'next_phase': '',
                'subtasks_completed': [],
                'phases': []
            }
        
        # Handle scope-based review logic
        if scope == "recent_phase":
            # Smart defaulting: if ALL phases are complete, automatically review full project
            all_phases_complete = all(p.get('subtasks_complete', False) for p in task_data['phases'])
            
            if all_phases_complete and task_data['phases']:
                # All phases complete - automatically switch to full project review
                completed_phases = [p for p in task_data['phases'] if p.get('subtasks_complete', False)]
                all_completed_subtasks = []
                phase_descriptions = []
                for p in completed_phases:
                    all_completed_subtasks.extend(p['subtasks_completed'])
                    phase_descriptions.append(f"{p['number']} {p['description']}")
                
                task_data.update({
                    'current_phase_number': f"Full Project ({len(completed_phases)} phases)",
                    'current_phase_description': f"Analysis of all completed phases: {', '.join(phase_descriptions)}",
                    'previous_phase_completed': '',
                    'next_phase': '',
                    'subtasks_completed': all_completed_subtasks
                })
                # Update scope to reflect the automatic expansion
                scope = "full_project"
            else:
                # Use default behavior (already parsed by detect_current_phase)
                # Override with legacy phase parameter if provided
                if phase:
                    # Find the specified phase
                    for i, p in enumerate(task_data['phases']):
                        if p['number'] == phase:
                            # Find previous completed phase
                            previous_phase_completed = ''
                            if i > 0:
                                prev_phase = task_data['phases'][i - 1]
                                previous_phase_completed = f"{prev_phase['number']} {prev_phase['description']}"
                            
                            # Find next phase
                            next_phase = ''
                            if i < len(task_data['phases']) - 1:
                                next_phase_obj = task_data['phases'][i + 1]
                                next_phase = f"{next_phase_obj['number']} {next_phase_obj['description']}"
                            
                            # Override the detected phase data
                            task_data.update({
                                'current_phase_number': p['number'],
                                'current_phase_description': p['description'],
                                'previous_phase_completed': previous_phase_completed,
                                'next_phase': next_phase,
                                'subtasks_completed': p['subtasks_completed']
                            })
                            break
        
        elif scope == "full_project":
            # Analyze all completed phases
            completed_phases = [p for p in task_data['phases'] if p.get('subtasks_complete', False)]
            if completed_phases:
                # Use summary information for all completed phases
                all_completed_subtasks = []
                phase_descriptions = []
                for p in completed_phases:
                    all_completed_subtasks.extend(p['subtasks_completed'])
                    phase_descriptions.append(f"{p['number']} {p['description']}")
                
                task_data.update({
                    'current_phase_number': f"Full Project ({len(completed_phases)} phases)",
                    'current_phase_description': f"Analysis of all completed phases: {', '.join(phase_descriptions)}",
                    'previous_phase_completed': '',
                    'next_phase': '',
                    'subtasks_completed': all_completed_subtasks
                })
            else:
                # No completed phases, use default behavior
                pass
        
        elif scope == "specific_phase":
            # Find and validate the specified phase
            target_phase = None
            for i, p in enumerate(task_data['phases']):
                if p['number'] == phase_number:
                    target_phase = (i, p)
                    break
            
            if target_phase is None:
                available_phases = [p['number'] for p in task_data['phases']]
                error_msg = f"""Phase {phase_number} not found in task list

Available phases: {', '.join(available_phases) if available_phases else 'none found'}

Working examples:
  # Use an available phase number
  {f'generate-code-review . --scope specific_phase --phase-number {available_phases[0]}' if available_phases else 'generate-code-review . --scope recent_phase  # Use default scope instead'}
  
  # List all phases
  generate-code-review . --scope full_project
  
  # Use default scope (most recent incomplete phase)
  generate-code-review ."""
                raise ValueError(error_msg)
            
            i, p = target_phase
            # Find previous completed phase
            previous_phase_completed = ''
            if i > 0:
                prev_phase = task_data['phases'][i - 1]
                previous_phase_completed = f"{prev_phase['number']} {prev_phase['description']}"
            
            # Find next phase
            next_phase = ''
            if i < len(task_data['phases']) - 1:
                next_phase_obj = task_data['phases'][i + 1]
                next_phase = f"{next_phase_obj['number']} {next_phase_obj['description']}"
            
            # Override with specific phase data
            task_data.update({
                'current_phase_number': p['number'],
                'current_phase_description': p['description'],
                'previous_phase_completed': previous_phase_completed,
                'next_phase': next_phase,
                'subtasks_completed': p['subtasks_completed']
            })
        
        elif scope == "specific_task":
            # Find and validate the specified task
            target_task = None
            target_phase = None
            for i, p in enumerate(task_data['phases']):
                for subtask in p['subtasks']:
                    if subtask['number'] == task_number:
                        target_task = subtask
                        target_phase = (i, p)
                        break
                if target_task:
                    break
            
            if target_task is None:
                # Get available tasks from all phases
                available_tasks = []
                for phase in task_data['phases']:
                    available_tasks.extend([t['number'] for t in phase.get('subtasks', [])])
                
                error_msg = f"""Task {task_number} not found in task list

Available tasks: {', '.join(available_tasks[:10]) if available_tasks else 'none found'}{' (showing first 10)' if len(available_tasks) > 10 else ''}

Working examples:
  # Use an available task number
  {f'generate-code-review . --scope specific_task --task-number {available_tasks[0]}' if available_tasks else 'generate-code-review . --scope recent_phase  # Use default scope instead'}
  
  # Review entire phase instead
  generate-code-review . --scope specific_phase --phase-number {task_number.split('.')[0]}.0
  
  # Use default scope (most recent incomplete phase)
  generate-code-review ."""
                raise ValueError(error_msg)
            
            i, p = target_phase
            # Override with specific task data
            task_data.update({
                'current_phase_number': target_task['number'],
                'current_phase_description': f"Specific task: {target_task['description']} (from {p['number']} {p['description']})",
                'previous_phase_completed': '',
                'next_phase': '',
                'subtasks_completed': [f"{target_task['number']} {target_task['description']}"]
            })
        
        # Get git changes based on review mode
        changed_files = []
        branch_comparison_data = None
        
        if current_mode == "github_pr":
            # GitHub PR analysis mode
            print(f"🔄 Fetching PR data from GitHub...")
            try:
                from github_pr_integration import get_complete_pr_analysis
                pr_analysis = get_complete_pr_analysis(github_pr_url)
                
                # Convert PR file changes to our expected format
                for file_change in pr_analysis['file_changes']['changed_files']:
                    changed_files.append({
                        'path': os.path.join(project_path, file_change['path']),
                        'status': f"PR-{file_change['status']}",
                        'content': file_change.get('patch', '[Content not available]')
                    })
                
                # Store PR metadata for template
                branch_comparison_data = {
                    'mode': 'github_pr',
                    'pr_data': pr_analysis['pr_data'],
                    'summary': pr_analysis['file_changes']['summary'],
                    'repository': pr_analysis['repository']
                }
                
                print(f"✅ Found {len(changed_files)} changed files in PR")
                print(f"📊 Files: +{branch_comparison_data['summary']['files_added']} "
                      f"~{branch_comparison_data['summary']['files_modified']} "
                      f"-{branch_comparison_data['summary']['files_deleted']}")
                
            except Exception as e:
                print(f"❌ Failed to fetch PR data: {e}")
                # Fallback to task list mode
                changed_files = get_changed_files(project_path)
                
        elif current_mode == "branch_comparison":
            # Git branch comparison mode  
            print(f"🔄 Comparing git branches...")
            try:
                from git_branch_comparison import detect_primary_branch, validate_branch_exists, get_branch_diff
                
                # Determine source and target branches
                if not target_branch:
                    target_branch = detect_primary_branch(project_path)
                    print(f"🎯 Auto-detected target branch: {target_branch}")
                
                if not compare_branch:
                    # Get current branch
                    result = subprocess.run(['git', 'branch', '--show-current'], 
                                          cwd=project_path, capture_output=True, text=True, check=True)
                    compare_branch = result.stdout.strip()
                    print(f"📦 Using current branch: {compare_branch}")
                
                # Validate branches exist
                if not validate_branch_exists(project_path, compare_branch):
                    raise ValueError(f"Source branch '{compare_branch}' does not exist")
                if not validate_branch_exists(project_path, target_branch):
                    raise ValueError(f"Target branch '{target_branch}' does not exist")
                
                # Get branch diff
                diff_data = get_branch_diff(project_path, compare_branch, target_branch)
                
                # Convert branch diff to our expected format
                for file_change in diff_data['changed_files']:
                    changed_files.append({
                        'path': os.path.join(project_path, file_change['path']),
                        'status': f"branch-{file_change['status']}",
                        'content': file_change['content']
                    })
                
                # Store branch comparison metadata
                branch_comparison_data = {
                    'mode': 'branch_comparison',
                    'source_branch': compare_branch,
                    'target_branch': target_branch,
                    'commits': diff_data.get('commits', []),
                    'summary': diff_data['summary']
                }
                
                print(f"✅ Found {len(changed_files)} changed files between branches")
                print(f"📊 Files: +{branch_comparison_data['summary']['files_added']} "
                      f"~{branch_comparison_data['summary']['files_modified']} "
                      f"-{branch_comparison_data['summary']['files_deleted']}")
                if diff_data.get('commits'):
                    print(f"📝 Commits: {len(diff_data['commits'])} commits ahead of {target_branch}")
                
            except Exception as e:
                print(f"❌ Failed to compare branches: {e}")
                # Fallback to task list mode
                changed_files = get_changed_files(project_path)
        else:
            # Task list based mode (default)
            changed_files = get_changed_files(project_path)
        
        # Generate file tree
        file_tree = generate_file_tree(project_path)
        
        # Prepare template data
        template_data = {
            'prd_summary': prd_summary,
            'total_phases': task_data['total_phases'],
            'current_phase_number': task_data['current_phase_number'],
            'previous_phase_completed': task_data['previous_phase_completed'],
            'next_phase': task_data['next_phase'],
            'current_phase_description': task_data['current_phase_description'],
            'subtasks_completed': task_data['subtasks_completed'],
            'project_path': project_path,
            'file_tree': file_tree,
            'changed_files': changed_files,
            'scope': scope,
            'phase_number': phase_number if scope == "specific_phase" else None,
            'task_number': task_number if scope == "specific_task" else None,
            'branch_comparison_data': branch_comparison_data,
            'review_mode': current_mode
        }
        
        # Format template
        review_context = format_review_template(template_data)
        
        # Save output with scope-based naming
        if output is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            
            # Generate mode and scope-specific filename
            if current_mode == "github_pr":
                mode_prefix = "github-pr"
            elif current_mode == "branch_comparison":
                mode_prefix = "branch-comparison"
            else:
                # Task list based mode - use scope-specific naming
                if scope == "recent_phase":
                    mode_prefix = "recent-phase"
                elif scope == "full_project":
                    mode_prefix = "full-project"
                elif scope == "specific_phase":
                    phase_safe = phase_number.replace(".", "-")
                    mode_prefix = f"phase-{phase_safe}"
                elif scope == "specific_task":
                    task_safe = task_number.replace(".", "-")
                    mode_prefix = f"task-{task_safe}"
                else:
                    mode_prefix = "unknown"
            
            output = os.path.join(project_path, f'code-review-context-{mode_prefix}-{timestamp}.md')
        
        with open(output, 'w', encoding='utf-8') as f:
            f.write(review_context)
        
        print(f"📝 Generated review context: {os.path.basename(output)}")
        
        # Send to Gemini for comprehensive review if enabled
        gemini_output = None
        if enable_gemini_review:
            print(f"🔄 Sending to Gemini for AI code review...")
            gemini_output = send_to_gemini_for_review(review_context, project_path, temperature)
            if gemini_output:
                print(f"✅ AI code review completed: {os.path.basename(gemini_output)}")
            else:
                print(f"⚠️  AI code review failed or was skipped (check API key and model availability)")
        
        return output, gemini_output
        
    except Exception as e:
        logger.error(f"Error generating review context: {e}")
        raise


def cli_main():
    """CLI entry point for generate-code-review command."""
    parser = argparse.ArgumentParser(
        description="Generate code review context with enhanced scope options",
        epilog="""
🚀 QUICK START:
  # Most common usage - analyze current project
  generate-code-review .
  
  # With environment variable for API key
  export GEMINI_API_KEY=your_key && generate-code-review .

📋 SCOPE OPTIONS:
  # Auto-detect most recent incomplete phase (default)
  generate-code-review /path/to/project
  
  # Review entire completed project
  generate-code-review . --scope full_project
  
  # Review specific phase only
  generate-code-review . --scope specific_phase --phase-number 2.0
  
  # Review individual task
  generate-code-review . --scope specific_task --task-number 1.3

🔀 GIT BRANCH COMPARISON:
  # Compare current branch against main/master
  generate-code-review . --compare-branch feature/auth-system
  
  # Compare specific branches
  generate-code-review . --compare-branch feature/payment --target-branch develop
  
  # Review GitHub Pull Request
  generate-code-review --github-pr-url https://github.com/owner/repo/pull/123
  
  # Combined with existing features
  generate-code-review . --compare-branch feature/new-ui --temperature 0.3

🎛️ TEMPERATURE CONTROL:
  # Focused/deterministic review (good for production code)
  generate-code-review . --temperature 0.0
  
  # Balanced review (default, recommended)
  generate-code-review . --temperature 0.5
  
  # Creative review (good for early development)
  generate-code-review . --temperature 1.0

⚙️ ENVIRONMENT SETUP:
  # Using uvx (recommended for latest version)
  GEMINI_API_KEY=your_key uvx task-list-code-review-mcp generate-code-review .
  
  # With .env file (project-specific)
  echo "GEMINI_API_KEY=your_key" > .env && generate-code-review .
  
  # Global config (~/.task-list-code-review-mcp.env)
  echo "GEMINI_API_KEY=your_key" > ~/.task-list-code-review-mcp.env

🛠️ ADVANCED OPTIONS:
  # Generate context only (no AI review)
  generate-code-review . --context-only --output /custom/path/review.md
  
  # Custom model via environment variable
  GEMINI_MODEL=gemini-2.5-pro-preview generate-code-review .
  
  # Override temperature via environment
  GEMINI_TEMPERATURE=0.3 generate-code-review .

📁 PROJECT STRUCTURE OPTIONS:
  
  # With task list (recommended)
  your-project/
  ├── tasks/
  │   ├── prd-feature.md       # Optional: Product Requirements Document  
  │   └── tasks-feature.md     # Task list file (auto-selected if multiple)
  └── ... (your source code)
  
  # Without task lists (uses default prompt)
  your-project/
  └── ... (your source code)

📋 TASK LIST DISCOVERY:
  # Auto-selects most recent tasks-*.md file
  generate-code-review .
  
  # Use specific task list
  generate-code-review . --task-list tasks-auth-system.md
  
  # Multiple task lists found? Tool shows which was selected:
  # "Multiple task lists found: tasks-auth.md, tasks-payment.md"
  # "Auto-selected most recent: tasks-payment.md"

🌐 GET API KEY: https://ai.google.dev/gemini-api/docs/api-key
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("project_path", nargs='?', default=None,
                      help="Path to project root")
    parser.add_argument("--phase", help="Override current phase detection (legacy parameter)")
    parser.add_argument("--output", help="Custom output file path")
    parser.add_argument("--context-only", action="store_true", 
                      help="Generate only the review context, skip AI review generation")
    # Keep --no-gemini for backward compatibility (deprecated)
    parser.add_argument("--no-gemini", action="store_true", 
                      help=argparse.SUPPRESS)  # Hidden deprecated option
    
    # New scope-based parameters
    parser.add_argument("--scope", default="recent_phase",
                      choices=["recent_phase", "full_project", "specific_phase", "specific_task"],
                      help="Review scope: recent_phase (default), full_project, specific_phase, specific_task")
    parser.add_argument("--phase-number", help="Phase number for specific_phase scope (e.g., '2.0')")
    parser.add_argument("--task-number", help="Task number for specific_task scope (e.g., '1.2')")
    parser.add_argument("--task-list", help="Specify which task list file to use (e.g., 'tasks-feature-x.md')")
    parser.add_argument("--default-prompt", help="Custom default prompt when no task list exists")
    parser.add_argument("--temperature", type=float, default=0.5,
                      help="Temperature for AI model (default: 0.5, range: 0.0-2.0)")
    
    # Git branch comparison parameters
    parser.add_argument("--compare-branch", help="Compare this branch against target branch (default: current branch)")
    parser.add_argument("--target-branch", help="Target branch for comparison (default: auto-detect main/master)")
    parser.add_argument("--github-pr-url", help="GitHub PR URL to review (e.g., 'https://github.com/owner/repo/pull/123')")
    
    args = parser.parse_args()
    
    try:
        # Validate and improve argument handling
        
        # Validate project path early
        if args.project_path:
            if not os.path.exists(args.project_path):
                suggestions = suggest_path_corrections(args.project_path, "project")
                error_msg = f"""Project path does not exist: {args.project_path}

💡 PATH SUGGESTIONS:
{suggestions}

📋 WORKING EXAMPLES:
  # Use current directory (if it has tasks/ folder)
  generate-code-review .
  
  # Use absolute path
  generate-code-review /path/to/your/project
  
  # Use relative path
  generate-code-review ../my-project
  
  # Auto-detect from current location
  generate-code-review"""
                raise FileNotFoundError(error_msg)
            
            if not os.path.isdir(args.project_path):
                suggestions = suggest_path_corrections(args.project_path, "project")
                error_msg = f"""Project path must be a directory: {args.project_path}

💡 PATH SUGGESTIONS:
{suggestions}

📋 WORKING EXAMPLES:
  # Point to directory, not file
  generate-code-review /path/to/project/  ✓
  generate-code-review /path/to/file.md   ✗
  
  # Use parent directory if you're pointing to a file
  generate-code-review {os.path.dirname(args.project_path) if os.path.dirname(args.project_path) else '.'}"""
                raise NotADirectoryError(error_msg)
        
        # Validate temperature range
        if not (0.0 <= args.temperature <= 2.0):
            error_msg = f"""Temperature must be between 0.0 and 2.0, got {args.temperature}

Working examples:
  # Deterministic/focused (good for code review)
  generate-code-review . --temperature 0.0
  
  # Balanced (default)
  generate-code-review . --temperature 0.5
  
  # Creative (good for brainstorming)
  generate-code-review . --temperature 1.0
  
  # Very creative (experimental)
  generate-code-review . --temperature 1.5
  
  # Use environment variable
  GEMINI_TEMPERATURE=0.3 generate-code-review ."""
            raise ValueError(error_msg)
        
        # Validate output path if provided
        if args.output:
            output_dir = os.path.dirname(args.output)
            if output_dir and not os.path.exists(output_dir):
                error_msg = f"""Output directory does not exist: {output_dir}

Working examples:
  # Use existing directory
  generate-code-review . --output /tmp/review.md
  
  # Use relative path
  generate-code-review . --output ./output/review.md
  
  # Create directory first
  mkdir -p /path/to/output && generate-code-review . --output /path/to/output/review.md
  
  # Or let tool auto-generate in project
  generate-code-review .  # creates in project/tasks/"""
                raise FileNotFoundError(error_msg)
        
        # Handle both new and legacy flags (prioritize new flag)
        enable_gemini = not (args.context_only or args.no_gemini)
        
        # Handle temperature: CLI arg takes precedence, then env var, then default 0.5
        temperature = args.temperature
        if temperature == 0.5:  # Default value, check if env var should override
            try:
                temperature = float(os.getenv('GEMINI_TEMPERATURE', '0.5'))
                if not (0.0 <= temperature <= 2.0):
                    logger.warning(f"Invalid GEMINI_TEMPERATURE={temperature}, using default 0.5")
                    temperature = 0.5
            except ValueError:
                logger.warning(f"Invalid GEMINI_TEMPERATURE format, using default 0.5")
                temperature = 0.5
        
        output_path, gemini_path = main(
            project_path=args.project_path,
            phase=args.phase,
            output=args.output,
            enable_gemini_review=enable_gemini,
            scope=args.scope,
            phase_number=getattr(args, 'phase_number'),
            task_number=getattr(args, 'task_number'),
            temperature=temperature,
            task_list=getattr(args, 'task_list'),
            default_prompt=getattr(args, 'default_prompt'),
            compare_branch=getattr(args, 'compare_branch'),
            target_branch=getattr(args, 'target_branch'),
            github_pr_url=getattr(args, 'github_pr_url')
        )
        
        print(f"\n🎉 Code review process completed!")
        files_generated = [os.path.basename(output_path)]
        if gemini_path:
            files_generated.append(os.path.basename(gemini_path))
        print(f"📄 Files generated: {', '.join(files_generated)}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()