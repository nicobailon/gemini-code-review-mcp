# Deprecation Schedule for v0.22.0

## Overview
This document tracks deprecated features and code scheduled for removal in v0.22.0.

## Deprecated Items

### 1. model_config.json
- **Status**: Deprecated in v0.20.0
- **Replacement**: Use `[tool.gemini]` section in `pyproject.toml`
- **Removal**: v0.22.0
- **Migration**: Configuration loader shows deprecation warning when file is detected
- **Files to update**:
  - Remove compatibility shim in `src/config/loader.py`
  - Remove deprecation warning logic
  - Update tests to remove deprecation checks

### 2. Legacy Dictionary-based Context
- **Status**: Replaced with typed dataclasses
- **Replacement**: `ReviewContext` dataclass
- **Removal**: v0.22.0
- **Files to clean**:
  - Remove any remaining `Dict[str, Any]` context handling
  - Update all type hints to use domain models

### 3. Monolithic generate_review_context_data Function
- **Status**: Refactored into Strategy pattern
- **Replacement**: Strategy classes (TaskDrivenStrategy, GeneralStrategy, GitHubPRStrategy)
- **Removal**: v0.22.0
- **Note**: Already removed as part of V3 refactor

## Migration Checklist for v0.22.0

- [ ] Remove `model_config.json` support from configuration loader
- [ ] Remove deprecation warnings from codebase
- [ ] Update documentation to remove references to deprecated features
- [ ] Update changelog with breaking changes
- [ ] Bump version to 0.22.0
- [ ] Tag release with clear migration guide

## User Communication

### Release Notes Template
```markdown
## Breaking Changes in v0.22.0

### Removed Features
1. **model_config.json** - Configuration must now be in `pyproject.toml` under `[tool.gemini]`
2. **Legacy context dictionaries** - All integrations must use the typed `ReviewContext` dataclass

### Migration Guide
1. Move any `model_config.json` settings to `pyproject.toml`:
   ```toml
   [tool.gemini]
   temperature = 0.5
   default_model = "gemini-1.5-flash"
   ```

2. Update any custom integrations to use typed models instead of dictionaries
```

## Timeline
- v0.20.0 (current): Deprecation warnings active
- v0.21.0: Final warning release
- v0.22.0: Complete removal of deprecated features