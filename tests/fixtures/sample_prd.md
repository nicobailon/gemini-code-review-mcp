# Code Review Context Generator PRD

## Summary
This tool automates the generation of code review context by parsing project documentation and git changes. It creates structured templates for AI-assisted code reviews.

## Goals
- Parse PRD and task lists automatically
- Generate comprehensive review templates with file trees and git diffs
- Integrate seamlessly with MCP for AI assistant workflows
- Support flexible configuration and error handling

## Functional Requirements

### Core Parsing Features
1. **PRD Analysis**: Extract summaries from markdown files using pattern matching
2. **Task List Processing**: Parse task completion status and identify current phase
3. **Git Integration**: Detect changed files and extract relevant content
4. **File Tree Generation**: Create ASCII representation of project structure

### Output Requirements
1. **Structured Template**: Generate markdown with specific formatting requirements
2. **Context Information**: Include project path, phase details, and file changes
3. **User Instructions**: Provide clear guidance for AI code review process

## Technical Specifications

- **Language**: Python 3.8+
- **Dependencies**: MCP, OpenAI (optional), pytest
- **Architecture**: Modular design with separate parsing components
- **Error Handling**: Graceful degradation for missing files or git issues