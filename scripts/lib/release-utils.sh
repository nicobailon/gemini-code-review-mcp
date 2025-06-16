#!/bin/bash
# Shared utilities for release scripts

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Print functions
print_header() {
    echo -e "\n${BLUE}${BOLD}=== $1 ===${NC}\n"
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

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

# Confirmation prompt
confirm() {
    local prompt="${1:-Are you sure?}"
    echo -en "${YELLOW}${prompt} [y/N] ${NC}"
    read -r response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Get current version from pyproject.toml
get_current_version() {
    grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'
}

# Check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --is-inside-work-tree &>/dev/null; then
        print_error "Not in a git repository"
        return 1
    fi
    return 0
}

# Check if working directory is clean
check_git_clean() {
    if [[ -n $(git status -s) ]]; then
        print_error "Working directory has uncommitted changes"
        echo "Please commit or stash your changes before releasing."
        return 1
    fi
    return 0
}

# Check current branch
check_git_branch() {
    local expected_branch="${1:-main}"
    local current_branch=$(git branch --show-current)
    
    if [[ "$current_branch" != "$expected_branch" ]]; then
        print_warning "Not on $expected_branch branch (current: $current_branch)"
        if ! confirm "Continue anyway?"; then
            return 1
        fi
    fi
    return 0
}

# Check if branch is up to date with remote
check_git_sync() {
    git fetch origin >/dev/null 2>&1
    
    local LOCAL=$(git rev-parse @)
    local REMOTE=$(git rev-parse @{u} 2>/dev/null)
    
    if [[ -z "$REMOTE" ]]; then
        print_warning "No upstream branch set"
        return 0
    fi
    
    if [[ "$LOCAL" != "$REMOTE" ]]; then
        print_error "Branch is not in sync with remote"
        echo "Please pull/push changes before releasing."
        return 1
    fi
    return 0
}

# Run tests with optional coverage
run_tests() {
    local with_coverage="${1:-false}"
    
    if [[ "$with_coverage" == "true" ]]; then
        python -m pytest tests/ -v --cov=src --cov-report=term-missing
    else
        python -m pytest tests/ -v
    fi
}

# Check if version exists on PyPI
check_pypi_version() {
    local package_name="$1"
    local version="$2"
    
    if pip index versions "$package_name" 2>/dev/null | grep -q "$version"; then
        return 0  # Version exists
    else
        return 1  # Version doesn't exist
    fi
}

# Export functions and variables
export -f print_header print_success print_error print_warning print_info confirm
export -f command_exists get_current_version check_git_repo check_git_clean
export -f check_git_branch check_git_sync run_tests check_pypi_version
export RED GREEN YELLOW BLUE MAGENTA CYAN NC BOLD