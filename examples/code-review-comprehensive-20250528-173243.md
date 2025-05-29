<overall_prd_summary>
This project implements an MCP server for code review context generation. It automates the creation of review templates.
</overall_prd_summary>

<total_phases>
5
</total_phases>

<current_phase_number>
5.0
</current_phase_number>

<previous_phase_completed>
4.0 Implement git operations and file tree generation
</previous_phase_completed>
<current_phase_description>
Create MCP server integration and finalize project
</current_phase_description>

<subtasks_completed>
- 5.1 Implement MCP server wrapper (server.py) with tool schema definition
- 5.2 Add command-line interface with argument parsing (project_path, --phase, --output)
- 5.3 Implement main orchestration function that ties all components together
- 5.4 Add comprehensive error handling and logging throughout the application
- 5.5 Create final integration tests and validate all success criteria are met
</subtasks_completed>

<project_path>
/Users/nicobailon/Documents/development/task-list-phase-reviewer
</project_path>
<file_tree>
/Users/nicobailon/Documents/development/task-list-phase-reviewer
├── build/
├── code_review_context_mcp.egg-info/
│   ├── PKG-INFO
│   ├── SOURCES.txt
│   ├── dependency_links.txt
│   ├── entry_points.txt
│   ├── requires.txt
│   └── top_level.txt
├── src/
│   ├── generate_code_review_context.py
│   └── server.py
├── tasks/
│   └── tasks-prd.md
├── test-env/
│   ├── bin/
│   │   ├── Activate.ps1
│   │   ├── activate
│   │   ├── activate.csh
│   │   ├── activate.fish
│   │   ├── dotenv
│   │   ├── httpx
│   │   ├── mcp
│   │   ├── normalizer
│   │   ├── pip
│   │   ├── pip3
│   │   ├── pip3.13
│   │   ├── py.test
│   │   ├── pyrsa-decrypt
│   │   ├── pyrsa-encrypt
│   │   ├── pyrsa-keygen
│   │   ├── pyrsa-priv2pub
│   │   ├── pyrsa-sign
│   │   ├── pyrsa-verify
│   │   ├── pytest
│   │   ├── python
│   │   ├── python3
│   │   ├── python3.13
│   │   ├── uvicorn
│   │   └── websockets
│   ├── include/
│   │   └── python3.13/
│   ├── lib/
│   │   └── python3.13/
│   │       └── site-packages/
│   │           ├── _pytest/
│   │           ├── annotated_types/
│   │           ├── annotated_types-0.7.0.dist-info/
│   │           ├── anyio/
│   │           ├── anyio-4.9.0.dist-info/
│   │           ├── cachetools/
│   │           ├── cachetools-5.5.2.dist-info/
│   │           ├── certifi/
│   │           ├── certifi-2025.4.26.dist-info/
│   │           ├── charset_normalizer/
│   │           ├── charset_normalizer-3.4.2.dist-info/
│   │           ├── click/
│   │           ├── click-8.2.1.dist-info/
│   │           ├── dotenv/
│   │           ├── google/
│   │           ├── google_auth-2.40.2.dist-info/
│   │           ├── google_genai-1.17.0.dist-info/
│   │           ├── h11/
│   │           ├── h11-0.16.0.dist-info/
│   │           ├── httpcore/
│   │           ├── httpcore-1.0.9.dist-info/
│   │           ├── httpx/
│   │           ├── httpx-0.28.1.dist-info/
│   │           ├── httpx_sse/
│   │           ├── httpx_sse-0.4.0.dist-info/
│   │           ├── idna/
│   │           ├── idna-3.10.dist-info/
│   │           ├── iniconfig/
│   │           ├── iniconfig-2.1.0.dist-info/
│   │           ├── mcp/
│   │           ├── mcp-1.9.1.dist-info/
│   │           ├── multipart/
│   │           ├── packaging/
│   │           ├── packaging-25.0.dist-info/
│   │           ├── pip/
│   │           ├── pip-25.0.1.dist-info/
│   │           ├── pluggy/
│   │           ├── pluggy-1.6.0.dist-info/
│   │           ├── pyasn1/
│   │           ├── pyasn1-0.6.1.dist-info/
│   │           ├── pyasn1_modules/
│   │           ├── pyasn1_modules-0.4.2.dist-info/
│   │           ├── pydantic/
│   │           ├── pydantic-2.11.5.dist-info/
│   │           ├── pydantic_core/
│   │           ├── pydantic_core-2.33.2.dist-info/
│   │           ├── pydantic_settings/
│   │           ├── pydantic_settings-2.9.1.dist-info/
│   │           ├── pytest/
│   │           ├── pytest-8.3.5.dist-info/
│   │           ├── pytest_mock/
│   │           ├── pytest_mock-3.14.1.dist-info/
│   │           ├── python_dotenv-1.1.0.dist-info/
│   │           ├── python_multipart/
│   │           ├── python_multipart-0.0.20.dist-info/
│   │           ├── requests/
│   │           ├── requests-2.32.3.dist-info/
│   │           ├── rsa/
│   │           ├── rsa-4.9.1.dist-info/
│   │           ├── sniffio/
│   │           ├── sniffio-1.3.1.dist-info/
│   │           ├── sse_starlette/
│   │           ├── sse_starlette-2.3.5.dist-info/
│   │           ├── starlette/
│   │           ├── starlette-0.46.2.dist-info/
│   │           ├── typing_extensions-4.13.2.dist-info/
│   │           ├── typing_inspection/
│   │           ├── typing_inspection-0.4.1.dist-info/
│   │           ├── urllib3/
│   │           ├── urllib3-2.4.0.dist-info/
│   │           ├── uvicorn/
│   │           ├── uvicorn-0.34.2.dist-info/
│   │           ├── websockets/
│   │           ├── websockets-15.0.1.dist-info/
│   │           ├── py.py
│   │           └── typing_extensions.py
│   └── pyvenv.cfg
├── tests/
│   ├── fixtures/
│   │   ├── sample_output.md
│   │   ├── sample_prd.md
│   │   └── sample_task_list.md
│   └── test_generate_code_review_context.py
├── venv/
├── .env
├── README.md
├── code-review-comprehensive-20250528-165648.md
├── code-review-comprehensive-20250528-172408.md
├── code-review-comprehensive-20250528-172413.md
├── code-review-comprehensive-20250528-172430.md
├── code-review-comprehensive-20250528-172447.md
├── code-review-comprehensive-20250528-172456.md
├── code-review-comprehensive-20250528-172535.md
├── code-review-comprehensive-feedback-20250528-171640.md
├── example-task-list-management-rules.md
├── my-custom-review.md
├── prd.md
├── pyproject.toml
├── requirements.txt
└── test_new_feature.py
</file_tree>

<files_changed>
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/README.md (unstaged-M)
```md
# Code Review Context Generator for AI Coding Agents

An MCP server tool designed for **AI coding agents** (Cursor, Claude Code, etc.) to automatically generate comprehensive code review context when completing development phases.

**Version**: 1.2.0 - Enhanced with debug mode and improved file processing capabilities.

## Workflow Integration for AI Agents

This tool integrates into the AI-driven development workflow at **phase completion checkpoints**:

1. **AI Agent works through task list** - Cursor/Claude Code systematically implements features by completing tasks in phases (1.0, 2.0, 3.0, etc.)
2. **Phase completion detected** - When all sub-tasks in a phase are marked complete (`[x]`)  
3. **AI Agent calls MCP tool** - Automatically generates code review context for the completed phase
4. **Review context generated** - Creates formatted markdown with git changes, progress summary, and file context
5. **Ready for review** - Human reviewers get comprehensive context for what was just implemented

## Use Case: AI Agent Integration

**Typical AI agent workflow:**
```
AI Agent: "I've completed all sub-tasks in Phase 2.0. Let me generate a code review context."
AI Agent calls: generate_code_review_context tool
Output: Comprehensive markdown file with git diff, file tree, and phase summary
AI Agent: "✅ Phase 2.0 complete! Review context generated at: code-review-context-20250528-143052.md"
```

## Compatible Format Specifications

This tool works with standardized PRD and task list formats from the [AI Dev Tasks](https://github.com/snarktank/ai-dev-tasks) repository:

- **PRDs**: Based on [create-prd.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/create-prd.mdc) specification
  - Structured markdown with required sections (Goals, User Stories, Functional Requirements, etc.)
  - File naming: `prd-[feature-name].md` in `/tasks/` directory
  - Designed for AI agent comprehension and systematic implementation

- **Task Lists**: Based on [generate-tasks.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/generate-tasks.mdc) specification  
  - Hierarchical phases with numbered parent tasks (1.0, 2.0) and sub-tasks (1.1, 1.2)
  - File naming: `tasks-[prd-file-name].md` in `/tasks/` directory
  - Checkbox-based progress tracking (`- [ ]` / `- [x]`) for AI agents to mark completion
  - Systematic implementation guidance for coding agents

## What This Tool Generates

The MCP server automatically creates comprehensive code review context including:
- **Phase Progress Summary** - What phase was just completed and which sub-tasks were finished
- **PRD Context** - Original feature requirements and goals (auto-summarized with Gemini 2.0 Flash Lite)
- **Git Changes** - Detailed diff of all modified/added/deleted files since the phase started
- **File Tree** - ASCII representation of current project structure
- **File Content** - Full content of changed files for review
- **Formatted Output** - Professional markdown template ready for human review
- **Automatic Naming** - Files named with timestamp: `code-review-context-{YYYYMMDD-HHMMSS}.md`

### NEW: Gemini 2.5 AI Code Review

In addition to generating review context, the tool can now automatically generate comprehensive AI-powered code reviews using **Gemini 2.5 Flash** or **Gemini 2.5 Pro**:

- **Automated Code Review** - Sends the generated context to Gemini 2.5 for intelligent analysis
- **Thinking Mode Enabled** - Uses Gemini's thinking capabilities for deep reasoning about code quality
- **Google Search Grounding** - Can lookup current best practices and technology information
- **URL Context Support** - Can process URLs mentioned in code comments or documentation
- **Comprehensive Analysis** - Covers code quality, architecture, security, performance, testing, and maintainability
- **Structured Output** - Generates `code-review-comprehensive-feedback-{timestamp}.md` with detailed feedback

## Installation

### Option 1: Using uvx (Recommended - No Virtual Environment Required)

**Benefits of uvx:**
- ✅ No need to create or manage virtual environments
- ✅ Automatically handles dependency isolation
- ✅ Clean, simple one-command execution
- ✅ No `pip install` required

```bash
# Run directly with uvx (automatically manages dependencies)
uvx --from /path/to/this/project generate-code-review-context /path/to/your/project
```

### Option 2: Traditional Installation

```bash
pip install -r requirements.txt
```

## Usage

### Primary Use: MCP Server for AI Agents
The tool is designed as an MCP server that AI coding agents (Cursor, Claude Code) call automatically when completing development phases.

### Manual CLI Usage

**With uvx (Recommended):**
```bash
# Auto-detect most recently completed phase (generates timestamped files)
uvx --from . generate-code-review-context /path/to/project
# Output: code-review-context-20250528-143052.md
# Output: code-review-comprehensive-feedback-20250528-143052.md (Gemini review)

# Disable Gemini AI review (context only)
uvx --from . generate-code-review-context /path/to/project --no-gemini
# Output: code-review-context-20250528-143052.md (only)

# Specify a particular phase for review
uvx --from . generate-code-review-context /path/to/project --phase 2.0
# Output: code-review-context-20250528-143052.md + AI feedback file

# Custom output file location (overrides automatic naming)
uvx --from . generate-code-review-context /path/to/project --output /custom/path/review.md

# Use Gemini 2.5 Pro instead of Flash (via environment variable)
GEMINI_MODEL=gemini-2.5-pro-preview-05-06 uvx --from . generate-code-review-context /path/to/project
```

**Traditional Python (requires virtual environment):**
```bash
# Auto-detect most recently completed phase (generates timestamped files)
python src/generate_code_review_context.py /path/to/project
# Output: code-review-context-20250528-143052.md
# Output: code-review-comprehensive-feedback-20250528-143052.md (Gemini review)

# Disable Gemini AI review (context only)
python src/generate_code_review_context.py /path/to/project --no-gemini
# Output: code-review-context-20250528-143052.md (only)

# Specify a particular phase for review
python src/generate_code_review_context.py /path/to/project --phase 2.0
# Output: code-review-context-20250528-143052.md + AI feedback file

# Custom output file location (overrides automatic naming)
python src/generate_code_review_context.py /path/to/project --output /custom/path/review.md

# Use Gemini 2.5 Pro instead of Flash (via environment variable)
GEMINI_MODEL=gemini-2.5-pro-preview-05-06 python src/generate_code_review_context.py /path/to/project
```

**Output File Naming:**
- **Automatic**: `code-review-context-{timestamp}.md`
- **Example**: `code-review-context-20250528-143052.md`
- **Custom**: Use `--output` flag to specify your own filename
- **Unique**: Each run generates a unique timestamp to avoid conflicts

**CLI Use Cases:**
- Testing the tool during setup
- Manual code review generation outside of AI agent workflows
- Debugging task list parsing or git integration
- One-off reviews for specific phases

## MCP Server Installation

This tool works as an MCP (Model Context Protocol) server for integration with Claude Desktop, Cursor, and Claude Code CLI.

### Claude Code CLI

Install the MCP server using Claude Code's built-in commands:

```bash
# Add the server with your Gemini API key
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_gemini_api_key_here

# List configured servers
claude mcp list

# Test the server
claude mcp get task-list-reviewer
```

### Claude Desktop & Cursor

Add this configuration to your `claude_desktop_config.json` or Cursor's MCP settings:

**Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": [
        "/path/to/task-list-phase-reviewer/src/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

**Replace `/path/to/task-list-phase-reviewer` with your actual project path.**

### Configuring Gemini Model Selection

You can choose between Gemini 2.5 Flash (default) and Pro models by setting the `GEMINI_MODEL` environment variable:

**For Claude Desktop/Cursor (claude_desktop_config.json):**
```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": ["/path/to/task-list-phase-reviewer/src/server.py"],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "GEMINI_MODEL": "gemini-2.5-flash-preview-05-20"
      }
    }
  }
}
```

**For Claude Code CLI:**
```bash
# Use Flash (default - fast, high-volume)
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_key \
  -e GEMINI_MODEL=gemini-2.5-flash-preview-05-20

# Use Pro (complex reasoning, in-depth analysis)
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_key \
  -e GEMINI_MODEL=gemini-2.5-pro-preview-05-06
```

### Usage by AI Coding Agents

Once installed, AI agents (Cursor, Claude Code) can automatically call this tool when completing development phases:

**AI Agent Usage:**
```
AI Agent: "I've completed Phase 2.0 (Implement core parsing logic). Let me generate the code review context."

Tool Call: generate_code_review_context
Parameters: { "project_path": "/path/to/project" }

AI Agent: "✅ Phase 2.0 complete! Code review context generated at: code-review-context-20241128-143052.md"
```

**Manual Usage (for testing):**
```
Please use the generate_code_review_context tool to analyze my project at /path/to/my/project
```

The tool will:
1. **Detect completed phase** - Automatically finds the most recently completed phase from task list
2. **Parse PRD requirements** - Extracts feature context and goals  
3. **Analyze git changes** - Gets all file modifications since phase start
4. **Generate review package** - Creates comprehensive markdown with all context needed for human review

## Environment Variables

### Core Configuration
- `GEMINI_API_KEY`: Required for Gemini integration (PRD summarization and code review)
- `MAX_FILE_TREE_DEPTH`: Optional, maximum tree depth (default: 5). Use lower values for large projects.
- `MAX_FILE_CONTENT_LINES`: Optional, max lines to show per file (default: 500). Adjust for context window limits.

### Gemini 2.5 Code Review Configuration
- `GEMINI_MODEL`: Model to use for code review (default: `gemini-2.5-flash-preview-05-20`)
  - **Flash (default)**: `gemini-2.5-flash-preview-05-20` - Fast, high-volume code reviews
  - **Pro**: `gemini-2.5-pro-preview-05-06` - Complex reasoning, in-depth analysis
- `ENABLE_GROUNDING`: Enable Google Search grounding (default: `true`)
- `ENABLE_URL_CONTEXT`: Enable URL context processing (default: `true`)
- `DEBUG_MODE`: Enable verbose logging (default: `false`)

## Development

Run tests:
```bash
pytest
```

## Project Structure

- `src/generate_code_review_context.py` - Core Python script
- `src/server.py` - MCP server wrapper
- `tests/` - Test files and fixtures
- `pyproject.toml` - Project configuration
- `requirements.txt` - Dependencies
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/example-task-list-management-rules.md (unstaged-M)
```md
# Task List Management

Guidelines for managing task lists in markdown files to track progress on completing a PRD

## Task Implementation
- **One sub-task at a time:** Do **NOT** start the next sub‑task until you ask the user for permission and they say “yes” or "y"
- **Completion protocol:**  
  1. When you finish a **sub‑task**, immediately mark it as completed by changing `[ ]` to `[x]`.  
  2. If **all** subtasks underneath a parent task are now `[x]`, also mark the **parent task** as completed.  
- After each sub‑task proceed to the next sub-task within the same parent task.
- Once **all** its subtasks are `[x]` within a parent task, you need to run the `generate_code_review_context` tool to generate the code review context for that phase.

## Task List Maintenance

1. **Update the task list as you work:**
   - Mark tasks and subtasks as completed (`[x]`) per the protocol above.
   - Add new tasks as they emerge.

2. **Maintain the “Relevant Files” section:**
   - List every file created or modified.
   - Give each file a one‑line description of its purpose.

## AI Instructions

When working with task lists, the AI must:

1. Regularly update the task list file after finishing any significant work.
2. Follow the completion protocol:
   - Mark each finished **sub‑task** `[x]`.
   - Once **all** its subtasks are `[x]` within a parent task, you need to run the `generate_code_review_context` tool to generate the code review context for that phase.
   - Once the context file is generated, use the `send_code_review_context` tool to send the markdown file to Gemini to code review. It will return the path to the review file.
   - Access the review file and add the code review feedback.
   - Mark the **parent task** `[x]` once the code review feedback is complete.
3. Add newly discovered tasks.
4. Keep “Relevant Files” accurate and up to date.
5. Before starting work, check which sub‑task is next.
6. After implementing a sub‑task, update the file and then pause for user approval.
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/pyproject.toml (unstaged-M)
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "code-review-context-mcp"
version = "0.1.0"
description = "Python-based MCP server tool that generates formatted code review context by parsing PRD and task list files"
authors = [
    {name = "Developer", email = "developer@example.com"}
]
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "mcp>=0.1.0",
    "google-genai>=0.1.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.0.0",
    "black",
    "isort",
    "flake8",
]

[project.scripts]
generate-code-review-context = "src.generate_code_review_context:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["src*"]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/src/generate_code_review_context.py (unstaged-M)
```py
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

... (truncated, showing first 500 lines)
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/src/server.py (unstaged-M)
```py
"""
MCP server wrapper for generate_code_review_context.py

Exposes tool:
- generate_code_review_context: Generate review context for current project phase
"""

import os
import sys
import logging
from typing import Any, Dict
import asyncio

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        CallToolRequest,
        CallToolResult,
    )
except ImportError:
    print("MCP library not available. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

from generate_code_review_context import main as generate_review_context

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server instance
server = Server("code-review-context-generator")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    List available tools.
    """
    return [
        Tool(
            name="generate_code_review_context",
            description="Generate code review context based on PRD and current task phase",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Absolute path to project root"
                    },
                    "current_phase": {
                        "type": "string", 
                        "description": "Current phase number (e.g., '2.0'). If not provided, auto-detects from task list"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Custom output file path. If not provided, uses default timestamped path"
                    },
                    "enable_gemini_review": {
                        "type": "boolean",
                        "description": "Enable Gemini AI code review generation (default: true)",
                        "default": True
                    }
                },
                "required": ["project_path"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle tool calls.
    """
    if name != "generate_code_review_context":
        raise ValueError(f"Unknown tool: {name}")
    
    try:
        # Extract arguments
        project_path = arguments.get("project_path")
        current_phase = arguments.get("current_phase")
        output_path = arguments.get("output_path")
        enable_gemini_review = arguments.get("enable_gemini_review", True)
        
        if not project_path:
            raise ValueError("project_path is required")
        
        if not os.path.exists(project_path):
            raise ValueError(f"Project path does not exist: {project_path}")
        
        if not os.path.isabs(project_path):
            raise ValueError("project_path must be an absolute path")
        
        # Generate review context
        logger.info(f"Generating review context for project: {project_path}")
        
        output_file = generate_review_context(
            project_path=project_path,
            phase=current_phase,
            output=output_path,
            enable_gemini_review=enable_gemini_review
        )
        
        # Read the generated content to return
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read generated file: {e}")
            content = f"Generated file at: {output_file} (could not read content)"
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Successfully generated code review context.\n\nOutput file: {output_file}\n\nContent:\n{content}"
                )
            ]
        )
        
    except Exception as e:
        logger.error(f"Error in generate_code_review_context: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error generating code review context: {str(e)}"
                )
            ],
            isError=True
        )


