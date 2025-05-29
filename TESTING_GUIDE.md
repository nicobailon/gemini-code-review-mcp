# 🧪 Testing Guide: Task List Code Review MCP Server v0.2.1

An ADHD-friendly guide for testing the code review functionality with clear sections, copy-paste commands, and organized complexity levels.

## 🚀 Quick Start (Copy & Paste Ready)

```bash
# 1. Test context generation
generate-code-review /path/to/your/project

# 2. Test AI review
review-with-ai tasks/code-review-context-*.md

# 3. Test MCP server
task-list-code-review-mcp
```

## 📋 Prerequisites Checklist

- [ ] **Python 3.8+** installed
- [ ] **Git repository** with committed changes
- [ ] **GEMINI_API_KEY** environment variable set
- [ ] **Tasks directory** with markdown files present
- [ ] **uvx** installed for isolated execution

## 🎯 Testing Levels

### 🟢 Basic Testing (Start Here)

#### Test 1: Context Generation Only
```bash
# Generate context without AI review
generate-code-review /path/to/project --context-only

# Expected output: tasks/code-review-context-{scope}-{timestamp}.md
```

#### Test 2: Scope Selection
```bash
# Recent phase (default - smart detection)
generate-code-review /path/to/project --scope recent_phase

# Full project analysis
generate-code-review /path/to/project --scope full_project

# Specific phase targeting
generate-code-review /path/to/project --scope specific_phase --phase-number 2.0

# Specific task targeting  
generate-code-review /path/to/project --scope specific_task --task-number 1.2
```

#### Test 3: Basic AI Review
```bash
# Generate context then review
generate-code-review /path/to/project
review-with-ai tasks/code-review-context-*.md
```

### 🟡 Intermediate Testing

#### Test 4: Model Configuration
```bash
# Test different models (cost-efficient → advanced)
review-with-ai context.md --model gemini-2.0-flash      # Default: fast, cost-efficient
review-with-ai context.md --model gemini-2.5-flash     # Advanced features
review-with-ai context.md --model gemini-2.5-pro       # Complex reasoning

# Test model aliases (resolves to preview versions)
review-with-ai context.md --model gemini-2.5-pro       # → gemini-2.5-pro-preview-05-06
```

#### Test 5: Temperature Control
```bash
# Environment variable override
GEMINI_TEMPERATURE=0.2 generate-code-review /path/to/project

# CLI parameter (overrides environment)
review-with-ai context.md --temperature 0.8

# Valid range: 0.0-2.0 (default: 0.5)
```

#### Test 6: File Size Limits
```bash
# Test with large files (default: 10MB limit)
MAX_FILE_SIZE_MB=5 generate-code-review /path/to/project

# Check for file size warnings in output
```

### 🔴 Advanced Testing

#### Test 7: Smart Scope Detection
```bash
# When recent_phase auto-expands to full_project (all phases complete)
generate-code-review /path/to/project --scope recent_phase

# Verify: Should detect completion and expand scope automatically
```

#### Test 8: MCP Server Integration
```bash
# Start MCP server
task-list-code-review-mcp

# Test server endpoints (in another terminal)
# Note: Requires MCP client for full testing
```

#### Test 9: Cross-Platform Testing
```bash
# Test uvx isolation (recommended)
uvx --from . --with google-genai --with python-dotenv generate-code-review /path/to/project

# Test direct execution
python src/generate_code_review_context.py /path/to/project

# Test pip installation (after building)
pip install dist/task_list_code_review_mcp-*.whl
```

## 🔧 Advanced Configuration

### Model Configuration (model_config.json)
```json
{
  "model_aliases": {
    "gemini-2.5-pro": "gemini-2.5-pro-preview-05-06",
    "gemini-2.5-flash": "gemini-2.5-flash-preview-05-20"
  },
  "model_capabilities": {
    "url_context_supported": ["gemini-2.5-pro-preview-05-06", "gemini-2.0-flash"],
    "thinking_mode_supported": ["gemini-2.5-pro-preview-05-06"]
  },
  "defaults": {
    "model": "gemini-2.0-flash",
    "summary_model": "gemini-2.0-flash-lite"
  }
}
```

### Environment Variables
```bash
export GEMINI_API_KEY="your-api-key"
export GEMINI_MODEL="gemini-2.5-pro"          # Override default model
export GEMINI_SUMMARY_MODEL="custom-model"     # Override summary model  
export GEMINI_TEMPERATURE="0.7"               # Override default temperature
export MAX_FILE_SIZE_MB="20"                  # Override file size limit (default: 10MB)
```

## 🐛 Troubleshooting

### ❌ Common Issues & Solutions

