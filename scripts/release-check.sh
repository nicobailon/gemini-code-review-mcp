#!/bin/bash
# Release readiness check script

set -e

# Source shared utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/release-utils.sh"

# Configuration
PACKAGE_NAME="gemini-code-review-mcp"
MAIN_BRANCH="main"

# Track overall readiness
READY=true

print_header "Release Readiness Check for $PACKAGE_NAME"

# 1. Git Repository Checks
print_header "Git Repository Status"

if ! check_git_repo; then
    READY=false
else
    print_success "In git repository"
fi

if ! check_git_clean; then
    READY=false
else
    print_success "Working directory is clean"
fi

if ! check_git_branch "$MAIN_BRANCH"; then
    READY=false
else
    print_success "On $MAIN_BRANCH branch"
fi

if ! check_git_sync; then
    READY=false
else
    print_success "Branch is up to date with remote"
fi

# 2. Python Environment Check
print_header "Python Environment"

if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python installed: $PYTHON_VERSION"
else
    print_error "Python 3 not found"
    READY=false
fi

# Check for required tools
for tool in pip pytest twine; do
    if command_exists "$tool"; then
        print_success "$tool is available"
    else
        print_error "$tool is not installed"
        READY=false
    fi
done

# 3. Code Quality Checks
print_header "Code Quality"

# Run tests
echo "Running tests..."
if run_tests; then
    print_success "All tests passed"
else
    print_error "Tests failed"
    READY=false
fi

# Type checking (if available)
if command_exists pyright; then
    echo "Running type checks..."
    if pyright src/ >/dev/null 2>&1; then
        print_success "Type checking passed"
    else
        print_warning "Type checking has issues (non-blocking)"
    fi
else
    print_info "pyright not installed - skipping type checks"
fi

# 4. Version Check
print_header "Version Information"

CURRENT_VERSION=$(get_current_version)
print_info "Current version: $CURRENT_VERSION"

if check_pypi_version "$PACKAGE_NAME" "$CURRENT_VERSION"; then
    print_error "Version $CURRENT_VERSION already exists on PyPI"
    print_info "Please update version in pyproject.toml before releasing"
    READY=false
else
    print_success "Version $CURRENT_VERSION is available for release"
fi

# 5. Documentation Check
print_header "Documentation"

for doc in README.md CHANGELOG.md LICENSE; do
    if [[ -f "$doc" ]]; then
        print_success "$doc exists"
    else
        print_error "$doc is missing"
        READY=false
    fi
done

# Check if CHANGELOG has been updated for current version
if grep -q "## $CURRENT_VERSION" CHANGELOG.md; then
    print_success "CHANGELOG.md has entry for version $CURRENT_VERSION"
else
    print_warning "CHANGELOG.md may need update for version $CURRENT_VERSION"
fi

# 6. Summary
print_header "Summary"

if $READY; then
    print_success "✅ All checks passed! Ready for release."
    echo
    echo "Next steps:"
    echo "  1. Run: ./scripts/release.sh"
    echo "  2. Follow the prompts to complete the release"
    exit 0
else
    print_error "❌ Some checks failed. Please fix the issues above before releasing."
    exit 1
fi