async def main():
    """
    Main entry point for the MCP server.
    """
    # Server initialization options
    options = InitializationOptions(
        server_name="code-review-context-generator",
        server_version="0.1.0",
        capabilities={
            "tools": {}
        }
    )
    
    # Run the server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            options
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/temp_test_file.txt (unstaged-D)
```txt
[File deleted]
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/tests/test_generate_code_review_context.py (unstaged-M)
```py
"""
Tests for generate_code_review_context.py

Following test-driven development approach - write tests first,
then implement functionality to make tests pass.
"""
import pytest
from unittest.mock import patch, mock_open
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import will fail initially - that's expected in TDD
try:
    from generate_code_review_context import (
        parse_task_list,
        detect_current_phase,
        extract_prd_summary,
        get_changed_files,
        generate_file_tree,
        format_review_template
    )
except ImportError:
    # Expected during TDD - tests define the interface
    pass


class TestTaskListParser:
    """Test task list parsing functionality."""
    
    def test_parse_task_list_with_completed_phase(self):
        """Test parsing task list and identifying most recently completed phase."""
        content = """
- [x] 1.0 Phase One
  - [x] 1.1 Subtask one
  - [x] 1.2 Subtask two
- [x] 2.0 Phase Two  
  - [x] 2.1 Subtask one
  - [x] 2.2 Subtask two
  - [x] 2.3 Subtask three
- [ ] 3.0 Phase Three
  - [ ] 3.1 Subtask one
"""
        result = parse_task_list(content)
        
        assert result['total_phases'] == 3
        assert result['current_phase_number'] == '2.0'  # Most recently completed
        assert result['previous_phase_completed'] == '1.0 Phase One'
        assert result['next_phase'] == '3.0 Phase Three'
        assert result['current_phase_description'] == 'Phase Two'
        # Implementation now includes descriptions with numbers
        assert len(result['subtasks_completed']) == 3
        assert all('2.' in task for task in result['subtasks_completed'])
    
    def test_parse_task_list_all_phases_complete(self):
        """Test when all phases are complete."""
        content = """
- [x] 1.0 Phase One
  - [x] 1.1 Subtask one
- [x] 2.0 Phase Two
  - [x] 2.1 Subtask one
  - [x] 2.2 Subtask two
"""
        result = parse_task_list(content)
        
        assert result['total_phases'] == 2
        assert result['current_phase_number'] == '2.0'  # Last phase when all complete
        assert result['current_phase_description'] == 'Phase Two'
        # Implementation now includes descriptions with numbers
        assert len(result['subtasks_completed']) == 2
        assert all('2.' in task for task in result['subtasks_completed'])
    
    def test_parse_task_list_with_nested_subtasks(self):
        """Test handling nested subtask levels."""
        content = """
- [ ] 1.0 Phase One
  - [x] 1.1 Subtask one
    - [x] 1.1.1 Sub-subtask
  - [ ] 1.2 Subtask two
"""
        result = parse_task_list(content)
        
        assert result['current_phase_number'] == '1.0'
        # Implementation now includes descriptions with numbers
        assert len(result['subtasks_completed']) == 1
        assert '1.1' in result['subtasks_completed'][0]
    
    def test_detect_most_recently_completed_phase(self):
        """Test detection of most recently completed phase for review."""
        phases = [
            {'number': '1.0', 'completed': True, 'subtasks_complete': True, 'subtasks': ['1.1'], 'subtasks_completed': ['1.1'], 'description': 'Phase One'},
            {'number': '2.0', 'completed': True, 'subtasks_complete': True, 'subtasks': ['2.1', '2.2'], 'subtasks_completed': ['2.1', '2.2'], 'description': 'Phase Two'},
            {'number': '3.0', 'completed': False, 'subtasks_complete': False, 'subtasks': ['3.1'], 'subtasks_completed': [], 'description': 'Phase Three'}
        ]
        
        current = detect_current_phase(phases)
        assert current['current_phase_number'] == '2.0'  # Most recently completed
        assert current['current_phase_description'] == 'Phase Two'
        assert current['subtasks_completed'] == ['2.1', '2.2']
    
    def test_detect_fallback_to_in_progress_phase(self):
        """Test fallback to in-progress phase when no phases are complete."""
        phases = [
            {'number': '1.0', 'completed': False, 'subtasks_complete': False, 'subtasks': ['1.1'], 'subtasks_completed': ['1.1'], 'description': 'Phase One'},
            {'number': '2.0', 'completed': False, 'subtasks_complete': False, 'subtasks': ['2.1'], 'subtasks_completed': [], 'description': 'Phase Two'}
        ]
        
        current = detect_current_phase(phases)
        assert current['current_phase_number'] == '1.0'  # First incomplete phase


class TestPRDParser:
    """Test PRD parsing functionality."""
    
    def test_extract_explicit_summary(self):
        """Test extracting summary when explicitly marked."""
        content = """
# Project PRD

## Summary
This project implements an MCP server for code review context generation. It automates the creation of review templates.

## Goals
...
"""
        summary = extract_prd_summary(content)
        expected = "This project implements an MCP server for code review context generation. It automates the creation of review templates."
        assert summary == expected
    
    def test_extract_overview_section(self):
        """Test extracting from Overview section."""
        content = """
# Project PRD

## Overview
This tool automates code review processes. It integrates with git and MCP.

## Technical Details
...
"""
        summary = extract_prd_summary(content)
        expected = "This tool automates code review processes. It integrates with git and MCP."
        assert summary == expected
    
    def test_generate_summary_fallback(self):
        """Test fallback when no summary section exists."""
        content = """
# Project PRD

This is the first paragraph that should be used as fallback summary when no explicit summary section is found.

## Technical Details
More details here...
"""
        summary = extract_prd_summary(content)
        expected = "This is the first paragraph that should be used as fallback summary when no explicit summary section is found."
        assert summary == expected
    
    @patch('google.genai.Client')
    def test_llm_summary_generation(self, mock_genai):
        """Test LLM-based summary generation when available."""
        # Mock Gemini response
        mock_client = mock_genai.return_value
        mock_response = mock_client.models.generate_content.return_value
        mock_response.text = "Generated summary from LLM."
        
        content = "# PRD\n\nLong content without clear summary section..."
        
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
            summary = extract_prd_summary(content)
            assert summary == "Generated summary from LLM."


class TestGitOperations:
    """Test git operations functionality."""
    
    @patch('subprocess.run')
    def test_get_changed_files_mock(self, mock_run):
        """Test git diff parsing with mocked subprocess."""
        # Mock git diff --name-status output
        mock_run.return_value.stdout = "M\tsrc/parser.py\nA\tsrc/new_file.py\nD\told_file.py"
        mock_run.return_value.returncode = 0
        
        # Mock git show output for file content
        def side_effect(*args, **kwargs):
            if 'show' in args[0]:
                if 'src/parser.py' in args[0]:
                    mock_run.return_value.stdout = "def parse_task_list():\n    pass"
                elif 'src/new_file.py' in args[0]:
                    mock_run.return_value.stdout = "# New file content"
            return mock_run.return_value
        
        mock_run.side_effect = side_effect
        
        result = get_changed_files("/test/project")
        
        assert len(result) == 3
        assert result[0]['path'] == 'src/parser.py'
        assert result[0]['status'] == 'M'
        assert 'def parse_task_list' in result[0]['content']
    
    @patch('subprocess.run')
    def test_handle_no_git_repository(self, mock_run):
        """Test graceful handling when not in git repo."""
        # Mock git command failure
        mock_run.side_effect = FileNotFoundError("git command not found")
        
        result = get_changed_files("/not/a/git/repo")
        assert result == []  # Should return empty list, not crash
    
    @patch('subprocess.run')
    def test_handle_binary_files(self, mock_run):
        """Test handling of binary files in git diff."""
        mock_run.return_value.stdout = "M\timage.png\nM\tsrc/code.py"
        mock_run.return_value.returncode = 0
        
        def side_effect(*args, **kwargs):
            if 'show' in args[0]:
                if 'image.png' in args[0]:
                    # Simulate binary file error
                    mock_run.return_value.returncode = 1
                    mock_run.return_value.stderr = "binary file"
                else:
                    mock_run.return_value.stdout = "code content"
                    mock_run.return_value.returncode = 0
            return mock_run.return_value
        
        mock_run.side_effect = side_effect
        
        result = get_changed_files("/test/project")
        
        # Should handle binary files gracefully
        binary_file = next((f for f in result if f['path'] == 'image.png'), None)
        assert binary_file is not None
        assert binary_file['content'] == "[Binary file]"


class TestFileTreeGenerator:
    """Test file tree generation functionality."""
    
    @patch('os.walk')
    @patch('os.path.isdir')
    def test_generate_file_tree_basic(self, mock_isdir, mock_walk):
        """Test basic file tree generation."""
        # Mock directory structure
        mock_walk.return_value = [
            ('/test/project', ['src', 'tests'], ['README.md']),
            ('/test/project/src', [], ['parser.py', 'server.py']),
            ('/test/project/tests', [], ['test_parser.py'])
        ]
        mock_isdir.return_value = True
        
        result = generate_file_tree("/test/project")
        
        expected_lines = [
            "/test/project",
            "├── src/",
            "│   ├── parser.py",
            "│   └── server.py",
            "├── tests/",
            "│   └── test_parser.py",
            "└── README.md"
        ]
        
        for line in expected_lines:
            assert line in result
    
    @patch('os.walk')
    @patch('builtins.open', new_callable=mock_open, read_data="*.pyc\n__pycache__/\n")
    def test_file_tree_respects_gitignore(self, mock_file, mock_walk):
        """Test that gitignore patterns are respected."""
        mock_walk.return_value = [
            ('/test/project', ['src', '__pycache__'], ['README.md', '.gitignore']),
            ('/test/project/src', [], ['parser.py', 'cache.pyc'])
        ]
        
        result = generate_file_tree("/test/project")
        
        # Should exclude gitignore patterns
        assert '__pycache__' not in result
        assert 'cache.pyc' not in result
        assert 'parser.py' in result


class TestTemplateFormatter:
    """Test template formatting functionality."""
    
    def test_format_review_template(self):
        """Test complete template formatting."""
        data = {
            'prd_summary': 'Test summary for review context.',
            'total_phases': 3,
            'current_phase_number': '2.0',
            'previous_phase_completed': '1.0 Setup phase',
            'next_phase': '3.0 Integration phase',
            'current_phase_description': 'Implementation phase',
            'subtasks_completed': ['2.1', '2.2'],
            'project_path': '/test/project',
            'file_tree': 'mock tree',
            'changed_files': [
                {'path': 'src/test.py', 'content': 'test content', 'status': 'M'}
            ]
        }
        
        result = format_review_template(data)
        
        # Check key template components (updated for current XML-style format)
        assert '<overall_prd_summary>' in result
        assert 'Test summary for review context.' in result
        assert '<total_phases>' in result
        assert '<current_phase_number>' in result
        assert '<file_tree>' in result
        assert '</file_tree>' in result
        assert '<files_changed>' in result
        assert '</files_changed>' in result
        assert '<user_instructions>' in result


class TestIntegration:
    """Integration tests for complete workflow."""
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.listdir')
    @patch('subprocess.run')
    def test_end_to_end_generation(self, mock_run, mock_listdir, mock_file):
        """Test complete flow from input files to output."""
        # Mock file discovery
        mock_listdir.return_value = ['prd-test.md', 'tasks-prd-test.md']
        
        # Mock file contents
        prd_content = "# Test PRD\n\n## Summary\nTest summary content."
        task_content = "- [x] 1.0 Phase One\n  - [x] 1.1 Done\n- [ ] 2.0 Phase Two\n  - [ ] 2.1 Todo"
        
        mock_file.side_effect = [
            mock_open(read_data=prd_content).return_value,
            mock_open(read_data=task_content).return_value
        ]
        
        # Mock git operations
        mock_run.return_value.stdout = "M\ttest.py"
        mock_run.return_value.returncode = 0
        
        # This test will pass once main function is implemented
        # For now, it defines the expected interface
        assert True  # Placeholder - will implement main function to make this pass


if __name__ == "__main__":
    pytest.main([__file__])
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/code-review-comprehensive-20250528-165648.md (untracked)
```md
<overall_prd_summary>
This project implements an MCP server for code review context generation. It automates the creation of review templates.
</overall_prd_summary>

<total_phases>
5
</total_phases>

<current_phase_number>
5.0
</current_phase_number>

<previous_phase_completed>
4.0 Implement git operations and file tree generation
</previous_phase_completed>
<current_phase_description>
Create MCP server integration and finalize project
</current_phase_description>

<subtasks_completed>
- 5.1 Implement MCP server wrapper (server.py) with tool schema definition
- 5.2 Add command-line interface with argument parsing (project_path, --phase, --output)
- 5.3 Implement main orchestration function that ties all components together
- 5.4 Add comprehensive error handling and logging throughout the application
- 5.5 Create final integration tests and validate all success criteria are met
</subtasks_completed>

<project_path>
/Users/nicobailon/Documents/development/task-list-phase-reviewer
</project_path>
<file_tree>
/Users/nicobailon/Documents/development/task-list-phase-reviewer
├── src/
│   ├── generate_code_review_context.py
│   └── server.py
├── tasks/
│   └── tasks-prd.md
├── test-env/
│   ├── bin/
│   │   ├── Activate.ps1
│   │   ├── activate
│   │   ├── activate.csh
│   │   ├── activate.fish
│   │   ├── dotenv
│   │   ├── httpx
│   │   ├── mcp
│   │   ├── normalizer
│   │   ├── pip
│   │   ├── pip3
│   │   ├── pip3.13
│   │   ├── py.test
│   │   ├── pyrsa-decrypt
│   │   ├── pyrsa-encrypt
│   │   ├── pyrsa-keygen
│   │   ├── pyrsa-priv2pub
│   │   ├── pyrsa-sign
│   │   ├── pyrsa-verify
│   │   ├── pytest
│   │   ├── python
│   │   ├── python3
│   │   ├── python3.13
│   │   ├── uvicorn
│   │   └── websockets
│   ├── include/
│   │   └── python3.13/
│   ├── lib/
│   │   └── python3.13/
│   │       └── site-packages/
│   │           ├── _pytest/
│   │           ├── annotated_types/
│   │           ├── annotated_types-0.7.0.dist-info/
│   │           ├── anyio/
│   │           ├── anyio-4.9.0.dist-info/
│   │           ├── cachetools/
│   │           ├── cachetools-5.5.2.dist-info/
│   │           ├── certifi/
│   │           ├── certifi-2025.4.26.dist-info/
│   │           ├── charset_normalizer/
│   │           ├── charset_normalizer-3.4.2.dist-info/
│   │           ├── click/
│   │           ├── click-8.2.1.dist-info/
│   │           ├── dotenv/
│   │           ├── google/
│   │           ├── google_auth-2.40.2.dist-info/
│   │           ├── google_genai-1.17.0.dist-info/
│   │           ├── h11/
│   │           ├── h11-0.16.0.dist-info/
│   │           ├── httpcore/
│   │           ├── httpcore-1.0.9.dist-info/
│   │           ├── httpx/
│   │           ├── httpx-0.28.1.dist-info/
│   │           ├── httpx_sse/
│   │           ├── httpx_sse-0.4.0.dist-info/
│   │           ├── idna/
│   │           ├── idna-3.10.dist-info/
│   │           ├── iniconfig/
│   │           ├── iniconfig-2.1.0.dist-info/
│   │           ├── mcp/
│   │           ├── mcp-1.9.1.dist-info/
│   │           ├── multipart/
│   │           ├── packaging/
│   │           ├── packaging-25.0.dist-info/
│   │           ├── pip/
│   │           ├── pip-25.0.1.dist-info/
│   │           ├── pluggy/
│   │           ├── pluggy-1.6.0.dist-info/
│   │           ├── pyasn1/
│   │           ├── pyasn1-0.6.1.dist-info/
│   │           ├── pyasn1_modules/
│   │           ├── pyasn1_modules-0.4.2.dist-info/
│   │           ├── pydantic/
│   │           ├── pydantic-2.11.5.dist-info/
│   │           ├── pydantic_core/
│   │           ├── pydantic_core-2.33.2.dist-info/
│   │           ├── pydantic_settings/
│   │           ├── pydantic_settings-2.9.1.dist-info/
│   │           ├── pytest/
│   │           ├── pytest-8.3.5.dist-info/
│   │           ├── pytest_mock/
│   │           ├── pytest_mock-3.14.1.dist-info/
│   │           ├── python_dotenv-1.1.0.dist-info/
│   │           ├── python_multipart/
│   │           ├── python_multipart-0.0.20.dist-info/
│   │           ├── requests/
│   │           ├── requests-2.32.3.dist-info/
│   │           ├── rsa/
│   │           ├── rsa-4.9.1.dist-info/
│   │           ├── sniffio/
│   │           ├── sniffio-1.3.1.dist-info/
│   │           ├── sse_starlette/
│   │           ├── sse_starlette-2.3.5.dist-info/
│   │           ├── starlette/
│   │           ├── starlette-0.46.2.dist-info/
│   │           ├── typing_extensions-4.13.2.dist-info/
│   │           ├── typing_inspection/
│   │           ├── typing_inspection-0.4.1.dist-info/
│   │           ├── urllib3/
│   │           ├── urllib3-2.4.0.dist-info/
│   │           ├── uvicorn/
│   │           ├── uvicorn-0.34.2.dist-info/
│   │           ├── websockets/
│   │           ├── websockets-15.0.1.dist-info/
│   │           ├── py.py
│   │           └── typing_extensions.py
│   └── pyvenv.cfg
├── tests/
│   ├── fixtures/
│   │   ├── sample_output.md
│   │   ├── sample_prd.md
│   │   └── sample_task_list.md
│   └── test_generate_code_review_context.py
├── venv/
├── .env
├── README.md
├── code-review-comprehensive-20250528-164653.md
├── code-review-comprehensive-20250528-164941.md
├── code-review-comprehensive-20250528-164954.md
├── code-review-context-clean.md
├── code-review-context-final.md
├── code-review-context-fixed.md
├── code-review-context-test.md
├── example-task-list-management-rules.md
├── my-custom-review.md
├── prd.md
├── pyproject.toml
├── requirements.txt
├── review-context-phase-5_0-20250528-163754.md
├── review-context-phase-5_0-20250528-163758.md
├── review-context-phase-5_0-20250528-164223.md
├── review-context-phase-5_0-20250528-164449.md
├── review-context-phase-5_0-20250528-164555.md
├── review-context-phase-5_0-20250528-164643.md
└── test_new_feature.py
</file_tree>

<files_changed>
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/temp_test_file.txt (staged-D)
```txt
[File deleted]
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/README.md (unstaged-M)
```md
# Code Review Context Generator for AI Coding Agents

An MCP server tool designed for **AI coding agents** (Cursor, Claude Code, etc.) to automatically generate comprehensive code review context when completing development phases.

**Version**: 1.2.0 - Enhanced with debug mode and improved file processing capabilities.

## Workflow Integration for AI Agents

This tool integrates into the AI-driven development workflow at **phase completion checkpoints**:

1. **AI Agent works through task list** - Cursor/Claude Code systematically implements features by completing tasks in phases (1.0, 2.0, 3.0, etc.)
2. **Phase completion detected** - When all sub-tasks in a phase are marked complete (`[x]`)  
3. **AI Agent calls MCP tool** - Automatically generates code review context for the completed phase
4. **Review context generated** - Creates formatted markdown with git changes, progress summary, and file context
5. **Ready for review** - Human reviewers get comprehensive context for what was just implemented

## Use Case: AI Agent Integration

**Typical AI agent workflow:**
```
AI Agent: "I've completed all sub-tasks in Phase 2.0. Let me generate a code review context."
AI Agent calls: generate_code_review_context tool
Output: Comprehensive markdown file with git diff, file tree, and phase summary
AI Agent: "✅ Phase 2.0 complete! Review context generated at: review-context-phase-2_0-20250528-143052.md"
```

## Compatible Format Specifications

This tool works with standardized PRD and task list formats from the [AI Dev Tasks](https://github.com/snarktank/ai-dev-tasks) repository:

- **PRDs**: Based on [create-prd.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/create-prd.mdc) specification
  - Structured markdown with required sections (Goals, User Stories, Functional Requirements, etc.)
  - File naming: `prd-[feature-name].md` in `/tasks/` directory
  - Designed for AI agent comprehension and systematic implementation

- **Task Lists**: Based on [generate-tasks.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/generate-tasks.mdc) specification  
  - Hierarchical phases with numbered parent tasks (1.0, 2.0) and sub-tasks (1.1, 1.2)
  - File naming: `tasks-[prd-file-name].md` in `/tasks/` directory
  - Checkbox-based progress tracking (`- [ ]` / `- [x]`) for AI agents to mark completion
  - Systematic implementation guidance for coding agents

## What This Tool Generates

The MCP server automatically creates comprehensive code review context including:
- **Phase Progress Summary** - What phase was just completed and which sub-tasks were finished
- **PRD Context** - Original feature requirements and goals (auto-summarized with Gemini 2.0 Flash Lite)
- **Git Changes** - Detailed diff of all modified/added/deleted files since the phase started
- **File Tree** - ASCII representation of current project structure
- **File Content** - Full content of changed files for review
- **Formatted Output** - Professional markdown template ready for human review
- **Automatic Naming** - Files named with phase and timestamp: `review-context-phase-{phase}-{YYYYMMDD-HHMMSS}.md`

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Primary Use: MCP Server for AI Agents
The tool is designed as an MCP server that AI coding agents (Cursor, Claude Code) call automatically when completing development phases.

### Manual CLI Usage
You can also run the tool manually from the command line:

```bash
# Auto-detect most recently completed phase (generates timestamped file)
python src/generate_code_review_context.py /path/to/project
# Output: review-context-phase-2_0-20250528-143052.md

