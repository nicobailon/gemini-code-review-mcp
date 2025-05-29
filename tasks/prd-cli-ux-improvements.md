# Product Requirements Document: CLI User Experience Improvements

## Executive Summary

Fix the fundamental CLI execution issues in task-list-code-review-mcp through a pragmatic, minimal-complexity approach. Focus on making documented examples work reliably by publishing to PyPI and adding direct CLI entry points, while preserving all existing MCP functionality unchanged.

## Problem Statement

### Root Cause Analysis

The core issue is **not** command structure complexity - it's that documented commands simply don't work:

1. **Package Not Published**: `uvx task-list-code-review-mcp` fails because package isn't on PyPI
2. **Missing CLI Entry Points**: No direct way to execute the CLI tools without complex Python execution
3. **Environment Variable Issues**: API keys don't pass reliably through uvx isolation  
4. **Documentation-Reality Gap**: README shows examples that are impossible to execute
5. **Discovery Problem**: Users can't find a working command pattern without deep uvx knowledge

### User Impact

Users want simple, working commands:
```bash
# What users expect to work (but doesn't):
uvx --from task-list-code-review-mcp generate-code-review /project

# What actually works (but is undiscoverable):
uvx --from . --with google-genai --with python-dotenv python -c "..."
```

### Impact Assessment

- **AI Agents**: Fail to execute tools without complex workarounds, requiring specialized testing guides
- **Human Users**: Frustrated by inconsistent interfaces and verbose command requirements  
- **Project Adoption**: Barrier to entry prevents wider usage of otherwise excellent functionality
- **Maintenance Burden**: Multiple execution paths create debugging and support complexity

## Goals and Success Criteria

### Primary Goals

1. **Make Documented Examples Work**: Ensure all README examples execute successfully
2. **Publish to PyPI**: Enable reliable `uvx` execution from published package
3. **Add Direct CLI Entry Points**: Provide simple, discoverable command access
4. **Fix Environment Variable Handling**: Ensure API keys work reliably with uvx
5. **Preserve MCP Functionality**: Zero changes to existing MCP server behavior

### Success Criteria

- [ ] `uvx --from task-list-code-review-mcp generate-code-review /project` works after PyPI publication  
- [ ] Environment variables (GEMINI_API_KEY) pass through uvx reliably
- [ ] All documentation examples work exactly as written
- [ ] MCP server functionality remains 100% unchanged
- [ ] AI agents can use tools without specialized workarounds
- [ ] Traditional `pip install` option also works seamlessly

## Target Users

### Primary Users
- **AI Development Agents**: Claude Code, Cursor, other AI assistants
- **Software Developers**: Individual developers using CLI for code reviews
- **DevOps Engineers**: Integrating tools into CI/CD pipelines

### Secondary Users
- **Technical Writers**: Creating documentation and tutorials
- **Open Source Contributors**: Contributing to and extending the project

## Functional Requirements

### 1. Direct CLI Entry Points (Minimal Approach)

#### 1.1 Simple Entry Point Addition
**Requirement**: Add dedicated CLI entry points without changing existing architecture

**Implementation**:
```toml
# pyproject.toml - Simple addition to existing entry points
[project.scripts]
task-list-code-review-mcp = "src.server:main"                     # Existing MCP server (unchanged)
generate-code-review = "src.generate_code_review_context:main"     # New direct CLI
review-with-ai = "src.ai_code_review:main"                       # New direct CLI
```

**Result After PyPI Publication**:
```bash
# MCP Server (unchanged)
uvx task-list-code-review-mcp                                    # Starts MCP server
task-list-code-review-mcp                                        # After pip install

# New Direct CLI Tools  
uvx --from task-list-code-review-mcp generate-code-review /project
uvx --from task-list-code-review-mcp review-with-ai context.md

# Traditional Installation
pip install task-list-code-review-mcp
generate-code-review /project
review-with-ai context.md
```

#### 1.2 Preserve Existing Architecture
**Requirement**: No changes to current tool separation or MCP server functionality

**Rationale**: 
- Tools serve different purposes (context generation vs AI review)
- Users often need only one or the other
- Current parameter structure is already well-designed  
- Minimal changes reduce risk and complexity

### 2. UX Improvements (Low Risk)

#### 2.1 Enhanced Help Text
**Requirement**: Improve discoverability through better help and examples

**Implementation**:
```bash
# Enhanced help with working examples
generate-code-review --help
review-with-ai --help

# Each tool shows:
# - Clear usage examples that work after publication
# - Parameter relationships explained
# - Output file naming patterns
# - Common use case scenarios
```

