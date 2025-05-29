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
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if GEMINI_AVAILABLE and api_key:
        try:
            client = genai.Client(api_key=api_key)
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
    template = f"""<overall_prd_summary>
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
</subtasks_completed>

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

<user_instructions>
We have just completed phase #{data['current_phase_number']}: "{data['current_phase_description']}".

Based on the PRD, the completed phase, all subtasks that were finished in that phase, and the files changed, your job is to conduct a code review and output your code review feedback for the completed phase. Identify specific lines or files that are concerning when appropriate.
</user_instructions>"""
    
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


def send_to_gemini_for_review(context_content: str, project_path: str) -> Optional[str]:
    """
    Send review context to Gemini for comprehensive code review with advanced features.
    
    Features enabled by default:
    - Thinking mode (for supported models)
    - URL context (for supported models) 
    - Google Search grounding (for supported models)
    
    Args:
        context_content: The formatted review context content
        project_path: Path to project root for saving output
        
    Returns:
        Path to saved Gemini response file, or None if failed
    """
    # Check for API key in multiple environment variables
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    
    if not GEMINI_AVAILABLE or not api_key:
        logger.warning("Gemini API not available or API key not provided (GEMINI_API_KEY or GOOGLE_API_KEY). Skipping Gemini review.")
        return None
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Configure model selection (Flash by default for best feature support)
        model_config = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        logger.info(f"Using Gemini model: {model_config}")
        
        # Model capability detection
        supports_url_context = model_config in [
            'gemini-2.5-pro-preview-05-06', 'gemini-2.5-flash-preview-05-20',
            'gemini-2.0-flash', 'gemini-2.0-flash-live-001', 'gemini-2.5-flash'
        ]
        supports_grounding = 'gemini-1.5' in model_config or 'gemini-2.5' in model_config
        supports_thinking = 'gemini-2.5' in model_config
        
        # Configure tools (enabled by default with opt-out)
        tools = []
        
        # URL Context - enabled by default for supported models
        disable_url_context = os.getenv('DISABLE_URL_CONTEXT', 'false').lower() == 'true'
        if supports_url_context and not disable_url_context:
            try:
                tools.append(types.Tool(url_context=types.UrlContext()))
                logger.info("URL context enabled")
            except (AttributeError, TypeError) as e:
                logger.warning(f"URL context configuration failed: {e}")
        elif not supports_url_context:
            logger.info(f"URL context not supported by {model_config}")
        
        # Google Search Grounding - enabled by default for supported models
        disable_grounding = os.getenv('DISABLE_GROUNDING', 'false').lower() == 'true'
        grounding_threshold = float(os.getenv('GROUNDING_THRESHOLD', '0.3'))
        
        if supports_grounding and not disable_grounding:
            try:
                if 'gemini-2.0' in model_config:
                    # Gemini 2.0 uses "Search as a tool" approach
                    grounding_config = types.GoogleSearchRetrieval()
                else:
                    # Gemini 1.5/2.5 uses dynamic retrieval
                    grounding_config = types.GoogleSearchRetrieval(
                        dynamic_retrieval_config=types.DynamicRetrievalConfig(
                            threshold=grounding_threshold
                        )
                    )
                tools.append(types.Tool(google_search_retrieval=grounding_config))
                logger.info(f"Google Search grounding enabled (threshold: {grounding_threshold})")
            except (AttributeError, TypeError) as e:
                logger.warning(f"Grounding configuration failed: {e}")
        elif not supports_grounding:
            logger.info(f"Grounding not supported by {model_config}")
        
        # Configure thinking mode - enabled by default for supported models
        thinking_config = None
        disable_thinking = os.getenv('DISABLE_THINKING', 'false').lower() == 'true'
        thinking_budget = int(os.getenv('THINKING_BUDGET', '2048'))
        include_thoughts = os.getenv('INCLUDE_THOUGHTS', 'true').lower() == 'true'
        
        if supports_thinking and not disable_thinking:
            try:
                if 'gemini-2.5-flash' in model_config:
                    # Full thinking support with budget control
                    thinking_config = types.ThinkingConfig(
                        thinking_budget=min(thinking_budget, 24576),  # Max 24,576 tokens
                        include_thoughts=include_thoughts
                    )
                elif 'gemini-2.5-pro' in model_config:
                    # Pro models support summaries only
                    thinking_config = types.ThinkingConfig(
                        include_thoughts=include_thoughts
                    )
                logger.info(f"Thinking mode enabled (budget: {thinking_budget}, include_thoughts: {include_thoughts})")
            except (AttributeError, TypeError) as e:
                logger.warning(f"Thinking configuration failed: {e}")
        elif not supports_thinking:
            logger.info(f"Thinking mode not supported by {model_config}")
        
        # Build configuration parameters
        config_params = {
            'max_output_tokens': 8000,
            'temperature': 0.1
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
        if supports_thinking and not disable_thinking:
            enabled_features.append("thinking mode")
        if supports_url_context and not disable_url_context:
            enabled_features.append("URL context")
        if supports_grounding and not disable_grounding:
            enabled_features.append("web grounding")
        
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


def main(project_path: str = None, phase: str = None, output: str = None, enable_gemini_review: bool = True) -> str:
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
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output = os.path.join(project_path, f'code-review-context-{timestamp}.md')
        
        with open(output, 'w', encoding='utf-8') as f:
            f.write(review_context)
        
        logger.info(f"Generated review context: {output}")
        
        # Send to Gemini for comprehensive review if enabled
        gemini_output = None
        if enable_gemini_review:
            gemini_output = send_to_gemini_for_review(review_context, project_path)
            if gemini_output:
                logger.info(f"Gemini review generated: {gemini_output}")
            else:
                logger.warning("Gemini review generation failed or was skipped")
        
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
    parser.add_argument("--no-gemini", action="store_true", 
                      help="Disable Gemini AI code review generation")
    
    args = parser.parse_args()
    
    try:
        enable_gemini = not args.no_gemini
        output_path = main(args.project_path, args.phase, args.output, enable_gemini)
        print(f"Review context generated: {output_path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)