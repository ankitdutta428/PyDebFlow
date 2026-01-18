#!/bin/bash
# =============================================================================
# build.sh - PyDebFlow Build Script for Linux/macOS
# =============================================================================
# Builds a standalone executable using PyInstaller.
#
# Usage:
#   ./scripts/build.sh
#   ./scripts/build.sh --onefile
#   ./scripts/build.sh --clean
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              PyDebFlow - Build Script                         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo

show_help() {
    echo "Usage: ./scripts/build.sh [OPTIONS]"
    echo
    echo "Options:"
    echo "  --onefile       Create single executable file (default)"
    echo "  --onedir        Create directory with executable and dependencies"
    echo "  --clean         Clean build artifacts before building"
    echo "  --no-console    Hide console window (GUI mode)"
    echo "  --help, -h      Show this help message"
    echo
    echo "Output will be in: dist/"
}

# Parse arguments
BUILD_TYPE="onefile"
CLEAN=false
CONSOLE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --onefile)
            BUILD_TYPE="onefile"
            shift
            ;;
        --onedir)
            BUILD_TYPE="onedir"
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --no-console)
            CONSOLE="--windowed"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Clean if requested
if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}Cleaning build artifacts...${NC}"
    rm -rf build/ dist/ *.spec
    echo -e "${GREEN}   ✓ Clean complete${NC}"
    echo
fi

# Check PyInstaller
echo -e "${YELLOW}[1/3] Checking PyInstaller...${NC}"
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo -e "   Installing PyInstaller..."
    pip install pyinstaller
fi
echo -e "${GREEN}   ✓ PyInstaller ready${NC}"

# Run build script
echo -e "\n${YELLOW}[2/3] Building executable...${NC}"
echo -e "   Build type: $BUILD_TYPE"

if [ -f "build_script.py" ]; then
    python build_script.py
else
    # Fallback to direct PyInstaller call
    PYINSTALLER_ARGS="--name=PyDebFlow --$BUILD_TYPE $CONSOLE"
    PYINSTALLER_ARGS="$PYINSTALLER_ARGS --add-data src:src"
    PYINSTALLER_ARGS="$PYINSTALLER_ARGS --hidden-import=numpy"
    PYINSTALLER_ARGS="$PYINSTALLER_ARGS --hidden-import=PyQt6"
    PYINSTALLER_ARGS="$PYINSTALLER_ARGS --hidden-import=pyvista"
    
    python -m PyInstaller $PYINSTALLER_ARGS main.py
fi

# Summary
echo -e "\n${YELLOW}[3/3] Build complete!${NC}"
echo
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Build successful!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo
echo -e "Output location:"
if [ "$BUILD_TYPE" = "onefile" ]; then
    echo -e "  ${YELLOW}dist/PyDebFlow${NC}"
else
    echo -e "  ${YELLOW}dist/PyDebFlow/${NC}"
fi