#### 2.2 Better Error Messages
**Requirement**: Provide helpful error messages with suggested corrections

**Focus Areas**:
- Parameter validation errors include working examples
- Environment variable issues provide setup guidance
- File not found errors suggest correct path patterns
- Scope parameter errors explain relationships clearly

### 3. Environment Variable Fixes

#### 3.1 uvx Environment Variable Handling
**Requirement**: Fix API key passing through uvx isolation

**Critical Issues to Resolve**:
- GEMINI_API_KEY not passing through uvx reliably
- Model configuration bugs (ANTHROPIC_MODEL vs GEMINI_MODEL)
- Grounding configuration differences between Gemini models

**Implementation**:
- Investigate and fix environment variable isolation
- Test API key scenarios across uvx versions
- Document reliable patterns for environment variable setup
- Provide fallback mechanisms when environment variables fail

### 4. PyPI Publishing (Core Requirement)

#### 4.1 Publishing Preparation
**Requirement**: Prepare package for reliable PyPI distribution

**Implementation Checklist**:
- [ ] Verify all dependencies properly declared in pyproject.toml
- [ ] Test package build process locally
- [ ] Validate entry points work across platforms  
- [ ] Test installation from PyPI test server
- [ ] Confirm uvx compatibility with published package
- [ ] Test environment variable handling in published version

#### 4.2 Release Process
**Requirement**: Establish reliable release workflow

**Implementation**:
- Test on PyPI test server first
- Validate all documented examples work with published package
- Cross-platform testing (Windows, macOS, Linux)
- Automated testing of both uvx and pip installation methods

### 5. Documentation Updates

#### 5.1 Update Examples to Match Reality
**Requirement**: Replace broken examples with working commands

**Key Changes**:
```markdown
# Replace current broken examples:
uvx task-list-code-review-mcp /project  # Doesn't work - package not published

# With working examples after publication:
uvx --from task-list-code-review-mcp generate-code-review /project
uvx --from task-list-code-review-mcp review-with-ai context.md
```

#### 5.2 Clear Installation Instructions
**Requirement**: Provide simple, reliable installation guidance

**Structure**:
1. **Quick Start**: Working uvx examples (primary method)
2. **Installation Options**: uvx vs pip with clear guidance
3. **Common Usage Patterns**: Real examples for typical workflows
4. **Environment Setup**: API key configuration that actually works
5. **MCP Integration**: Keep existing documentation (unchanged)
6. **Troubleshooting**: Target actual user issues

## Technical Requirements

### 1. Simple Entry Point Addition

#### 1.1 pyproject.toml Updates (Minimal Change)
**Current**:
```toml
[project.scripts]
task-list-code-review-mcp = "src.server:main"
```

**Target** (add two lines):
```toml
[project.scripts]
task-list-code-review-mcp = "src.server:main"                     # Unchanged - MCP server
generate-code-review = "src.generate_code_review_context:main"     # New CLI entry
review-with-ai = "src.ai_code_review:main"                       # New CLI entry
```

#### 1.2 No New Architecture Required
**Rationale**: Existing tools already have proper main() functions and argument parsing. Adding entry points directly to existing modules requires zero architectural changes and minimal risk.

### 2. Environment Variable Fixes

#### 2.1 uvx Environment Variable Investigation
**Requirement**: Fix API key passing through uvx

**Implementation**:
- Investigate root cause of GEMINI_API_KEY isolation in uvx
- Test environment variable patterns across uvx versions
- Fix any bugs in environment variable detection code
- Provide clear documentation for reliable API key setup

#### 2.2 Dependency Validation
**Requirement**: Ensure package dependencies work with uvx

**Implementation**:
- Verify all dependencies properly declared in pyproject.toml
- Test uvx execution with optional dependencies (google-genai)
- Validate cross-platform dependency resolution

### 3. MCP Server Preservation (Critical)

#### 3.1 Zero Changes to MCP Functionality
**Requirement**: MCP server must remain 100% identical

**Implementation**:
- No changes to src/server.py
- No changes to MCP tool definitions
- No changes to MCP protocol responses
- Existing `task-list-code-review-mcp` command continues starting MCP server

#### 3.2 Backward Compatibility Testing
**Requirement**: Validate no regressions in MCP functionality

**Testing Requirements**:
- All existing MCP tool calls work identically
- Claude Desktop configuration unchanged
- Claude Code CLI integration unaffected
- MCP protocol responses identical
- Performance characteristics unchanged

## Design Requirements

### 1. Simple Command Naming

#### 1.1 Direct, Discoverable Names
**Requirement**: Command names that clearly indicate function

