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
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
                current_phase['subtasks_completed'].append(number)
    
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
    if review_idx and review_idx > 0:
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
    if GEMINI_AVAILABLE and os.getenv('GEMINI_API_KEY'):
        try:
            client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
            first_2000_chars = content[:2000]
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
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
        # Get list of changed files
        result = subprocess.run(
            ['git', 'diff', '--name-status', 'HEAD'],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        changed_files = []
        max_lines = int(os.getenv('MAX_FILE_CONTENT_LINES', '500'))
        debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        
        if debug_mode:
            logger.info(f"Debug mode enabled. Processing max {max_lines} lines per file.")
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
                
            parts = line.split('\t', 1)
            if len(parts) != 2:
                continue
                
            status, file_path = parts
            
            # Get file content
            try:
                content_result = subprocess.run(
                    ['git', 'show', f'HEAD:{file_path}'],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                content_lines = content_result.stdout.split('\n')
                if len(content_lines) > max_lines:
                    content = '\n'.join(content_lines[:max_lines])
                    content += f'\n... (truncated, showing first {max_lines} lines)'
                else:
                    content = content_result.stdout
                    
            except subprocess.CalledProcessError:
                # Handle binary files or other errors
                content = "[Binary file or content not available]"
            
            changed_files.append({
                'path': file_path,
                'status': status,
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
    template = f"""**Overall PRD summary: (2-3 sentences max)**
{data['prd_summary']}

**Total Number of phases in Task List: {data['total_phases']}**

**Current phase number: {data['current_phase_number']}**
**Previous phase completed: {data['previous_phase_completed']}**

**Next phase: {data['next_phase']}**

**Current phase description: "{data['current_phase_description']}"**

**Subtasks completed in current phase: {data['subtasks_completed']}**

**{data['project_path']}**
**<file_tree>**
{data['file_tree']}
**</file_tree>**

**<files_changed>**"""
    
    for file_info in data['changed_files']:
        file_ext = os.path.splitext(file_info['path'])[1].lstrip('.')
        if not file_ext:
            file_ext = 'txt'
            
        template += f"""
**File: {file_info['path']}**
**```{file_ext}**
{file_info['content']}
**```**"""
    
    template += f"""
**</files_changed>**

**<user_instructions>**
We have just completed phase #{data['current_phase_number']}: "{data['current_phase_description']}".

Based on the PRD, the completed phase, all subtasks that were finished in that phase, and the files changed, your job is to conduct a code review and output your code review feedback for the completed phase. Identify specific lines or files that are concerning when appropriate.
**</user_instructions>**"""
    
    return template


def find_project_files(project_path: str) -> tuple[Optional[str], Optional[str]]:
    """
    Find PRD and task list files in the project.
    
    Args:
        project_path: Path to project root
        
    Returns:
        Tuple of (prd_file_path, task_list_path)
    """
    tasks_dir = os.path.join(project_path, 'tasks')
    
    if not os.path.exists(tasks_dir):
        raise FileNotFoundError(f"Tasks directory not found: {tasks_dir}")
    
    # Find PRD files
    prd_files = glob.glob(os.path.join(tasks_dir, 'prd-*.md'))
    if not prd_files:
        # Also check root directory
        prd_files = glob.glob(os.path.join(project_path, 'prd.md'))
    
    if not prd_files:
        raise FileNotFoundError("No PRD files found (prd-*.md or prd.md)")
    
    # Use most recently modified if multiple
    prd_file = max(prd_files, key=os.path.getmtime)
    
    # Find task list files
    task_files = glob.glob(os.path.join(tasks_dir, 'tasks-prd-*.md'))
    if not task_files:
        task_files = glob.glob(os.path.join(tasks_dir, 'tasks-*.md'))
    
    if not task_files:
        raise FileNotFoundError("No task list files found (tasks-prd-*.md)")
    
    # Use most recently modified if multiple
    task_file = max(task_files, key=os.path.getmtime)
    
    return prd_file, task_file


def main(project_path: str = None, phase: str = None, output: str = None) -> str:
    """
    Main function to generate code review context.
    
    Args:
        project_path: Path to project root
        phase: Override current phase detection
        output: Custom output file path
        
    Returns:
        Path to generated file
    """
    if project_path is None:
        project_path = os.getcwd()
    
    try:
        # Find project files
        prd_file, task_file = find_project_files(project_path)
        
        # Read files
        with open(prd_file, 'r', encoding='utf-8') as f:
            prd_content = f.read()
        
        with open(task_file, 'r', encoding='utf-8') as f:
            task_content = f.read()
        
        # Parse data
        prd_summary = extract_prd_summary(prd_content)
        task_data = parse_task_list(task_content)
        
        # Override phase if provided
        if phase:
            # Find the specified phase
            for p in task_data['phases']:
                if p['number'] == phase:
                    phase_data = detect_current_phase([p])
                    task_data.update(phase_data)
                    break
        
        # Get git changes
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
            'changed_files': changed_files
        }
        
        # Format template
        review_context = format_review_template(template_data)
        
        # Save output
        if output is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = os.path.join(project_path, 'tasks', f'review-context-{timestamp}.md')
        
        with open(output, 'w', encoding='utf-8') as f:
            f.write(review_context)
        
        logger.info(f"Generated review context: {output}")
        return output
        
    except Exception as e:
        logger.error(f"Error generating review context: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate code review context")
    parser.add_argument("project_path", nargs='?', default=None,
                      help="Path to project root")
    parser.add_argument("--phase", help="Override current phase detection")
    parser.add_argument("--output", help="Custom output file path")
    
    args = parser.parse_args()
    
    try:
        output_path = main(args.project_path, args.phase, args.output)
        print(f"Review context generated: {output_path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)