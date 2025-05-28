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