#### Issue: "No executable found"
```bash
# ❌ Wrong - these don't exist
uvx task-list-code-review-mcp /path/to/project
uvx generate_code_review_context /path/to/project

# ✅ Correct - use proper entry points
generate-code-review /path/to/project
review-with-ai tasks/context-file.md
task-list-code-review-mcp
```

#### Issue: Environment Variables Not Working
```bash
# ❌ Wrong - env vars may not pass through uvx
GEMINI_API_KEY="key" uvx command

# ✅ Correct - use .env file or system environment
echo "GEMINI_API_KEY=your-key" > .env
generate-code-review /path/to/project
```

#### Issue: Model Not Found
```bash
# Check available models and aliases
review-with-ai context.md --model gemini-2.0-flash --verbose

# Use model aliases for latest versions
review-with-ai context.md --model gemini-2.5-pro  # Auto-resolves to preview version
```

#### Issue: File Too Large Errors
```bash
# Increase file size limit
MAX_FILE_SIZE_MB=50 generate-code-review /path/to/project

# Or exclude large files from git changes
echo "large-file.dat" >> .gitignore
```

### 🔍 Debug Mode
```bash
# Enable verbose logging
generate-code-review /path/to/project --verbose
review-with-ai context.md --verbose

# Check what files are being processed
generate-code-review /path/to/project --context-only --verbose
```

## 🧪 Running Tests

### Unit Tests
```bash
# Install test dependencies
pip install pytest pytest-mock pytest-asyncio

# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_model_configuration.py -v      # Model config tests
python -m pytest tests/test_scope_based_reviews.py -v      # Scope functionality
python -m pytest tests/test_cli_enhancements.py -v         # CLI parameter tests
```

### Integration Tests
```bash
# Test with real project
mkdir test-project && cd test-project
git init
mkdir tasks
echo "# Test Tasks\n- [x] 1.0 Phase One\n- [ ] 2.0 Phase Two" > tasks/tasks-test.md
echo "print('hello')" > test.py
git add . && git commit -m "test"

# Test the full pipeline
generate-code-review . --scope full_project
review-with-ai tasks/code-review-context-*.md
```

## ✅ Success Indicators

### Context Generation Success
```
INFO:generate_code_review_context:Using model: gemini-2.0-flash
INFO:generate_code_review_context:Smart scope detection: recent_phase → full_project
INFO:generate_code_review_context:File size check: 15 files, largest 2.3MB
INFO:generate_code_review_context:Context saved: tasks/code-review-context-full-project-20250529-120514.md
```

### AI Review Success
```
INFO:ai_code_review:Loading context from: tasks/code-review-context-full-project-20250529-120514.md
INFO:ai_code_review:Using model: gemini-2.5-pro-preview-05-06 (resolved from gemini-2.5-pro)
INFO:ai_code_review:URL context: enabled, Google Search: enabled, Thinking mode: enabled
INFO:ai_code_review:Review saved: code-review-comprehensive-feedback-20250529-120515.md
```

### File Outputs Expected
1. **Context file**: `tasks/code-review-context-{scope}-{timestamp}.md`
2. **AI review file**: `code-review-comprehensive-feedback-{timestamp}.md`
3. **Log confirmation**: All features enabled based on model capabilities

## 📚 Help & Documentation

### Get Help
```bash
# Command help
generate-code-review --help
review-with-ai --help
task-list-code-review-mcp --help

# Parameter examples
generate-code-review --help | grep -A5 "scope"
review-with-ai --help | grep -A3 "model"
```

### Usage Examples in Help
```bash
# Examples from help text
generate-code-review /project/path --scope full_project
generate-code-review /project/path --scope specific_phase --phase-number 2.0
review-with-ai context.md --output custom-review.md --model gemini-2.5-flash
```

## 🔄 Migration Notes

### From v0.1.x to v0.2.1

#### Updated Commands
- ✅ `generate-code-review` (new entry point)
- ✅ `review-with-ai` (new entry point)  
- ❌ ~~`generate_code_review_context`~~ (removed)

#### New Features
- 🆕 Smart scope detection (recent_phase → full_project)
- 🆕 Model aliases and JSON configuration
- 🆕 File size limits (MAX_FILE_SIZE_MB)
- 🆕 Enhanced CLI with --context-only flag
- 🆕 Temperature control via CLI and environment

#### Backward Compatibility
- Legacy `--no-gemini` flag → use `--context-only` instead
- Legacy `--phase` parameter → use `--scope specific_phase --phase-number`

---

## 📞 Need Help?

- 🐛 **Bug reports**: Check test outputs and include full error messages
- 💡 **Feature requests**: Test with `--verbose` flag first
- 📖 **Documentation**: All commands have `--help` with examples
- 🧪 **Testing**: Run `python -m pytest tests/ -v` for comprehensive validation

**Remember**: Start with basic testing (🟢) before moving to advanced features (🔴)!