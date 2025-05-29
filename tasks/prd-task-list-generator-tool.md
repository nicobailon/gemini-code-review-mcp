# PRD: Task List Generator Tool for MCP Server

**Version**: 1.0  
**Date**: 2025-05-28  
**Status**: Draft  

## Executive Summary

Add a new MCP tool to the existing code review context generator server that automatically generates detailed task lists from Product Requirements Documents (PRDs) following established rules and formatting standards.

## Problem Statement

### Current Issues
- **Manual Task Planning**: Developers must manually create task lists from PRDs, leading to inconsistent structure and missed requirements
- **Time-Intensive Process**: Breaking down PRDs into actionable tasks requires significant planning time
- **Inconsistent Format**: Task lists lack standardized structure across projects
- **Missing Implementation Guidance**: Junior developers need detailed, step-by-step task breakdowns to implement features effectively

### Target Users Affected
- Development teams using PRD-driven development workflows
- Junior developers who need detailed implementation guidance
- Project managers tracking feature implementation progress
- AI assistants helping with development planning

## Goals

### Primary Goals
1. **Automate Task Generation**: Convert PRDs into structured, actionable task lists automatically
2. **Standardize Task Format**: Ensure all generated task lists follow consistent markdown structure
3. **Enable Phased Implementation**: Support 2-phase generation (parent tasks → confirmation → sub-tasks)
4. **Integrate with Existing Workflow**: Seamlessly add to existing MCP server infrastructure

### Secondary Goals
1. **Support Multiple PRD Sources**: Handle both local file paths and URL references
2. **Maintain Rule Compliance**: Strictly follow rules defined in `rules/generate-tasks-rules.md`
3. **Enable File Prediction**: Identify relevant files that will need creation or modification
4. **Provide Implementation Context**: Include notes and guidance for junior developers

## Solution Design

### Tool Architecture

#### New MCP Tool: `generate_task_list_from_prd`

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "prd_path": {
      "type": "string",
      "description": "Absolute path to PRD file or URL to PRD content"
    },
    "project_root": {
      "type": "string", 
      "description": "Absolute path to project root for file path prediction"
    },
    "phase": {
      "type": "string",
      "enum": ["parent_tasks", "full_tasks"],
      "description": "Generation phase: 'parent_tasks' for initial high-level tasks, 'full_tasks' for complete breakdown",
      "default": "parent_tasks"
    },
    "output_path": {
      "type": "string",
      "description": "Custom output file path. If not provided, uses default: /tasks/tasks-[prd-name].md"
    }
  },
  "required": ["prd_path"]
}
```

#### Implementation Strategy

**Phase 1 Process (Parent Tasks):**
1. Read and parse PRD content (local file or URL)
2. Extract functional requirements and user stories
3. Generate 5-7 high-level parent tasks
4. Create initial task list file with parent tasks only
5. Return parent tasks to user with confirmation request

**Phase 2 Process (Full Tasks):**
1. Read existing task list file with parent tasks
2. Break down each parent task into detailed sub-tasks
3. Identify relevant files that need creation/modification
4. Generate complete task list with sub-tasks and file predictions
5. Save final formatted task list

#### File Structure Integration

**New Module**: `src/generate_task_list.py`
- `parse_prd(prd_path: str) -> Dict[str, Any]`
- `generate_parent_tasks(prd_data: Dict) -> List[str]`
- `generate_sub_tasks(parent_tasks: List, prd_data: Dict) -> Dict`
- `predict_relevant_files(tasks: Dict, project_root: str) -> List[str]`
- `format_task_list(tasks: Dict, files: List, prd_name: str) -> str`
- `main(prd_path: str, phase: str, project_root: str, output_path: str) -> str`

**Updated**: `src/server.py`
- Add new tool definition to `handle_list_tools()`
- Add new tool handler to `handle_call_tool()`

### Output Format Compliance

Generated task lists must follow exact structure from `rules/generate-tasks-rules.md`:

```markdown
## Relevant Files

