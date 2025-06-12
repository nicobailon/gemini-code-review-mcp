# Gemini Code Review MCP

[![PyPI version](https://badge.fury.io/py/gemini-code-review-mcp.svg)](https://badge.fury.io/py/gemini-code-review-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green)](https://github.com/anthropics/mcp)
[![Gemini](https://img.shields.io/badge/Gemini-API-orange)](https://ai.google.dev)

![Gemini Code Review MCP](gemini-code-review-mcp.jpg)

> 🚀 **AI-powered code reviews that understand your project's context and development progress**

Transform your git diffs into actionable insights with contextual awareness of your project guidelines, task progress, and coding standards.

## 📚 Table of Contents

- [Why Use This?](#why-use-this)
- [Quick Start](#-quick-start)
- [Available MCP Tools](#-available-mcp-tools)
- [Configuration](#️-configuration)
- [Key Features](#-key-features)
- [CLI Usage](#️-cli-usage)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)

## Why Use This?

- **🎯 Context-Aware Reviews**: Automatically includes your CLAUDE.md guidelines and project standards
- **📊 Progress Tracking**: Understands your task lists and development phases
- **🤖 AI Agent Integration**: Seamless MCP integration with Claude Code and Cursor
- **🔄 Flexible Workflows**: GitHub PR reviews, project analysis, or custom scopes
- **⚡ Smart Defaults**: Auto-detects what to review based on your project state

## 🚀 Claude Code Installation

**Option A:** Install the MCP server to Claude Code as user-scoped MCP server:
```
claude mcp add-json gemini-code-review -s user '{"command":"uvx","args":["gemini-code-review-mcp"],"env":{"GEMINI_API_KEY":"your_key_here","GITHUB_TOKEN":"your_key_here"}}'
```
(`-s user` installs as user-scoped and will be available to you across all projects on your machine, and will be private to you. Omit `-s user` to install the as locally scoped.)

**Option B:** Install the MCP server to Claude Code as project-scoped MCP server:
```
claude mcp add-json gemini-code-review -s project /path/to/server '{"type":"stdio","command":"npx","args":["gemini-code-review"],"env":{"GEMINI_API_KEY":"your_key_here","GITHUB_TOKEN":"your_key_here"}}'
```

The command above creates or updates a `.mcp.json` file to the project root with the following structure:
```
{
  "mcpServers": {
    "gemini-code-review": {
      "command": "/path/to/server",
      "args": ["gemini-code-review"],
      "env": {"GEMINI_API_KEY":"your_key_here","GITHUB_TOKEN":"your_key_here"}
    }
  }
}
```

Get your Gemini API key:  https://ai.google.dev/gemini-api/docs/api-key

Get your GitHub token: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token

Docs for setting up MCP for Claude Code: https://docs.anthropic.com/en/docs/claude-code/tutorials#set-up-model-context-protocol-mcp


### Troubleshooting MCP Installation

If the MCP tools aren't working:
1. Check your installation: `claude mcp list`
2. Verify API key is set: `claude mcp get gemini-code-review`
3. If API key shows empty, remove and re-add:
   ```bash
   claude mcp remove gemini-code-review
   claude mcp add-json gemini-code-review -s user '{"type":"stdio","command":"npx","args":["@modelcontextprotocol/server-gemini-code-review"],"env":{"GEMINI_API_KEY":"your_key_here","GITHUB_TOKEN":"your_key_here"}}'
   ```
   (Make sure you replace `/path/to/server` with the path to your server executable)
4. **Always restart Claude Desktop after any MCP configuration changes**

## 📋 Available MCP Tools

| Tool | Purpose | Key Options |
|------|---------|-------------|
| **`generate_ai_code_review`** | Complete AI code review | `project_path`, `model`, `scope` |
| **`generate_pr_review`** | GitHub PR analysis | `github_pr_url`, `project_path` |
| **`ask_gemini`** | Generate context and get AI response | `user_instructions`, `file_selections` |
| **`generate_file_context`** (Deprecated) | Generate context without AI | `file_selections`, `user_instructions` |

<details>
<summary>📖 Detailed Tool Examples</summary>

### AI Code Review
```javascript
// Quick project review (uses default model: gemini-2.0-flash)
{
  tool_name: "generate_ai_code_review",
  arguments: {
    project_path: "/path/to/project"
  }
}

// With advanced model
{
  tool_name: "generate_ai_code_review",
  arguments: {
    project_path: "/path/to/project",
    model: "gemini-2.5-pro",  // Uses alias for gemini-2.5-pro-preview-06-05
    thinking_budget: 15000    // Optional: thinking tokens (when supported)
  }
}
```

### GitHub PR Review
```javascript
// Analyze GitHub pull request
{
  tool_name: "generate_pr_review",
  arguments: {
    github_pr_url: "https://github.com/owner/repo/pull/123",
    thinking_budget: 20000    // Optional: thinking tokens
  }
}

// With reference documentation
{
  tool_name: "generate_pr_review",
  arguments: {
    github_pr_url: "https://github.com/owner/repo/pull/123",
    url_context: ["https://docs.api.com/v2/guidelines"]  // Optional: Reference docs for the review
  }
}
```

### Ask Gemini (NEW!)
```javascript
// Generate context from files and get AI response in one step
{
  tool_name: "ask_gemini",
  arguments: {
    user_instructions: "Review for security vulnerabilities and suggest fixes",
    file_selections: [
      { path: "src/auth.py" },
      { path: "src/database.py", line_ranges: [[50, 100]] }
    ],
    project_path: "/path/to/project",
    model: "gemini-2.5-pro"
  }
}

// Simple query without files
{
  tool_name: "ask_gemini",
  arguments: {
    user_instructions: "Explain the security implications of the current authentication approach",
    include_claude_memory: true  // Includes project guidelines
  }
}
```

### File-Based Context Generation (Deprecated)
```javascript
// DEPRECATED: Use ask_gemini instead for AI responses
{
  tool_name: "generate_file_context",
  arguments: {
    file_selections: [
      { path: "src/main.py" },
      { path: "src/utils.py", line_ranges: [[10, 50], [100, 150]] }
    ],
    project_path: "/path/to/project",
    user_instructions: "Review for security vulnerabilities"
  }
}
```

</details>

### Common Workflows

#### Quick Project Review
```
Human: Generate a code review for my project

Claude: I'll analyze your project and generate a comprehensive review.

[Uses generate_ai_code_review with project_path]
```

#### GitHub PR Review
```
Human: Review this PR: https://github.com/owner/repo/pull/123

Claude: I'll fetch the PR and analyze the changes.

[Uses generate_pr_review with github_pr_url]
```

#### Custom Model Review
```
Human: Generate a detailed review using Gemini 2.5 Pro

Claude: I'll use Gemini 2.5 Pro for a more detailed analysis.

[Uses generate_ai_code_review with model="gemini-2.5-pro"]
```

#### File-Specific Review with AI
```
Human: Review auth.py and database.py lines 50-100 for security issues

Claude: I'll analyze those specific files for security vulnerabilities.

[Uses ask_gemini with file_selections and security-focused instructions]
```

#### Quick Code Question
```
Human: What are the performance implications of the current caching strategy?

Claude: I'll analyze your caching implementation and provide insights.

[Uses ask_gemini with user_instructions only, leveraging project context]
```

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|:---------|:--------:|:-------:|:------------|
| `GEMINI_API_KEY` | ✅ | - | Your [Gemini API key](https://ai.google.dev/gemini-api/docs/api-key) |
| `GITHUB_TOKEN` | ⬜ | - | GitHub token for PR reviews ([create one](https://github.com/settings/tokens)) |
| `GEMINI_MODEL` | ⬜ | `gemini-2.0-flash` | AI model selection |
| `GEMINI_TEMPERATURE` | ⬜ | `0.5` | Creativity (0.0-2.0) |
| `THINKING_BUDGET` | ⬜ | Auto | Thinking tokens (Pro: 128-32768, Flash: 0-24576) |

### Model Configuration

#### Default Models
- **Primary Model**: `gemini-2.0-flash` - Fast, efficient model for code reviews
- **Summary Model**: `gemini-2.0-flash-lite` - Used internally for quick summaries

#### Model Aliases
For convenience, you can use these short aliases instead of full model names:

| Alias | Full Model Name | Features |
|:------|:----------------|:---------|
| `gemini-2.5-pro` | `gemini-2.5-pro-preview-06-05` | Advanced reasoning, thinking mode, URL context |
| `gemini-2.5-flash` | `gemini-2.5-flash-preview-05-20` | Fast, thinking mode, URL context |

#### Available Models
All models support code review, with varying capabilities:

**With Thinking Mode + URL Context:**
- `gemini-2.5-pro` (alias) / `gemini-2.5-pro-preview-06-05`
- `gemini-2.5-flash` (alias) / `gemini-2.5-flash-preview-05-20`

**With URL Context Only:**
- `gemini-2.0-flash` (default)
- `gemini-2.0-flash-live-001`

**Basic Models:**
- `gemini-1.5-pro`
- `gemini-1.5-flash` (used for integration tests - cost-effective)

#### Usage Examples
```javascript
// Using default model (gemini-2.0-flash)
{ tool_name: "generate_ai_code_review", arguments: { project_path: "/path" } }

// Using alias for advanced model
{ tool_name: "generate_ai_code_review", arguments: { 
  project_path: "/path",
  model: "gemini-2.5-pro"  // Automatically resolves to gemini-2.5-pro-preview-06-05
} }

// Using full model name
{ tool_name: "generate_ai_code_review", arguments: { 
  project_path: "/path",
  model: "gemini-2.5-pro-preview-06-05"
} }
```

### Automatic Configuration Discovery

The tool automatically discovers and includes:
- 📁 **CLAUDE.md** files at project/user/enterprise levels
- 📝 **Cursor rules** (`.cursorrules`, `.cursor/rules/*.mdc`)
- 🔗 **Import syntax** (`@path/to/file.md`) for modular configs

## ✨ Key Features

- 🤖 **Smart Context** - Automatically includes CLAUDE.md, task lists, and project structure
- 🎯 **Flexible Scopes** - Review PRs, recent changes, or entire projects
- ⚡ **Model Selection** - Choose between Gemini 2.0 Flash (speed) or 2.5 Pro (depth)
- 🔄 **GitHub Integration** - Direct PR analysis with full context
- 📊 **Progress Aware** - Understands development phases and task completion
- 🔗 **URL Context** - Gemini automatically fetches and analyzes URLs in prompts (or use `--url-context` flag)

## 🖥️ CLI Usage

Alternative: Command-line interface for development/testing

### Installation

```bash
# Quick start with uvx (no install needed)
uvx gemini-code-review-mcp /path/to/project

# Or install globally
pip install gemini-code-review-mcp
```

### Commands

```bash
# Basic review (current directory)
generate-code-review

# Review specific project
generate-code-review /path/to/project

# Advanced options
generate-code-review . \
  --scope full_project \
  --model gemini-2.5-pro

# With thinking budget (current directory)
generate-code-review --thinking-budget 20000 --temperature 0.7

# With URL context for framework-specific review
generate-code-review \
  --file-instructions "Review my async implementation against the official docs" \
  --url-context https://docs.python.org/3/library/asyncio.html

# File-based context generation (for debugging - does not call AI)
generate-file-context -f src/main.py -f src/utils.py:10-50 \
  --user-instructions "Review for performance issues" \
  -o context.md

# Meta-prompt only (current directory)
generate-meta-prompt --stream
```

### Supported File Formats

- 📋 **Task Lists**: `/tasks/tasks-*.md` - Track development phases
- 📄 **PRDs**: `/tasks/prd-*.md` - Project requirements
- 📦 **Configs**: `CLAUDE.md`, `.cursorrules` - Coding standards

## 🆘 Troubleshooting

- **Missing API key?** → Get one at [ai.google.dev](https://ai.google.dev/gemini-api/docs/api-key)
- **MCP not working?** → Run `claude mcp list` to verify installation
- **Old version cached?** → Run `uv cache clean`

## 📦 Development

```bash
# Setup
git clone https://github.com/yourusername/gemini-code-review-mcp
cd gemini-code-review-mcp
pip install -e ".[dev]"

# Testing commands
python -m pytest tests/    # Run all tests in venv
make lint                  # Check code style
make test-cli             # Test CLI commands
```

### Testing Configuration

The test suite includes both mocked unit tests and real API integration tests:

#### Unit Tests (Default)
- **Fast execution**: Mock all external API calls
- **No API key required**: Run without any setup
- **Model configuration**: Tests use `gemini-2.0-flash` defaults
- **Run with**: `pytest` or `python -m pytest tests/`

#### Integration Tests (Optional)
- **Real API calls**: Uses `gemini-1.5-flash` for cost-effective testing
- **API key required**: Set `GEMINI_API_KEY` environment variable
- **Limited features**: Tests only features supported by `gemini-1.5-flash` (no thinking mode/URL context)
- **Run with**: `pytest -m integration` or `pytest tests/integration/`

#### Running Tests
```bash
# Run only unit tests (default, fast)
pytest

# Run only integration tests (requires API key)
export GEMINI_API_KEY=your_key_here
pytest -m integration

# Run all tests including integration
pytest -m ""

# Run specific integration test
pytest tests/integration/test_gemini_real.py::TestGeminiRealAPI::test_basic_code_review_generation

# Verbose output with integration tests
pytest -v -m integration
```

#### Test Features
- **Model verification**: Ensures `gemini-1.5-flash` is used for integration tests
- **Capability testing**: Validates that unsupported features are properly handled
- **Error handling**: Tests graceful degradation with invalid inputs
- **Temperature testing**: Verifies model parameter effects

## 📏 License

MIT License - see [LICENSE](LICENSE) file for details.

## 👥 Credits

Built by [Nico Bailon](https://github.com/nicobailon).