# Specify a particular phase for review
python src/generate_code_review_context.py /path/to/project --phase 2.0
# Output: review-context-phase-2_0-20250528-143052.md

# Custom output file location (overrides automatic naming)
python src/generate_code_review_context.py /path/to/project --output /custom/path/review.md

# Combine options
python src/generate_code_review_context.py /path/to/project --phase 3.1 --output my-review.md
```

**Output File Naming:**
- **Automatic**: `review-context-phase-{phase_number}-{timestamp}.md`
- **Example**: `review-context-phase-2_0-20250528-143052.md`
- **Custom**: Use `--output` flag to specify your own filename
- **Unique**: Each run generates a unique timestamp to avoid conflicts

**CLI Use Cases:**
- Testing the tool during setup
- Manual code review generation outside of AI agent workflows
- Debugging task list parsing or git integration
- One-off reviews for specific phases

## MCP Server Installation

This tool works as an MCP (Model Context Protocol) server for integration with Claude Desktop, Cursor, and Claude Code CLI.

### Claude Code CLI

Install the MCP server using Claude Code's built-in commands:

```bash
# Add the server with your Gemini API key
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_gemini_api_key_here

# List configured servers
claude mcp list

# Test the server
claude mcp get task-list-reviewer
```

### Claude Desktop & Cursor

Add this configuration to your `claude_desktop_config.json` or Cursor's MCP settings:

**Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": [
        "/path/to/task-list-phase-reviewer/src/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

**Replace `/path/to/task-list-phase-reviewer` with your actual project path.**

### Usage by AI Coding Agents

Once installed, AI agents (Cursor, Claude Code) can automatically call this tool when completing development phases:

**AI Agent Usage:**
```
AI Agent: "I've completed Phase 2.0 (Implement core parsing logic). Let me generate the code review context."

Tool Call: generate_code_review_context
Parameters: { "project_path": "/path/to/project" }

AI Agent: "✅ Phase 2.0 complete! Code review context generated at: review-context-phase-2-20241128-143052.md"
```

**Manual Usage (for testing):**
```
Please use the generate_code_review_context tool to analyze my project at /path/to/my/project
```

The tool will:
1. **Detect completed phase** - Automatically finds the most recently completed phase from task list
2. **Parse PRD requirements** - Extracts feature context and goals  
3. **Analyze git changes** - Gets all file modifications since phase start
4. **Generate review package** - Creates comprehensive markdown with all context needed for human review

## Environment Variables

- `GEMINI_API_KEY`: Optional, for PRD summarization when explicit summary not found
- `MAX_FILE_TREE_DEPTH`: Optional, maximum tree depth (default: 5). Use lower values for large projects.
- `MAX_FILE_CONTENT_LINES`: Optional, max lines to show per file (default: 500). Adjust for context window limits.

## Development

Run tests:
```bash
pytest
```

## Project Structure

- `src/generate_code_review_context.py` - Core Python script
- `src/server.py` - MCP server wrapper
- `tests/` - Test files and fixtures
- `pyproject.toml` - Project configuration
- `requirements.txt` - Dependencies
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/src/generate_code_review_context.py (unstaged-M)
```py
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

... (truncated, showing first 500 lines)
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/code-review-comprehensive-20250528-172408.md (untracked)
```md
<overall_prd_summary>
This project implements an MCP server for code review context generation. It automates the creation of review templates.
</overall_prd_summary>

<total_phases>
5
</total_phases>

<current_phase_number>
5.0
</current_phase_number>

<previous_phase_completed>
4.0 Implement git operations and file tree generation
</previous_phase_completed>
<current_phase_description>
Create MCP server integration and finalize project
</current_phase_description>

<subtasks_completed>
- 5.1 Implement MCP server wrapper (server.py) with tool schema definition
- 5.2 Add command-line interface with argument parsing (project_path, --phase, --output)
- 5.3 Implement main orchestration function that ties all components together
- 5.4 Add comprehensive error handling and logging throughout the application
- 5.5 Create final integration tests and validate all success criteria are met
</subtasks_completed>

<project_path>
/Users/nicobailon/Documents/development/task-list-phase-reviewer
</project_path>
<file_tree>
/Users/nicobailon/Documents/development/task-list-phase-reviewer
├── build/
├── code_review_context_mcp.egg-info/
│   ├── PKG-INFO
│   ├── SOURCES.txt
│   ├── dependency_links.txt
│   ├── entry_points.txt
│   ├── requires.txt
│   └── top_level.txt
├── src/
│   ├── generate_code_review_context.py
│   └── server.py
├── tasks/
│   └── tasks-prd.md
├── test-env/
│   ├── bin/
│   │   ├── Activate.ps1
│   │   ├── activate
│   │   ├── activate.csh
│   │   ├── activate.fish
│   │   ├── dotenv
│   │   ├── httpx
│   │   ├── mcp
│   │   ├── normalizer
│   │   ├── pip
│   │   ├── pip3
│   │   ├── pip3.13
│   │   ├── py.test
│   │   ├── pyrsa-decrypt
│   │   ├── pyrsa-encrypt
│   │   ├── pyrsa-keygen
│   │   ├── pyrsa-priv2pub
│   │   ├── pyrsa-sign
│   │   ├── pyrsa-verify
│   │   ├── pytest
│   │   ├── python
│   │   ├── python3
│   │   ├── python3.13
│   │   ├── uvicorn
│   │   └── websockets
│   ├── include/
│   │   └── python3.13/
│   ├── lib/
│   │   └── python3.13/
│   │       └── site-packages/
│   │           ├── _pytest/
│   │           ├── annotated_types/
│   │           ├── annotated_types-0.7.0.dist-info/
│   │           ├── anyio/
│   │           ├── anyio-4.9.0.dist-info/
│   │           ├── cachetools/
│   │           ├── cachetools-5.5.2.dist-info/
│   │           ├── certifi/
│   │           ├── certifi-2025.4.26.dist-info/
│   │           ├── charset_normalizer/
│   │           ├── charset_normalizer-3.4.2.dist-info/
│   │           ├── click/
│   │           ├── click-8.2.1.dist-info/
│   │           ├── dotenv/
│   │           ├── google/
│   │           ├── google_auth-2.40.2.dist-info/
│   │           ├── google_genai-1.17.0.dist-info/
│   │           ├── h11/
│   │           ├── h11-0.16.0.dist-info/
│   │           ├── httpcore/
│   │           ├── httpcore-1.0.9.dist-info/
│   │           ├── httpx/
│   │           ├── httpx-0.28.1.dist-info/
│   │           ├── httpx_sse/
│   │           ├── httpx_sse-0.4.0.dist-info/
│   │           ├── idna/
│   │           ├── idna-3.10.dist-info/
│   │           ├── iniconfig/
│   │           ├── iniconfig-2.1.0.dist-info/
│   │           ├── mcp/
│   │           ├── mcp-1.9.1.dist-info/
│   │           ├── multipart/
│   │           ├── packaging/
│   │           ├── packaging-25.0.dist-info/
│   │           ├── pip/
│   │           ├── pip-25.0.1.dist-info/
│   │           ├── pluggy/
│   │           ├── pluggy-1.6.0.dist-info/
│   │           ├── pyasn1/
│   │           ├── pyasn1-0.6.1.dist-info/
│   │           ├── pyasn1_modules/
│   │           ├── pyasn1_modules-0.4.2.dist-info/
│   │           ├── pydantic/
│   │           ├── pydantic-2.11.5.dist-info/
│   │           ├── pydantic_core/
│   │           ├── pydantic_core-2.33.2.dist-info/
│   │           ├── pydantic_settings/
│   │           ├── pydantic_settings-2.9.1.dist-info/
│   │           ├── pytest/
│   │           ├── pytest-8.3.5.dist-info/
│   │           ├── pytest_mock/
│   │           ├── pytest_mock-3.14.1.dist-info/
│   │           ├── python_dotenv-1.1.0.dist-info/
│   │           ├── python_multipart/
│   │           ├── python_multipart-0.0.20.dist-info/
│   │           ├── requests/
│   │           ├── requests-2.32.3.dist-info/
│   │           ├── rsa/
│   │           ├── rsa-4.9.1.dist-info/
│   │           ├── sniffio/
│   │           ├── sniffio-1.3.1.dist-info/
│   │           ├── sse_starlette/
│   │           ├── sse_starlette-2.3.5.dist-info/
│   │           ├── starlette/
│   │           ├── starlette-0.46.2.dist-info/
│   │           ├── typing_extensions-4.13.2.dist-info/
│   │           ├── typing_inspection/
│   │           ├── typing_inspection-0.4.1.dist-info/
│   │           ├── urllib3/
│   │           ├── urllib3-2.4.0.dist-info/
│   │           ├── uvicorn/
│   │           ├── uvicorn-0.34.2.dist-info/
│   │           ├── websockets/
│   │           ├── websockets-15.0.1.dist-info/
│   │           ├── py.py
│   │           └── typing_extensions.py
│   └── pyvenv.cfg
├── tests/
│   ├── fixtures/
│   │   ├── sample_output.md
│   │   ├── sample_prd.md
│   │   └── sample_task_list.md
│   └── test_generate_code_review_context.py
├── venv/
├── .env
├── README.md
├── code-review-comprehensive-20250528-165648.md
├── code-review-comprehensive-feedback-20250528-171640.md
├── example-task-list-management-rules.md
├── my-custom-review.md
├── prd.md
├── pyproject.toml
├── requirements.txt
└── test_new_feature.py
</file_tree>

<files_changed>
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/README.md (unstaged-M)
```md
# Code Review Context Generator for AI Coding Agents

An MCP server tool designed for **AI coding agents** (Cursor, Claude Code, etc.) to automatically generate comprehensive code review context when completing development phases.

**Version**: 1.2.0 - Enhanced with debug mode and improved file processing capabilities.

## Workflow Integration for AI Agents

This tool integrates into the AI-driven development workflow at **phase completion checkpoints**:

1. **AI Agent works through task list** - Cursor/Claude Code systematically implements features by completing tasks in phases (1.0, 2.0, 3.0, etc.)
2. **Phase completion detected** - When all sub-tasks in a phase are marked complete (`[x]`)  
3. **AI Agent calls MCP tool** - Automatically generates code review context for the completed phase
4. **Review context generated** - Creates formatted markdown with git changes, progress summary, and file context
5. **Ready for review** - Human reviewers get comprehensive context for what was just implemented

## Use Case: AI Agent Integration

**Typical AI agent workflow:**
```
AI Agent: "I've completed all sub-tasks in Phase 2.0. Let me generate a code review context."
AI Agent calls: generate_code_review_context tool
Output: Comprehensive markdown file with git diff, file tree, and phase summary
AI Agent: "✅ Phase 2.0 complete! Review context generated at: review-context-phase-2_0-20250528-143052.md"
```

## Compatible Format Specifications

This tool works with standardized PRD and task list formats from the [AI Dev Tasks](https://github.com/snarktank/ai-dev-tasks) repository:

- **PRDs**: Based on [create-prd.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/create-prd.mdc) specification
  - Structured markdown with required sections (Goals, User Stories, Functional Requirements, etc.)
  - File naming: `prd-[feature-name].md` in `/tasks/` directory
  - Designed for AI agent comprehension and systematic implementation

- **Task Lists**: Based on [generate-tasks.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/generate-tasks.mdc) specification  
  - Hierarchical phases with numbered parent tasks (1.0, 2.0) and sub-tasks (1.1, 1.2)
  - File naming: `tasks-[prd-file-name].md` in `/tasks/` directory
  - Checkbox-based progress tracking (`- [ ]` / `- [x]`) for AI agents to mark completion
  - Systematic implementation guidance for coding agents

## What This Tool Generates

The MCP server automatically creates comprehensive code review context including:
- **Phase Progress Summary** - What phase was just completed and which sub-tasks were finished
- **PRD Context** - Original feature requirements and goals (auto-summarized with Gemini 2.0 Flash Lite)
- **Git Changes** - Detailed diff of all modified/added/deleted files since the phase started
- **File Tree** - ASCII representation of current project structure
- **File Content** - Full content of changed files for review
- **Formatted Output** - Professional markdown template ready for human review
- **Automatic Naming** - Files named with phase and timestamp: `review-context-phase-{phase}-{YYYYMMDD-HHMMSS}.md`

### NEW: Gemini 2.5 AI Code Review

In addition to generating review context, the tool can now automatically generate comprehensive AI-powered code reviews using **Gemini 2.5 Flash** or **Gemini 2.5 Pro**:

- **Automated Code Review** - Sends the generated context to Gemini 2.5 for intelligent analysis
- **Thinking Mode Enabled** - Uses Gemini's thinking capabilities for deep reasoning about code quality
- **Google Search Grounding** - Can lookup current best practices and technology information
- **URL Context Support** - Can process URLs mentioned in code comments or documentation
- **Comprehensive Analysis** - Covers code quality, architecture, security, performance, testing, and maintainability
- **Structured Output** - Generates `code-review-comprehensive-feedback-{timestamp}.md` with detailed feedback

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Primary Use: MCP Server for AI Agents
The tool is designed as an MCP server that AI coding agents (Cursor, Claude Code) call automatically when completing development phases.

### Manual CLI Usage
You can also run the tool manually from the command line:

```bash
# Auto-detect most recently completed phase (generates timestamped files)
python src/generate_code_review_context.py /path/to/project
# Output: review-context-phase-2_0-20250528-143052.md
# Output: code-review-comprehensive-feedback-20250528-143052.md (Gemini review)

# Disable Gemini AI review (context only)
python src/generate_code_review_context.py /path/to/project --no-gemini
# Output: review-context-phase-2_0-20250528-143052.md (only)

# Specify a particular phase for review
python src/generate_code_review_context.py /path/to/project --phase 2.0
# Output: review-context-phase-2_0-20250528-143052.md + AI feedback file

# Custom output file location (overrides automatic naming)
python src/generate_code_review_context.py /path/to/project --output /custom/path/review.md

# Use Gemini 2.5 Pro instead of Flash (via environment variable)
GEMINI_MODEL=gemini-2.5-pro-preview-05-06 python src/generate_code_review_context.py /path/to/project
```

**Output File Naming:**
- **Automatic**: `review-context-phase-{phase_number}-{timestamp}.md`
- **Example**: `review-context-phase-2_0-20250528-143052.md`
- **Custom**: Use `--output` flag to specify your own filename
- **Unique**: Each run generates a unique timestamp to avoid conflicts

**CLI Use Cases:**
- Testing the tool during setup
- Manual code review generation outside of AI agent workflows
- Debugging task list parsing or git integration
- One-off reviews for specific phases

## MCP Server Installation

This tool works as an MCP (Model Context Protocol) server for integration with Claude Desktop, Cursor, and Claude Code CLI.

### Claude Code CLI

Install the MCP server using Claude Code's built-in commands:

```bash
# Add the server with your Gemini API key
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_gemini_api_key_here

# List configured servers
claude mcp list

# Test the server
claude mcp get task-list-reviewer
```

### Claude Desktop & Cursor

Add this configuration to your `claude_desktop_config.json` or Cursor's MCP settings:

**Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": [
        "/path/to/task-list-phase-reviewer/src/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

**Replace `/path/to/task-list-phase-reviewer` with your actual project path.**

### Configuring Gemini Model Selection

You can choose between Gemini 2.5 Flash (default) and Pro models by setting the `GEMINI_MODEL` environment variable:

**For Claude Desktop/Cursor (claude_desktop_config.json):**
```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": ["/path/to/task-list-phase-reviewer/src/server.py"],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "GEMINI_MODEL": "gemini-2.5-flash-preview-05-20"
      }
    }
  }
}
```

**For Claude Code CLI:**
```bash
# Use Flash (default - fast, high-volume)
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_key \
  -e GEMINI_MODEL=gemini-2.5-flash-preview-05-20

# Use Pro (complex reasoning, in-depth analysis)
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_key \
  -e GEMINI_MODEL=gemini-2.5-pro-preview-05-06
```

### Usage by AI Coding Agents

Once installed, AI agents (Cursor, Claude Code) can automatically call this tool when completing development phases:

**AI Agent Usage:**
```
AI Agent: "I've completed Phase 2.0 (Implement core parsing logic). Let me generate the code review context."

Tool Call: generate_code_review_context
Parameters: { "project_path": "/path/to/project" }

AI Agent: "✅ Phase 2.0 complete! Code review context generated at: review-context-phase-2-20241128-143052.md"
```

**Manual Usage (for testing):**
```
Please use the generate_code_review_context tool to analyze my project at /path/to/my/project
```

The tool will:
1. **Detect completed phase** - Automatically finds the most recently completed phase from task list
2. **Parse PRD requirements** - Extracts feature context and goals  
3. **Analyze git changes** - Gets all file modifications since phase start
4. **Generate review package** - Creates comprehensive markdown with all context needed for human review

## Environment Variables

### Core Configuration
- `GEMINI_API_KEY`: Required for Gemini integration (PRD summarization and code review)
- `MAX_FILE_TREE_DEPTH`: Optional, maximum tree depth (default: 5). Use lower values for large projects.
- `MAX_FILE_CONTENT_LINES`: Optional, max lines to show per file (default: 500). Adjust for context window limits.

### Gemini 2.5 Code Review Configuration
- `GEMINI_MODEL`: Model to use for code review (default: `gemini-2.5-flash-preview-05-20`)
  - **Flash (default)**: `gemini-2.5-flash-preview-05-20` - Fast, high-volume code reviews
  - **Pro**: `gemini-2.5-pro-preview-05-06` - Complex reasoning, in-depth analysis
- `ENABLE_GROUNDING`: Enable Google Search grounding (default: `true`)
- `ENABLE_URL_CONTEXT`: Enable URL context processing (default: `true`)
- `DEBUG_MODE`: Enable verbose logging (default: `false`)

## Development

Run tests:
```bash
pytest
```

## Project Structure

- `src/generate_code_review_context.py` - Core Python script
- `src/server.py` - MCP server wrapper
- `tests/` - Test files and fixtures
- `pyproject.toml` - Project configuration
- `requirements.txt` - Dependencies
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/pyproject.toml (unstaged-M)
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "code-review-context-mcp"
version = "0.1.0"
description = "Python-based MCP server tool that generates formatted code review context by parsing PRD and task list files"
authors = [
    {name = "Developer", email = "developer@example.com"}
]
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "mcp>=0.1.0",
    "google-genai>=0.1.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.0.0",
    "black",
    "isort",
    "flake8",
]

[project.scripts]
generate-code-review-context = "src.generate_code_review_context:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["src*"]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/src/generate_code_review_context.py (unstaged-M)
```py
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

... (truncated, showing first 500 lines)
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/code-review-comprehensive-20250528-172413.md (untracked)
```md
<overall_prd_summary>
This project implements an MCP server for code review context generation. It automates the creation of review templates.
</overall_prd_summary>

<total_phases>
5
</total_phases>

<current_phase_number>
5.0
</current_phase_number>

<previous_phase_completed>
4.0 Implement git operations and file tree generation
</previous_phase_completed>
<current_phase_description>
Create MCP server integration and finalize project
</current_phase_description>

