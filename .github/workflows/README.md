# GitHub Workflows

This directory contains GitHub Actions workflows for the project.

## Active Workflows

### ci.yml
- **Purpose**: Basic continuous integration checks
- **Triggers**: Pull requests, pushes to master
- **Actions**: Runs tests and basic checks

### test-and-type-check.yml
- **Purpose**: Comprehensive testing and type checking
- **Triggers**: Pull requests, manual dispatch
- **Actions**: 
  - Runs full test suite
  - Performs type checking with pyright
  - Tests on multiple Python versions

### full-test.yml
- **Purpose**: Extended test suite including slower tests
- **Triggers**: Manual dispatch, scheduled (if configured)
- **Actions**: Runs all tests including those marked as slow

### integration-tests.yml
- **Purpose**: Integration tests with external services
- **Triggers**: Manual dispatch only
- **Actions**: Tests that require API keys or external services
- **Requirements**: Requires GENAI_API_KEY secret

### version-bump.yml
- **Purpose**: Automated version bumping
- **Triggers**: Manual dispatch with version type selection
- **Actions**: Updates version in pyproject.toml and creates PR

## Deprecated Workflows

### publish-to-pypi.yml (DISABLED)
- **Status**: DEPRECATED - Do not use
- **Replacement**: Use manual release process
- **See**: 
  - [MANUAL_RELEASE_GUIDE.md](../../MANUAL_RELEASE_GUIDE.md)
  - [scripts/release.sh](../../scripts/release.sh)
- **Reason**: Manual releases provide better control and prevent accidental publishes

## Workflow Maintenance

### Adding New Workflows
1. Create workflow file in `.github/workflows/`
2. Document purpose and triggers in this README
3. Ensure workflow has appropriate permissions
4. Test workflow in a feature branch first

### Modifying Workflows
1. Test changes in a feature branch
2. Ensure backwards compatibility
3. Update this documentation
4. Consider impact on existing PRs

### Security Considerations
- Use least-privilege permissions
- Store sensitive data in GitHub Secrets
- Pin action versions for security
- Review third-party actions before use