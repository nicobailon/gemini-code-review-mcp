## Relevant Files

- `src/git_branch_comparison.py` - Core module for git branch comparison functionality
- `src/git_branch_comparison.test.py` - Unit tests for git branch comparison
- `src/github_pr_integration.py` - GitHub Pull Request API integration module  
- `src/github_pr_integration.test.py` - Unit tests for GitHub PR integration
- `src/generate_code_review_context.py` - Extend existing module with new comparison modes
- `tests/test_branch_comparison_behavior.py` - Behavior tests for branch comparison features
- `tests/test_github_pr_behavior.py` - Behavior tests for GitHub PR integration
- `src/server.py` - Add new MCP tools for branch comparison and PR review
- `tests/test_mcp_branch_tools.py` - Tests for new MCP server tools

### Notes

- Unit tests should be placed alongside the code files they are testing
- Use `npx jest [optional/path/to/test/file]` to run tests. Running without a path executes all tests found by the Jest configuration.
- Follow TDD approach: write tests first, then implement functionality
- New functionality should integrate seamlessly with existing codebase patterns

## Tasks

- [x] 1.0 Core Git Branch Comparison Infrastructure
  - [x] 1.1 Create git_branch_comparison.py module with branch detection and validation functions
  - [x] 1.2 Implement get_branch_diff() function to compare two branches using git diff
  - [x] 1.3 Add detect_primary_branch() function to auto-detect main vs master
  - [x] 1.4 Create parse_git_diff_output() function to structure diff data for templates
  - [x] 1.5 Write comprehensive tests for all git operations and edge cases
  - [x] 1.6 Add error handling for invalid repositories, missing branches, and git failures

- [ ] 2.0 GitHub Pull Request API Integration
  - [ ] 2.1 Create github_pr_integration.py module with URL parsing and validation
  - [ ] 2.2 Implement parse_github_pr_url() function to extract owner, repo, and PR number
  - [ ] 2.3 Add fetch_pr_data() function using GitHub REST API to get PR information
  - [ ] 2.4 Create get_pr_file_changes() function to retrieve PR diff data via API
  - [ ] 2.5 Implement GitHub authentication handling with token support
  - [ ] 2.6 Add rate limiting, timeout handling, and network error recovery
  - [ ] 2.7 Write comprehensive tests including API mocking and error scenarios

- [ ] 3.0 CLI Interface Enhancement  
  - [ ] 3.1 Add new CLI parameters: --compare-branch, --target-branch, --github-pr-url
  - [ ] 3.2 Implement parameter validation and mode detection logic
  - [ ] 3.3 Update help text and usage examples for new comparison modes
  - [ ] 3.4 Add user feedback for branch comparison operations (commits ahead/behind, file stats)
  - [ ] 3.5 Ensure backward compatibility with all existing CLI parameters
  - [ ] 3.6 Write behavior tests for new CLI parameters and user feedback

- [ ] 4.0 MCP Server Tool Integration
  - [ ] 4.1 Add generate_branch_comparison_review MCP tool to server.py
  - [ ] 4.2 Add generate_pr_review MCP tool with GitHub URL parameter
  - [ ] 4.3 Implement parameter validation and error handling for new MCP tools
  - [ ] 4.4 Ensure consistent response format with existing MCP tools (user feedback, file paths)
  - [ ] 4.5 Add comprehensive behavior tests for new MCP tools
  - [ ] 4.6 Update FastMCP tool registration and documentation

- [ ] 5.0 Template and Output Format Updates
  - [ ] 5.1 Extend format_review_template() to handle branch comparison metadata
  - [ ] 5.2 Add new template sections for commit information, branch statistics, and PR metadata
  - [ ] 5.3 Update user instructions section to reflect comparison context vs working directory
  - [ ] 5.4 Ensure file naming reflects comparison mode (e.g., code-review-branch-comparison-*)
  - [ ] 5.5 Add tests for template formatting with branch comparison data
  - [ ] 5.6 Update README documentation with new features and usage examples