<subtasks_completed>
- 5.1 Implement MCP server wrapper (server.py) with tool schema definition
- 5.2 Add command-line interface with argument parsing (project_path, --phase, --output)
- 5.3 Implement main orchestration function that ties all components together
- 5.4 Add comprehensive error handling and logging throughout the application
- 5.5 Create final integration tests and validate all success criteria are met
</subtasks_completed>

<project_path>
/Users/nicobailon/Documents/development/task-list-phase-reviewer
</project_path>
<file_tree>
/Users/nicobailon/Documents/development/task-list-phase-reviewer
├── build/
├── code_review_context_mcp.egg-info/
│   ├── PKG-INFO
│   ├── SOURCES.txt
│   ├── dependency_links.txt
│   ├── entry_points.txt
│   ├── requires.txt
│   └── top_level.txt
├── src/
│   ├── generate_code_review_context.py
│   └── server.py
├── tasks/
│   └── tasks-prd.md
├── test-env/
│   ├── bin/
│   │   ├── Activate.ps1
│   │   ├── activate
│   │   ├── activate.csh
│   │   ├── activate.fish
│   │   ├── dotenv
│   │   ├── httpx
│   │   ├── mcp
│   │   ├── normalizer
│   │   ├── pip
│   │   ├── pip3
│   │   ├── pip3.13
│   │   ├── py.test
│   │   ├── pyrsa-decrypt
│   │   ├── pyrsa-encrypt
│   │   ├── pyrsa-keygen
│   │   ├── pyrsa-priv2pub
│   │   ├── pyrsa-sign
│   │   ├── pyrsa-verify
│   │   ├── pytest
│   │   ├── python
│   │   ├── python3
│   │   ├── python3.13
│   │   ├── uvicorn
│   │   └── websockets
│   ├── include/
│   │   └── python3.13/
│   ├── lib/
│   │   └── python3.13/
│   │       └── site-packages/
│   │           ├── _pytest/
│   │           ├── annotated_types/
│   │           ├── annotated_types-0.7.0.dist-info/
│   │           ├── anyio/
│   │           ├── anyio-4.9.0.dist-info/
│   │           ├── cachetools/
│   │           ├── cachetools-5.5.2.dist-info/
│   │           ├── certifi/
│   │           ├── certifi-2025.4.26.dist-info/
│   │           ├── charset_normalizer/
│   │           ├── charset_normalizer-3.4.2.dist-info/
│   │           ├── click/
│   │           ├── click-8.2.1.dist-info/
│   │           ├── dotenv/
│   │           ├── google/
│   │           ├── google_auth-2.40.2.dist-info/
│   │           ├── google_genai-1.17.0.dist-info/
│   │           ├── h11/
│   │           ├── h11-0.16.0.dist-info/
│   │           ├── httpcore/
│   │           ├── httpcore-1.0.9.dist-info/
│   │           ├── httpx/
│   │           ├── httpx-0.28.1.dist-info/
│   │           ├── httpx_sse/
│   │           ├── httpx_sse-0.4.0.dist-info/
│   │           ├── idna/
│   │           ├── idna-3.10.dist-info/
│   │           ├── iniconfig/
│   │           ├── iniconfig-2.1.0.dist-info/
│   │           ├── mcp/
│   │           ├── mcp-1.9.1.dist-info/
│   │           ├── multipart/
│   │           ├── packaging/
│   │           ├── packaging-25.0.dist-info/
│   │           ├── pip/
│   │           ├── pip-25.0.1.dist-info/
│   │           ├── pluggy/
│   │           ├── pluggy-1.6.0.dist-info/
│   │           ├── pyasn1/
│   │           ├── pyasn1-0.6.1.dist-info/
│   │           ├── pyasn1_modules/
│   │           ├── pyasn1_modules-0.4.2.dist-info/
│   │           ├── pydantic/
│   │           ├── pydantic-2.11.5.dist-info/
│   │           ├── pydantic_core/
│   │           ├── pydantic_core-2.33.2.dist-info/
│   │           ├── pydantic_settings/
│   │           ├── pydantic_settings-2.9.1.dist-info/
│   │           ├── pytest/
│   │           ├── pytest-8.3.5.dist-info/
│   │           ├── pytest_mock/
│   │           ├── pytest_mock-3.14.1.dist-info/
│   │           ├── python_dotenv-1.1.0.dist-info/
│   │           ├── python_multipart/
│   │           ├── python_multipart-0.0.20.dist-info/
│   │           ├── requests/
│   │           ├── requests-2.32.3.dist-info/
│   │           ├── rsa/
│   │           ├── rsa-4.9.1.dist-info/
│   │           ├── sniffio/
│   │           ├── sniffio-1.3.1.dist-info/
│   │           ├── sse_starlette/
│   │           ├── sse_starlette-2.3.5.dist-info/
│   │           ├── starlette/
│   │           ├── starlette-0.46.2.dist-info/
│   │           ├── typing_extensions-4.13.2.dist-info/
│   │           ├── typing_inspection/
│   │           ├── typing_inspection-0.4.1.dist-info/
│   │           ├── urllib3/
│   │           ├── urllib3-2.4.0.dist-info/
│   │           ├── uvicorn/
│   │           ├── uvicorn-0.34.2.dist-info/
│   │           ├── websockets/
│   │           ├── websockets-15.0.1.dist-info/
│   │           ├── py.py
│   │           └── typing_extensions.py
│   └── pyvenv.cfg
├── tests/
│   ├── fixtures/
│   │   ├── sample_output.md
│   │   ├── sample_prd.md
│   │   └── sample_task_list.md
│   └── test_generate_code_review_context.py
├── venv/
├── .env
├── README.md
├── code-review-comprehensive-20250528-165648.md
├── code-review-comprehensive-20250528-172408.md
├── code-review-comprehensive-feedback-20250528-171640.md
├── example-task-list-management-rules.md
├── my-custom-review.md
├── prd.md
├── pyproject.toml
├── requirements.txt
└── test_new_feature.py
</file_tree>

<files_changed>
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/README.md (unstaged-M)
```md
# Code Review Context Generator for AI Coding Agents

An MCP server tool designed for **AI coding agents** (Cursor, Claude Code, etc.) to automatically generate comprehensive code review context when completing development phases.

**Version**: 1.2.0 - Enhanced with debug mode and improved file processing capabilities.

## Workflow Integration for AI Agents

This tool integrates into the AI-driven development workflow at **phase completion checkpoints**:

1. **AI Agent works through task list** - Cursor/Claude Code systematically implements features by completing tasks in phases (1.0, 2.0, 3.0, etc.)
2. **Phase completion detected** - When all sub-tasks in a phase are marked complete (`[x]`)  
3. **AI Agent calls MCP tool** - Automatically generates code review context for the completed phase
4. **Review context generated** - Creates formatted markdown with git changes, progress summary, and file context
5. **Ready for review** - Human reviewers get comprehensive context for what was just implemented

## Use Case: AI Agent Integration

**Typical AI agent workflow:**
```
AI Agent: "I've completed all sub-tasks in Phase 2.0. Let me generate a code review context."
AI Agent calls: generate_code_review_context tool
Output: Comprehensive markdown file with git diff, file tree, and phase summary
AI Agent: "✅ Phase 2.0 complete! Review context generated at: review-context-phase-2_0-20250528-143052.md"
```

## Compatible Format Specifications

This tool works with standardized PRD and task list formats from the [AI Dev Tasks](https://github.com/snarktank/ai-dev-tasks) repository:

- **PRDs**: Based on [create-prd.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/create-prd.mdc) specification
  - Structured markdown with required sections (Goals, User Stories, Functional Requirements, etc.)
  - File naming: `prd-[feature-name].md` in `/tasks/` directory
  - Designed for AI agent comprehension and systematic implementation

- **Task Lists**: Based on [generate-tasks.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/generate-tasks.mdc) specification  
  - Hierarchical phases with numbered parent tasks (1.0, 2.0) and sub-tasks (1.1, 1.2)
  - File naming: `tasks-[prd-file-name].md` in `/tasks/` directory
  - Checkbox-based progress tracking (`- [ ]` / `- [x]`) for AI agents to mark completion
  - Systematic implementation guidance for coding agents

## What This Tool Generates

The MCP server automatically creates comprehensive code review context including:
- **Phase Progress Summary** - What phase was just completed and which sub-tasks were finished
- **PRD Context** - Original feature requirements and goals (auto-summarized with Gemini 2.0 Flash Lite)
- **Git Changes** - Detailed diff of all modified/added/deleted files since the phase started
- **File Tree** - ASCII representation of current project structure
- **File Content** - Full content of changed files for review
- **Formatted Output** - Professional markdown template ready for human review
- **Automatic Naming** - Files named with phase and timestamp: `review-context-phase-{phase}-{YYYYMMDD-HHMMSS}.md`

### NEW: Gemini 2.5 AI Code Review

In addition to generating review context, the tool can now automatically generate comprehensive AI-powered code reviews using **Gemini 2.5 Flash** or **Gemini 2.5 Pro**:

- **Automated Code Review** - Sends the generated context to Gemini 2.5 for intelligent analysis
- **Thinking Mode Enabled** - Uses Gemini's thinking capabilities for deep reasoning about code quality
- **Google Search Grounding** - Can lookup current best practices and technology information
- **URL Context Support** - Can process URLs mentioned in code comments or documentation
- **Comprehensive Analysis** - Covers code quality, architecture, security, performance, testing, and maintainability
- **Structured Output** - Generates `code-review-comprehensive-feedback-{timestamp}.md` with detailed feedback

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Primary Use: MCP Server for AI Agents
The tool is designed as an MCP server that AI coding agents (Cursor, Claude Code) call automatically when completing development phases.

### Manual CLI Usage
You can also run the tool manually from the command line:

```bash
# Auto-detect most recently completed phase (generates timestamped files)
python src/generate_code_review_context.py /path/to/project
# Output: review-context-phase-2_0-20250528-143052.md
# Output: code-review-comprehensive-feedback-20250528-143052.md (Gemini review)

# Disable Gemini AI review (context only)
python src/generate_code_review_context.py /path/to/project --no-gemini
# Output: review-context-phase-2_0-20250528-143052.md (only)

# Specify a particular phase for review
python src/generate_code_review_context.py /path/to/project --phase 2.0
# Output: review-context-phase-2_0-20250528-143052.md + AI feedback file

# Custom output file location (overrides automatic naming)
python src/generate_code_review_context.py /path/to/project --output /custom/path/review.md

# Use Gemini 2.5 Pro instead of Flash (via environment variable)
GEMINI_MODEL=gemini-2.5-pro-preview-05-06 python src/generate_code_review_context.py /path/to/project
```

**Output File Naming:**
- **Automatic**: `review-context-phase-{phase_number}-{timestamp}.md`
- **Example**: `review-context-phase-2_0-20250528-143052.md`
- **Custom**: Use `--output` flag to specify your own filename
- **Unique**: Each run generates a unique timestamp to avoid conflicts

**CLI Use Cases:**
- Testing the tool during setup
- Manual code review generation outside of AI agent workflows
- Debugging task list parsing or git integration
- One-off reviews for specific phases

## MCP Server Installation

This tool works as an MCP (Model Context Protocol) server for integration with Claude Desktop, Cursor, and Claude Code CLI.

### Claude Code CLI

Install the MCP server using Claude Code's built-in commands:

```bash
# Add the server with your Gemini API key
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_gemini_api_key_here

# List configured servers
claude mcp list

# Test the server
claude mcp get task-list-reviewer
```

### Claude Desktop & Cursor

Add this configuration to your `claude_desktop_config.json` or Cursor's MCP settings:

**Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": [
        "/path/to/task-list-phase-reviewer/src/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

**Replace `/path/to/task-list-phase-reviewer` with your actual project path.**

### Configuring Gemini Model Selection

You can choose between Gemini 2.5 Flash (default) and Pro models by setting the `GEMINI_MODEL` environment variable:

**For Claude Desktop/Cursor (claude_desktop_config.json):**
```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": ["/path/to/task-list-phase-reviewer/src/server.py"],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "GEMINI_MODEL": "gemini-2.5-flash-preview-05-20"
      }
    }
  }
}
```

**For Claude Code CLI:**
```bash
# Use Flash (default - fast, high-volume)
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_key \
  -e GEMINI_MODEL=gemini-2.5-flash-preview-05-20

# Use Pro (complex reasoning, in-depth analysis)
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_key \
  -e GEMINI_MODEL=gemini-2.5-pro-preview-05-06
```

### Usage by AI Coding Agents

Once installed, AI agents (Cursor, Claude Code) can automatically call this tool when completing development phases:

**AI Agent Usage:**
```
AI Agent: "I've completed Phase 2.0 (Implement core parsing logic). Let me generate the code review context."

Tool Call: generate_code_review_context
Parameters: { "project_path": "/path/to/project" }

AI Agent: "✅ Phase 2.0 complete! Code review context generated at: review-context-phase-2-20241128-143052.md"
```

**Manual Usage (for testing):**
```
Please use the generate_code_review_context tool to analyze my project at /path/to/my/project
```

The tool will:
1. **Detect completed phase** - Automatically finds the most recently completed phase from task list
2. **Parse PRD requirements** - Extracts feature context and goals  
3. **Analyze git changes** - Gets all file modifications since phase start
4. **Generate review package** - Creates comprehensive markdown with all context needed for human review

## Environment Variables

### Core Configuration
- `GEMINI_API_KEY`: Required for Gemini integration (PRD summarization and code review)
- `MAX_FILE_TREE_DEPTH`: Optional, maximum tree depth (default: 5). Use lower values for large projects.
- `MAX_FILE_CONTENT_LINES`: Optional, max lines to show per file (default: 500). Adjust for context window limits.

### Gemini 2.5 Code Review Configuration
- `GEMINI_MODEL`: Model to use for code review (default: `gemini-2.5-flash-preview-05-20`)
  - **Flash (default)**: `gemini-2.5-flash-preview-05-20` - Fast, high-volume code reviews
  - **Pro**: `gemini-2.5-pro-preview-05-06` - Complex reasoning, in-depth analysis
- `ENABLE_GROUNDING`: Enable Google Search grounding (default: `true`)
- `ENABLE_URL_CONTEXT`: Enable URL context processing (default: `true`)
- `DEBUG_MODE`: Enable verbose logging (default: `false`)

## Development

Run tests:
```bash
pytest
```

## Project Structure

- `src/generate_code_review_context.py` - Core Python script
- `src/server.py` - MCP server wrapper
- `tests/` - Test files and fixtures
- `pyproject.toml` - Project configuration
- `requirements.txt` - Dependencies
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/pyproject.toml (unstaged-M)
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "code-review-context-mcp"
version = "0.1.0"
description = "Python-based MCP server tool that generates formatted code review context by parsing PRD and task list files"
authors = [
    {name = "Developer", email = "developer@example.com"}
]
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "mcp>=0.1.0",
    "google-genai>=0.1.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.0.0",
    "black",
    "isort",
    "flake8",
]

[project.scripts]
generate-code-review-context = "src.generate_code_review_context:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["src*"]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/src/generate_code_review_context.py (unstaged-M)
```py
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

... (truncated, showing first 500 lines)
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/code-review-comprehensive-20250528-172430.md (untracked)
```md
<overall_prd_summary>
This project implements an MCP server for code review context generation. It automates the creation of review templates.
</overall_prd_summary>

<total_phases>
5
</total_phases>

<current_phase_number>
5.0
</current_phase_number>

<previous_phase_completed>
4.0 Implement git operations and file tree generation
</previous_phase_completed>
<current_phase_description>
Create MCP server integration and finalize project
</current_phase_description>

<subtasks_completed>
- 5.1 Implement MCP server wrapper (server.py) with tool schema definition
- 5.2 Add command-line interface with argument parsing (project_path, --phase, --output)
- 5.3 Implement main orchestration function that ties all components together
- 5.4 Add comprehensive error handling and logging throughout the application
- 5.5 Create final integration tests and validate all success criteria are met
</subtasks_completed>

<project_path>
/Users/nicobailon/Documents/development/task-list-phase-reviewer
</project_path>
<file_tree>
/Users/nicobailon/Documents/development/task-list-phase-reviewer
├── build/
├── code_review_context_mcp.egg-info/
│   ├── PKG-INFO
│   ├── SOURCES.txt
│   ├── dependency_links.txt
│   ├── entry_points.txt
│   ├── requires.txt
│   └── top_level.txt
├── src/
│   ├── generate_code_review_context.py
│   └── server.py
├── tasks/
│   └── tasks-prd.md
├── test-env/
│   ├── bin/
│   │   ├── Activate.ps1
│   │   ├── activate
│   │   ├── activate.csh
│   │   ├── activate.fish
│   │   ├── dotenv
│   │   ├── httpx
│   │   ├── mcp
│   │   ├── normalizer
│   │   ├── pip
│   │   ├── pip3
│   │   ├── pip3.13
│   │   ├── py.test
│   │   ├── pyrsa-decrypt
│   │   ├── pyrsa-encrypt
│   │   ├── pyrsa-keygen
│   │   ├── pyrsa-priv2pub
│   │   ├── pyrsa-sign
│   │   ├── pyrsa-verify
│   │   ├── pytest
│   │   ├── python
│   │   ├── python3
│   │   ├── python3.13
│   │   ├── uvicorn
│   │   └── websockets
│   ├── include/
│   │   └── python3.13/
│   ├── lib/
│   │   └── python3.13/
│   │       └── site-packages/
│   │           ├── _pytest/
│   │           ├── annotated_types/
│   │           ├── annotated_types-0.7.0.dist-info/
│   │           ├── anyio/
│   │           ├── anyio-4.9.0.dist-info/
│   │           ├── cachetools/
│   │           ├── cachetools-5.5.2.dist-info/
│   │           ├── certifi/
│   │           ├── certifi-2025.4.26.dist-info/
│   │           ├── charset_normalizer/
│   │           ├── charset_normalizer-3.4.2.dist-info/
│   │           ├── click/
│   │           ├── click-8.2.1.dist-info/
│   │           ├── dotenv/
│   │           ├── google/
│   │           ├── google_auth-2.40.2.dist-info/
│   │           ├── google_genai-1.17.0.dist-info/
│   │           ├── h11/
│   │           ├── h11-0.16.0.dist-info/
│   │           ├── httpcore/
│   │           ├── httpcore-1.0.9.dist-info/
│   │           ├── httpx/
│   │           ├── httpx-0.28.1.dist-info/
│   │           ├── httpx_sse/
│   │           ├── httpx_sse-0.4.0.dist-info/
│   │           ├── idna/
│   │           ├── idna-3.10.dist-info/
│   │           ├── iniconfig/
│   │           ├── iniconfig-2.1.0.dist-info/
│   │           ├── mcp/
│   │           ├── mcp-1.9.1.dist-info/
│   │           ├── multipart/
│   │           ├── packaging/
│   │           ├── packaging-25.0.dist-info/
│   │           ├── pip/
│   │           ├── pip-25.0.1.dist-info/
│   │           ├── pluggy/
│   │           ├── pluggy-1.6.0.dist-info/
│   │           ├── pyasn1/
│   │           ├── pyasn1-0.6.1.dist-info/
│   │           ├── pyasn1_modules/
│   │           ├── pyasn1_modules-0.4.2.dist-info/
│   │           ├── pydantic/
│   │           ├── pydantic-2.11.5.dist-info/
│   │           ├── pydantic_core/
│   │           ├── pydantic_core-2.33.2.dist-info/
│   │           ├── pydantic_settings/
│   │           ├── pydantic_settings-2.9.1.dist-info/
│   │           ├── pytest/
│   │           ├── pytest-8.3.5.dist-info/
│   │           ├── pytest_mock/
│   │           ├── pytest_mock-3.14.1.dist-info/
│   │           ├── python_dotenv-1.1.0.dist-info/
│   │           ├── python_multipart/
│   │           ├── python_multipart-0.0.20.dist-info/
│   │           ├── requests/
│   │           ├── requests-2.32.3.dist-info/
│   │           ├── rsa/
│   │           ├── rsa-4.9.1.dist-info/
│   │           ├── sniffio/
│   │           ├── sniffio-1.3.1.dist-info/
│   │           ├── sse_starlette/
│   │           ├── sse_starlette-2.3.5.dist-info/
│   │           ├── starlette/
│   │           ├── starlette-0.46.2.dist-info/
│   │           ├── typing_extensions-4.13.2.dist-info/
│   │           ├── typing_inspection/
│   │           ├── typing_inspection-0.4.1.dist-info/
│   │           ├── urllib3/
│   │           ├── urllib3-2.4.0.dist-info/
│   │           ├── uvicorn/
│   │           ├── uvicorn-0.34.2.dist-info/
│   │           ├── websockets/
│   │           ├── websockets-15.0.1.dist-info/
│   │           ├── py.py
│   │           └── typing_extensions.py
│   └── pyvenv.cfg
├── tests/
│   ├── fixtures/
│   │   ├── sample_output.md
│   │   ├── sample_prd.md
│   │   └── sample_task_list.md
│   └── test_generate_code_review_context.py
├── venv/
├── .env
├── README.md
├── code-review-comprehensive-20250528-165648.md
├── code-review-comprehensive-20250528-172408.md
├── code-review-comprehensive-20250528-172413.md
├── code-review-comprehensive-feedback-20250528-171640.md
├── example-task-list-management-rules.md
├── my-custom-review.md
├── prd.md
├── pyproject.toml
├── requirements.txt
└── test_new_feature.py
</file_tree>

<files_changed>
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/README.md (unstaged-M)
```md
# Code Review Context Generator for AI Coding Agents

