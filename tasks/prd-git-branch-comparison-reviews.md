# PRD: Git Branch Comparison Code Reviews

## Summary

Extend the existing task-list-code-review-mcp tool to support code reviews comparing feature branches against main/master branches, both for local branches and GitHub pull requests. This enables developers to review their feature branch changes in context rather than just reviewing the current working directory state.

## Goals

1. **Local Branch Comparison**: Generate code review context comparing a local feature branch against main/master branch
2. **GitHub PR Integration**: Generate code review context from a GitHub PR URL by comparing the PR branch against the target branch
3. **Maintain Existing Functionality**: Preserve all current task-list-based review capabilities
4. **Consistent User Experience**: Provide the same quality feedback and output format as existing reviews

## User Stories

### As a developer with committed local changes
**I want** to review my feature branch against main before pushing
**So that** I can ensure my changes are ready for pull request submission

### As a developer reviewing a GitHub PR
**I want** to generate a comprehensive code review from a PR URL
**So that** I can analyze the changes with AI assistance and provide thorough feedback

### As a team lead reviewing multiple PRs
**I want** to quickly generate standardized review contexts for GitHub PRs
**So that** I can maintain consistent review quality across all pull requests

## Functional Requirements

### FR1: Local Branch Comparison
- **Input**: Local git repository with committed changes on a feature branch
- **Process**: Compare current branch against main/master branch using git diff
- **Output**: Standard code review context file showing branch comparison
- **Validation**: Ensure target branch (main/master) exists and is up-to-date

### FR2: GitHub PR URL Processing  
- **Input**: GitHub PR URL (e.g., `https://github.com/owner/repo/pull/123`)
- **Process**: Extract repository info and PR number, fetch PR data via GitHub API
- **Output**: Code review context comparing PR branch against target branch
- **Authentication**: Support GitHub token for private repositories

### FR3: Branch Detection and Validation
- **Auto-detect**: Automatically identify main branch (main vs master)
- **Validation**: Verify branches exist and have commits
- **Error Handling**: Provide clear error messages for invalid branches/PRs

### FR4: Enhanced CLI Interface
- **New Parameters**: `--compare-branch`, `--github-pr-url`, `--target-branch`
- **Mode Detection**: Auto-detect comparison mode based on parameters provided
- **Backward Compatibility**: Maintain all existing CLI parameters and behavior

### FR5: MCP Server Integration
- **New MCP Tools**: Add `generate_branch_comparison_review` and `generate_pr_review` tools
- **Consistent Interface**: Same parameter validation and response format as existing tools
- **Error Handling**: Proper error responses for invalid repositories or network issues

## Technical Requirements

### TR1: Git Integration
- Use `git diff` commands to compare branches
- Support both local and remote branch comparisons
- Handle large diffs with proper truncation
- Detect renamed/moved files appropriately

### TR2: GitHub API Integration
- Use GitHub REST API v4 for PR data retrieval
- Parse PR URLs to extract owner, repository, and PR number
- Fetch PR file changes, commit information, and metadata
- Handle API rate limiting and authentication

### TR3: Network Resilience
- Graceful handling of network failures
- Timeout configuration for API calls
- Fallback strategies for API unavailability
- Clear error messages for connectivity issues

### TR4: Security Considerations
- Secure handling of GitHub tokens
- No logging of sensitive information
- Validation of user-provided URLs
- Protection against malicious repository data

## User Interface Requirements

### UIR1: CLI Parameters
```bash
# Local branch comparison
generate-code-review . --compare-branch feature/auth-system --target-branch main

# GitHub PR review
generate-code-review --github-pr-url https://github.com/owner/repo/pull/123

# Combined with existing features
generate-code-review . --compare-branch feature/auth --scope full_project --temperature 0.3
```

### UIR2: User Feedback
- Show branch comparison summary (commits ahead/behind)
- Display file change statistics (added, modified, deleted)
- Progress indicators for GitHub API calls
- Clear indication of comparison mode being used

### UIR3: Output Format
- Maintain existing review context template structure
- Add new sections for branch comparison metadata
- Include commit messages and author information
- Show PR description and metadata when applicable

## Success Criteria

### SC1: Feature Completeness
- [x] Local branch comparison generates accurate diff-based reviews
- [x] GitHub PR URL processing works with public and private repositories
- [x] All existing functionality remains unchanged
- [x] New MCP tools integrate seamlessly with existing server

### SC2: User Experience
- [x] CLI provides intuitive parameter names and help text
- [x] Error messages guide users toward correct usage
- [x] Performance is acceptable for typical branch sizes (< 5 seconds for 100 files)
- [x] Output format is consistent with existing review templates

### SC3: Reliability
- [x] Handles network failures gracefully
- [x] Validates all user inputs before processing
- [x] Provides comprehensive test coverage for new functionality
- [x] No regressions in existing features

## Non-Functional Requirements

### NFR1: Performance
- Local branch comparisons complete within 10 seconds for repositories with < 1000 files
- GitHub API calls timeout after 30 seconds with clear error messages
- Memory usage remains reasonable for large diffs (< 500MB)

### NFR2: Compatibility
- Support Git versions 2.20+
- Work with GitHub Enterprise and GitHub.com
- Maintain Python 3.8+ compatibility
- Cross-platform support (Windows, macOS, Linux)

### NFR3: Maintainability
- Follow existing code patterns and architecture
- Comprehensive test coverage for new functionality
- Clear documentation for new CLI parameters
- Modular design allowing future git providers (GitLab, Bitbucket)

## Dependencies

### External Dependencies
- **GitHub REST API**: For PR data retrieval
- **Git CLI**: For local branch comparisons
- **requests library**: For HTTP API calls
- **urllib.parse**: For URL validation and parsing

### Internal Dependencies
- Existing `generate_code_review_context` module
- Current MCP server architecture
- Existing template formatting system
- Model configuration and capability detection

## Assumptions

1. Users have git installed and repositories are valid git repositories
2. GitHub tokens (when required) are provided via environment variables
3. Network connectivity is available for GitHub API calls
4. Existing task list functionality remains primary use case
5. Users understand git branch concepts (main vs feature branches)

## Risks and Mitigations

### Risk 1: GitHub API Rate Limiting
- **Mitigation**: Implement proper rate limiting handling and user guidance
- **Fallback**: Provide option to use local git commands for GitHub repositories

### Risk 2: Large Repository Performance
- **Mitigation**: Implement file and diff size limits with configuration options
- **Monitoring**: Add performance logging and optimization opportunities

### Risk 3: Network Dependency
- **Mitigation**: Clear offline/online mode distinction
- **Graceful Degradation**: Local features work without network access

### Risk 4: Authentication Complexity
- **Mitigation**: Clear documentation and error messages for token setup
- **Alternative**: Support multiple authentication methods (token, SSH)

## Future Considerations

1. **GitLab Support**: Extend to GitLab merge requests
2. **Bitbucket Integration**: Support Bitbucket pull requests  
3. **Advanced Filtering**: Allow filtering by file types or directories
4. **Review Templates**: Customizable review templates per repository
5. **Batch Processing**: Review multiple PRs or branches simultaneously