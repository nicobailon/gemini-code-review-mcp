#!/bin/bash
# Main release script for gemini-code-review-mcp

set -e

# Source shared utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/release-utils.sh"

# Configuration
PACKAGE_NAME="gemini-code-review-mcp"

print_header "Release Script for $PACKAGE_NAME"

# 1. Run release readiness check
print_header "Running Release Checks"

if ! "$SCRIPT_DIR/release-check.sh"; then
    print_error "Release checks failed. Please fix issues before proceeding."
    exit 1
fi

# 2. Get version information
CURRENT_VERSION=$(get_current_version)
print_info "Preparing to release version: $CURRENT_VERSION"

# 3. Confirm release
if ! confirm "Do you want to proceed with releasing v$CURRENT_VERSION?"; then
    print_info "Release cancelled."
    exit 0
fi

# 4. Build the package
print_header "Building Package"

# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build the package
print_info "Running build..."
if python -m build; then
    print_success "Package built successfully"
else
    print_error "Build failed"
    exit 1
fi

# 5. Test the built package
print_header "Testing Built Package"

# Create a temporary virtual environment
TEMP_ENV=$(mktemp -d)
print_info "Creating test environment in $TEMP_ENV"

python -m venv "$TEMP_ENV/venv"
source "$TEMP_ENV/venv/bin/activate"

# Install the built package
print_info "Installing built package..."
pip install dist/*.whl

# Run a smoke test
print_info "Running smoke test..."
if python -c "import gemini_code_review_mcp; print(f'Version: {gemini_code_review_mcp.__version__}')"; then
    print_success "Package imports successfully"
else
    print_error "Package import failed"
    deactivate
    rm -rf "$TEMP_ENV"
    exit 1
fi

# Test CLI commands
for cmd in gemini-code-review-mcp generate-code-review; do
    if command -v "$cmd" >/dev/null; then
        print_success "CLI command '$cmd' is available"
    else
        print_error "CLI command '$cmd' not found"
    fi
done

deactivate
rm -rf "$TEMP_ENV"

# 6. Upload to PyPI
print_header "PyPI Upload"

print_warning "About to upload to PyPI. This action cannot be undone!"
if ! confirm "Upload to PyPI?"; then
    print_info "Upload cancelled. Package files are in dist/"
    exit 0
fi

print_info "Uploading to PyPI..."
if python -m twine upload dist/*; then
    print_success "Package uploaded successfully!"
else
    print_error "Upload failed"
    exit 1
fi

# 7. Create Git tag
print_header "Git Tagging"

TAG_NAME="v$CURRENT_VERSION"
if git tag -l "$TAG_NAME" | grep -q "$TAG_NAME"; then
    print_warning "Tag $TAG_NAME already exists"
else
    print_info "Creating tag $TAG_NAME"
    git tag -a "$TAG_NAME" -m "Release version $CURRENT_VERSION"
    
    if confirm "Push tag to remote?"; then
        git push origin "$TAG_NAME"
        print_success "Tag pushed to remote"
    fi
fi

# 8. Create GitHub release (if gh CLI is available)
if command_exists gh; then
    print_header "GitHub Release"
    
    if confirm "Create GitHub release?"; then
        # Extract changelog for this version
        CHANGELOG_FILE=$(mktemp)
        awk "/^## $CURRENT_VERSION/{flag=1; next} /^## /{flag=0} flag" CHANGELOG.md > "$CHANGELOG_FILE"
        
        gh release create "$TAG_NAME" \
            --title "Release v$CURRENT_VERSION" \
            --notes-file "$CHANGELOG_FILE" \
            dist/*
        
        rm "$CHANGELOG_FILE"
        print_success "GitHub release created"
    fi
else
    print_info "GitHub CLI (gh) not found - skipping GitHub release"
    print_info "You can create a release manually at:"
    print_info "https://github.com/YOUR_USERNAME/$PACKAGE_NAME/releases/new"
fi

# 9. Final steps
print_header "Release Complete! 🎉"

print_success "Version $CURRENT_VERSION has been released!"
echo
echo "Next steps:"
echo "  1. Verify the package on PyPI: https://pypi.org/project/$PACKAGE_NAME/"
echo "  2. Test installation: pip install $PACKAGE_NAME==$CURRENT_VERSION"
echo "  3. Update version in pyproject.toml for next development cycle"
echo "  4. Create a new changelog section for the next version"
echo
print_info "Thank you for releasing $PACKAGE_NAME!"