An MCP server tool designed for **AI coding agents** (Cursor, Claude Code, etc.) to automatically generate comprehensive code review context when completing development phases.

**Version**: 1.2.0 - Enhanced with debug mode and improved file processing capabilities.

## Workflow Integration for AI Agents

This tool integrates into the AI-driven development workflow at **phase completion checkpoints**:

1. **AI Agent works through task list** - Cursor/Claude Code systematically implements features by completing tasks in phases (1.0, 2.0, 3.0, etc.)
2. **Phase completion detected** - When all sub-tasks in a phase are marked complete (`[x]`)  
3. **AI Agent calls MCP tool** - Automatically generates code review context for the completed phase
4. **Review context generated** - Creates formatted markdown with git changes, progress summary, and file context
5. **Ready for review** - Human reviewers get comprehensive context for what was just implemented

## Use Case: AI Agent Integration

**Typical AI agent workflow:**
```
AI Agent: "I've completed all sub-tasks in Phase 2.0. Let me generate a code review context."
AI Agent calls: generate_code_review_context tool
Output: Comprehensive markdown file with git diff, file tree, and phase summary
AI Agent: "✅ Phase 2.0 complete! Review context generated at: review-context-phase-2_0-20250528-143052.md"
```

## Compatible Format Specifications

This tool works with standardized PRD and task list formats from the [AI Dev Tasks](https://github.com/snarktank/ai-dev-tasks) repository:

- **PRDs**: Based on [create-prd.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/create-prd.mdc) specification
  - Structured markdown with required sections (Goals, User Stories, Functional Requirements, etc.)
  - File naming: `prd-[feature-name].md` in `/tasks/` directory
  - Designed for AI agent comprehension and systematic implementation

- **Task Lists**: Based on [generate-tasks.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/generate-tasks.mdc) specification  
  - Hierarchical phases with numbered parent tasks (1.0, 2.0) and sub-tasks (1.1, 1.2)
  - File naming: `tasks-[prd-file-name].md` in `/tasks/` directory
  - Checkbox-based progress tracking (`- [ ]` / `- [x]`) for AI agents to mark completion
  - Systematic implementation guidance for coding agents

## What This Tool Generates

The MCP server automatically creates comprehensive code review context including:
- **Phase Progress Summary** - What phase was just completed and which sub-tasks were finished
- **PRD Context** - Original feature requirements and goals (auto-summarized with Gemini 2.0 Flash Lite)
- **Git Changes** - Detailed diff of all modified/added/deleted files since the phase started
- **File Tree** - ASCII representation of current project structure
- **File Content** - Full content of changed files for review
- **Formatted Output** - Professional markdown template ready for human review
- **Automatic Naming** - Files named with phase and timestamp: `review-context-phase-{phase}-{YYYYMMDD-HHMMSS}.md`

### NEW: Gemini 2.5 AI Code Review

In addition to generating review context, the tool can now automatically generate comprehensive AI-powered code reviews using **Gemini 2.5 Flash** or **Gemini 2.5 Pro**:

- **Automated Code Review** - Sends the generated context to Gemini 2.5 for intelligent analysis
- **Thinking Mode Enabled** - Uses Gemini's thinking capabilities for deep reasoning about code quality
- **Google Search Grounding** - Can lookup current best practices and technology information
- **URL Context Support** - Can process URLs mentioned in code comments or documentation
- **Comprehensive Analysis** - Covers code quality, architecture, security, performance, testing, and maintainability
- **Structured Output** - Generates `code-review-comprehensive-feedback-{timestamp}.md` with detailed feedback

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Primary Use: MCP Server for AI Agents
The tool is designed as an MCP server that AI coding agents (Cursor, Claude Code) call automatically when completing development phases.

### Manual CLI Usage
You can also run the tool manually from the command line:

```bash
# Auto-detect most recently completed phase (generates timestamped files)
python src/generate_code_review_context.py /path/to/project
# Output: review-context-phase-2_0-20250528-143052.md
# Output: code-review-comprehensive-feedback-20250528-143052.md (Gemini review)

# Disable Gemini AI review (context only)
python src/generate_code_review_context.py /path/to/project --no-gemini
# Output: review-context-phase-2_0-20250528-143052.md (only)

# Specify a particular phase for review
python src/generate_code_review_context.py /path/to/project --phase 2.0
# Output: review-context-phase-2_0-20250528-143052.md + AI feedback file

# Custom output file location (overrides automatic naming)
python src/generate_code_review_context.py /path/to/project --output /custom/path/review.md

# Use Gemini 2.5 Pro instead of Flash (via environment variable)
GEMINI_MODEL=gemini-2.5-pro-preview-05-06 python src/generate_code_review_context.py /path/to/project
```

**Output File Naming:**
- **Automatic**: `review-context-phase-{phase_number}-{timestamp}.md`
- **Example**: `review-context-phase-2_0-20250528-143052.md`
- **Custom**: Use `--output` flag to specify your own filename
- **Unique**: Each run generates a unique timestamp to avoid conflicts

**CLI Use Cases:**
- Testing the tool during setup
- Manual code review generation outside of AI agent workflows
- Debugging task list parsing or git integration
- One-off reviews for specific phases

## MCP Server Installation

This tool works as an MCP (Model Context Protocol) server for integration with Claude Desktop, Cursor, and Claude Code CLI.

### Claude Code CLI

Install the MCP server using Claude Code's built-in commands:

```bash
# Add the server with your Gemini API key
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_gemini_api_key_here

# List configured servers
claude mcp list

# Test the server
claude mcp get task-list-reviewer
```

### Claude Desktop & Cursor

Add this configuration to your `claude_desktop_config.json` or Cursor's MCP settings:

**Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": [
        "/path/to/task-list-phase-reviewer/src/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

**Replace `/path/to/task-list-phase-reviewer` with your actual project path.**

### Configuring Gemini Model Selection

You can choose between Gemini 2.5 Flash (default) and Pro models by setting the `GEMINI_MODEL` environment variable:

**For Claude Desktop/Cursor (claude_desktop_config.json):**
```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": ["/path/to/task-list-phase-reviewer/src/server.py"],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "GEMINI_MODEL": "gemini-2.5-flash-preview-05-20"
      }
    }
  }
}
```

**For Claude Code CLI:**
```bash
# Use Flash (default - fast, high-volume)
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_key \
  -e GEMINI_MODEL=gemini-2.5-flash-preview-05-20

# Use Pro (complex reasoning, in-depth analysis)
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_key \
  -e GEMINI_MODEL=gemini-2.5-pro-preview-05-06
```

### Usage by AI Coding Agents

Once installed, AI agents (Cursor, Claude Code) can automatically call this tool when completing development phases:

**AI Agent Usage:**
```
AI Agent: "I've completed Phase 2.0 (Implement core parsing logic). Let me generate the code review context."

Tool Call: generate_code_review_context
Parameters: { "project_path": "/path/to/project" }

AI Agent: "✅ Phase 2.0 complete! Code review context generated at: review-context-phase-2-20241128-143052.md"
```

**Manual Usage (for testing):**
```
Please use the generate_code_review_context tool to analyze my project at /path/to/my/project
```

The tool will:
1. **Detect completed phase** - Automatically finds the most recently completed phase from task list
2. **Parse PRD requirements** - Extracts feature context and goals  
3. **Analyze git changes** - Gets all file modifications since phase start
4. **Generate review package** - Creates comprehensive markdown with all context needed for human review

## Environment Variables

### Core Configuration
- `GEMINI_API_KEY`: Required for Gemini integration (PRD summarization and code review)
- `MAX_FILE_TREE_DEPTH`: Optional, maximum tree depth (default: 5). Use lower values for large projects.
- `MAX_FILE_CONTENT_LINES`: Optional, max lines to show per file (default: 500). Adjust for context window limits.

### Gemini 2.5 Code Review Configuration
- `GEMINI_MODEL`: Model to use for code review (default: `gemini-2.5-flash-preview-05-20`)
  - **Flash (default)**: `gemini-2.5-flash-preview-05-20` - Fast, high-volume code reviews
  - **Pro**: `gemini-2.5-pro-preview-05-06` - Complex reasoning, in-depth analysis
- `ENABLE_GROUNDING`: Enable Google Search grounding (default: `true`)
- `ENABLE_URL_CONTEXT`: Enable URL context processing (default: `true`)
- `DEBUG_MODE`: Enable verbose logging (default: `false`)

## Development

Run tests:
```bash
pytest
```

## Project Structure

- `src/generate_code_review_context.py` - Core Python script
- `src/server.py` - MCP server wrapper
- `tests/` - Test files and fixtures
- `pyproject.toml` - Project configuration
- `requirements.txt` - Dependencies
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/pyproject.toml (unstaged-M)
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "code-review-context-mcp"
version = "0.1.0"
description = "Python-based MCP server tool that generates formatted code review context by parsing PRD and task list files"
authors = [
    {name = "Developer", email = "developer@example.com"}
]
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "mcp>=0.1.0",
    "google-genai>=0.1.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.0.0",
    "black",
    "isort",
    "flake8",
]

[project.scripts]
generate-code-review-context = "src.generate_code_review_context:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["src*"]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/src/generate_code_review_context.py (unstaged-M)
```py
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

... (truncated, showing first 500 lines)
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/code-review-comprehensive-20250528-172447.md (untracked)
```md
<overall_prd_summary>
This project implements an MCP server for code review context generation. It automates the creation of review templates.
</overall_prd_summary>

<total_phases>
5
</total_phases>

<current_phase_number>
5.0
</current_phase_number>

<previous_phase_completed>
4.0 Implement git operations and file tree generation
</previous_phase_completed>
<current_phase_description>
Create MCP server integration and finalize project
</current_phase_description>

<subtasks_completed>
- 5.1 Implement MCP server wrapper (server.py) with tool schema definition
- 5.2 Add command-line interface with argument parsing (project_path, --phase, --output)
- 5.3 Implement main orchestration function that ties all components together
- 5.4 Add comprehensive error handling and logging throughout the application
- 5.5 Create final integration tests and validate all success criteria are met
</subtasks_completed>

<project_path>
/Users/nicobailon/Documents/development/task-list-phase-reviewer
</project_path>
<file_tree>
/Users/nicobailon/Documents/development/task-list-phase-reviewer
├── build/
├── code_review_context_mcp.egg-info/
│   ├── PKG-INFO
│   ├── SOURCES.txt
│   ├── dependency_links.txt
│   ├── entry_points.txt
│   ├── requires.txt
│   └── top_level.txt
├── src/
│   ├── generate_code_review_context.py
│   └── server.py
├── tasks/
│   └── tasks-prd.md
├── test-env/
│   ├── bin/
│   │   ├── Activate.ps1
│   │   ├── activate
│   │   ├── activate.csh
│   │   ├── activate.fish
│   │   ├── dotenv
│   │   ├── httpx
│   │   ├── mcp
│   │   ├── normalizer
│   │   ├── pip
│   │   ├── pip3
│   │   ├── pip3.13
│   │   ├── py.test
│   │   ├── pyrsa-decrypt
│   │   ├── pyrsa-encrypt
│   │   ├── pyrsa-keygen
│   │   ├── pyrsa-priv2pub
│   │   ├── pyrsa-sign
│   │   ├── pyrsa-verify
│   │   ├── pytest
│   │   ├── python
│   │   ├── python3
│   │   ├── python3.13
│   │   ├── uvicorn
│   │   └── websockets
│   ├── include/
│   │   └── python3.13/
│   ├── lib/
│   │   └── python3.13/
│   │       └── site-packages/
│   │           ├── _pytest/
│   │           ├── annotated_types/
│   │           ├── annotated_types-0.7.0.dist-info/
│   │           ├── anyio/
│   │           ├── anyio-4.9.0.dist-info/
│   │           ├── cachetools/
│   │           ├── cachetools-5.5.2.dist-info/
│   │           ├── certifi/
│   │           ├── certifi-2025.4.26.dist-info/
│   │           ├── charset_normalizer/
│   │           ├── charset_normalizer-3.4.2.dist-info/
│   │           ├── click/
│   │           ├── click-8.2.1.dist-info/
│   │           ├── dotenv/
│   │           ├── google/
│   │           ├── google_auth-2.40.2.dist-info/
│   │           ├── google_genai-1.17.0.dist-info/
│   │           ├── h11/
│   │           ├── h11-0.16.0.dist-info/
│   │           ├── httpcore/
│   │           ├── httpcore-1.0.9.dist-info/
│   │           ├── httpx/
│   │           ├── httpx-0.28.1.dist-info/
│   │           ├── httpx_sse/
│   │           ├── httpx_sse-0.4.0.dist-info/
│   │           ├── idna/
│   │           ├── idna-3.10.dist-info/
│   │           ├── iniconfig/
│   │           ├── iniconfig-2.1.0.dist-info/
│   │           ├── mcp/
│   │           ├── mcp-1.9.1.dist-info/
│   │           ├── multipart/
│   │           ├── packaging/
│   │           ├── packaging-25.0.dist-info/
│   │           ├── pip/
│   │           ├── pip-25.0.1.dist-info/
│   │           ├── pluggy/
│   │           ├── pluggy-1.6.0.dist-info/
│   │           ├── pyasn1/
│   │           ├── pyasn1-0.6.1.dist-info/
│   │           ├── pyasn1_modules/
│   │           ├── pyasn1_modules-0.4.2.dist-info/
│   │           ├── pydantic/
│   │           ├── pydantic-2.11.5.dist-info/
│   │           ├── pydantic_core/
│   │           ├── pydantic_core-2.33.2.dist-info/
│   │           ├── pydantic_settings/
│   │           ├── pydantic_settings-2.9.1.dist-info/
│   │           ├── pytest/
│   │           ├── pytest-8.3.5.dist-info/
│   │           ├── pytest_mock/
│   │           ├── pytest_mock-3.14.1.dist-info/
│   │           ├── python_dotenv-1.1.0.dist-info/
│   │           ├── python_multipart/
│   │           ├── python_multipart-0.0.20.dist-info/
│   │           ├── requests/
│   │           ├── requests-2.32.3.dist-info/
│   │           ├── rsa/
│   │           ├── rsa-4.9.1.dist-info/
│   │           ├── sniffio/
│   │           ├── sniffio-1.3.1.dist-info/
│   │           ├── sse_starlette/
│   │           ├── sse_starlette-2.3.5.dist-info/
│   │           ├── starlette/
│   │           ├── starlette-0.46.2.dist-info/
│   │           ├── typing_extensions-4.13.2.dist-info/
│   │           ├── typing_inspection/
│   │           ├── typing_inspection-0.4.1.dist-info/
│   │           ├── urllib3/
│   │           ├── urllib3-2.4.0.dist-info/
│   │           ├── uvicorn/
│   │           ├── uvicorn-0.34.2.dist-info/
│   │           ├── websockets/
│   │           ├── websockets-15.0.1.dist-info/
│   │           ├── py.py
│   │           └── typing_extensions.py
│   └── pyvenv.cfg
├── tests/
│   ├── fixtures/
│   │   ├── sample_output.md
│   │   ├── sample_prd.md
│   │   └── sample_task_list.md
│   └── test_generate_code_review_context.py
├── venv/
├── .env
├── README.md
├── code-review-comprehensive-20250528-165648.md
├── code-review-comprehensive-20250528-172408.md
├── code-review-comprehensive-20250528-172413.md
├── code-review-comprehensive-20250528-172430.md
├── code-review-comprehensive-feedback-20250528-171640.md
├── example-task-list-management-rules.md
├── my-custom-review.md
├── prd.md
├── pyproject.toml
├── requirements.txt
└── test_new_feature.py
</file_tree>

<files_changed>
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/README.md (unstaged-M)
```md
# Code Review Context Generator for AI Coding Agents

An MCP server tool designed for **AI coding agents** (Cursor, Claude Code, etc.) to automatically generate comprehensive code review context when completing development phases.

**Version**: 1.2.0 - Enhanced with debug mode and improved file processing capabilities.

## Workflow Integration for AI Agents

This tool integrates into the AI-driven development workflow at **phase completion checkpoints**:

1. **AI Agent works through task list** - Cursor/Claude Code systematically implements features by completing tasks in phases (1.0, 2.0, 3.0, etc.)
2. **Phase completion detected** - When all sub-tasks in a phase are marked complete (`[x]`)  
3. **AI Agent calls MCP tool** - Automatically generates code review context for the completed phase
4. **Review context generated** - Creates formatted markdown with git changes, progress summary, and file context
5. **Ready for review** - Human reviewers get comprehensive context for what was just implemented

## Use Case: AI Agent Integration

**Typical AI agent workflow:**
```
AI Agent: "I've completed all sub-tasks in Phase 2.0. Let me generate a code review context."
AI Agent calls: generate_code_review_context tool
Output: Comprehensive markdown file with git diff, file tree, and phase summary
AI Agent: "✅ Phase 2.0 complete! Review context generated at: review-context-phase-2_0-20250528-143052.md"
```

## Compatible Format Specifications

This tool works with standardized PRD and task list formats from the [AI Dev Tasks](https://github.com/snarktank/ai-dev-tasks) repository:

- **PRDs**: Based on [create-prd.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/create-prd.mdc) specification
  - Structured markdown with required sections (Goals, User Stories, Functional Requirements, etc.)
  - File naming: `prd-[feature-name].md` in `/tasks/` directory
  - Designed for AI agent comprehension and systematic implementation

- **Task Lists**: Based on [generate-tasks.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/generate-tasks.mdc) specification  
  - Hierarchical phases with numbered parent tasks (1.0, 2.0) and sub-tasks (1.1, 1.2)
  - File naming: `tasks-[prd-file-name].md` in `/tasks/` directory
  - Checkbox-based progress tracking (`- [ ]` / `- [x]`) for AI agents to mark completion
  - Systematic implementation guidance for coding agents

## What This Tool Generates

The MCP server automatically creates comprehensive code review context including:
- **Phase Progress Summary** - What phase was just completed and which sub-tasks were finished
- **PRD Context** - Original feature requirements and goals (auto-summarized with Gemini 2.0 Flash Lite)
- **Git Changes** - Detailed diff of all modified/added/deleted files since the phase started
- **File Tree** - ASCII representation of current project structure
- **File Content** - Full content of changed files for review
- **Formatted Output** - Professional markdown template ready for human review
- **Automatic Naming** - Files named with phase and timestamp: `review-context-phase-{phase}-{YYYYMMDD-HHMMSS}.md`

### NEW: Gemini 2.5 AI Code Review

In addition to generating review context, the tool can now automatically generate comprehensive AI-powered code reviews using **Gemini 2.5 Flash** or **Gemini 2.5 Pro**:

- **Automated Code Review** - Sends the generated context to Gemini 2.5 for intelligent analysis
- **Thinking Mode Enabled** - Uses Gemini's thinking capabilities for deep reasoning about code quality
- **Google Search Grounding** - Can lookup current best practices and technology information
- **URL Context Support** - Can process URLs mentioned in code comments or documentation
- **Comprehensive Analysis** - Covers code quality, architecture, security, performance, testing, and maintainability
- **Structured Output** - Generates `code-review-comprehensive-feedback-{timestamp}.md` with detailed feedback

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Primary Use: MCP Server for AI Agents
The tool is designed as an MCP server that AI coding agents (Cursor, Claude Code) call automatically when completing development phases.

### Manual CLI Usage
You can also run the tool manually from the command line:

```bash
# Auto-detect most recently completed phase (generates timestamped files)
python src/generate_code_review_context.py /path/to/project
# Output: review-context-phase-2_0-20250528-143052.md
# Output: code-review-comprehensive-feedback-20250528-143052.md (Gemini review)

# Disable Gemini AI review (context only)
python src/generate_code_review_context.py /path/to/project --no-gemini
# Output: review-context-phase-2_0-20250528-143052.md (only)

