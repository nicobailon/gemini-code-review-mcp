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

- **🎯 Context-Aware Reviews**: Can include your CLAUDE.md guidelines and project standards (opt-in)
- **📊 Progress Tracking**: Understands your task lists and development phases
- **🤖 AI Agent Integration**: Seamless MCP integration with Claude Code and Cursor
- **🔄 Flexible Workflows**: GitHub PR reviews, project analysis, or custom scopes
- **⚡ Smart Defaults**: Auto-detects what to review based on your project state

## 🚀 Claude Code Installation

**Option A:** Install the MCP server to Claude Code as user-scoped MCP server (recommended):
```bash
claude mcp add-json gemini-code-review -s user '{"command":"uvx","args":["gemini-code-review-mcp"],"env":{"GEMINI_API_KEY":"your_key_here","GITHUB_TOKEN":"your_github_token_here"}}'
```
(`-s user` installs as user-scoped and will be available to you across all projects on your machine, and will be private to you.)

**Option B:** Install the MCP server to Claude Code as project-scoped MCP server:
```bash
claude mcp add-json gemini-code-review -s project '{"command":"uvx","args":["gemini-code-review-mcp"],"env":{"GEMINI_API_KEY":"your_key_here","GITHUB_TOKEN":"your_github_token_here"}}'
```
(This creates or updates a `.mcp.json` file in the project root)

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
   claude mcp add-json gemini-code-review -s user '{"command":"uvx","args":["gemini-code-review-mcp"],"env":{"GEMINI_API_KEY":"your_key_here","GITHUB_TOKEN":"your_github_token_here"}}'
   ```
4. **Always restart Claude Desktop after any MCP configuration changes**

## 📋 Available MCP Tools

| Tool | Purpose | Key Options |
|------|---------|-------------|
| **`generate_ai_code_review`** | Complete AI code review | `project_path`, `model`, `scope` |
| **`generate_pr_review`** | GitHub PR analysis | `github_pr_url`, `project_path` |
| **`ask_gemini`** | Generate context and get AI response | `user_instructions`, `file_selections` |

📖 Detailed Tool Examples

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
    include_claude_memory: true  // Optional - includes project guidelines (off by default)
  }
}
```

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

### Optional Configuration Discovery

The tool can discover and include when opted-in:
- 📁 **CLAUDE.md** files at project/user/enterprise levels (use `include_claude_memory: true`)
- 📝 **Cursor rules** (`.cursorrules`, `.cursor/rules/*.mdc`) (use `include_cursor_rules: true`)
- 🔗 **Import syntax** (`@path/to/file.md`) for modular configs

## ✨ Key Features

- 🤖 **Smart Context** - Includes task lists and project structure, with optional CLAUDE.md/cursor rules
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

# Include project guidelines (CLAUDE.md)
generate-code-review --include-claude-memory

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

### Installation for Development

If you want to contribute or modify the code, clone the repository:

```bash
# Clone the repository
git clone https://github.com/nicobailon/gemini-code-review-mcp
cd gemini-code-review-mcp

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY and GITHUB_TOKEN
```

### Development Workflow

```bash
# Run the MCP server locally
python -m src.server

# Test CLI commands
generate-code-review /path/to/project

# Run tests
python -m pytest tests/    # Run all tests
python -m pytest tests/ -v # Verbose output

# Code quality
make lint                  # Check code style
make format               # Auto-format code
make test-cli             # Test CLI commands
```

### Installing Development Version in Claude Code

To use your local development version with Claude Code:

```bash
# Option 1: Use the local Python script directly
claude mcp add-json gemini-code-review-dev -s user '{"command":"python","args":["-m","src.server"],"cwd":"/path/to/gemini-code-review-mcp","env":{"GEMINI_API_KEY":"your_key_here","GITHUB_TOKEN":"your_github_token_here"}}'

# Option 2: Install your local version with pip and use it
pip install -e /path/to/gemini-code-review-mcp
claude mcp add-json gemini-code-review-dev -s user '{"command":"gemini-code-review-mcp","env":{"GEMINI_API_KEY":"your_key_here","GITHUB_TOKEN":"your_github_token_here"}}'
```

Remember to restart Claude Desktop after adding the development server.

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
