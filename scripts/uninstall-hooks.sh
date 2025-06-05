#!/bin/bash
# Script to uninstall git hooks

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Uninstalling Git Hooks${NC}"
echo ""

# Get the git directory
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: Not a git repository${NC}"
    exit 1
fi

HOOKS_DIR="$GIT_DIR/hooks"

# Function to uninstall a hook
uninstall_hook() {
    local hook_name=$1
    local hook_file="$HOOKS_DIR/$hook_name"
    
    if [ -L "$hook_file" ]; then
        # It's a symlink, remove it
        rm "$hook_file"
        echo -e "${GREEN}✅ Removed $hook_name hook${NC}"
        
        # Restore backup if it exists
        if [ -f "$hook_file.backup" ]; then
            mv "$hook_file.backup" "$hook_file"
            echo -e "${YELLOW}↩️  Restored original $hook_name hook from backup${NC}"
        fi
    elif [ -f "$hook_file" ]; then
        echo -e "${YELLOW}⚠️  $hook_name is not a symlink, skipping${NC}"
    else
        echo -e "${BLUE}ℹ️  No $hook_name hook found${NC}"
    fi
}

# Uninstall hooks
echo -e "${BLUE}Removing hooks...${NC}"
uninstall_hook "pre-commit"
uninstall_hook "pre-push"

echo ""
echo -e "${GREEN}🎉 Git hooks uninstalled successfully!${NC}"