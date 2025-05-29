# 🔍 MCP Inspector Testing Guide for Task List Code Review MCP Server v0.2.1

This guide walks you through installing and using MCP Inspector to test our Task List Code Review MCP server functionality. MCP Inspector is the official testing tool for Model Context Protocol (MCP) servers.

## 🤔 What is MCP Inspector?

MCP Inspector is a web-based tool that allows you to:
- Connect to and test MCP servers
- Explore available tools and their schemas
- Execute tools with custom parameters
- View tool responses and debug issues
- Understand how MCP servers communicate

## ✅ Prerequisites

- Node.js 18+ installed on your system
- Our Task List Code Review MCP server v0.2.1 (already built and available)
- Basic understanding of our project structure
- GEMINI_API_KEY environment variable (required for AI features)

## 📦 Installation

### Option 1: Run with npx (Recommended)
```bash
npx @modelcontextprotocol/inspector
```

### Option 2: Install globally
```bash
npm install -g @modelcontextprotocol/inspector
mcp-inspector
```

## 🚀 Starting MCP Inspector

1. **Launch Inspector**:
   ```bash
   npx @modelcontextprotocol/inspector
   ```

2. **Open in Browser**: 
   - Inspector will automatically open in your default browser
   - If not, navigate to: `http://localhost:5173`

3. **Inspector Interface**: You'll see a clean web interface with connection options

## 🔌 Connecting Our MCP Server

### Method 1: Using uvx (Recommended for Testing)

1. **In MCP Inspector**, click "Add Server" or "Connect to Server"

2. **Configure Server Connection**:
   ```json
   {
     "name": "Task List Code Review MCP v0.2.1",
     "command": "uvx",
     "args": ["task-list-code-review-mcp"],
     "env": {
       "GEMINI_API_KEY": "your_actual_gemini_api_key_here"
     }
   }
   ```

3. **Alternative if uvx fails**:
   ```json
   {
     "name": "Task List Code Review MCP v0.2.1 (explicit version)",
     "command": "uvx",
     "args": ["--from", "task-list-code-review-mcp==0.2.1", "task-list-code-review-mcp"]
   }
   ```

### Method 2: Using Local Development Version

If you want to test the local development version:

1. **Configure Server Connection**:
   ```json
   {
     "name": "Task List Code Review MCP (Local Dev)",
     "command": "python",
     "args": ["-m", "src.server"],
     "cwd": "/Users/nicobailon/Documents/development/task-list-code-review-mcp",
     "env": {
       "GEMINI_API_KEY": "your_actual_gemini_api_key_here"
     }
   }
   ```

### 🔧 Environment Variable Configuration

To test with custom settings, you can add environment variables in MCP Inspector:

1. **In Server Configuration**, click "Environment Variables"
2. **Add environment variables** (✅ = required, 🔧 = optional):
   ```json
   {
     "GEMINI_API_KEY": "your_actual_gemini_api_key_here",  // ✅ Required
     "GEMINI_MODEL": "gemini-2.0-flash",                   // 🔧 Optional (uses model aliases)
     "GEMINI_TEMPERATURE": "0.5"                           // 🔧 Optional (CLI/MCP override)
   }
   ```

3. **🔥 New in v0.2.1: Model Aliases**
   ```json
   {
     "GEMINI_MODEL": "gemini-2.5-pro"     // → Uses gemini-2.5-pro-preview-05-06
   }
   ```

4. **Save Configuration** and connect to the server

## ✅ Testing Server Connection

### 1. Verify Connection Status
- Look for a green "Connected" indicator
- Server name should appear in the left sidebar
- No error messages in the connection panel

### 2. Server Information
Once connected, you should see:
- **Server Name**: "MCP Server - Code Review Context Generator"
- **Protocol Version**: MCP version (usually 2024-11-05)
- **Capabilities**: List of supported MCP features

## 🛠️ Exploring Available Tools

### 1. Tools Panel
In the MCP Inspector interface:
- Click on "Tools" in the left navigation
- You should see **2 available tools**:
  - `generate_code_review_context`
  - `generate_ai_code_review`

### 2. Tool Schemas

