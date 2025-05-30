# Task List Code Review MCP Server

An MCP server tool designed for **AI coding agents** (Cursor, Claude Code, etc.) to automatically generate comprehensive code review context when completing development phases.

**Version**: 0.2.1 - Enhanced with scope-based reviews, dual tool architecture, AI-powered code analysis, and configurable model management.

## 🚀 Quick Start

### Try It First (No Installation Required)

**Recommended**: Test the tool with uvx before deciding to install globally:

```bash
# Set your Gemini API key (get one at https://ai.google.dev/gemini-api/docs/api-key)
export GEMINI_API_KEY=your_key_here

# Or create a .env file (copy from .env.example)
# cp .env.example .env  # then edit with your keys

# Run directly without installing anything (uvx handles everything)
uvx task-list-code-review-mcp /path/to/your/project

# Shows real-time progress and model capabilities:
# 🔍 Analyzing project: my-app
# 📊 Review scope: recent_phase  
# 🤖 Using Gemini model: gemini-2.0-flash
# ✨ Enhanced features enabled: web grounding, thinking mode
# 📄 Files generated: code-review-context-recent-phase-20241201-143052.md, ...
```

### Install Globally (If You Like It)

```bash
# Install from PyPI
pip install task-list-code-review-mcp

# Now available as a command
task-list-code-review-mcp /path/to/your/project
```

## ✨ Key Features

### Smart Scope Detection
- **All phases complete** → Automatically generates comprehensive full-project review
- **Phases in progress** → Reviews most recently completed phase
- **Manual override** → Target specific phases or tasks

### AI-Powered Code Review
- **Smart Model Selection**: Auto-detects and displays enabled capabilities
- **Enhanced Features**: Thinking mode, web grounding, URL context (when available)
- **Real-time Feedback**: Shows model name and active features during execution
- **Comprehensive Analysis**: Security, performance, testing, maintainability

### Flexible Architecture
- **Context Generation**: Creates structured review context from git changes and task progress
- **AI Review**: Separate tool for generating AI-powered feedback from context files
- **Model Configuration**: Easy model switching and alias management via JSON config

## 📖 Basic Usage

### CLI Usage

```bash
# Smart Default: Auto-detects project completion status and task list
uvx task-list-code-review-mcp /path/to/project
# Shows: 🔍 Project analysis → 🤖 Model capabilities → 📄 Generated files

# Review entire project (force full scope)
uvx task-list-code-review-mcp /path/to/project --scope full_project

# Review specific phase by number
uvx task-list-code-review-mcp /path/to/project --scope specific_phase --phase-number 2.0

# Use specific task list (when multiple exist)
uvx task-list-code-review-mcp /path/to/project --task-list tasks-auth-system.md

# Generate context only (skip AI review)
uvx task-list-code-review-mcp /path/to/project --context-only

# Use different Gemini model
GEMINI_MODEL=gemini-2.5-pro uvx task-list-code-review-mcp /path/to/project

# Works without task lists (uses intelligent default prompt)
uvx task-list-code-review-mcp /path/to/project --default-prompt "Review security and performance"
```

### Task List Discovery

**How the tool finds task lists:**

- **Auto-discovery**: Searches `/tasks/` directory for `tasks-*.md` files
- **Multiple files**: Uses most recently modified task list
- **Specific selection**: Use `--task-list filename.md` to choose exact file  
- **No task lists**: Falls back to intelligent default prompts
- **Logging**: Shows which task list was selected when multiple exist

**Examples:**
```bash
# Multiple task lists in /tasks/:
# - tasks-auth-system.md (modified yesterday)
# - tasks-payment-flow.md (modified today) ← Auto-selected

# Tool output: "Auto-selected most recent: tasks-payment-flow.md"

# Override auto-selection:
uvx task-list-code-review-mcp . --task-list tasks-auth-system.md
```

### MCP Server Integration

