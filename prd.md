# Meta Prompt: Code Review Context Generator with MCP Integration

## Project Overview

Create a Python-based MCP server tool that generates formatted code review context by parsing PRD and task list files, detecting git changes, and outputting a structured markdown template for AI code reviews.

## Complete Implementation Requirements

### 1. Project Structure
```
code-review-context-mcp/
├── src/
│   ├── server.py                    # MCP server wrapper
│   └── generate_code_review_context.py  # Core Python script
├── tests/
│   ├── test_generate_code_review_context.py
│   └── fixtures/
│       ├── sample_prd.md
│       ├── sample_task_list.md
│       └── sample_output.md
├── pyproject.toml
├── requirements.txt
└── README.md
```

### 2. Core Script Implementation (`generate_code_review_context.py`)

```python
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
```

### 3. Detailed Component Specifications

#### 3.1 Task List Parser

**Input Format** (from tasks-prd-*.md):
```markdown
- [x] 1.0 Set up project dependencies and infrastructure
  - [x] 1.1 Review ConduitMCP's package.json and identify required dependencies
  - [x] 1.2 Add new dependencies to DevControlMCP's package.json
  - [ ] 1.3 Run npm install and verify all dependencies are properly installed
- [ ] 2.0 Implement fetch_url tool for web content processing
  - [x] 2.1 Add FetchUrlArgsSchema to src/tools/schemas.ts
  - [ ] 2.2 Create fetchUrl function in src/tools/url-fetcher.ts
```

**Required Parsing Logic**:
- Phase pattern: `^- \[([ x])\] (\d+\.\d+) (.+)$`
- Subtask pattern: `^  - \[([ x])\] (\d+\.\d+) (.+)$`
- Current phase detection: First phase with incomplete subtasks OR first incomplete phase
- Extract completed subtasks in current phase (those marked with [x])

**Output Data Structure**:
```python
{
    'total_phases': 5,
    'current_phase_number': '2.0',
    'previous_phase_completed': '1.0 Set up project dependencies and infrastructure',
    'next_phase': '3.0 Implement find tool for advanced file search',
    'current_phase_description': 'Implement fetch_url tool for web content processing',
    'subtasks_completed': ['2.1']  # Just the numbers
}
```

#### 3.2 PRD Parser

**PRD Summary Extraction Logic**:
1. Search for explicit summary sections (regex patterns):
   - `## Summary\n(.+?)(?=\n##|\Z)`
   - `## Overview\n(.+?)(?=\n##|\Z)`
   - `### Summary\n(.+?)(?=\n###|\Z)`
   - `## Executive Summary\n(.+?)(?=\n##|\Z)`

2. If no summary found, use LLM (make OpenAI API optional):
   ```python
   if OPENAI_API_KEY:
       prompt = "Summarize this PRD in 2-3 sentences focusing on the main goal and key deliverables:\n\n{first_2000_chars}"
       # Use OpenAI API to generate summary
   ```

3. Fallback: Use first paragraph or first 200 characters

#### 3.3 Git Operations

**Get Changed Files**:
```bash
git diff --name-status HEAD  # Get list of changed files
git show HEAD:path/to/file   # Get file content for display
```

**Output Format**:
```python
[
    {
        'path': 'src/server.ts',
        'status': 'M',  # M=modified, A=added, D=deleted
        'content': '// First 100 lines of file or full content if < 100 lines'
    }
]
```

**Edge Cases**:
- Handle when not in git repository (skip git section)
- Handle binary files (show only path, no content)
- Handle very large files (limit to first 100 lines)

#### 3.4 File Tree Generator

**Requirements**:
- ASCII tree format like `tree` command
- Respect .gitignore patterns
- Default ignore: `.git`, `node_modules`, `__pycache__`, `.pytest_cache`, `*.pyc`
- Max depth: 5 levels (configurable)
- Sort directories first, then files alphabetically

