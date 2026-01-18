#!/bin/bash
# =============================================================================
# run.sh - PyDebFlow Runner Script for Linux/macOS
# =============================================================================
# Quick launcher for simulations with common presets.
#
# Usage:
#   ./scripts/run.sh --synthetic-test
#   ./scripts/run.sh --dem terrain.tif
#   ./scripts/run.sh --gui
# =============================================================================

set -e

# Colors
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

# Parse arguments
show_help() {
    echo -e "${BLUE}PyDebFlow - Mass Flow Simulation Tool${NC}"
    echo
    echo "Usage: ./scripts/run.sh [OPTIONS]"
    echo
    echo "Quick Commands:"
    echo "  --synthetic-test    Run quick demo with synthetic terrain"
    echo "  --gui               Launch the graphical interface"
    echo "  --dem FILE          Run simulation on a DEM file"
    echo "  --help              Show this help message"
    echo
    echo "Examples:"
    echo "  ./scripts/run.sh --synthetic-test"
    echo "  ./scripts/run.sh --dem samples/sample_dem.asc --t-end 60 --animate-3d"
    echo "  ./scripts/run.sh --gui"
    echo
    echo "All other arguments are passed to run_simulation.py"
}

case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --gui)
        echo -e "${GREEN}Launching PyDebFlow GUI...${NC}"
        python main.py
        ;;
    --synthetic-test)
        echo -e "${GREEN}Running synthetic test simulation...${NC}"
        python run_simulation.py --synthetic-test "${@:2}"
        ;;
    --dem)
        if [ -z "${2:-}" ]; then
            echo "Error: --dem requires a file path"
            exit 1
        fi
        echo -e "${GREEN}Running DEM simulation: $2${NC}"
        python run_simulation.py --dem-file "${@:2}"
        ;;
    "")
        show_help
        ;;
    *)
        # Pass all arguments to run_simulation.py
        python run_simulation.py "$@"
        ;;
esac