#### 📋 `generate_code_review_context`
- **Description**: "Generate code review context with flexible scope options"
- **Parameters**:
  - `project_path` (✅ required, string): Absolute path to project root directory
  - `scope` (🔧 optional, string): Review scope - 'recent_phase', 'full_project', 'specific_phase', 'specific_task' (default: 'recent_phase')
  - `phase_number` (🔧 optional, string): Phase number for specific_phase scope (e.g., '2.0')
  - `task_number` (🔧 optional, string): Task number for specific_task scope (e.g., '1.2')
  - `current_phase` (🔧 optional, string): Legacy phase override (e.g., '2.0'). Auto-detects if not provided
  - `output_path` (🔧 optional, string): Custom output file path. Uses smart naming if not provided
  - `enable_gemini_review` (🔧 optional, boolean): Enable Gemini AI code review (default: true)
  - `temperature` (🔧 optional, number): Temperature for AI model (default: 0.5, range: 0.0-2.0)

#### 🤖 `generate_ai_code_review`
- **Description**: "Generate AI-powered code review from existing context file"
- **Parameters**:
  - `context_file_path` (✅ required, string): Path to existing code review context file (.md)
  - `output_path` (🔧 optional, string): Custom output file path for AI review
  - `model` (🔧 optional, string): Optional Gemini model name (supports aliases)
  - `temperature` (🔧 optional, number): Temperature for AI model (default: 0.5, range: 0.0-2.0)

## 🧪 Testing Tool Functionality

### Test Case 1: Basic Functionality Test

1. **Click "Execute" on the `generate_code_review_context` tool**

2. **Configure Parameters**:
   ```json
   {
     "project_path": "/Users/nicobailon/Documents/development/task-list-code-review-mcp",
     "scope": "specific_phase",
     "phase_number": "3.0",
     "enable_gemini_review": false
   }
   ```

3. **Expected Response**:
   - Status: Success (green indicator)
   - Response should contain:
     - "Successfully generated code review context"
     - Output file path (scope-based naming: `phase-3-0-*.md`)
     - Content preview (first 2000 characters)

### Test Case 2: Smart Scope Detection (🔥 New in v0.2.1)

1. **Execute with minimal parameters**:
   ```json
   {
     "project_path": "/Users/nicobailon/Documents/development/task-list-code-review-mcp"
   }
   ```

2. **Expected Behavior**:
   - 🧠 **Smart Logic**: Auto-detects current phase from task list
   - 🚀 **Auto-upgrade**: If ALL phases complete → automatically becomes `full_project` scope
   - 📁 **Smart naming**: Output file named based on detected scope (`recent-phase-*.md` or `full-project-*.md`)
   - Generate review context with Gemini review enabled (default)

### Test Case 3: Error Handling

1. **Test with invalid path**:
   ```json
   {
     "project_path": "/nonexistent/path"
   }
   ```

2. **Expected Response**:
   - Error message: "ERROR: Project path does not exist: /nonexistent/path"

3. **Test with relative path**:
   ```json
   {
     "project_path": "./relative/path"
   }
   ```

4. **Expected Response**:
   - Error message: "ERROR: project_path must be an absolute path"

### Test Case 4: Temperature Configuration (🔥 Enhanced in v0.2.1)

1. **Test with MCP parameter (highest priority)**:
   ```json
   {
     "project_path": "/Users/nicobailon/Documents/development/task-list-code-review-mcp",
     "scope": "full_project",
     "enable_gemini_review": true,
     "temperature": 0.2
   }
   ```

2. **Expected Behavior**:
   - 🎯 **Priority Order**: MCP parameter > Environment variable > Default (0.5)
   - Should use temperature 0.2 (more deterministic AI responses)
   - Output file: `full-project-*.md`

3. **Test with environment variable fallback**:
   - Set `GEMINI_TEMPERATURE=0.8` in environment variables
   - Execute without temperature parameter:
   ```json
   {
     "project_path": "/Users/nicobailon/Documents/development/task-list-code-review-mcp",
     "enable_gemini_review": true
   }
   ```

4. **Expected Behavior**:
   - Should use temperature 0.8 from environment variable
   - More creative/varied AI responses compared to default 0.5

### Test Case 5: Custom Output Path

1. **Execute with custom output**:
   ```json
   {
     "project_path": "/Users/nicobailon/Documents/development/task-list-code-review-mcp",
     "output_path": "/tmp/custom-review-context.md"
   }
   ```

