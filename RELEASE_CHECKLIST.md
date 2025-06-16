# Release Checklist for gemini-code-review-mcp

Complete this checklist before releasing a new version. Check off each item as you complete it.

## Pre-Release Preparation

### Code Quality
- [ ] All tests pass locally: `python -m pytest tests/`
- [ ] Type checking passes: `pyright src/`
- [ ] Linting passes: `flake8 src/` and `pyflakes src/`
- [ ] Code formatting is consistent: `black src/ tests/ --check`
- [ ] No uncommitted changes: `git status` shows clean
- [ ] On master branch: `git branch --show-current` shows `master`
- [ ] Master is up to date: `git pull origin master`

### Version Management
- [ ] Version in `pyproject.toml` has been bumped appropriately:
  - Patch version (X.Y.Z+1) for bug fixes
  - Minor version (X.Y+1.0) for new features
  - Major version (X+1.0.0) for breaking changes
- [ ] Version follows semantic versioning (semver.org)
- [ ] New version doesn't exist on PyPI: `pip index versions gemini-code-review-mcp`

### Documentation
- [ ] README.md is up to date with new features/changes
- [ ] CLAUDE.md reflects any changes to development workflow
- [ ] MANUAL_RELEASE_GUIDE.md is current (if process changed)
- [ ] Any new CLI commands or options are documented
- [ ] API changes are documented (if applicable)

### Dependencies
- [ ] All dependencies in `pyproject.toml` have appropriate version constraints
- [ ] No unnecessary dependencies added
- [ ] Security vulnerabilities checked: `pip audit` (if installed)

## Release Execution

### Building
- [ ] Clean build environment (fresh virtual environment)
- [ ] Build tools are up to date: `pip install --upgrade build twine`
- [ ] Previous build artifacts removed: `rm -rf dist/ build/ *.egg-info`
- [ ] Package builds successfully: `python -m build`
- [ ] Both `.tar.gz` and `.whl` files created in `dist/`

### Testing the Build
- [ ] Install from wheel works: `pip install dist/*.whl`
- [ ] CLI commands work: `generate-code-review --help`
- [ ] Basic functionality verified
- [ ] Package metadata is correct: `pip show gemini-code-review-mcp`

### Publishing
- [ ] PyPI credentials configured (token in ~/.pypirc or environment)
- [ ] Dry run successful: `twine check dist/*`
- [ ] Upload to PyPI successful: `twine upload dist/*`
- [ ] Package appears on PyPI: https://pypi.org/project/gemini-code-review-mcp/

### Git & GitHub
- [ ] Version bump committed: `git add pyproject.toml && git commit -m "chore: bump version to X.Y.Z"`
- [ ] Changes pushed to master: `git push origin master`
- [ ] Git tag created: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
- [ ] Tag pushed: `git push origin vX.Y.Z`
- [ ] GitHub release created with release notes
- [ ] Release artifacts uploaded to GitHub (optional)

## Post-Release Verification

### Installation Testing
- [ ] Clean install from PyPI works: `pip install gemini-code-review-mcp==X.Y.Z`
- [ ] Upgrade from previous version works: `pip install --upgrade gemini-code-review-mcp`
- [ ] All CLI commands function correctly
- [ ] MCP server starts without errors

### Communication
- [ ] Release notes highlight key changes
- [ ] Breaking changes clearly documented (if any)
- [ ] Users notified through appropriate channels (if needed)

## Emergency Procedures

If something goes wrong:

### Failed PyPI Upload
- [ ] Check error message for specific issue
- [ ] Verify credentials are correct
- [ ] Ensure version doesn't already exist
- [ ] Fix issue and retry

### Wrong Version Published
- [ ] Yank the version on PyPI: `twine yank gemini-code-review-mcp==X.Y.Z`
- [ ] Delete GitHub release and tag
- [ ] Fix the issue
- [ ] Release new patch version

### Critical Bug Found Post-Release
- [ ] Document the issue immediately
- [ ] Yank affected version if severe
- [ ] Prepare hotfix release
- [ ] Notify users of the issue and fix

## Notes

- Never force push to master after release
- Keep release commits atomic and clean
- Test in a clean environment to catch missing dependencies
- Consider releasing to TestPyPI first for major changes
- Document any deviations from this checklist