- `path/to/file.py` - Description of file purpose
- `path/to/file.test.py` - Unit tests for file.py

### Notes

- Implementation notes for junior developers
- Testing instructions and commands

## Tasks

- [ ] 1.0 Parent Task Title
  - [ ] 1.1 Sub-task description
  - [ ] 1.2 Sub-task description
- [ ] 2.0 Parent Task Title
  - [ ] 2.1 Sub-task description
```

### User Experience Flow

**Phase 1 - Initial Generation:**
```bash
# User calls MCP tool
mcp-tool generate_task_list_from_prd \
  --prd_path "/path/to/prd-feature.md" \
  --project_root "/path/to/project" \
  --phase "parent_tasks"

# Tool responds with:
# "Generated high-level tasks based on PRD. Ready to generate sub-tasks? 
#  Call again with phase='full_tasks' to proceed."
```

**Phase 2 - Complete Generation:**
```bash
# User calls again with full_tasks
mcp-tool generate_task_list_from_prd \
  --prd_path "/path/to/prd-feature.md" \
  --project_root "/path/to/project" \
  --phase "full_tasks"

# Tool generates complete task list with sub-tasks
```

### File Naming Convention

**Output Files**: `/tasks/tasks-[prd-file-name].md`
- Input: `prd-user-profile-editing.md`
- Output: `tasks-prd-user-profile-editing.md`

## Technical Requirements

### Dependencies
- **Existing**: All current MCP server dependencies
- **New**: `requests` (for URL PRD support) - optional dependency
- **File I/O**: Standard Python libraries for markdown parsing

### Rule Compliance Engine

**Rules Source**: `rules/generate-tasks-rules.md`
- Must read and parse rules dynamically
- Generate tasks following exact format specifications
- Implement 2-phase confirmation workflow
- Target junior developer audience in task descriptions

### Error Handling
- **Invalid PRD Path**: Clear error message with path validation
- **Missing Project Root**: Default to PRD file directory
- **Parse Failures**: Graceful handling with informative errors
- **File Write Permissions**: Handle permission errors gracefully

## Implementation Plan

### Phase 1: Core Module Development (Week 1)
- [ ] Create `src/generate_task_list.py` with core functions
- [ ] Implement PRD parsing for local files
- [ ] Build parent task generation logic
- [ ] Create task list formatting functions
- [ ] Add comprehensive unit tests

### Phase 2: MCP Integration (Week 1-2)
- [ ] Add new tool definition to `src/server.py`
- [ ] Implement tool handler with input validation
- [ ] Test MCP tool registration and execution
- [ ] Validate output format compliance
- [ ] Test 2-phase workflow

### Phase 3: Enhanced Features (Week 2)
- [ ] Add URL PRD support for remote documents
- [ ] Implement intelligent file path prediction
- [ ] Add project structure analysis for relevant files
- [ ] Enhance error handling and user feedback

### Phase 4: Testing & Documentation (Week 2-3)
- [ ] Test with existing PRD files in `/tasks/`
- [ ] Validate rule compliance with `rules/generate-tasks-rules.md`
- [ ] Create comprehensive test cases
- [ ] Update server documentation
- [ ] Test integration with Claude Desktop MCP configuration

## Success Metrics

### Quantitative Metrics
- **Task Generation Time**: < 30 seconds for typical PRD
- **Rule Compliance**: 100% adherence to format specifications
- **File Prediction Accuracy**: >80% relevant file identification
- **Error Rate**: <5% tool execution failures

### Qualitative Metrics
- **Developer Feedback**: Positive feedback on task clarity and completeness
- **Junior Developer Usability**: Task lists provide sufficient implementation guidance
- **Format Consistency**: All generated task lists follow identical structure
- **Integration Seamlessness**: Tool integrates smoothly with existing MCP workflow

## Risk Assessment

### Technical Risks
- **PRD Format Variations**: Mitigation via flexible parsing with fallback strategies
- **Rule Interpretation**: Mitigation via comprehensive rule parsing and validation
- **File Path Prediction**: Mitigation via conservative prediction with manual override option
- **MCP Integration**: Mitigation via thorough testing with existing server infrastructure

### User Experience Risks
- **2-Phase Confusion**: Mitigation via clear confirmation messages and workflow guidance
- **Over-Complex Tasks**: Mitigation via junior developer review and simplification
- **Missing Context**: Mitigation via comprehensive PRD analysis and context preservation

## Alternative Approaches Considered

### Single-Phase Generation
**Pros**: Simpler user experience, faster completion
**Cons**: Violates established rules, reduces user control over high-level planning
**Decision**: Rejected - rules explicitly require 2-phase confirmation workflow

### Separate MCP Server
**Pros**: Clear separation of concerns, independent deployment
**Cons**: Additional server management, configuration complexity
**Decision**: Rejected - current server has capacity and related functionality

### AI-Enhanced Generation
**Pros**: More intelligent task breakdown, better file prediction
**Cons**: Additional API dependencies, cost, complexity
**Decision**: Deferred - implement basic version first, enhance later

## Dependencies & Prerequisites

### Development Environment
- Existing MCP server codebase functional
- Python 3.8+ with all current dependencies
- Access to `rules/generate-tasks-rules.md` for rule compliance
- Test PRD files in `/tasks/` directory for validation

### External Dependencies
- Optional: `requests` library for URL PRD support
- MCP protocol infrastructure (already available)
- File system access for reading PRDs and writing task lists

## Appendix

### Example PRD Input
```markdown
# PRD: User Profile Editing