2. **Expected Behavior**:
   - Should create file at specified path
   - Response should reference the custom path
   - Overrides smart naming logic

### Test Case 6: Testing `generate_ai_code_review` Tool (🔥 New in v0.2.1)

1. **First generate a context file**:
   ```json
   {
     "project_path": "/Users/nicobailon/Documents/development/task-list-code-review-mcp",
     "enable_gemini_review": false
   }
   ```

2. **Note the output file path from the response**

3. **Execute AI review tool**:
   ```json
   {
     "context_file_path": "/path/from/step1/recent-phase-TIMESTAMP.md",
     "model": "gemini-2.5-pro",
     "temperature": 0.3
   }
   ```

4. **Expected Behavior**:
   - Uses model alias (gemini-2.5-pro → gemini-2.5-pro-preview-05-06)
   - Generates comprehensive AI review
   - Returns full AI review content

## 📊 Understanding the Response

### Successful Response Structure
```
Successfully generated code review context.

Output file: /path/to/output/file.md

Content:
[First 2000 characters of generated content]...
```

### 🔥 New in v0.2.1: Smart File Naming
- `recent-phase-TIMESTAMP.md` - Recent phase reviews
- `full-project-TIMESTAMP.md` - Full project reviews (auto-detected or explicit)
- `phase-X-Y-TIMESTAMP.md` - Specific phase reviews
- `task-X-Y-TIMESTAMP.md` - Specific task reviews

### Error Response Structure
```
ERROR: [Descriptive error message]
```

## 🚨 Common Issues and Troubleshooting

### Connection Issues

**❌ Problem**: "Failed to connect to server"
**✅ Solutions**:
1. Ensure uvx is installed: `pip install uvx`
2. Verify package installation: `uvx task-list-code-review-mcp --help`
3. Check for any Python environment issues
4. 🔥 **New**: Verify you're using correct version: `uvx --from task-list-code-review-mcp==0.2.1 task-list-code-review-mcp`

**❌ Problem**: "Server process exited"
**✅ Solutions**:
1. Check if all dependencies are installed
2. Verify Python version compatibility (3.8+)
3. Look at server logs in Inspector's debug panel
4. 🔥 **New**: Check GEMINI_API_KEY is set (required for AI features)

### Tool Execution Issues

**❌ Problem**: "Tool execution failed"
**✅ Solutions**:
1. Verify all required parameters are provided
2. Ensure paths are absolute and exist
3. Check file permissions for output directory
4. 🔥 **New**: For `generate_ai_code_review`, ensure context file exists and is readable

**❌ Problem**: "Gemini API errors"
**✅ Solutions**:
1. Set `enable_gemini_review: false` to test without AI
2. Check if GEMINI_API_KEY environment variable is set (required)
3. Verify API key has proper permissions
4. 🔥 **New**: Use model aliases for easier configuration (e.g., "gemini-2.5-pro" instead of full preview names)
5. Check if model supports advanced features based on model_config.json

## 🔥 v0.2.1 Feature Highlights

### 🎯 Model Configuration System
- **JSON-based aliases**: Use simple names like `gemini-2.5-pro` instead of full preview names
- **Capability detection**: Automatic feature enablement based on model support
- **Configuration file**: `/src/model_config.json` defines aliases and capabilities

### 🧠 Smart Scope Detection
- **Auto-upgrade logic**: `recent_phase` automatically becomes `full_project` when all phases complete
- **Intelligent detection**: Finds most recently completed phase for review
- **Smart fallback**: Uses in-progress phase if no phases are complete

### 📁 Enhanced File Naming
- **Scope-based naming**: Output files named by scope type
- **Timestamp preservation**: Unique timestamped filenames
- **Intuitive patterns**: `recent-phase-*.md`, `full-project-*.md`, `phase-X-Y-*.md`, `task-X-Y-*.md`

### 🎛️ Temperature Support
- **Parameter hierarchy**: MCP parameter > Environment variable > Default (0.5)
- **Range validation**: 0.0-2.0 with proper error handling
- **Both tools support**: Context generation and AI review tools

