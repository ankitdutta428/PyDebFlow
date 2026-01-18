#!/bin/bash
# =============================================================================
# test.sh - PyDebFlow Test Runner Script for Linux/macOS
# =============================================================================
# Runs all tests or specific test modules.
#
# Usage:
#   ./scripts/test.sh              # Run all tests
#   ./scripts/test.sh --coverage   # Run with coverage report
#   ./scripts/test.sh --unit       # Run unit tests only
#   ./scripts/test.sh --module rheology  # Run specific module test
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
echo -e "${BLUE}║               PyDebFlow - Test Runner                         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo

show_help() {
    echo "Usage: ./scripts/test.sh [OPTIONS]"
    echo
    echo "Options:"
    echo "  --all, -a          Run all tests (default)"
    echo "  --unit             Run pytest unit tests only"
    echo "  --integration      Run integration tests"
    echo "  --component        Run built-in component tests"
    echo "  --coverage, -c     Run with coverage report"
    echo "  --verbose, -v      Verbose output"
    echo "  --module NAME      Run specific test module (rheology, solver, integration)"
    echo "  --help, -h         Show this help message"
    echo
    echo "Examples:"
    echo "  ./scripts/test.sh"
    echo "  ./scripts/test.sh --coverage"
    echo "  ./scripts/test.sh --module rheology"
    echo "  ./scripts/test.sh --component"
}

# Default options
RUN_PYTEST=true
RUN_COMPONENT=false
COVERAGE=false
VERBOSE=""
MODULE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --all|-a)
            RUN_PYTEST=true
            RUN_COMPONENT=true
            shift
            ;;
        --unit)
            RUN_PYTEST=true
            RUN_COMPONENT=false
            shift
            ;;
        --component)
            RUN_PYTEST=false
            RUN_COMPONENT=true
            shift
            ;;
        --integration)
            MODULE="integration"
            shift
            ;;
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE="-v"
            shift
            ;;
        --module)
            MODULE="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Run pytest
if [ "$RUN_PYTEST" = true ]; then
    echo -e "${YELLOW}Running pytest...${NC}"
    echo

    PYTEST_ARGS="tests/ $VERBOSE"
    
    if [ -n "$MODULE" ]; then
        PYTEST_ARGS="tests/test_${MODULE}.py $VERBOSE"
    fi

    if [ "$COVERAGE" = true ]; then
        python -m pytest $PYTEST_ARGS --cov=src --cov-report=html --cov-report=term
        echo
        echo -e "${GREEN}Coverage report generated: htmlcov/index.html${NC}"
    else
        python -m pytest $PYTEST_ARGS
    fi
    
    echo
fi

# Run built-in component tests
if [ "$RUN_COMPONENT" = true ]; then
    echo -e "${YELLOW}Running built-in component tests...${NC}"
    echo
    python run_simulation.py --test-all
    echo
fi

echo -e "${GREEN}✓ All tests completed!${NC}"