## Functional Requirements
1. Users can edit profile information
2. Changes are validated before saving
3. Profile photos can be uploaded
```

### Example Generated Output (Phase 1)
```markdown
## Tasks

- [ ] 1.0 Create user profile editing interface
- [ ] 2.0 Implement profile data validation
- [ ] 3.0 Add profile photo upload functionality
- [ ] 4.0 Build profile update API endpoints
- [ ] 5.0 Add comprehensive testing coverage
```

### Example Generated Output (Phase 2)
```markdown
## Relevant Files

- `src/components/ProfileEditor.tsx` - Main profile editing form component
- `src/components/ProfileEditor.test.tsx` - Unit tests for ProfileEditor
- `src/api/profile.ts` - Profile API endpoints and validation
- `src/api/profile.test.ts` - API endpoint tests

### Notes

- Use existing form validation library for consistency
- Follow component naming conventions in codebase
- Test file uploads with various image formats

## Tasks

- [ ] 1.0 Create user profile editing interface
  - [ ] 1.1 Design ProfileEditor component with form fields
  - [ ] 1.2 Implement controlled form state management
  - [ ] 1.3 Add form styling consistent with design system
- [ ] 2.0 Implement profile data validation
  - [ ] 2.1 Add client-side field validation
  - [ ] 2.2 Implement server-side validation rules
  - [ ] 2.3 Display validation errors to user
- [ ] 3.0 Add profile photo upload functionality
  - [ ] 3.1 Create photo upload component with drag-and-drop
  - [ ] 3.2 Implement image preview before upload
  - [ ] 3.3 Add image compression and format validation
```

### Configuration Integration

**Claude Desktop MCP Configuration:**
```json
{
  "mcpServers": {
    "code-review": {
      "command": "uvx",
      "args": ["task-list-phase-reviewer"],
      "env": {
        "GEMINI_API_KEY": "your-key-here"
      }
    }
  }
}
```

**Tool Usage:**
- Tool Name: `generate_task_list_from_prd`
- Phase 1: Generate parent tasks and request confirmation
- Phase 2: Generate complete task breakdown with sub-tasks
- Output: Formatted markdown task list in `/tasks/` directory