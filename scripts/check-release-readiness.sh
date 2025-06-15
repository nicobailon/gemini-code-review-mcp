#!/bin/bash

# Pre-release checks for gemini-code-review-mcp
# This script verifies that the project is ready for release

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}==== $1 ====${NC}"
}

print_check() {
    echo -n "  Checking $1... "
}

print_success() {
    echo -e "${GREEN}✓${NC}"
}

print_error() {
    echo -e "${RED}✗${NC}"
    echo -e "    ${RED}Error: $1${NC}"
    ((ERRORS++))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC}"
    echo -e "    ${YELLOW}Warning: $1${NC}"
    ((WARNINGS++))
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found. Are you in the project root?${NC}"
    exit 1
fi

print_header "Git Repository Status"

# Check git is initialized
print_check "git repository"
if git rev-parse --git-dir > /dev/null 2>&1; then
    print_success
else
    print_error "Not a git repository"
fi

# Check for uncommitted changes
print_check "working directory clean"
if git diff-index --quiet HEAD -- 2>/dev/null; then
    print_success
else
    print_error "Uncommitted changes found. Run 'git status' to see details"
fi

# Check current branch
print_check "on master branch"
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" == "master" ]; then
    print_success
else
    print_warning "Not on master branch (current: $CURRENT_BRANCH)"
fi

# Check if up to date with remote
print_check "up to date with remote"
git fetch origin master --quiet
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/master)
if [ "$LOCAL" == "$REMOTE" ]; then
    print_success
else
    print_error "Local branch is not up to date with origin/master"
fi

print_header "Python Environment"

# Check Python version
print_check "Python version"
PYTHON_VERSION=$(python --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
REQUIRED_VERSION="3.11"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" == "$REQUIRED_VERSION" ]; then
    print_success
else
    print_warning "Python $PYTHON_VERSION found, but $REQUIRED_VERSION or higher recommended"
fi

# Check virtual environment
print_check "virtual environment active"
if [ -n "$VIRTUAL_ENV" ]; then
    print_success
else
    print_warning "No virtual environment active. Consider activating one"
fi

# Check required tools
print_check "build tools installed"
if python -c "import build" 2>/dev/null && python -c "import twine" 2>/dev/null; then
    print_success
else
    print_error "Missing build tools. Run: pip install build twine"
fi

print_header "Code Quality"

# Run tests
print_check "all tests pass"
if python -m pytest tests/ -q --tb=no 2>/dev/null; then
    print_success
else
    print_error "Tests failed. Run 'python -m pytest tests/' for details"
fi

# Check type hints (if pyright is installed)
print_check "type checking (pyright)"
if command -v pyright &> /dev/null; then
    if pyright src/ --outputjson 2>/dev/null | grep -q '"errorCount": 0'; then
        print_success
    else
        print_warning "Type errors found. Run 'pyright src/' for details"
    fi
else
    echo "skipped (pyright not installed)"
fi

# Check code formatting (if black is installed)
print_check "code formatting (black)"
if command -v black &> /dev/null; then
    if black src/ tests/ --check --quiet 2>/dev/null; then
        print_success
    else
        print_warning "Code not formatted. Run 'black src/ tests/' to fix"
    fi
else
    echo "skipped (black not installed)"
fi

print_header "Version Check"

# Get current version
print_check "current version"
CURRENT_VERSION=$(grep -Po 'version = "\K[^"]+' pyproject.toml)
if [ -n "$CURRENT_VERSION" ]; then
    echo "$CURRENT_VERSION"
else
    print_error "Could not determine version from pyproject.toml"
fi

# Check if version exists on PyPI
print_check "version availability on PyPI"
if pip index versions gemini-code-review-mcp 2>/dev/null | grep -q "$CURRENT_VERSION"; then
    print_error "Version $CURRENT_VERSION already exists on PyPI!"
else
    print_success
fi

print_header "Documentation"

# Check if key documentation files exist
for doc in "README.md" "MANUAL_RELEASE_GUIDE.md" "RELEASE_CHECKLIST.md"; do
    print_check "$doc exists"
    if [ -f "$doc" ]; then
        print_success
    else
        print_warning "$doc not found"
    fi
done

print_header "Dependencies"

# Check for security vulnerabilities (if safety is installed)
print_check "security vulnerabilities"
if command -v safety &> /dev/null; then
    if safety check --json 2>/dev/null | grep -q '"vulnerabilities": \[\]'; then
        print_success
    else
        print_warning "Security vulnerabilities found. Run 'safety check' for details"
    fi
else
    echo "skipped (safety not installed)"
fi

# Summary
print_header "Summary"
echo -e "Errors:   ${RED}$ERRORS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"

if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "\n${GREEN}✓ All checks passed! Ready for release.${NC}"
    else
        echo -e "\n${YELLOW}⚠ Ready for release with warnings.${NC}"
    fi
    echo -e "\nNext step: Run ${BLUE}./scripts/release.sh${NC}"
    exit 0
else
    echo -e "\n${RED}✗ Not ready for release. Please fix the errors above.${NC}"
    exit 1
fi