### 🔧 Environment Variables for v0.2.1
```bash
# Required
GEMINI_API_KEY=your_api_key_here        # ✅ Required for AI features

# Optional with smart defaults
GEMINI_MODEL=gemini-2.0-flash           # 🔧 Uses model aliases from config
GEMINI_TEMPERATURE=0.5                  # 🔧 Overridden by MCP parameters
```

## 🧪 Advanced Testing Scenarios for v0.2.1

### 1. Model Alias Testing
- Test with aliases: `"model": "gemini-2.5-pro"`
- Verify resolution: Should use `gemini-2.5-pro-preview-05-06`
- Test invalid aliases: Should fall back to default

### 2. Smart Scope Testing
- Create completed phases in a test task list
- Use `"scope": "recent_phase"` and verify auto-upgrade to `full_project`
- Check output file naming matches detected scope

### 3. Two-Tool Workflow Testing
- Generate context with `generate_code_review_context` (AI disabled)
- Pass output file to `generate_ai_code_review`
- Verify proper chaining and file handling

### 4. Temperature Hierarchy Testing
- Set environment variable: `"GEMINI_TEMPERATURE": "0.8"`
- Override with MCP parameter: `"temperature": 0.2`
- Verify MCP parameter takes precedence

### 5. Performance Testing
- Execute the tool multiple times with different parameters
- Monitor response times and resource usage
- Test with large project directories

### 6. Concurrent Execution
- Open multiple Inspector tabs
- Execute tools simultaneously
- Verify no conflicts or race conditions

### 7. Parameter Validation
- Test edge cases: empty strings, very long paths, special characters
- Verify proper error messages for invalid inputs
- Test optional parameter combinations

## 📚 Learning Opportunities

### Understanding MCP Protocol
- Observe the raw MCP messages in Inspector's debug panel
- See how tools are discovered and schemas are communicated
- Learn about MCP capabilities and protocol features

### Debugging Server Behavior
- Use Inspector's logging to understand server responses
- Identify bottlenecks or error patterns
- Test server stability under various conditions

### Exploring v0.2.1 Features
- Study how model aliases are resolved in practice
- Observe smart scope detection in action
- Learn about parameter hierarchy and fallback logic

### Exploring MCP Ecosystem
- Compare our server with other MCP servers
- Understand common MCP patterns and best practices
- Learn about different transport mechanisms

## 🚀 Next Steps After Testing

Once you've successfully tested with MCP Inspector:

1. **Integration Testing**: Test with Claude Desktop or other MCP clients
2. **Production Usage**: Use in real code review workflows
3. **Feature Exploration**: Test all v0.2.1 features thoroughly
4. **Performance Optimization**: Identify and fix any performance issues
5. **Configuration**: Set up your preferred model aliases in model_config.json

## 💻 Useful Commands for Development

```bash
# Check current version and entry points
uvx task-list-code-review-mcp --help

# Test direct execution (starts MCP server)
uvx task-list-code-review-mcp

# Use specific version
uvx --from task-list-code-review-mcp==0.2.1 task-list-code-review-mcp

# Check available CLI tools (v0.2.1)
uvx --from task-list-code-review-mcp==0.2.1 generate-code-review --help
uvx --from task-list-code-review-mcp==0.2.1 review-with-ai --help

# View package info
pip show task-list-code-review-mcp

# Check MCP Inspector version
npx @modelcontextprotocol/inspector --version
```

## 📖 Resources

- [MCP Specification](https://modelcontextprotocol.io/introduction)
- [MCP Inspector GitHub](https://github.com/modelcontextprotocol/inspector)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Our Project Repository](https://github.com/nicobailon/task-list-code-review-mcp)
- [Model Configuration Guide](./src/model_config.json)

---

## 🎯 Quick Reference for Claude Desktop

To use this server with Claude Desktop, add to your configuration:

```json
{
  "mcpServers": {
    "task-list-code-review-mcp": {
      "command": "uvx",
      "args": ["task-list-code-review-mcp"],
      "env": {
        "GEMINI_API_KEY": "your_actual_gemini_api_key_here"
      }
    }
  }
}
```

---

✨ This guide covers all v0.2.1 features including smart scope detection, model aliases, enhanced file naming, and the new `generate_ai_code_review` tool. The ADHD-friendly format with emojis, clear sections, and copy-paste JSON examples should make testing much easier!