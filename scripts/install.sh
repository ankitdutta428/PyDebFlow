#!/bin/bash
# =============================================================================
# install.sh - PyDebFlow Installation Script for Linux/macOS
# =============================================================================
# This script creates a virtual environment and installs all dependencies.
#
# Usage:
#   chmod +x scripts/install.sh
#   ./scripts/install.sh
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory (to find project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           PyDebFlow - Installation Script                     ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo

cd "$PROJECT_ROOT"
echo -e "${YELLOW}📁 Project root: $PROJECT_ROOT${NC}"

# Check Python version
echo -e "\n${YELLOW}[1/4] Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo -e "${RED}❌ Python not found. Please install Python 3.10, 3.11, or 3.12${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo -e "   Found: Python ${PYTHON_VERSION}"

# Check if version is compatible (3.10+)
MAJOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)")
MINOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)")

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
    echo -e "${RED}❌ Python 3.10 or higher is required (found $PYTHON_VERSION)${NC}"
    exit 1
fi
echo -e "${GREEN}   ✓ Python version is compatible${NC}"

# Create virtual environment
echo -e "\n${YELLOW}[2/4] Creating virtual environment...${NC}"
VENV_DIR="$PROJECT_ROOT/venv"

if [ -d "$VENV_DIR" ]; then
    echo -e "   Virtual environment already exists at $VENV_DIR"
    read -p "   Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
        $PYTHON_CMD -m venv "$VENV_DIR"
        echo -e "${GREEN}   ✓ Virtual environment recreated${NC}"
    else
        echo -e "   Using existing virtual environment"
    fi
else
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo -e "${GREEN}   ✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}[3/4] Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}   ✓ Virtual environment activated${NC}"

# Upgrade pip
pip install --upgrade pip --quiet

# Install dependencies
echo -e "\n${YELLOW}[4/4] Installing dependencies...${NC}"
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    pip install -r "$PROJECT_ROOT/requirements.txt"
    echo -e "${GREEN}   ✓ Dependencies installed${NC}"
else
    echo -e "${RED}   ❌ requirements.txt not found${NC}"
    exit 1
fi

# Verify installation
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Installation complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo
echo -e "To activate the virtual environment:"
echo -e "  ${YELLOW}source venv/bin/activate${NC}"
echo
echo -e "To run PyDebFlow:"
echo -e "  ${YELLOW}./scripts/run.sh --synthetic-test${NC}"
echo -e "  ${YELLOW}python main.py${NC}  (for GUI)"
echo
echo -e "To run tests:"
echo -e "  ${YELLOW}./scripts/test.sh${NC}"