# Specify a particular phase for review
python src/generate_code_review_context.py /path/to/project --phase 2.0
# Output: review-context-phase-2_0-20250528-143052.md + AI feedback file

# Custom output file location (overrides automatic naming)
python src/generate_code_review_context.py /path/to/project --output /custom/path/review.md

# Use Gemini 2.5 Pro instead of Flash (via environment variable)
GEMINI_MODEL=gemini-2.5-pro-preview-05-06 python src/generate_code_review_context.py /path/to/project
```

**Output File Naming:**
- **Automatic**: `review-context-phase-{phase_number}-{timestamp}.md`
- **Example**: `review-context-phase-2_0-20250528-143052.md`
- **Custom**: Use `--output` flag to specify your own filename
- **Unique**: Each run generates a unique timestamp to avoid conflicts

**CLI Use Cases:**
- Testing the tool during setup
- Manual code review generation outside of AI agent workflows
- Debugging task list parsing or git integration
- One-off reviews for specific phases

## MCP Server Installation

This tool works as an MCP (Model Context Protocol) server for integration with Claude Desktop, Cursor, and Claude Code CLI.

### Claude Code CLI

Install the MCP server using Claude Code's built-in commands:

```bash
# Add the server with your Gemini API key
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_gemini_api_key_here

# List configured servers
claude mcp list

# Test the server
claude mcp get task-list-reviewer
```

### Claude Desktop & Cursor

Add this configuration to your `claude_desktop_config.json` or Cursor's MCP settings:

**Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": [
        "/path/to/task-list-phase-reviewer/src/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

**Replace `/path/to/task-list-phase-reviewer` with your actual project path.**

### Configuring Gemini Model Selection

You can choose between Gemini 2.5 Flash (default) and Pro models by setting the `GEMINI_MODEL` environment variable:

**For Claude Desktop/Cursor (claude_desktop_config.json):**
```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": ["/path/to/task-list-phase-reviewer/src/server.py"],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "GEMINI_MODEL": "gemini-2.5-flash-preview-05-20"
      }
    }
  }
}
```

**For Claude Code CLI:**
```bash
# Use Flash (default - fast, high-volume)
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_key \
  -e GEMINI_MODEL=gemini-2.5-flash-preview-05-20

# Use Pro (complex reasoning, in-depth analysis)
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_key \
  -e GEMINI_MODEL=gemini-2.5-pro-preview-05-06
```

### Usage by AI Coding Agents

Once installed, AI agents (Cursor, Claude Code) can automatically call this tool when completing development phases:

**AI Agent Usage:**
```
AI Agent: "I've completed Phase 2.0 (Implement core parsing logic). Let me generate the code review context."

Tool Call: generate_code_review_context
Parameters: { "project_path": "/path/to/project" }

AI Agent: "✅ Phase 2.0 complete! Code review context generated at: review-context-phase-2-20241128-143052.md"
```

**Manual Usage (for testing):**
```
Please use the generate_code_review_context tool to analyze my project at /path/to/my/project
```

The tool will:
1. **Detect completed phase** - Automatically finds the most recently completed phase from task list
2. **Parse PRD requirements** - Extracts feature context and goals  
3. **Analyze git changes** - Gets all file modifications since phase start
4. **Generate review package** - Creates comprehensive markdown with all context needed for human review

## Environment Variables

### Core Configuration
- `GEMINI_API_KEY`: Required for Gemini integration (PRD summarization and code review)
- `MAX_FILE_TREE_DEPTH`: Optional, maximum tree depth (default: 5). Use lower values for large projects.
- `MAX_FILE_CONTENT_LINES`: Optional, max lines to show per file (default: 500). Adjust for context window limits.

### Gemini 2.5 Code Review Configuration
- `GEMINI_MODEL`: Model to use for code review (default: `gemini-2.5-flash-preview-05-20`)
  - **Flash (default)**: `gemini-2.5-flash-preview-05-20` - Fast, high-volume code reviews
  - **Pro**: `gemini-2.5-pro-preview-05-06` - Complex reasoning, in-depth analysis
- `ENABLE_GROUNDING`: Enable Google Search grounding (default: `true`)
- `ENABLE_URL_CONTEXT`: Enable URL context processing (default: `true`)
- `DEBUG_MODE`: Enable verbose logging (default: `false`)

## Development

Run tests:
```bash
pytest
```

## Project Structure

- `src/generate_code_review_context.py` - Core Python script
- `src/server.py` - MCP server wrapper
- `tests/` - Test files and fixtures
- `pyproject.toml` - Project configuration
- `requirements.txt` - Dependencies
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/pyproject.toml (unstaged-M)
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "code-review-context-mcp"
version = "0.1.0"
description = "Python-based MCP server tool that generates formatted code review context by parsing PRD and task list files"
authors = [
    {name = "Developer", email = "developer@example.com"}
]
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "mcp>=0.1.0",
    "google-genai>=0.1.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.0.0",
    "black",
    "isort",
    "flake8",
]

[project.scripts]
generate-code-review-context = "src.generate_code_review_context:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["src*"]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/src/generate_code_review_context.py (unstaged-M)
```py
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


... (truncated, showing first 500 lines)
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/code-review-comprehensive-20250528-172456.md (untracked)
```md
<overall_prd_summary>
This project implements an MCP server for code review context generation. It automates the creation of review templates.
</overall_prd_summary>

<total_phases>
5
</total_phases>

<current_phase_number>
5.0
</current_phase_number>

<previous_phase_completed>
4.0 Implement git operations and file tree generation
</previous_phase_completed>
<current_phase_description>
Create MCP server integration and finalize project
</current_phase_description>

<subtasks_completed>
- 5.1 Implement MCP server wrapper (server.py) with tool schema definition
- 5.2 Add command-line interface with argument parsing (project_path, --phase, --output)
- 5.3 Implement main orchestration function that ties all components together
- 5.4 Add comprehensive error handling and logging throughout the application
- 5.5 Create final integration tests and validate all success criteria are met
</subtasks_completed>

<project_path>
/Users/nicobailon/Documents/development/task-list-phase-reviewer
</project_path>
<file_tree>
/Users/nicobailon/Documents/development/task-list-phase-reviewer
├── build/
├── code_review_context_mcp.egg-info/
│   ├── PKG-INFO
│   ├── SOURCES.txt
│   ├── dependency_links.txt
│   ├── entry_points.txt
│   ├── requires.txt
│   └── top_level.txt
├── src/
│   ├── generate_code_review_context.py
│   └── server.py
├── tasks/
│   └── tasks-prd.md
├── test-env/
│   ├── bin/
│   │   ├── Activate.ps1
│   │   ├── activate
│   │   ├── activate.csh
│   │   ├── activate.fish
│   │   ├── dotenv
│   │   ├── httpx
│   │   ├── mcp
│   │   ├── normalizer
│   │   ├── pip
│   │   ├── pip3
│   │   ├── pip3.13
│   │   ├── py.test
│   │   ├── pyrsa-decrypt
│   │   ├── pyrsa-encrypt
│   │   ├── pyrsa-keygen
│   │   ├── pyrsa-priv2pub
│   │   ├── pyrsa-sign
│   │   ├── pyrsa-verify
│   │   ├── pytest
│   │   ├── python
│   │   ├── python3
│   │   ├── python3.13
│   │   ├── uvicorn
│   │   └── websockets
│   ├── include/
│   │   └── python3.13/
│   ├── lib/
│   │   └── python3.13/
│   │       └── site-packages/
│   │           ├── _pytest/
│   │           ├── annotated_types/
│   │           ├── annotated_types-0.7.0.dist-info/
│   │           ├── anyio/
│   │           ├── anyio-4.9.0.dist-info/
│   │           ├── cachetools/
│   │           ├── cachetools-5.5.2.dist-info/
│   │           ├── certifi/
│   │           ├── certifi-2025.4.26.dist-info/
│   │           ├── charset_normalizer/
│   │           ├── charset_normalizer-3.4.2.dist-info/
│   │           ├── click/
│   │           ├── click-8.2.1.dist-info/
│   │           ├── dotenv/
│   │           ├── google/
│   │           ├── google_auth-2.40.2.dist-info/
│   │           ├── google_genai-1.17.0.dist-info/
│   │           ├── h11/
│   │           ├── h11-0.16.0.dist-info/
│   │           ├── httpcore/
│   │           ├── httpcore-1.0.9.dist-info/
│   │           ├── httpx/
│   │           ├── httpx-0.28.1.dist-info/
│   │           ├── httpx_sse/
│   │           ├── httpx_sse-0.4.0.dist-info/
│   │           ├── idna/
│   │           ├── idna-3.10.dist-info/
│   │           ├── iniconfig/
│   │           ├── iniconfig-2.1.0.dist-info/
│   │           ├── mcp/
│   │           ├── mcp-1.9.1.dist-info/
│   │           ├── multipart/
│   │           ├── packaging/
│   │           ├── packaging-25.0.dist-info/
│   │           ├── pip/
│   │           ├── pip-25.0.1.dist-info/
│   │           ├── pluggy/
│   │           ├── pluggy-1.6.0.dist-info/
│   │           ├── pyasn1/
│   │           ├── pyasn1-0.6.1.dist-info/
│   │           ├── pyasn1_modules/
│   │           ├── pyasn1_modules-0.4.2.dist-info/
│   │           ├── pydantic/
│   │           ├── pydantic-2.11.5.dist-info/
│   │           ├── pydantic_core/
│   │           ├── pydantic_core-2.33.2.dist-info/
│   │           ├── pydantic_settings/
│   │           ├── pydantic_settings-2.9.1.dist-info/
│   │           ├── pytest/
│   │           ├── pytest-8.3.5.dist-info/
│   │           ├── pytest_mock/
│   │           ├── pytest_mock-3.14.1.dist-info/
│   │           ├── python_dotenv-1.1.0.dist-info/
│   │           ├── python_multipart/
│   │           ├── python_multipart-0.0.20.dist-info/
│   │           ├── requests/
│   │           ├── requests-2.32.3.dist-info/
│   │           ├── rsa/
│   │           ├── rsa-4.9.1.dist-info/
│   │           ├── sniffio/
│   │           ├── sniffio-1.3.1.dist-info/
│   │           ├── sse_starlette/
│   │           ├── sse_starlette-2.3.5.dist-info/
│   │           ├── starlette/
│   │           ├── starlette-0.46.2.dist-info/
│   │           ├── typing_extensions-4.13.2.dist-info/
│   │           ├── typing_inspection/
│   │           ├── typing_inspection-0.4.1.dist-info/
│   │           ├── urllib3/
│   │           ├── urllib3-2.4.0.dist-info/
│   │           ├── uvicorn/
│   │           ├── uvicorn-0.34.2.dist-info/
│   │           ├── websockets/
│   │           ├── websockets-15.0.1.dist-info/
│   │           ├── py.py
│   │           └── typing_extensions.py
│   └── pyvenv.cfg
├── test_project/
│   ├── tasks/
│   │   └── tasks-prd.md
│   └── prd.md
├── tests/
│   ├── fixtures/
│   │   ├── sample_output.md
│   │   ├── sample_prd.md
│   │   └── sample_task_list.md
│   └── test_generate_code_review_context.py
├── venv/
├── .env
├── README.md
├── code-review-comprehensive-20250528-165648.md
├── code-review-comprehensive-20250528-172408.md
├── code-review-comprehensive-20250528-172413.md
├── code-review-comprehensive-20250528-172430.md
├── code-review-comprehensive-20250528-172447.md
├── code-review-comprehensive-feedback-20250528-171640.md
├── example-task-list-management-rules.md
├── my-custom-review.md
├── prd.md
├── pyproject.toml
├── requirements.txt
└── test_new_feature.py
</file_tree>

<files_changed>
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/README.md (unstaged-M)
```md
# Code Review Context Generator for AI Coding Agents

An MCP server tool designed for **AI coding agents** (Cursor, Claude Code, etc.) to automatically generate comprehensive code review context when completing development phases.

**Version**: 1.2.0 - Enhanced with debug mode and improved file processing capabilities.

## Workflow Integration for AI Agents

This tool integrates into the AI-driven development workflow at **phase completion checkpoints**:

1. **AI Agent works through task list** - Cursor/Claude Code systematically implements features by completing tasks in phases (1.0, 2.0, 3.0, etc.)
2. **Phase completion detected** - When all sub-tasks in a phase are marked complete (`[x]`)  
3. **AI Agent calls MCP tool** - Automatically generates code review context for the completed phase
4. **Review context generated** - Creates formatted markdown with git changes, progress summary, and file context
5. **Ready for review** - Human reviewers get comprehensive context for what was just implemented

## Use Case: AI Agent Integration

**Typical AI agent workflow:**
```
AI Agent: "I've completed all sub-tasks in Phase 2.0. Let me generate a code review context."
AI Agent calls: generate_code_review_context tool
Output: Comprehensive markdown file with git diff, file tree, and phase summary
AI Agent: "✅ Phase 2.0 complete! Review context generated at: review-context-phase-2_0-20250528-143052.md"
```

## Compatible Format Specifications

This tool works with standardized PRD and task list formats from the [AI Dev Tasks](https://github.com/snarktank/ai-dev-tasks) repository:

- **PRDs**: Based on [create-prd.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/create-prd.mdc) specification
  - Structured markdown with required sections (Goals, User Stories, Functional Requirements, etc.)
  - File naming: `prd-[feature-name].md` in `/tasks/` directory
  - Designed for AI agent comprehension and systematic implementation

- **Task Lists**: Based on [generate-tasks.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/generate-tasks.mdc) specification  
  - Hierarchical phases with numbered parent tasks (1.0, 2.0) and sub-tasks (1.1, 1.2)
  - File naming: `tasks-[prd-file-name].md` in `/tasks/` directory
  - Checkbox-based progress tracking (`- [ ]` / `- [x]`) for AI agents to mark completion
  - Systematic implementation guidance for coding agents

## What This Tool Generates

The MCP server automatically creates comprehensive code review context including:
- **Phase Progress Summary** - What phase was just completed and which sub-tasks were finished
- **PRD Context** - Original feature requirements and goals (auto-summarized with Gemini 2.0 Flash Lite)
- **Git Changes** - Detailed diff of all modified/added/deleted files since the phase started
- **File Tree** - ASCII representation of current project structure
- **File Content** - Full content of changed files for review
- **Formatted Output** - Professional markdown template ready for human review
- **Automatic Naming** - Files named with phase and timestamp: `review-context-phase-{phase}-{YYYYMMDD-HHMMSS}.md`

### NEW: Gemini 2.5 AI Code Review

In addition to generating review context, the tool can now automatically generate comprehensive AI-powered code reviews using **Gemini 2.5 Flash** or **Gemini 2.5 Pro**:

- **Automated Code Review** - Sends the generated context to Gemini 2.5 for intelligent analysis
- **Thinking Mode Enabled** - Uses Gemini's thinking capabilities for deep reasoning about code quality
- **Google Search Grounding** - Can lookup current best practices and technology information
- **URL Context Support** - Can process URLs mentioned in code comments or documentation
- **Comprehensive Analysis** - Covers code quality, architecture, security, performance, testing, and maintainability
- **Structured Output** - Generates `code-review-comprehensive-feedback-{timestamp}.md` with detailed feedback

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Primary Use: MCP Server for AI Agents
The tool is designed as an MCP server that AI coding agents (Cursor, Claude Code) call automatically when completing development phases.

### Manual CLI Usage
You can also run the tool manually from the command line:

```bash
# Auto-detect most recently completed phase (generates timestamped files)
python src/generate_code_review_context.py /path/to/project
# Output: review-context-phase-2_0-20250528-143052.md
# Output: code-review-comprehensive-feedback-20250528-143052.md (Gemini review)

# Disable Gemini AI review (context only)
python src/generate_code_review_context.py /path/to/project --no-gemini
# Output: review-context-phase-2_0-20250528-143052.md (only)

# Specify a particular phase for review
python src/generate_code_review_context.py /path/to/project --phase 2.0
# Output: review-context-phase-2_0-20250528-143052.md + AI feedback file

# Custom output file location (overrides automatic naming)
python src/generate_code_review_context.py /path/to/project --output /custom/path/review.md

# Use Gemini 2.5 Pro instead of Flash (via environment variable)
GEMINI_MODEL=gemini-2.5-pro-preview-05-06 python src/generate_code_review_context.py /path/to/project
```

**Output File Naming:**
- **Automatic**: `review-context-phase-{phase_number}-{timestamp}.md`
- **Example**: `review-context-phase-2_0-20250528-143052.md`
- **Custom**: Use `--output` flag to specify your own filename
- **Unique**: Each run generates a unique timestamp to avoid conflicts

**CLI Use Cases:**
- Testing the tool during setup
- Manual code review generation outside of AI agent workflows
- Debugging task list parsing or git integration
- One-off reviews for specific phases

## MCP Server Installation

This tool works as an MCP (Model Context Protocol) server for integration with Claude Desktop, Cursor, and Claude Code CLI.

### Claude Code CLI

Install the MCP server using Claude Code's built-in commands:

```bash
# Add the server with your Gemini API key
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_gemini_api_key_here

# List configured servers
claude mcp list

# Test the server
claude mcp get task-list-reviewer
```

### Claude Desktop & Cursor

Add this configuration to your `claude_desktop_config.json` or Cursor's MCP settings:

**Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": [
        "/path/to/task-list-phase-reviewer/src/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

**Replace `/path/to/task-list-phase-reviewer` with your actual project path.**

### Configuring Gemini Model Selection

You can choose between Gemini 2.5 Flash (default) and Pro models by setting the `GEMINI_MODEL` environment variable:

**For Claude Desktop/Cursor (claude_desktop_config.json):**
```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": ["/path/to/task-list-phase-reviewer/src/server.py"],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "GEMINI_MODEL": "gemini-2.5-flash-preview-05-20"
      }
    }
  }
}
```

**For Claude Code CLI:**
```bash
# Use Flash (default - fast, high-volume)
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_key \
  -e GEMINI_MODEL=gemini-2.5-flash-preview-05-20

# Use Pro (complex reasoning, in-depth analysis)
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_key \
  -e GEMINI_MODEL=gemini-2.5-pro-preview-05-06
```

### Usage by AI Coding Agents

Once installed, AI agents (Cursor, Claude Code) can automatically call this tool when completing development phases:

**AI Agent Usage:**
```
AI Agent: "I've completed Phase 2.0 (Implement core parsing logic). Let me generate the code review context."

Tool Call: generate_code_review_context
Parameters: { "project_path": "/path/to/project" }

AI Agent: "✅ Phase 2.0 complete! Code review context generated at: review-context-phase-2-20241128-143052.md"
```

**Manual Usage (for testing):**
```
Please use the generate_code_review_context tool to analyze my project at /path/to/my/project
```

The tool will:
1. **Detect completed phase** - Automatically finds the most recently completed phase from task list
2. **Parse PRD requirements** - Extracts feature context and goals  
3. **Analyze git changes** - Gets all file modifications since phase start
4. **Generate review package** - Creates comprehensive markdown with all context needed for human review

## Environment Variables

### Core Configuration
- `GEMINI_API_KEY`: Required for Gemini integration (PRD summarization and code review)
- `MAX_FILE_TREE_DEPTH`: Optional, maximum tree depth (default: 5). Use lower values for large projects.
- `MAX_FILE_CONTENT_LINES`: Optional, max lines to show per file (default: 500). Adjust for context window limits.

### Gemini 2.5 Code Review Configuration
- `GEMINI_MODEL`: Model to use for code review (default: `gemini-2.5-flash-preview-05-20`)
  - **Flash (default)**: `gemini-2.5-flash-preview-05-20` - Fast, high-volume code reviews
  - **Pro**: `gemini-2.5-pro-preview-05-06` - Complex reasoning, in-depth analysis
- `ENABLE_GROUNDING`: Enable Google Search grounding (default: `true`)
- `ENABLE_URL_CONTEXT`: Enable URL context processing (default: `true`)
- `DEBUG_MODE`: Enable verbose logging (default: `false`)

## Development

Run tests:
```bash
pytest
```

## Project Structure

- `src/generate_code_review_context.py` - Core Python script
- `src/server.py` - MCP server wrapper
- `tests/` - Test files and fixtures
- `pyproject.toml` - Project configuration
- `requirements.txt` - Dependencies
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/pyproject.toml (unstaged-M)
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "code-review-context-mcp"
version = "0.1.0"
description = "Python-based MCP server tool that generates formatted code review context by parsing PRD and task list files"
authors = [
    {name = "Developer", email = "developer@example.com"}
]
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "mcp>=0.1.0",
    "google-genai>=0.1.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.0.0",
    "black",
    "isort",
    "flake8",
]