#### Claude Desktop/Cursor Configuration
**Setup** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "task-list-reviewer": {
      "command": "uvx",
      "args": ["task-list-code-review-mcp"],
      "env": {
        "GEMINI_API_KEY": "your_key_here",
        "GITHUB_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

**For GitHub PR Review Support**: Add your GitHub token to enable `generate_pr_review` tool.
Create token at: https://github.com/settings/tokens (scopes: `repo` or `public_repo`)

**Usage in Claude Desktop:**
```
Human: Generate a code review context for my project at /Users/myname/projects/my-app

Claude: I'll generate a code review context using smart scope detection.

[Tool Use: generate_code_review_context]
{
  "project_path": "/Users/myname/projects/my-app"
}

[Tool Result] Successfully generated: code-review-context-full-project-20241201-143052.md
```

**With Configuration Control:**
```
Human: Review my project but include Cursor rules and disable CLAUDE.md files

Claude: I'll generate a review with Cursor rules enabled and CLAUDE.md disabled.

[Tool Use: generate_code_review_context]
{
  "project_path": "/Users/myname/projects/my-app",
  "include_claude_memory": false,
  "include_cursor_rules": true
}

[Tool Result] 🔍 Discovered Cursor rules... ✅ Found 0 Claude memory files, 3 Cursor rules
```

#### Claude Code CLI Integration

**Add this MCP server to Claude Code:**
```bash
# Add the MCP server (set your API keys)
claude mcp add task-list-reviewer -e GEMINI_API_KEY=your_key_here -e GITHUB_TOKEN=your_github_token_here -- uvx task-list-code-review-mcp

# Verify it's added
claude mcp list

# Use in Claude Code sessions
claude # Opens Claude Code with MCP server available
```

**Usage in Claude Code:**
```
Human: Generate a code review for my current project

Claude: I'll analyze your project and generate a comprehensive code review.

[Tool Use: generate_code_review_context]
{
  "project_path": "/Users/myname/projects/my-app"
}

[Tool Result] Generated: code-review-context-full-project-20241201-143052.md
```

**Branch Comparison Review:**
```
Human: Compare my feature branch against main and generate a review

Claude: I'll compare your feature branch changes against the main branch.

[Tool Use: generate_branch_comparison_review]
{
  "project_path": "/Users/myname/projects/my-app",
  "compare_branch": "feature/auth-system",
  "target_branch": "main"
}

[Tool Result] 🔍 Analyzed project: my-app
🌿 Branch comparison: feature/auth-system → main
📝 Generated review context: code-review-branch-comparison-20241201-143052.md
```

**GitHub PR Review:**
```
Human: Review this GitHub PR: https://github.com/owner/repo/pull/123

Claude: I'll fetch the PR data and generate a comprehensive review.

[Tool Use: generate_pr_review]
{
  "github_pr_url": "https://github.com/owner/repo/pull/123"
}

[Tool Result] 🔍 Analyzed project: repo
🔗 GitHub PR: owner/repo/pull/123
📝 Generated review context: code-review-github-pr-20241201-143052.md
```

**MCP Server Management:**
```bash
# List all MCP servers
claude mcp list

# Get server details
claude mcp get task-list-reviewer

# Remove server if needed
claude mcp remove task-list-reviewer
```

## 🛠 Advanced Configuration

### Environment Variables

**Essential:**
- `GEMINI_API_KEY`: Required for AI features
- `GEMINI_MODEL`: Model selection (`gemini-2.0-flash`, `gemini-2.5-pro`, `gemini-2.5-flash`)
- `GEMINI_TEMPERATURE`: AI creativity (0.0-2.0, default: 0.5)

**Advanced:**
- `MAX_FILE_SIZE_MB`: File size limit (default: 10)
- `DISABLE_THINKING`: Disable thinking mode (`true`/`false`)
- `DISABLE_GROUNDING`: Disable web grounding (`true`/`false`)

### 📋 Configuration File Integration

**The tool can automatically discover and include project configuration files in code reviews.**

#### 🔧 CLAUDE.md Files (Default: **ENABLED**)
- **Project-level**: `/project/CLAUDE.md` - Project-specific guidelines
- **User-level**: `~/.claude/CLAUDE.md` - Personal coding preferences  
- **Enterprise-level**: System-wide policies (platform-specific)
- **With imports**: Supports `@path/to/file.md` import syntax

#### ⚙️ Cursor Rules (Default: **DISABLED**)
- **Legacy format**: `.cursorrules` - Simple text rules
- **Modern format**: `.cursor/rules/*.mdc` - Rich metadata with frontmatter
- **Monorepo support**: Recursive discovery in nested directories

#### 🎛️ Control Flags

```bash
# Default behavior (CLAUDE.md enabled, Cursor rules disabled)
uvx task-list-code-review-mcp /path/to/project

# Disable CLAUDE.md inclusion
uvx task-list-code-review-mcp /path/to/project --no-claude-memory

# Enable Cursor rules inclusion  
uvx task-list-code-review-mcp /path/to/project --include-cursor-rules

# Enable both configuration types
uvx task-list-code-review-mcp /path/to/project --include-cursor-rules

# Disable all configurations
uvx task-list-code-review-mcp /path/to/project --no-claude-memory
```

#### 🎯 Smart Features
- **Deduplication**: Handles `.gitignore` cases (tracked vs untracked files)
- **Hierarchy**: Project configs override user configs override enterprise
- **Caching**: File modification time tracking for performance
- **Error handling**: Graceful degradation when files are malformed/missing

### Security Best Practices

**Environment Setup:**
```bash
# Copy the example file and fill in your values
cp .env.example .env

# Secure .env file permissions
chmod 600 .env

# Never commit .env files to version control (already in .gitignore)
```

**API Key Protection:**
- Get your Gemini API key at: https://ai.google.dev/gemini-api/docs/api-key
- Create GitHub token at: https://github.com/settings/tokens (scopes: `repo` or `public_repo`)
- Use separate API keys for development and production
- Regularly rotate your API keys for security

### Model Configuration

**Auto-Detection**: The tool automatically detects and displays model capabilities:
- **Thinking Mode**: Deep reasoning (gemini-2.5 models)
- **Web Grounding**: Real-time information lookup (gemini-2.0+)
- **URL Context**: Enhanced web understanding (supported models)

**Simple Usage:**
```bash
# Use friendly aliases instead of preview model names
GEMINI_MODEL=gemini-2.5-pro uvx task-list-code-review-mcp /project
GEMINI_MODEL=gemini-2.5-flash uvx task-list-code-review-mcp /project
```

**Configuration File**: `src/model_config.json` manages aliases and capabilities. Updates automatically when Google releases new models.

## 🔧 MCP Tools Reference

### generate_code_review_context

**Primary tool for generating code review context with flexible scope options.**

**Scope Options:**

| Scope | Description | Output Pattern |
|-------|-------------|----------------|
| `recent_phase` | **Smart Default**: Reviews recent phase OR full project if all complete | `*-recent-phase-*` or `*-full-project-*` |
| `full_project` | Reviews all completed phases | `*-full-project-*` |
| `specific_phase` | Reviews specific phase (requires `phase_number`) | `*-phase-X-Y-*` |
| `specific_task` | Reviews specific task (requires `task_number`) | `*-task-X-Y-*` |

**MCP Usage Examples:**
```javascript
// Smart default - auto-detects completion status
await use_mcp_tool({
  server_name: "task-list-code-review-mcp",
  tool_name: "generate_code_review_context",
  arguments: {
    project_path: "/absolute/path/to/project"
  }
});

// Review specific phase
await use_mcp_tool({
  server_name: "task-list-code-review-mcp",
  tool_name: "generate_code_review_context",
  arguments: {
    project_path: "/absolute/path/to/project",
    scope: "specific_phase",
    phase_number: "2.0"
  }
});
```

### generate_ai_code_review

**Standalone tool for generating AI-powered code reviews from existing context files.**

```javascript
await use_mcp_tool({
  server_name: "task-list-code-review-mcp",
  tool_name: "generate_ai_code_review",
  arguments: {
    context_file_path: "/path/to/code-review-context-*.md",
    model: "gemini-2.5-pro"
  }
});
```

### generate_branch_comparison_review

**Generate code review by comparing git branches.**

```javascript
await use_mcp_tool({
  server_name: "task-list-code-review-mcp",
  tool_name: "generate_branch_comparison_review",
  arguments: {
    project_path: "/absolute/path/to/project",
    compare_branch: "feature/auth-system",
    target_branch: "main"  // Optional - auto-detects main/master if omitted
  }
});
```

**Example output:**
```
🔍 Analyzed project: my-app
🌿 Branch comparison: feature/auth-system → main
🌡️ AI temperature: 0.5
📝 Generated review context: code-review-branch-comparison-20241201-143052.md
✅ AI code review completed: code-review-comprehensive-feedback-20241201-143052.md
🎉 Branch comparison review completed!
📄 Files generated: code-review-branch-comparison-20241201-143052.md, code-review-comprehensive-feedback-20241201-143052.md
```

### generate_pr_review

**Generate code review for a GitHub Pull Request.**

```javascript
await use_mcp_tool({
  server_name: "task-list-code-review-mcp",
  tool_name: "generate_pr_review",
  arguments: {
    github_pr_url: "https://github.com/owner/repo/pull/123",
    project_path: "/absolute/path/to/project"  // Optional - uses current directory if omitted
  }
});
```

**Example output:**
```
🔍 Analyzed project: my-app
🔗 GitHub PR: owner/repo/pull/123
🌡️ AI temperature: 0.5
📝 Generated review context: code-review-github-pr-20241201-143052.md
✅ AI code review completed: code-review-comprehensive-feedback-20241201-143052.md
🎉 GitHub PR review completed!
📄 Files generated: code-review-github-pr-20241201-143052.md, code-review-comprehensive-feedback-20241201-143052.md
```

## 📋 Enhanced Review Context Formats

### Branch Comparison Context

When using `generate_branch_comparison_review`, the generated context includes:

**Enhanced Metadata Sections:**
- **Branch Comparison Metadata**: Source/target branches, file statistics, commit counts
- **Detailed Commit Information**: Up to 15 commits with authors, timestamps, and messages
- **Branch Statistics**: Comprehensive summary of changes between branches
- **Specialized Instructions**: Context-aware guidance for reviewing branch differences

**Filename Format:** `code-review-context-branch-comparison-YYYYMMDD-HHMMSS.md`

### GitHub PR Context

When using `generate_pr_review`, the generated context includes:

**Enhanced Metadata Sections:**
- **GitHub PR Metadata**: Repository, PR number, title, author, SHA hashes, timestamps
- **PR Description**: First 200 characters of the PR description
- **File Change Statistics**: Detailed breakdown of additions, modifications, deletions
- **Specialized Instructions**: PR-specific review guidance focusing on quality and security

**Filename Format:** `code-review-context-github-pr-YYYYMMDD-HHMMSS.md`

### Task-Based Context (Traditional)

Standard task list reviews include:
- **Phase/Task Metadata**: Current phase, completed subtasks, next steps
- **Working Directory Changes**: Git status and modified files
- **PRD Context**: Project requirements and scope information

**Filename Formats:**
- `code-review-context-recent-phase-YYYYMMDD-HHMMSS.md`
- `code-review-context-full-project-YYYYMMDD-HHMMSS.md`
- `code-review-context-phase-X-Y-YYYYMMDD-HHMMSS.md`

## 🔄 Workflow Integration for AI Agents

### Smart Completion Detection

The tool automatically detects project completion status:

**Project Complete Workflow:**
```
Human: "Generate a code review for my completed project"
AI Agent: I'll analyze your project and generate a comprehensive review.
Tool detects: All phases (1.0-7.0) complete → Full project review
Output: code-review-context-full-project-{timestamp}.md
```

**Mid-Development Workflow:**
```
Human: "I just finished Phase 2.0, can you review what I've done?"
AI Agent: I'll review your recent work using the MCP server.
Tool detects: Phases in progress → Recent completed phase
Output: code-review-context-recent-phase-{timestamp}.md
```

### Compatible Format Specifications

**PRDs (Optional)**: Based on [create-prd.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/create-prd.mdc)
- File naming: `prd-[feature-name].md` in `/tasks/` directory
- Structured markdown with Goals, User Stories, Functional Requirements
- **Not required**: Tool works without PRD files

**Task Lists**: Based on [generate-tasks.mdc](https://github.com/snarktank/ai-dev-tasks/blob/main/generate-tasks.mdc)
- File naming: `tasks-[feature-name].md` in `/tasks/` directory
- Hierarchical phases (1.0, 2.0) with sub-tasks (1.1, 1.2)
- Checkbox progress tracking (`- [ ]` / `- [x]`)
- **Flexible**: Multiple task lists supported, auto-discovery available

## 🆘 Need Help?

**Missing API key?** Get one at: https://ai.google.dev/gemini-api/docs/api-key  
**Error messages?** The tool provides specific solutions for each issue  
**Still stuck?** Check the [MCP Inspector Guide](./MCP_INSPECTOR_GUIDE.md) for testing

## 📋 What This Tool Generates

- **Phase Progress Summary** - Completed phases and sub-tasks
- **PRD Context** - Original requirements (auto-summarized with Gemini)
- **Git Changes** - Detailed diff of all modified/added/deleted files
- **File Tree** - ASCII project structure representation
- **File Content** - Full content of changed files for review
- **AI Code Review** - Comprehensive feedback using Gemini 2.5
- **Structured Output** - Professional markdown ready for human review

## 📦 Development

```bash
# Clone and install in development mode
git clone <repository-url>
cd task-list-code-review-mcp
pip install -e .

# Run tests
pytest
```

## 📄 Project Structure

- `src/generate_code_review_context.py` - Core context generation
- `src/ai_code_review.py` - Standalone AI review tool
- `src/server.py` - MCP server wrapper
- `src/model_config.json` - Model configuration and aliases
- `tests/` - Comprehensive test suite
- `pyproject.toml` - Project configuration and entry points