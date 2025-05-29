# AI Dev Tasks MCP Server

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

### 🚀 Try It First (No Installation Required)

**Recommended**: Test the tool with uvx before deciding to install globally:

```bash
# Run directly without installing anything (uvx handles everything)
uvx ai-dev-tasks-mcp /path/to/your/project

# With specific options
uvx ai-dev-tasks-mcp /path/to/your/project --phase 2.0 --no-gemini
```

**Benefits of uvx approach:**
- ✅ No installation needed - just run and try it
- ✅ Automatic dependency isolation (no conflicts)
- ✅ Always gets the latest version
- ✅ Clean system - nothing left behind

### 📦 Install Globally (If You Like It)

After trying with uvx, install globally if you want it permanently available:

```bash
# Install from PyPI
pip install ai-dev-tasks-mcp

# Now available as a command
ai-dev-tasks-mcp /path/to/your/project
```

### 🛠️ Development Installation

For development or local testing:

```bash
# Clone and install in development mode
git clone <repository-url>
cd ai-dev-tasks-mcp
pip install -e .
```

## Usage

### Primary Use: MCP Server for AI Agents
The tool is designed as an MCP server that AI coding agents (Cursor, Claude Code) call automatically when completing development phases.

### Manual CLI Usage

**With uvx (Recommended - No Installation Required):**
```bash
# Auto-detect most recently completed phase (generates timestamped files)
uvx ai-dev-tasks-mcp /path/to/project
# Output: code-review-context-20250528-143052.md
# Output: code-review-comprehensive-feedback-20250528-143052.md (Gemini review)

# Disable Gemini AI review (context only)
uvx ai-dev-tasks-mcp /path/to/project --no-gemini
# Output: code-review-context-20250528-143052.md (only)

# Specify a particular phase for review
uvx ai-dev-tasks-mcp /path/to/project --phase 2.0
# Output: code-review-context-20250528-143052.md + AI feedback file

# Custom output file location (overrides automatic naming)
uvx ai-dev-tasks-mcp /path/to/project --output /custom/path/review.md

# Use Gemini 2.5 Pro instead of Flash (via environment variable)
GEMINI_MODEL=gemini-2.5-pro-preview-05-06 uvx ai-dev-tasks-mcp /path/to/project
```

**With Global Installation:**
```bash
# After installing with: pip install ai-dev-tasks-mcp

# Auto-detect most recently completed phase (generates timestamped files)
ai-dev-tasks-mcp /path/to/project
# Output: code-review-context-20250528-143052.md
# Output: code-review-comprehensive-feedback-20250528-143052.md (Gemini review)

# Disable Gemini AI review (context only)
ai-dev-tasks-mcp /path/to/project --no-gemini
# Output: code-review-context-20250528-143052.md (only)

# Specify a particular phase for review
ai-dev-tasks-mcp /path/to/project --phase 2.0
# Output: code-review-context-20250528-143052.md + AI feedback file

# Custom output file location (overrides automatic naming)
ai-dev-tasks-mcp /path/to/project --output /custom/path/review.md

# Use Gemini 2.5 Pro instead of Flash (via environment variable)
GEMINI_MODEL=gemini-2.5-pro-preview-05-06 ai-dev-tasks-mcp /path/to/project
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

### Option 1: Using Script Entry Point (Recommended)

After installing the package, you can use the dedicated MCP server entry point:

```bash
# Install the package first
uvx install .

# Use the MCP server entry point
ai-dev-tasks-mcp
```

### Option 2: Claude Code CLI

Install the MCP server using Claude Code's built-in commands:

```bash
# Option A: Using entry point (recommended)
claude mcp add task-list-reviewer ai-dev-tasks-mcp \
  -e GEMINI_API_KEY=your_gemini_api_key_here

# Option B: Direct Python execution
claude mcp add task-list-reviewer python /path/to/ai-dev-tasks-mcp/src/server.py \
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

**Option A: Using entry point (recommended):**
```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "ai-dev-tasks-mcp",
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

**Option B: Direct Python execution:**
```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": [
        "/path/to/ai-dev-tasks-mcp/src/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

**Note**: Option A requires `uvx install .` first. Option B requires replacing `/path/to/ai-dev-tasks-mcp` with your actual project path.

### Configuring Gemini Model Selection

You can choose between Gemini 2.5 Flash (default) and Pro models by setting the `GEMINI_MODEL` environment variable:

**For Claude Desktop/Cursor (claude_desktop_config.json):**
```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "python",
      "args": ["/path/to/ai-dev-tasks-mcp/src/server.py"],
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
claude mcp add task-list-reviewer python /path/to/ai-dev-tasks-mcp/src/server.py \
  -e GEMINI_API_KEY=your_key \
  -e GEMINI_MODEL=gemini-2.5-flash-preview-05-20

# Use Pro (complex reasoning, in-depth analysis)
claude mcp add task-list-reviewer python /path/to/ai-dev-tasks-mcp/src/server.py \
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