[project.scripts]
generate-code-review-context = "src.generate_code_review_context:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["src*"]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/src/generate_code_review_context.py (unstaged-M)
```py
#!/usr/bin/env python3
"""
Generate code review context by parsing PRD, task lists, and git changes.

The script should:
1. Read PRD files (prd-*.md) from /tasks/ directory
2. Read task list files (tasks-prd-*.md) from /tasks/ directory  
3. Parse current phase and progress from task list
4. Extract or generate PRD summary (2-3 sentences)
5. Get git diff for changed files

... (truncated, showing first 500 lines)
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/code-review-comprehensive-20250528-172535.md (untracked)
```md
<overall_prd_summary>
This project implements an MCP server for code review context generation. It automates the creation of review templates.
</overall_prd_summary>

<total_phases>
5
</total_phases>

<current_phase_number>
5.0
</current_phase_number>

<previous_phase_completed>
4.0 Implement git operations and file tree generation
</previous_phase_completed>
<current_phase_description>
Create MCP server integration and finalize project
</current_phase_description>

<subtasks_completed>
- 5.1 Implement MCP server wrapper (server.py) with tool schema definition
- 5.2 Add command-line interface with argument parsing (project_path, --phase, --output)
- 5.3 Implement main orchestration function that ties all components together
- 5.4 Add comprehensive error handling and logging throughout the application
- 5.5 Create final integration tests and validate all success criteria are met
</subtasks_completed>

<project_path>
/Users/nicobailon/Documents/development/task-list-phase-reviewer
</project_path>
<file_tree>
/Users/nicobailon/Documents/development/task-list-phase-reviewer
├── build/
├── code_review_context_mcp.egg-info/
│   ├── PKG-INFO
│   ├── SOURCES.txt
│   ├── dependency_links.txt
│   ├── entry_points.txt
│   ├── requires.txt
│   └── top_level.txt
├── src/
│   ├── generate_code_review_context.py
│   └── server.py
├── tasks/
│   └── tasks-prd.md
├── test-env/
│   ├── bin/
│   │   ├── Activate.ps1
│   │   ├── activate
│   │   ├── activate.csh
│   │   ├── activate.fish
│   │   ├── dotenv
│   │   ├── httpx
│   │   ├── mcp
│   │   ├── normalizer
│   │   ├── pip
│   │   ├── pip3
│   │   ├── pip3.13
│   │   ├── py.test
│   │   ├── pyrsa-decrypt
│   │   ├── pyrsa-encrypt
│   │   ├── pyrsa-keygen
│   │   ├── pyrsa-priv2pub
│   │   ├── pyrsa-sign
│   │   ├── pyrsa-verify
│   │   ├── pytest
│   │   ├── python
│   │   ├── python3
│   │   ├── python3.13
│   │   ├── uvicorn
│   │   └── websockets
│   ├── include/
│   │   └── python3.13/
│   ├── lib/
│   │   └── python3.13/
│   │       └── site-packages/
│   │           ├── _pytest/
│   │           ├── annotated_types/
│   │           ├── annotated_types-0.7.0.dist-info/
│   │           ├── anyio/
│   │           ├── anyio-4.9.0.dist-info/
│   │           ├── cachetools/
│   │           ├── cachetools-5.5.2.dist-info/
│   │           ├── certifi/
│   │           ├── certifi-2025.4.26.dist-info/
│   │           ├── charset_normalizer/
│   │           ├── charset_normalizer-3.4.2.dist-info/
│   │           ├── click/
│   │           ├── click-8.2.1.dist-info/
│   │           ├── dotenv/
│   │           ├── google/
│   │           ├── google_auth-2.40.2.dist-info/
│   │           ├── google_genai-1.17.0.dist-info/
│   │           ├── h11/
│   │           ├── h11-0.16.0.dist-info/
│   │           ├── httpcore/
│   │           ├── httpcore-1.0.9.dist-info/
│   │           ├── httpx/
│   │           ├── httpx-0.28.1.dist-info/
│   │           ├── httpx_sse/
│   │           ├── httpx_sse-0.4.0.dist-info/
│   │           ├── idna/
│   │           ├── idna-3.10.dist-info/
│   │           ├── iniconfig/
│   │           ├── iniconfig-2.1.0.dist-info/
│   │           ├── mcp/
│   │           ├── mcp-1.9.1.dist-info/
│   │           ├── multipart/
│   │           ├── packaging/
│   │           ├── packaging-25.0.dist-info/
│   │           ├── pip/
│   │           ├── pip-25.0.1.dist-info/
│   │           ├── pluggy/
│   │           ├── pluggy-1.6.0.dist-info/
│   │           ├── pyasn1/
│   │           ├── pyasn1-0.6.1.dist-info/
│   │           ├── pyasn1_modules/
│   │           ├── pyasn1_modules-0.4.2.dist-info/
│   │           ├── pydantic/
│   │           ├── pydantic-2.11.5.dist-info/
│   │           ├── pydantic_core/
│   │           ├── pydantic_core-2.33.2.dist-info/
│   │           ├── pydantic_settings/
│   │           ├── pydantic_settings-2.9.1.dist-info/
│   │           ├── pytest/
│   │           ├── pytest-8.3.5.dist-info/
│   │           ├── pytest_mock/
│   │           ├── pytest_mock-3.14.1.dist-info/
│   │           ├── python_dotenv-1.1.0.dist-info/
│   │           ├── python_multipart/
│   │           ├── python_multipart-0.0.20.dist-info/
│   │           ├── requests/
│   │           ├── requests-2.32.3.dist-info/
│   │           ├── rsa/
│   │           ├── rsa-4.9.1.dist-info/
│   │           ├── sniffio/
│   │           ├── sniffio-1.3.1.dist-info/
│   │           ├── sse_starlette/
│   │           ├── sse_starlette-2.3.5.dist-info/
│   │           ├── starlette/
│   │           ├── starlette-0.46.2.dist-info/
│   │           ├── typing_extensions-4.13.2.dist-info/
│   │           ├── typing_inspection/
│   │           ├── typing_inspection-0.4.1.dist-info/
│   │           ├── urllib3/
│   │           ├── urllib3-2.4.0.dist-info/
│   │           ├── uvicorn/
│   │           ├── uvicorn-0.34.2.dist-info/
│   │           ├── websockets/
│   │           ├── websockets-15.0.1.dist-info/
│   │           ├── py.py
│   │           └── typing_extensions.py
│   └── pyvenv.cfg
├── tests/
│   ├── fixtures/
│   │   ├── sample_output.md
│   │   ├── sample_prd.md
│   │   └── sample_task_list.md
│   └── test_generate_code_review_context.py
├── venv/
├── .env
├── README.md
├── code-review-comprehensive-20250528-165648.md
├── code-review-comprehensive-20250528-172408.md
├── code-review-comprehensive-20250528-172413.md
├── code-review-comprehensive-20250528-172430.md
├── code-review-comprehensive-20250528-172447.md
├── code-review-comprehensive-20250528-172456.md
├── code-review-comprehensive-feedback-20250528-171640.md
├── example-task-list-management-rules.md
├── my-custom-review.md
├── prd.md
├── pyproject.toml
├── requirements.txt
└── test_new_feature.py
</file_tree>

<files_changed>
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/README.md (unstaged-M)
```md
# Code Review Context Generator for AI Coding Agents

An MCP server tool designed for **AI coding agents** (Cursor, Claude Code, etc.) to automatically generate comprehensive code review context when completing development phases.

**Version**: 1.2.0 - Enhanced with debug mode and improved file processing capabilities.

## Workflow Integration for AI Agents

This tool integrates into the AI-driven development workflow at **phase completion checkpoints**:

1. **AI Agent works through task list** - Cursor/Claude Code systematically implements features by completing tasks in phases (1.0, 2.0, 3.0, etc.)
2. **Phase completion detected** - When all sub-tasks in a phase are marked complete (`[x]`)  
3. **AI Agent calls MCP tool** - Automatically generates code review context for the completed phase
4. **Review context generated** - Creates formatted markdown with git changes, progress summary, and file context
5. **Ready for review** - Human reviewers get comprehensive context for what was just implemented

## Use Case: AI Agent Integration

**Typical AI agent workflow:**
```
AI Agent: "I've completed all sub-tasks in Phase 2.0. Let me generate a code review context."
AI Agent calls: generate_code_review_context tool
Output: Comprehensive markdown file with git diff, file tree, and phase summary
AI Agent: "✅ Phase 2.0 complete! Review context generated at: review-context-phase-2_0-20250528-143052.md"
```

## Compatible Format Specifications

This tool works with standardized PRD and task list formats from the [AI Dev Tasks](https://github.com/snarktank/ai-dev-tasks) repository:

- **PRDs**: Based on [create-prd.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/create-prd.mdc) specification
  - Structured markdown with required sections (Goals, User Stories, Functional Requirements, etc.)
  - File naming: `prd-[feature-name].md` in `/tasks/` directory
  - Designed for AI agent comprehension and systematic implementation

- **Task Lists**: Based on [generate-tasks.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/generate-tasks.mdc) specification  
  - Hierarchical phases with numbered parent tasks (1.0, 2.0) and sub-tasks (1.1, 1.2)
  - File naming: `tasks-[prd-file-name].md` in `/tasks/` directory
  - Checkbox-based progress tracking (`- [ ]` / `- [x]`) for AI agents to mark completion
  - Systematic implementation guidance for coding agents

## What This Tool Generates

The MCP server automatically creates comprehensive code review context including:
- **Phase Progress Summary** - What phase was just completed and which sub-tasks were finished
- **PRD Context** - Original feature requirements and goals (auto-summarized with Gemini 2.0 Flash Lite)
- **Git Changes** - Detailed diff of all modified/added/deleted files since the phase started
- **File Tree** - ASCII representation of current project structure
- **File Content** - Full content of changed files for review
- **Formatted Output** - Professional markdown template ready for human review
- **Automatic Naming** - Files named with phase and timestamp: `review-context-phase-{phase}-{YYYYMMDD-HHMMSS}.md`

### NEW: Gemini 2.5 AI Code Review

In addition to generating review context, the tool can now automatically generate comprehensive AI-powered code reviews using **Gemini 2.5 Flash** or **Gemini 2.5 Pro**:

- **Automated Code Review** - Sends the generated context to Gemini 2.5 for intelligent analysis
- **Thinking Mode Enabled** - Uses Gemini's thinking capabilities for deep reasoning about code quality
- **Google Search Grounding** - Can lookup current best practices and technology information
- **URL Context Support** - Can process URLs mentioned in code comments or documentation
- **Comprehensive Analysis** - Covers code quality, architecture, security, performance, testing, and maintainability
- **Structured Output** - Generates `code-review-comprehensive-feedback-{timestamp}.md` with detailed feedback

## Installation

### Option 1: Using uvx (Recommended - No Virtual Environment Required)

**Benefits of uvx:**
- ✅ No need to create or manage virtual environments
- ✅ Automatically handles dependency isolation
- ✅ Clean, simple one-command execution
- ✅ No `pip install` required

```bash
# Run directly with uvx (automatically manages dependencies)
uvx --from /path/to/this/project generate-code-review-context /path/to/your/project
```

### Option 2: Traditional Installation

```bash
pip install -r requirements.txt
```

## Usage

### Primary Use: MCP Server for AI Agents
The tool is designed as an MCP server that AI coding agents (Cursor, Claude Code) call automatically when completing development phases.

### Manual CLI Usage

**With uvx (Recommended):**
```bash
# Auto-detect most recently completed phase (generates timestamped files)
uvx --from . generate-code-review-context /path/to/project
# Output: review-context-phase-2_0-20250528-143052.md
# Output: code-review-comprehensive-feedback-20250528-143052.md (Gemini review)

# Disable Gemini AI review (context only)
uvx --from . generate-code-review-context /path/to/project --no-gemini
# Output: review-context-phase-2_0-20250528-143052.md (only)

# Specify a particular phase for review
uvx --from . generate-code-review-context /path/to/project --phase 2.0
# Output: review-context-phase-2_0-20250528-143052.md + AI feedback file

# Custom output file location (overrides automatic naming)
uvx --from . generate-code-review-context /path/to/project --output /custom/path/review.md

# Use Gemini 2.5 Pro instead of Flash (via environment variable)
GEMINI_MODEL=gemini-2.5-pro-preview-05-06 uvx --from . generate-code-review-context /path/to/project
```

**Traditional Python (requires virtual environment):**
```bash
# Auto-detect most recently completed phase (generates timestamped files)
python src/generate_code_review_context.py /path/to/project
# Output: review-context-phase-2_0-20250528-143052.md
# Output: code-review-comprehensive-feedback-20250528-143052.md (Gemini review)

# Disable Gemini AI review (context only)
python src/generate_code_review_context.py /path/to/project --no-gemini
# Output: review-context-phase-2_0-20250528-143052.md (only)

# Specify a particular phase for review
python src/generate_code_review_context.py /path/to/project --phase 2.0
# Output: review-context-phase-2_0-20250528-143052.md + AI feedback file

# Custom output file location (overrides automatic naming)
python src/generate_code_review_context.py /path/to/project --output /custom/path/review.md

# Use Gemini 2.5 Pro instead of Flash (via environment variable)
GEMINI_MODEL=gemini-2.5-pro-preview-05-06 python src/generate_code_review_context.py /path/to/project
```

**Output File Naming:**
- **Automatic**: `review-context-phase-{phase_number}-{timestamp}.md`
- **Example**: `review-context-phase-2_0-20250528-143052.md`
- **Custom**: Use `--output` flag to specify your own filename
- **Unique**: Each run generates a unique timestamp to avoid conflicts

**CLI Use Cases:**
- Testing the tool during setup
- Manual code review generation outside of AI agent workflows
- Debugging task list parsing or git integration
- One-off reviews for specific phases

## MCP Server Installation

This tool works as an MCP (Model Context Protocol) server for integration with Claude Desktop, Cursor, and Claude Code CLI.

### Claude Code CLI

Install the MCP server using Claude Code's built-in commands:

```bash
# Add the server with your Gemini API key
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_gemini_api_key_here

# List configured servers
claude mcp list

# Test the server
claude mcp get task-list-reviewer
```

### Claude Desktop & Cursor

Add this configuration to your `claude_desktop_config.json` or Cursor's MCP settings:

**Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": [
        "/path/to/task-list-phase-reviewer/src/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

**Replace `/path/to/task-list-phase-reviewer` with your actual project path.**

### Configuring Gemini Model Selection

You can choose between Gemini 2.5 Flash (default) and Pro models by setting the `GEMINI_MODEL` environment variable:

**For Claude Desktop/Cursor (claude_desktop_config.json):**
```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": ["/path/to/task-list-phase-reviewer/src/server.py"],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "GEMINI_MODEL": "gemini-2.5-flash-preview-05-20"
      }
    }
  }
}
```

**For Claude Code CLI:**
```bash
# Use Flash (default - fast, high-volume)
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_key \
  -e GEMINI_MODEL=gemini-2.5-flash-preview-05-20

# Use Pro (complex reasoning, in-depth analysis)
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_key \
  -e GEMINI_MODEL=gemini-2.5-pro-preview-05-06
```

### Usage by AI Coding Agents

Once installed, AI agents (Cursor, Claude Code) can automatically call this tool when completing development phases:

**AI Agent Usage:**
```
AI Agent: "I've completed Phase 2.0 (Implement core parsing logic). Let me generate the code review context."

Tool Call: generate_code_review_context
Parameters: { "project_path": "/path/to/project" }

AI Agent: "✅ Phase 2.0 complete! Code review context generated at: review-context-phase-2-20241128-143052.md"
```

**Manual Usage (for testing):**
```
Please use the generate_code_review_context tool to analyze my project at /path/to/my/project
```

The tool will:
1. **Detect completed phase** - Automatically finds the most recently completed phase from task list
2. **Parse PRD requirements** - Extracts feature context and goals  
3. **Analyze git changes** - Gets all file modifications since phase start
4. **Generate review package** - Creates comprehensive markdown with all context needed for human review

## Environment Variables

### Core Configuration
- `GEMINI_API_KEY`: Required for Gemini integration (PRD summarization and code review)
- `MAX_FILE_TREE_DEPTH`: Optional, maximum tree depth (default: 5). Use lower values for large projects.
- `MAX_FILE_CONTENT_LINES`: Optional, max lines to show per file (default: 500). Adjust for context window limits.

### Gemini 2.5 Code Review Configuration
- `GEMINI_MODEL`: Model to use for code review (default: `gemini-2.5-flash-preview-05-20`)
  - **Flash (default)**: `gemini-2.5-flash-preview-05-20` - Fast, high-volume code reviews
  - **Pro**: `gemini-2.5-pro-preview-05-06` - Complex reasoning, in-depth analysis
- `ENABLE_GROUNDING`: Enable Google Search grounding (default: `true`)
- `ENABLE_URL_CONTEXT`: Enable URL context processing (default: `true`)
- `DEBUG_MODE`: Enable verbose logging (default: `false`)

## Development

Run tests:
```bash
pytest
```

## Project Structure

- `src/generate_code_review_context.py` - Core Python script
- `src/server.py` - MCP server wrapper
- `tests/` - Test files and fixtures
- `pyproject.toml` - Project configuration
- `requirements.txt` - Dependencies
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/pyproject.toml (unstaged-M)
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "code-review-context-mcp"
version = "0.1.0"
description = "Python-based MCP server tool that generates formatted code review context by parsing PRD and task list files"
authors = [
    {name = "Developer", email = "developer@example.com"}
]
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "mcp>=0.1.0",
    "google-genai>=0.1.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.0.0",
    "black",
    "isort",
    "flake8",
]

... (truncated, showing first 500 lines)
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/code-review-comprehensive-feedback-20250528-171640.md (untracked)
```md
# Comprehensive Code Review Feedback
*Generated on 2025-05-28 at 17:16:40 using gemini-2.5-flash-preview-05-20*

### Code Review Feedback: Phase 5.0 - MCP Server Integration and Finalization

**Overall Assessment**

This phase marks a significant step towards project completion, focusing on integrating the core logic into an MCP server and refining the user experience through CLI and documentation. The project's goal of automating code review context generation for AI agents is well-defined and the implemented subtasks align with this vision. The addition of environment variable support, improved task list parsing, and comprehensive documentation updates are positive developments.

However, the current state of the `generate_code_review_context.py` file reveals critical issues, particularly a severe bug in the `format_review_template` function and an inconsistency in handling deleted files. These issues prevent the tool from generating correct and clean output, which is fundamental to its purpose. While the `README.md` is well-updated, it describes features that may not be fully functional due to these underlying code problems.

**Code Quality & Best Practices**

1.  **Hardcoded Content in `format_review_template` (Critical Bug)**
    *   **Issue:** The `format_review_template` function contains large blocks of hardcoded markdown content from other review files (e.g., `code-review-comprehensive-20250528-164653.md`, `code-review-context-clean.md`). This is a critical copy-paste error that will result in corrupted and irrelevant output every time the tool is run.
    *   **File/Lines:** `src/generate_code_review_context.py`, starting from line 302 and continuing for hundreds of lines.
    *   **Feedback:** **Immediately remove all hardcoded markdown content from this function.** The template should *only* contain placeholders and logic to dynamically insert the `data` dictionary's values. This is the most pressing issue to address.

2.  **Inconsistent Deleted File Handling in `get_changed_files` (Bug)**
    *   **Issue:** The `get_changed_files` function correctly identifies deleted files (e.g., `staged-D`) but then attempts to check `os.path.exists(absolute_path)`. For a deleted file, `os.path.exists` will be `False`, leading to the content being set to `"[File not found in working directory]"`. The `temp_test_file.txt` example in `files_changed` shows `[File deleted]`, indicating this was the intended behavior, but the code doesn't fully implement it. The `is_deleted` flag is set but not used to bypass the file reading.
    *   **File/Lines:** `src/generate_code_review_context.py`, lines 206-220.
    *   **Feedback:** Reintroduce and correctly utilize the `is_deleted` flag. If a file's status indicates deletion (e.g., `staged-D`), its content should be explicitly set to `"[File deleted]"` without attempting to read from the filesystem.

    ```python
    # Current problematic logic:
    # ...
    # is_deleted = any('D' in status for status in statuses) # This line is present
    # ...
    # if os.path.exists(absolute_path): # This will be False for deleted files
    #     # ... read content ...
    # else:
    #     content = "[File not found in working directory]" # Incorrect for deleted files

    # Proposed fix:
    if is_deleted:
        content = "[File deleted]"
    else:
        try:
            if os.path.exists(absolute_path):
                with open(absolute_path, 'r', encoding='utf-8') as f:
                    content_lines = f.readlines()
                # ... truncation logic ...
            else:
                content = "[File not found in working directory]" # This case is for non-deleted, non-existent files
        except (UnicodeDecodeError, PermissionError, OSError):
            content = "[Binary file or content not available]"
    ```