**Selected Names**:
- `generate-code-review` - Generate code review context (clear purpose)
- `review-with-ai` - Generate AI-powered review (clear purpose)
- `task-list-code-review-mcp` - MCP server (unchanged)

**Rationale**: Names describe what the tool does, making discovery intuitive.

### 2. Minimal UX Improvements

#### 2.1 Enhanced Help Text
**Requirement**: Help text includes working examples

**Implementation**:
```bash
generate-code-review --help  # Shows working uvx examples
review-with-ai --help        # Shows working uvx examples
```

#### 2.2 Better Error Messages
**Requirement**: Error messages include working command examples

**Implementation**:
- Parameter validation errors show correct usage patterns
- Environment variable errors provide setup guidance
- File path errors suggest correct project structure

## Implementation Strategy (Simplified)

### Phase 1: Minimal Viable Fix (Week 1)
**Priority**: Make documented examples work

1. **Add CLI Entry Points** (2 lines in pyproject.toml)
   - Add `generate-code-review` entry point
   - Add `review-with-ai` entry point
   - Test local installation

2. **Fix Environment Variables**
   - Investigate GEMINI_API_KEY isolation in uvx
   - Fix any bugs in environment variable detection
   - Test API key scenarios

3. **PyPI Test Publishing**
   - Build and test package locally
   - Publish to PyPI test server
   - Test installation and execution from test PyPI

### Phase 2: Documentation and Polish (Week 1)
**Priority**: Update documentation with working examples

1. **Update README Examples**
   - Replace broken examples with working commands
   - Test all documented examples work with published package
   - Add clear installation instructions

2. **Enhance Help Text**
   - Add working examples to help output
   - Improve error messages with suggestions
   - Document environment variable setup

3. **MCP Compatibility Validation**
   - Test MCP server functionality unchanged
   - Validate Claude Desktop integration
   - Verify Claude Code CLI integration

### Phase 3: Production Release (Week 1)
**Priority**: Reliable production deployment

1. **Production Publishing**
   - Publish to production PyPI
   - Validate all examples work with production package
   - Cross-platform testing (Windows, macOS, Linux)

2. **Final Validation**
   - Test both uvx and pip installation methods
   - Verify MCP server functionality preserved
   - Confirm AI agent compatibility

**Total Time**: 2-3 weeks instead of 4, focusing on the core issue.

## Success Metrics (Simplified)

### Core Success Criteria
- **Working Examples**: 100% of documented examples work as written after PyPI publication
- **uvx Compatibility**: `uvx --from task-list-code-review-mcp generate-code-review /project` works reliably
- **MCP Preservation**: Zero regressions in MCP server functionality
- **Environment Variables**: GEMINI_API_KEY works consistently with uvx

### User Experience Metrics
- **Reduced Support Burden**: Fewer CLI-related issues and questions
- **AI Agent Success**: AI agents execute tools without specialized workarounds
- **Installation Success**: Both uvx and pip installation methods work reliably

## Risk Mitigation (Minimal Approach)

### Technical Risks (Reduced)
- **MCP Server Breaking**: **CRITICAL** - Zero changes to MCP functionality reduces this risk significantly
- **PyPI Publishing**: Test on PyPI test server before production
- **Environment Variables**: Isolated fix to uvx compatibility issues
- **Cross-Platform**: Test on Windows, macOS, Linux

### Implementation Risks (Low)
- **Minimal Code Changes**: Adding entry points is low-risk
- **No Architecture Changes**: Existing tools work as-is
- **Backward Compatibility**: MCP server unchanged, direct execution still works

### Mitigation Strategy
- **Phase 1 Validation**: Test everything works before proceeding
- **Incremental Approach**: Each phase validates before next
- **Rollback Plan**: Can revert entry point changes if issues arise

## Future Considerations

### Potential Future Enhancements (Only if needed)
Based on user feedback after the minimal fix:

- **Configuration Files**: If users request parameter persistence
- **Shell Completion**: If command discovery becomes an issue
- **Unified Interface**: If users specifically request subcommand structure
- **Additional CLI Tools**: If workflow gaps are identified

### Philosophy
Implement the minimal fix first. Add complexity only if users actually request it and the benefit clearly outweighs the maintenance cost.

## Conclusion

This PRD takes a pragmatic approach to fixing CLI UX issues by addressing the root cause: documented examples don't work because the package isn't published and entry points don't exist.

**Core Solution**: 
- Add 2 lines to pyproject.toml for direct CLI entry points
- Fix environment variable handling in uvx
- Publish to PyPI
- Update documentation with working examples

**Result**: Users get exactly what they expect - working commands that match the documentation - with minimal complexity and risk.