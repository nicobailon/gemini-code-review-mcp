#!/bin/bash
# Script to install git hooks for the project
# This sets up pre-commit and pre-push hooks to enforce code quality

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Installing Git Hooks for gemini-code-review-mcp${NC}"
echo ""

# Get the git directory
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: Not a git repository${NC}"
    exit 1
fi

# Check if hooks directory exists
HOOKS_DIR="$GIT_DIR/hooks"
if [ ! -d "$HOOKS_DIR" ]; then
    echo -e "${YELLOW}Creating hooks directory...${NC}"
    mkdir -p "$HOOKS_DIR"
fi

# Function to install a hook
install_hook() {
    local hook_name=$1
    local source_file=".githooks/$hook_name"
    local dest_file="$HOOKS_DIR/$hook_name"
    
    if [ ! -f "$source_file" ]; then
        echo -e "${RED}❌ Error: $source_file not found${NC}"
        return 1
    fi
    
    # Backup existing hook if it exists
    if [ -f "$dest_file" ] && [ ! -L "$dest_file" ]; then
        echo -e "${YELLOW}⚠️  Backing up existing $hook_name hook to $hook_name.backup${NC}"
        mv "$dest_file" "$dest_file.backup"
    fi
    
    # Create symlink
    ln -sf "../../$source_file" "$dest_file"
    chmod +x "$source_file"
    
    echo -e "${GREEN}✅ Installed $hook_name hook${NC}"
    return 0
}

# Install hooks
echo -e "${BLUE}Installing hooks...${NC}"
install_hook "pre-commit"
install_hook "pre-push"

echo ""
echo -e "${GREEN}🎉 Git hooks installed successfully!${NC}"
echo ""
echo "Hooks installed:"
echo "  • pre-commit: Runs tests when committing to master/main"
echo "  • pre-push: Prevents direct pushes to master/main"
echo ""
echo -e "${YELLOW}📝 Note: You can bypass hooks in emergencies with:${NC}"
echo "  • git commit --no-verify"
echo "  • git push --no-verify"
echo ""
echo -e "${BLUE}But please use these flags responsibly!${NC}"