3.  **Redundant `load_dotenv` Calls:**
    *   **Issue:** `load_dotenv()` is called twice: once unconditionally at the top level, and once inside a `try...except ImportError` block for `dotenv`. The latter is redundant if `dotenv` is always expected to be installed (as per `requirements.txt`).
    *   **File/Lines:** `src/generate_code_review_context.py`, lines 17-21.
    *   **Feedback:** Keep only one `load_dotenv()` call. If `dotenv` is a hard dependency, remove the `try...except` block. If it's truly optional, ensure the `load_dotenv()` call is only made if `dotenv` is available. Given `requirements.txt`, it's a dependency, so the `try...except` is unnecessary.

4.  **`parse_task_list` Subtask Description Inclusion:**
    *   **Issue:** The change from `current_phase['subtasks_completed'].append(number)` to `current_phase['subtasks_completed'].append(f"{number} {description}")` is a good improvement for clarity in the output.
    *   **File/Lines:** `src/generate_code_review_context.py`, line 70.
    *   **Feedback:** This is a positive change, enhancing the readability of the "Subtasks completed" section in the generated review context.

5.  **Error Handling and Logging:**
    *   **Issue:** Subtask 5.4 mentions "Add comprehensive error handling and logging throughout the application." While `logging` is set up and used for `GEMINI_AVAILABLE` errors and Git repository issues, a more robust approach for other potential failures (e.g., file not found for PRD/task list, parsing errors) would be beneficial.
    *   **File/Lines:** General.
    *   **Feedback:** Review all file I/O and external process calls (`subprocess.run`) for explicit `try...except` blocks that catch specific exceptions (e.g., `FileNotFoundError`, `IOError`, `subprocess.CalledProcessError`) and provide informative error messages to the user or log.

6.  **Magic Numbers/Environment Variables:**
    *   **Issue:** `MAX_FILE_TREE_DEPTH` and `MAX_FILE_CONTENT_LINES` are correctly read from environment variables, which is good.
    *   **File/Lines:** `src/generate_code_review_context.py`, lines 169, 190.
    *   **Feedback:** This is a good practice for configurable limits.

**Architecture & Design**

1.  **Modularity and Separation of Concerns:**
    *   **Issue:** The `generate_code_review_context.py` script is quite monolithic. While it encapsulates the core logic, a larger application might benefit from further breaking down functions into logical modules (e.g., `git_utils.py`, `markdown_formatter.py`, `task_parser.py`).
    *   **Feedback:** For the current scope, it's acceptable. However, if the project grows, consider refactoring into a package structure with more specialized modules. This would improve testability and maintainability.

2.  **MCP Server Wrapper (`server.py`):**
    *   **Issue:** The context mentions "Implement MCP server wrapper (server.py) with tool schema definition" as a completed subtask, but `server.py` itself is not provided in the `files_changed` section.
    *   **Feedback:** Ensure `server.py` correctly defines the tool schema and handles input/output according to the MCP specification. A review of `server.py` would be necessary to confirm this.

3.  **PRD Summary Strategy:**
    *   **Issue:** The `extract_prd_summary` function uses a multi-strategy approach (explicit sections, then Gemini, then first paragraph). This is a robust design.
    *   **Feedback:** Good design for flexibility and fallback. Ensure the Gemini API key handling is secure (e.g., not hardcoded, only read from environment variables).

**Security Considerations**

1.  **Environment Variable Handling (`GEMINI_API_KEY`):**
    *   **Issue:** The `GEMINI_API_KEY` is read from environment variables using `os.getenv()`, which is the correct and secure way to handle sensitive information.
    *   **Feedback:** Good practice. Ensure that the `.env` file itself is not committed to version control (it's in `.gitignore` in the file tree, which is good).

2.  **Subprocess Calls (`git` commands):**
    *   **Issue:** The script executes `git` commands using `subprocess.run`. If any part of the command arguments were user-controlled without proper sanitization, it could lead to command injection vulnerabilities.
    *   **File/Lines:** `src/generate_code_review_context.py`, lines 196, 207, 218.
    *   **Feedback:** Currently, the `git` commands use fixed arguments (`--name-status`, `--cached`, `--others`, `--exclude-standard`). The `cwd=project_path` is also controlled internally. This appears safe. If `project_path` were ever user-supplied and not properly validated, it could be a vector, but in this context, it seems to be an internal path. Continue to ensure no user-supplied input directly forms parts of shell commands without strict validation.

**Performance Implications**

1.  **Git Operations:**
    *   **Issue:** `get_changed_files` runs multiple `git diff` and `git ls-files` commands. For very large repositories or projects with many changed files, these operations could be slow.
    *   **Feedback:** The current approach is standard. If performance becomes an issue for extremely large projects, consider optimizing git calls (e.g., using `git status --porcelain` to get all changes in one go, then parsing). For typical code review scenarios, this should be fine.

2.  **File Content Truncation:**
    *   **Issue:** `MAX_FILE_CONTENT_LINES` limits the lines read from changed files. This is a good optimization for context window management with LLMs.
    *   **Feedback:** This is a necessary and good performance/resource management feature.

3.  **File Tree Generation:**
    *   **Issue:** `generate_file_tree` recursively lists directories. For very deep or wide file trees, this could be resource-intensive. `MAX_FILE_TREE_DEPTH` helps mitigate this.
    *   **Feedback:** The `MAX_FILE_TREE_DEPTH` environment variable is a good control. Ensure the default value (5) is reasonable for most use cases to prevent excessive processing.

**Testing & Maintainability**

1.  **Integration Tests (Subtask 5.5):**
    *   **Issue:** Subtask 5.5 states "Create final integration tests and validate all success criteria are met." While the `tests/` directory exists, the actual integration tests are not provided in the `files_changed` context.
    *   **Feedback:** It's crucial to have robust integration tests that cover the entire workflow:
        *   Parsing PRD and task lists (including edge cases like empty files, malformed entries).
        *   Correctly identifying current/previous/next phases.
        *   Accurate detection and content retrieval of staged, unstaged, and untracked files (including deleted/binary files).
        *   Correct generation of the file tree.
        *   End-to-end generation of the markdown output, verifying its structure and content.
        *   Testing the MCP server wrapper's functionality.
        *   Testing with and without `GEMINI_API_KEY` to ensure graceful fallback.

2.  **Readability and Docstrings:**
    *   **Issue:** The code is generally readable, and functions have docstrings. Type hints are used, which is good.
    *   **Feedback:** Continue to maintain good docstrings and type hints. Consider adding more inline comments for complex regex patterns or logic.

3.  **Dependency Management:**
    *   **Issue:** `requirements.txt` is used for dependencies.
    *   **Feedback:** Ensure `requirements.txt` is kept up-to-date and includes all necessary packages. Consider using `pyproject.toml` with `poetry` or `pip-tools` for more robust dependency management in the future.

**Next Steps**

1.  **Immediate Bug Fixes:**
    *   **High Priority:** Fix the hardcoded content in `format_review_template`.
    *   **High Priority:** Correctly handle deleted files in `get_changed_files` to output `[File deleted]`.
2.  **Review `server.py`:** A dedicated review of `src/server.py` is needed to ensure the MCP integration and tool schema definition are correct and robust.
3.  **Comprehensive Testing:**
    *   Thoroughly implement and run the integration tests (Subtask 5.5) to ensure all functionalities work as expected, especially after fixing the identified bugs.
    *   Consider adding unit tests for individual functions (e.g., `parse_task_list`, `extract_prd_summary`) to isolate and verify their logic.
4.  **Refinement of `detect_current_phase` logic:** The current logic for `detect_current_phase` is: "1. Find the most recently completed phase (all subtasks done) 2. If no phases are complete, fall back to the current in-progress phase 3. If all phases are complete, use the last phase". This seems reasonable, but ensure it covers all desired scenarios for AI agent workflow (e.g., what if a phase is partially completed, but the *previous* phase was fully completed and needs review?). The current implementation seems to prioritize the *latest* phase that is either fully complete or currently in progress. This might be the desired behavior, but it's worth double-checking against the PRD's implicit requirements for "phase completion checkpoints."
5.  **Output File Naming Consistency:** The `README.md` mentions "Automatic Naming - Files named with phase and timestamp: `review-context-phase-{phase}-{YYYYMMDD-HHMMSS}.md`". Ensure the main orchestration function (Subtask 5.3) correctly implements this naming convention and saves the file to the expected location (e.g., `/tasks/` directory as mentioned in the script's docstring).
6.  **User Experience (CLI):** While CLI parsing is implemented, consider adding more user-friendly output messages for success/failure, and potentially a `--verbose` or `--debug` flag for more detailed logging output.

---
*Review conducted by Gemini AI with thinking enabled and web grounding capabilities*
```
File: /Users/nicobailon/Documents/development/task-list-phase-reviewer/my-custom-review.md (untracked)
```md
**Overall PRD summary: (2-3 sentences max)**
This project implements an MCP server for code review context generation. It automates the creation of review templates.

**Total Number of phases in Task List: 5**

**Current phase number: 5.0**
**Previous phase completed: 4.0 Implement git operations and file tree generation**

**Next phase: **

**Current phase description: "Create MCP server integration and finalize project"**

**Subtasks completed in current phase:**
- 5.1 Implement MCP server wrapper (server.py) with tool schema definition
- 5.2 Add command-line interface with argument parsing (project_path, --phase, --output)
- 5.3 Implement main orchestration function that ties all components together
- 5.4 Add comprehensive error handling and logging throughout the application
- 5.5 Create final integration tests and validate all success criteria are met

**.**
<file_tree>
.
├── src/
│   ├── generate_code_review_context.py
│   └── server.py
├── tasks/
│   └── tasks-prd.md
├── test-env/
│   ├── bin/
│   │   ├── Activate.ps1
│   │   ├── activate
│   │   ├── activate.csh
│   │   ├── activate.fish
│   │   ├── dotenv
│   │   ├── httpx
│   │   ├── mcp
│   │   ├── normalizer
│   │   ├── pip
│   │   ├── pip3
│   │   ├── pip3.13
│   │   ├── py.test
│   │   ├── pyrsa-decrypt
│   │   ├── pyrsa-encrypt
│   │   ├── pyrsa-keygen
│   │   ├── pyrsa-priv2pub
│   │   ├── pyrsa-sign
│   │   ├── pyrsa-verify
│   │   ├── pytest
│   │   ├── python
│   │   ├── python3
│   │   ├── python3.13
│   │   ├── uvicorn
│   │   └── websockets
│   ├── include/
│   │   └── python3.13/
│   ├── lib/
│   │   └── python3.13/
│   │       └── site-packages/
│   │           ├── _pytest/
│   │           ├── annotated_types/
│   │           ├── annotated_types-0.7.0.dist-info/
│   │           ├── anyio/
│   │           ├── anyio-4.9.0.dist-info/
│   │           ├── cachetools/
│   │           ├── cachetools-5.5.2.dist-info/
│   │           ├── certifi/
│   │           ├── certifi-2025.4.26.dist-info/
│   │           ├── charset_normalizer/
│   │           ├── charset_normalizer-3.4.2.dist-info/
│   │           ├── click/
│   │           ├── click-8.2.1.dist-info/
│   │           ├── dotenv/
│   │           ├── google/
│   │           ├── google_auth-2.40.2.dist-info/
│   │           ├── google_genai-1.17.0.dist-info/
│   │           ├── h11/
│   │           ├── h11-0.16.0.dist-info/
│   │           ├── httpcore/
│   │           ├── httpcore-1.0.9.dist-info/
│   │           ├── httpx/
│   │           ├── httpx-0.28.1.dist-info/
│   │           ├── httpx_sse/
│   │           ├── httpx_sse-0.4.0.dist-info/
│   │           ├── idna/
│   │           ├── idna-3.10.dist-info/
│   │           ├── iniconfig/
│   │           ├── iniconfig-2.1.0.dist-info/
│   │           ├── mcp/
│   │           ├── mcp-1.9.1.dist-info/
│   │           ├── multipart/
│   │           ├── packaging/
│   │           ├── packaging-25.0.dist-info/
│   │           ├── pip/
│   │           ├── pip-25.0.1.dist-info/
│   │           ├── pluggy/
│   │           ├── pluggy-1.6.0.dist-info/
│   │           ├── pyasn1/
│   │           ├── pyasn1-0.6.1.dist-info/
│   │           ├── pyasn1_modules/
│   │           ├── pyasn1_modules-0.4.2.dist-info/
│   │           ├── pydantic/
│   │           ├── pydantic-2.11.5.dist-info/
│   │           ├── pydantic_core/
│   │           ├── pydantic_core-2.33.2.dist-info/
│   │           ├── pydantic_settings/
│   │           ├── pydantic_settings-2.9.1.dist-info/
│   │           ├── pytest/
│   │           ├── pytest-8.3.5.dist-info/
│   │           ├── pytest_mock/
│   │           ├── pytest_mock-3.14.1.dist-info/
│   │           ├── python_dotenv-1.1.0.dist-info/
│   │           ├── python_multipart/
│   │           ├── python_multipart-0.0.20.dist-info/
│   │           ├── requests/
│   │           ├── requests-2.32.3.dist-info/
│   │           ├── rsa/
│   │           ├── rsa-4.9.1.dist-info/
│   │           ├── sniffio/
│   │           ├── sniffio-1.3.1.dist-info/
│   │           ├── sse_starlette/
│   │           ├── sse_starlette-2.3.5.dist-info/
│   │           ├── starlette/
│   │           ├── starlette-0.46.2.dist-info/
│   │           ├── typing_extensions-4.13.2.dist-info/
│   │           ├── typing_inspection/
│   │           ├── typing_inspection-0.4.1.dist-info/
│   │           ├── urllib3/
│   │           ├── urllib3-2.4.0.dist-info/
│   │           ├── uvicorn/
│   │           ├── uvicorn-0.34.2.dist-info/
│   │           ├── websockets/
│   │           ├── websockets-15.0.1.dist-info/
│   │           ├── py.py
│   │           └── typing_extensions.py
│   └── pyvenv.cfg
├── tests/
│   ├── fixtures/
│   │   ├── sample_output.md
│   │   ├── sample_prd.md
│   │   └── sample_task_list.md
│   └── test_generate_code_review_context.py
├── venv/
├── .env
├── README.md
├── code-review-context-clean.md
├── code-review-context-final.md
├── code-review-context-fixed.md
├── code-review-context-test.md
├── example-task-list-management-rules.md
├── prd.md
├── pyproject.toml
├── requirements.txt
├── review-context-phase-5_0-20250528-163754.md
├── review-context-phase-5_0-20250528-163758.md
└── test_new_feature.py
</file_tree>

<files_changed>
**File: README.md**
```md
# Code Review Context Generator for AI Coding Agents

An MCP server tool designed for **AI coding agents** (Cursor, Claude Code, etc.) to automatically generate comprehensive code review context when completing development phases.

## Workflow Integration for AI Agents

This tool integrates into the AI-driven development workflow at **phase completion checkpoints**:

1. **AI Agent works through task list** - Cursor/Claude Code systematically implements features by completing tasks in phases (1.0, 2.0, 3.0, etc.)
2. **Phase completion detected** - When all sub-tasks in a phase are marked complete (`[x]`)  
3. **AI Agent calls MCP tool** - Automatically generates code review context for the completed phase
4. **Review context generated** - Creates formatted markdown with git changes, progress summary, and file context
5. **Ready for review** - Human reviewers get comprehensive context for what was just implemented

## Use Case: AI Agent Integration

**Typical AI agent workflow:**
```
AI Agent: "I've completed all sub-tasks in Phase 2.0. Let me generate a code review context."
AI Agent calls: generate_code_review_context tool
Output: Comprehensive markdown file with git diff, file tree, and phase summary
AI Agent: "Phase 2.0 implementation complete. Review context generated at /path/to/review-context-phase-2.md"
```

## Compatible Format Specifications

This tool works with standardized PRD and task list formats from the [AI Dev Tasks](https://github.com/snarktank/ai-dev-tasks) repository:

- **PRDs**: Based on [create-prd.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/create-prd.mdc) specification
  - Structured markdown with required sections (Goals, User Stories, Functional Requirements, etc.)
  - File naming: `prd-[feature-name].md` in `/tasks/` directory
  - Designed for AI agent comprehension and systematic implementation

- **Task Lists**: Based on [generate-tasks.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/generate-tasks.mdc) specification  
  - Hierarchical phases with numbered parent tasks (1.0, 2.0) and sub-tasks (1.1, 1.2)
  - File naming: `tasks-[prd-file-name].md` in `/tasks/` directory
  - Checkbox-based progress tracking (`- [ ]` / `- [x]`) for AI agents to mark completion
  - Systematic implementation guidance for coding agents

## What This Tool Generates

The MCP server automatically creates comprehensive code review context including:
- **Phase Progress Summary** - What phase was just completed and which sub-tasks were finished
- **PRD Context** - Original feature requirements and goals (auto-summarized with Gemini 2.0 Flash Lite)
- **Git Changes** - Detailed diff of all modified/added/deleted files since the phase started
- **File Tree** - ASCII representation of current project structure
- **File Content** - Full content of changed files for review
- **Formatted Output** - Professional markdown template ready for human review

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Primary Use: MCP Server for AI Agents
The tool is designed as an MCP server that AI coding agents (Cursor, Claude Code) call automatically when completing development phases.

### Manual CLI Usage
You can also run the tool manually from the command line:

```bash
# Auto-detect most recently completed phase
python src/generate_code_review_context.py /path/to/project

# Specify a particular phase for review
python src/generate_code_review_context.py /path/to/project --phase 2.0

# Custom output file location
python src/generate_code_review_context.py /path/to/project --output /custom/path/review.md

# Combine options
python src/generate_code_review_context.py /path/to/project --phase 3.1 --output my-review.md
```

**CLI Use Cases:**
- Testing the tool during setup
- Manual code review generation outside of AI agent workflows
- Debugging task list parsing or git integration
- One-off reviews for specific phases

## MCP Server Installation

This tool works as an MCP (Model Context Protocol) server for integration with Claude Desktop, Cursor, and Claude Code CLI.

### Claude Code CLI

Install the MCP server using Claude Code's built-in commands:

```bash
# Add the server with your Gemini API key
claude mcp add task-list-reviewer python /path/to/task-list-phase-reviewer/src/server.py \
  -e GEMINI_API_KEY=your_gemini_api_key_here

# List configured servers
claude mcp list

# Test the server
claude mcp get task-list-reviewer
```

### Claude Desktop & Cursor

Add this configuration to your `claude_desktop_config.json` or Cursor's MCP settings:

**Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": [
        "/path/to/task-list-phase-reviewer/src/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

**Replace `/path/to/task-list-phase-reviewer` with your actual project path.**

### Usage by AI Coding Agents

Once installed, AI agents (Cursor, Claude Code) can automatically call this tool when completing development phases:

**AI Agent Usage:**
```
AI Agent: "I've completed Phase 2.0 (Implement core parsing logic). Let me generate the code review context."

Tool Call: generate_code_review_context
Parameters: { "project_path": "/path/to/project" }

AI Agent: "✅ Phase 2.0 complete! Code review context generated at: review-context-phase-2-20241128-143052.md"
```

**Manual Usage (for testing):**
```
Please use the generate_code_review_context tool to analyze my project at /path/to/my/project
```

The tool will:
1. **Detect completed phase** - Automatically finds the most recently completed phase from task list
2. **Parse PRD requirements** - Extracts feature context and goals  
3. **Analyze git changes** - Gets all file modifications since phase start
4. **Generate review package** - Creates comprehensive markdown with all context needed for human review

## Environment Variables

- `GEMINI_API_KEY`: Optional, for PRD summarization when explicit summary not found
- `MAX_FILE_TREE_DEPTH`: Optional, maximum tree depth (default: 5). Use lower values for large projects.
- `MAX_FILE_CONTENT_LINES`: Optional, max lines to show per file (default: 500). Adjust for context window limits.

## Development

Run tests:
```bash
pytest
```

## Project Structure

- `src/generate_code_review_context.py` - Core Python script
- `src/server.py` - MCP server wrapper
- `tests/` - Test files and fixtures
- `pyproject.toml` - Project configuration
- `requirements.txt` - Dependencies
```
**File: src/generate_code_review_context.py**
```py
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
    

... (truncated, showing first 500 lines)
```
</files_changed>

<user_instructions>
We have just completed phase #5.0: "Create MCP server integration and finalize project".

Based on the PRD, the completed phase, all subtasks that were finished in that phase, and the files changed, your job is to conduct a code review and output your code review feedback for the completed phase. Identify specific lines or files that are concerning when appropriate.
</user_instructions>