**Example Output**:
```
/Users/nicobailon/Documents/development/project
├── src/
│   ├── tools/
│   │   ├── find-tool.ts
│   │   └── write-tool.ts
│   └── server.ts
├── tests/
│   └── test_server.py
└── README.md
```

#### 3.5 Template Format

**Exact Template Structure**:
```markdown
**Overall PRD summary: (2-3 sentences max)**
{prd_summary}

**Total Number of phases in Task List: {total_phases}**

**Current phase number: {current_phase_number}**
**Previous phase completed: {previous_phase_completed}**

**Next phase: {next_phase}**

**Current phase description: "{current_phase_description}"**

**Subtasks completed in current phase: {subtasks_completed}**

**{project_path}**
**<file_tree>**
{file_tree}
**</file_tree>**

**<files_changed>**
{for each changed file:}
**File: {file_path}**
**```{file_extension}**
{file_content}
**```**
{end for}
**</files_changed>**

**<user_instructions>**
We are working on the current phase number #{current_phase_number}.

Based on the PRD, current phase, subtasks completed for that phase and the files changed, your job is to conduct a code review and output your code review feedback. Identify specific lines or files that are concerning when appropriate.
**</user_instructions>**
```

### 4. MCP Server Wrapper (`server.py`)

```python
"""
MCP server wrapper for generate_code_review_context.py

Exposes tool:
- generate_code_review_context: Generate review context for current project phase
"""

# MCP tool definition:
{
    "name": "generate_code_review_context",
    "description": "Generate code review context based on PRD and current task phase",
    "inputSchema": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "description": "Absolute path to project root"
            },
            "current_phase": {
                "type": "string", 
                "description": "Current phase number (e.g., '2.0'). If not provided, auto-detects from task list"
            }
        },
        "required": ["project_path"]
    }
}

# Implementation should:
# 1. Call generate_code_review_context.py with arguments
# 2. Return the path to generated file
# 3. Handle errors gracefully
```

### 5. Test-Driven Development Tests

#### 5.1 Test Task Parser (`test_task_parser`)
```python
def test_parse_task_list_with_current_phase():
    """Test parsing task list and identifying current phase"""
    content = """
- [x] 1.0 Phase One
  - [x] 1.1 Subtask one
  - [x] 1.2 Subtask two
- [ ] 2.0 Phase Two  
  - [x] 2.1 Subtask one
  - [ ] 2.2 Subtask two
  - [ ] 2.3 Subtask three
- [ ] 3.0 Phase Three
  - [ ] 3.1 Subtask one
"""
    # Expected: current phase is 2.0 (first with incomplete subtasks)
    # Expected: completed subtasks in current phase: ['2.1']
    # Expected: total phases: 3

def test_parse_task_list_all_phases_complete():
    """Test when all phases are complete"""
    # Should handle gracefully, maybe return last phase

def test_parse_task_list_with_nested_subtasks():
    """Test handling nested subtask levels"""
    # Some task lists might have sub-subtasks
```

#### 5.2 Test PRD Parser (`test_prd_parser`)
```python
def test_extract_explicit_summary():
    """Test extracting summary when explicitly marked"""
    content = """
# Project PRD

## Summary
This project implements an MCP server for code review context generation. It automates the creation of review templates.

## Goals
...
"""
    # Expected: "This project implements an MCP server for code review context generation. It automates the creation of review templates."

def test_generate_summary_fallback():
    """Test fallback when no summary section exists"""
    # Should use first paragraph or LLM if available
```

#### 5.3 Test Git Operations (`test_git_operations`)
```python
def test_get_changed_files_mock():
    """Test git diff parsing with mocked subprocess"""
    # Mock subprocess.run to return sample git diff output
    # Verify correct parsing of M, A, D statuses

def test_handle_no_git_repository():
    """Test graceful handling when not in git repo"""
    # Should return empty list or skip section
```

