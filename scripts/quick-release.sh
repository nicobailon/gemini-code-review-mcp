#!/bin/bash
# Quick release helper - validates and shows next steps
# This is a simplified wrapper around the main release process

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== Quick Release Helper ==="
echo

# Run readiness check
echo "Running release readiness check..."
if "$SCRIPT_DIR/check-release-readiness.sh"; then
    echo
    echo -e "${GREEN}✓ Ready for release!${NC}"
    echo
    echo "Next steps:"
    echo "1. Run the release script:"
    echo "   ./scripts/release.sh"
    echo
    echo "2. Or follow manual steps:"
    echo "   - Update version in pyproject.toml"
    echo "   - Build: python -m build"
    echo "   - Upload: python -m twine upload dist/*"
    echo "   - Tag: git tag -a vX.Y.Z -m 'Release vX.Y.Z'"
    echo
    echo "See MANUAL_RELEASE_GUIDE.md for detailed instructions"
else
    echo
    echo -e "${YELLOW}⚠ Please fix issues before releasing${NC}"
    echo
    echo "After fixing issues, run this script again."
fi