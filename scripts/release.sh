#!/bin/bash

# Release script for gemini-code-review-mcp
# This script guides you through the manual release process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

confirm() {
    read -p "$1 (y/n): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Check prerequisites
print_header "Checking Prerequisites"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "pyproject.toml not found. Are you in the project root?"
    exit 1
fi

# Check git status
if ! git diff-index --quiet HEAD --; then
    print_error "You have uncommitted changes. Please commit or stash them first."
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "master" ]; then
    print_warning "You're not on master branch (current: $CURRENT_BRANCH)"
    if ! confirm "Do you want to switch to master?"; then
        exit 1
    fi
    git checkout master
fi

# Pull latest changes
print_header "Updating from Remote"
git pull origin master

# Get current version
CURRENT_VERSION=$(grep -Po 'version = "\K[^"]+' pyproject.toml)
print_success "Current version: $CURRENT_VERSION"

# Prompt for new version
print_header "Version Management"
echo "Current version: $CURRENT_VERSION"
echo "Semantic versioning reminder:"
echo "  - Patch (x.y.Z): Bug fixes"
echo "  - Minor (x.Y.z): New features (backwards compatible)"
echo "  - Major (X.y.z): Breaking changes"
echo
read -p "Enter new version: " NEW_VERSION

if [ -z "$NEW_VERSION" ]; then
    print_error "Version cannot be empty"
    exit 1
fi

# Check if version already exists on PyPI
print_header "Checking PyPI"
if pip index versions gemini-code-review-mcp 2>/dev/null | grep -q "$NEW_VERSION"; then
    print_error "Version $NEW_VERSION already exists on PyPI!"
    exit 1
fi
print_success "Version $NEW_VERSION is available"

# Run tests
print_header "Running Tests"
if confirm "Run tests before proceeding?"; then
    python -m pytest tests/
    print_success "Tests passed"
fi

# Update version in pyproject.toml
print_header "Updating Version"
sed -i.bak "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
rm pyproject.toml.bak
print_success "Updated version in pyproject.toml"

# Commit version bump
git add pyproject.toml
git commit -m "chore: bump version to $NEW_VERSION"
print_success "Committed version bump"

# Build the package
print_header "Building Package"
rm -rf dist/ build/ *.egg-info
python -m build
print_success "Package built successfully"

# List build artifacts
echo -e "\nBuild artifacts:"
ls -la dist/

# Test the package
if confirm "Test the built package?"; then
    print_header "Testing Package"
    python -m venv test-env
    source test-env/bin/activate
    pip install dist/*.whl
    generate-code-review --help
    deactivate
    rm -rf test-env
    print_success "Package test successful"
fi

# Push version bump
print_header "Pushing Changes"
if confirm "Push version bump to master?"; then
    git push origin master
    print_success "Pushed to master"
else
    print_warning "Remember to push changes before creating release!"
fi

# Upload to PyPI
print_header "PyPI Upload"
echo "Ready to upload to PyPI."
echo -e "${YELLOW}Make sure you have your PyPI token ready!${NC}"
echo

if confirm "Upload to PyPI now?"; then
    if [ -f ~/.pypirc ]; then
        print_success "Found ~/.pypirc"
        python -m twine upload dist/*
    else
        print_warning "No ~/.pypirc found. You'll need to enter credentials."
        echo "Username: __token__"
        echo "Password: <your-pypi-token>"
        python -m twine upload dist/*
    fi
    print_success "Uploaded to PyPI"
else
    print_warning "Skipping PyPI upload. You can run later:"
    echo "  python -m twine upload dist/*"
fi

# Create git tag and GitHub release
print_header "GitHub Release"
if confirm "Create GitHub release?"; then
    # Create and push tag
    git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"
    git push origin "v$NEW_VERSION"
    print_success "Created and pushed tag v$NEW_VERSION"
    
    # Get previous tag for changelog
    PREVIOUS_TAG=$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo "")
    
    # Create release notes
    RELEASE_NOTES="## What's Changed

"
    if [ -n "$PREVIOUS_TAG" ]; then
        RELEASE_NOTES+="### Commits since $PREVIOUS_TAG

"
        RELEASE_NOTES+=$(git log --pretty=format:"- %s" "$PREVIOUS_TAG"..HEAD)
        RELEASE_NOTES+="

**Full Changelog**: https://github.com/nicobailon/gemini-code-review-mcp/compare/$PREVIOUS_TAG...v$NEW_VERSION"
    else
        RELEASE_NOTES+="Initial release"
    fi
    
    # Create GitHub release
    gh release create "v$NEW_VERSION" \
        --title "Release v$NEW_VERSION" \
        --notes "$RELEASE_NOTES" \
        dist/*.tar.gz dist/*.whl
    
    print_success "Created GitHub release"
else
    print_warning "Skipping GitHub release. You can create it later:"
    echo "  git tag -a v$NEW_VERSION -m \"Release v$NEW_VERSION\""
    echo "  git push origin v$NEW_VERSION"
    echo "  gh release create v$NEW_VERSION"
fi

# Final verification
print_header "Release Complete!"
echo -e "${GREEN}Successfully released version $NEW_VERSION${NC}"
echo
echo "Verification steps:"
echo "  1. Check PyPI: https://pypi.org/project/gemini-code-review-mcp/$NEW_VERSION/"
echo "  2. Check GitHub: https://github.com/nicobailon/gemini-code-review-mcp/releases/tag/v$NEW_VERSION"
echo "  3. Test installation: pip install gemini-code-review-mcp==$NEW_VERSION"
echo
echo "If something went wrong, see MANUAL_RELEASE_GUIDE.md for rollback procedures."