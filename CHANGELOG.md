# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.2] - 2025-01-06

### Changed
- **BREAKING**: Removed `generate_code_review_context` and `generate_meta_prompt` from public MCP tool registry
  - These functions remain available for internal use but are no longer exposed as MCP tools
  - This reduces the public tool count from 6 to 4, simplifying the LLM tool catalogue
- Updated docstrings to remove references to MCP tool usage for internal helpers
- Added comments marking internal helper functions
- Enhanced `get_mcp_tools()` documentation to remind maintainers about registry synchronization

### Added
- Test to verify `get_mcp_tools()` list matches actual MCP registry
- Registry consistency check to prevent future mismatches

### Previous Unreleased Changes

### Added
- **ask_gemini** MCP tool - NEW unified tool that combines file context generation with AI response in one step
- Shared file selection normalization function `normalize_file_selections_from_dicts` for code reuse
- Logging when no files are selected in ask_gemini tool
- Validation that either file_selections or user_instructions must be provided to ask_gemini
- Comprehensive documentation for ask_gemini in README.md

### Changed
- Improved error handling in ask_gemini to use exceptions instead of ERROR strings
- Updated CLI to use `parse_file_selections` for cleaner code
- Enhanced module docstring in file_selector.py to document all public functions

### Deprecated
- **generate_file_context** MCP tool - Use ask_gemini instead for AI responses
- The generate_file_context tool now shows a deprecation warning

### Fixed
- Removed unused `output_path` and `url_context` parameters from ask_gemini
- Fixed docstring drift mentioning removed parameters
- Corrected generate_file_context shim to properly handle output_path parameter

### Technical Details
- ask_gemini performs in-memory context generation without creating intermediate files
- Maintains backward compatibility for generate_file_context with ERROR string returns
- All existing tests pass with the refactored implementation