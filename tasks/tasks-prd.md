## Relevant Files

- `src/generate_code_review_context.py` - Core Python script that parses PRD, task lists, git changes and generates review context
- `src/server.py` - MCP server wrapper that exposes the code review context generation tool
- `tests/test_generate_code_review_context.py` - Comprehensive unit tests for all functionality
- `tests/fixtures/sample_prd.md` - Sample PRD file for testing
- `tests/fixtures/sample_task_list.md` - Sample task list file for testing
- `tests/fixtures/sample_output.md` - Expected output template for testing
- `pyproject.toml` - Python project configuration and dependencies
- `requirements.txt` - Python package dependencies
- `README.md` - Project documentation and usage instructions
- `.gitignore` - Git ignore patterns to exclude venv and temporary files

### Notes

- Unit tests should typically be placed alongside the code files they are testing (e.g., `MyComponent.tsx` and `MyComponent.test.tsx` in the same directory).
- Use `npx jest [optional/path/to/test/file]` to run tests. Running without a path executes all tests found by the Jest configuration.

## Tasks

- [x] 1.0 Set up project structure and development environment
  - [x] 1.1 Create project directory structure (src/, tests/, tests/fixtures/)
  - [x] 1.2 Initialize pyproject.toml with project metadata and dependencies
  - [x] 1.3 Create requirements.txt with core dependencies (mcp, pytest, pytest-mock, openai)
  - [x] 1.4 Set up basic README.md with project overview and installation instructions
- [x] 2.0 Implement test-driven development foundation with comprehensive test suites
  - [x] 2.1 Create test fixtures (sample_prd.md, sample_task_list.md, sample_output.md)
  - [x] 2.2 Write tests for task list parser (test_parse_task_list_with_current_phase, test_parse_task_list_all_phases_complete)
  - [x] 2.3 Write tests for PRD parser (test_extract_explicit_summary, test_generate_summary_fallback)
  - [x] 2.4 Write tests for git operations (test_get_changed_files_mock, test_handle_no_git_repository)
  - [x] 2.5 Write tests for file tree generator (test_generate_file_tree_basic, test_file_tree_respects_gitignore)
  - [x] 2.6 Write integration test (test_end_to_end_generation)
- [x] 3.0 Develop core parsing and data extraction functionality
  - [x] 3.1 Implement task list parser with regex patterns for phases and subtasks
  - [x] 3.2 Implement current phase detection logic (first phase with incomplete subtasks)
  - [x] 3.3 Implement PRD parser with summary extraction (explicit sections, LLM fallback, first paragraph fallback)
  - [x] 3.4 Create file discovery functions for prd-*.md and tasks-prd-*.md files
  - [x] 3.5 Implement template formatter with exact markdown structure from PRD specifications
- [x] 4.0 Implement git operations and file tree generation
  - [x] 4.1 Implement git diff parsing to get changed files with status (M/A/D)
  - [x] 4.2 Add file content extraction with line limits (100 lines max per file)
  - [x] 4.3 Implement ASCII file tree generator with gitignore pattern support
  - [x] 4.4 Add error handling for non-git repositories and git command failures
  - [x] 4.5 Handle edge cases (binary files, large files, unicode paths, Windows/Unix paths)
- [x] 5.0 Create MCP server integration and finalize project
  - [x] 5.1 Implement MCP server wrapper (server.py) with tool schema definition
  - [x] 5.2 Add command-line interface with argument parsing (project_path, --phase, --output)
  - [x] 5.3 Implement main orchestration function that ties all components together
  - [x] 5.4 Add comprehensive error handling and logging throughout the application
  - [x] 5.5 Create final integration tests and validate all success criteria are met