#### 5.4 Test File Tree (`test_file_tree`)
```python
def test_generate_file_tree_basic():
    """Test basic file tree generation"""
    # Create temp directory structure
    # Verify correct ASCII formatting

def test_file_tree_respects_gitignore():
    """Test that gitignore patterns are respected"""
    # Create .gitignore with patterns
    # Verify ignored files don't appear
```

#### 5.5 Integration Test (`test_integration`)
```python
def test_end_to_end_generation():
    """Test complete flow from input files to output"""
    # Set up complete test project structure
    # Run generator
    # Verify output matches expected template
```

### 6. Error Handling Requirements

1. **Missing Files**:
   - If no prd-*.md found: Error with helpful message
   - If no tasks-prd-*.md found: Error with helpful message
   - If multiple matches: Use most recently modified

2. **Parsing Errors**:
   - Malformed task list: Best effort parsing, log warnings
   - Invalid markdown: Continue with what can be parsed

3. **Git Errors**:
   - Not a git repo: Skip git section, continue
   - Git command fails: Log warning, skip git section

4. **File System Errors**:
   - Permission denied: Skip those files/directories
   - Broken symlinks: Skip

### 7. Configuration and Environment

**Environment Variables**:
```bash
OPENAI_API_KEY=sk-...  # Optional, for PRD summarization
MAX_FILE_TREE_DEPTH=5   # Maximum tree depth
MAX_FILE_CONTENT_LINES=100  # Max lines to show per file
```

**Command Line Arguments**:
```bash
python generate_code_review_context.py /path/to/project [--phase 2.0] [--output custom-path.md]
```

### 8. Dependencies

**requirements.txt**:
```
mcp>=0.1.0  # For MCP server
openai>=1.0.0  # Optional, for LLM summarization
pytest>=7.0.0  # For testing
pytest-mock>=3.0.0  # For mocking in tests
```

### 9. Sample Test Fixtures

**fixtures/sample_prd.md**:
```markdown
# Code Review Context Generator PRD

## Summary
This tool automates the generation of code review context by parsing project documentation and git changes. It creates structured templates for AI-assisted code reviews.

## Goals
- Parse PRD and task lists
- Generate review templates
- Integrate with MCP
```

**fixtures/sample_task_list.md**:
```markdown
## Tasks

- [x] 1.0 Set up project structure
  - [x] 1.1 Create directory layout
  - [x] 1.2 Initialize git repository
- [ ] 2.0 Implement core parsing logic
  - [x] 2.1 Create task parser
  - [ ] 2.2 Create PRD parser
  - [ ] 2.3 Add git integration
- [ ] 3.0 Add MCP integration
  - [ ] 3.1 Create MCP server wrapper
  - [ ] 3.2 Define tool schema
```

### 10. Implementation Order

1. **Start with tests** - Write all test files first with expected behavior
2. **Implement core script** - Make tests pass one by one:
   - File finding/reading functions
   - Task parser
   - PRD parser  
   - Git operations
   - File tree generator
   - Template formatter
   - Main orchestration

3. **Add MCP wrapper** - Simple subprocess wrapper
4. **Integration testing** - Full end-to-end tests
5. **Documentation** - README with examples

### 11. Key Edge Cases to Handle

- Task list with no checkboxes (use different format)
- Very large codebases (limit file tree depth)
- Binary files in git diff
- Unicode in file paths
- Windows vs Unix path separators
- Concurrent file modifications
- Missing optional dependencies (OpenAI)

### 12. Success Criteria

The implementation is complete when:
1. All tests pass
2. Script works standalone: `python generate_code_review_context.py /path`
3. MCP integration works: Tool can be called from MCP client
4. Handles all edge cases gracefully
5. Generated output matches template exactly
6. Performance: Completes in <5 seconds for typical projects

## CRITICAL: Use Test-Driven Development

Write the tests FIRST before implementing any functionality. Each test should define the expected behavior clearly. Only write implementation code to make tests pass.