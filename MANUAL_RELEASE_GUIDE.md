# Manual Release Guide for gemini-code-review-mcp

This guide provides step-by-step instructions for manually releasing new versions of `gemini-code-review-mcp` to PyPI.

## Prerequisites

Before starting a release, ensure you have:

1. **PyPI Account & API Token**
   - Create an account at https://pypi.org
   - Generate an API token: Account Settings → API tokens → Add API token
   - Scope: Project (`gemini-code-review-mcp`)
   - Save the token securely (starts with `pypi-`)

2. **Local Environment Setup**
   ```bash
   # Create and activate virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install required tools
   pip install --upgrade pip
   pip install build twine
   ```

3. **Git & GitHub CLI**
   ```bash
   # Ensure you're on the latest master
   git checkout master
   git pull origin master
   
   # Install GitHub CLI if not already installed
   # macOS: brew install gh
   # Linux: See https://github.com/cli/cli/blob/trunk/docs/install_linux.md
   gh auth login  # One-time setup
   ```

## Release Process

### Step 1: Pre-Release Checks

Run the release checklist to ensure everything is ready:

```bash
# Use the provided checklist
cat RELEASE_CHECKLIST.md

# Or use the automated check script (if available)
./scripts/check-release-readiness.sh
```

### Step 2: Update Version

1. Edit `pyproject.toml`:
   ```toml
   [project]
   version = "X.Y.Z"  # Update this line
   ```

2. Commit the version bump:
   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to X.Y.Z"
   git push origin master
   ```

### Step 3: Build the Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build source distribution and wheel
python -m build

# Verify the build
ls -la dist/
# Should show:
# - gemini-code-review-mcp-X.Y.Z.tar.gz
# - gemini_code_review_mcp-X.Y.Z-py3-none-any.whl
```

### Step 4: Test the Package (Optional but Recommended)

```bash
# Create a test virtual environment
python3 -m venv test-release
source test-release/bin/activate

# Install from the built wheel
pip install dist/gemini_code_review_mcp-X.Y.Z-py3-none-any.whl

# Test basic functionality
generate-code-review --help

# Deactivate and clean up
deactivate
rm -rf test-release
```

### Step 5: Upload to PyPI

```bash
# Set up PyPI credentials (one-time)
# Create ~/.pypirc file:
cat > ~/.pypirc << EOF
[distutils]
index-servers = pypi

[pypi]
username = __token__
password = <your-pypi-token>
EOF

# Set proper permissions
chmod 600 ~/.pypirc

# Upload to PyPI
python -m twine upload dist/*

# Alternatively, use environment variables:
TWINE_USERNAME=__token__ TWINE_PASSWORD=<your-token> python -m twine upload dist/*
```

### Step 6: Create GitHub Release

```bash
# Create a git tag
git tag -a v$VERSION -m "Release v$VERSION"
git push origin v$VERSION

# Create GitHub release
gh release create v$VERSION \
  --title "Release v$VERSION" \
  --notes "## What's Changed

- Feature: Description of new features
- Fix: Description of bug fixes
- Docs: Documentation updates

**Full Changelog**: https://github.com/nicobailon/gemini-code-review-mcp/compare/vPREVIOUS...v$VERSION"

# Upload the built artifacts (optional)
gh release upload v$VERSION dist/*.tar.gz dist/*.whl
```

### Step 7: Verify the Release

1. **Check PyPI**:
   ```bash
   # Verify it's available
   pip index versions gemini-code-review-mcp
   
   # Test installation in a fresh environment
   python3 -m venv verify-release
   source verify-release/bin/activate
   pip install gemini-code-review-mcp==$VERSION
   generate-code-review --version
   deactivate
   rm -rf verify-release
   ```

2. **Check GitHub**:
   - Visit https://github.com/nicobailon/gemini-code-review-mcp/releases
   - Ensure the release appears with correct tag and notes

## Rollback Procedure

If something goes wrong after publishing:

1. **PyPI**: You cannot delete released versions, but you can "yank" them:
   ```bash
   python -m twine yank gemini-code-review-mcp==$VERSION
   ```

2. **GitHub Release**: Delete the release and tag:
   ```bash
   gh release delete v$VERSION --yes
   git push --delete origin v$VERSION
   git tag -d v$VERSION
   ```

3. **Fix the issue** and release a new patch version (e.g., X.Y.Z+1)

## Security Considerations

1. **Protect Your PyPI Token**:
   - Never commit tokens to git
   - Use environment variables in CI/CD
   - Rotate tokens regularly
   - Use project-scoped tokens, not account-wide

2. **Verify Package Integrity**:
   ```bash
   # Generate checksums for your artifacts
   cd dist/
   sha256sum * > SHA256SUMS
   ```

3. **Sign Your Commits** (optional but recommended):
   ```bash
   git config --global commit.gpgsign true
   ```

## Troubleshooting

### Common Issues

1. **"Version already exists" error**:
   - You cannot re-upload the same version to PyPI
   - Bump the version number and try again

2. **Authentication failed**:
   - Ensure your token starts with `pypi-`
   - Check token hasn't expired
   - Verify token has correct project scope

3. **Build errors**:
   - Ensure you're in a clean virtual environment
   - Update build tools: `pip install --upgrade build wheel`
   - Check `pyproject.toml` syntax

### Getting Help

- PyPI documentation: https://packaging.python.org/
- Twine documentation: https://twine.readthedocs.io/
- Project issues: https://github.com/nicobailon/gemini-code-review-mcp/issues

## Quick Reference

```bash
# Complete release in one script (if available)
./scripts/release.sh

# Or manual steps:
git checkout master && git pull
vim pyproject.toml  # Update version
git add pyproject.toml && git commit -m "chore: bump version to X.Y.Z"
git push origin master
python -m build
python -m twine upload dist/*
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
gh release create vX.Y.Z --title "Release vX.Y.Z" --notes "..."
```