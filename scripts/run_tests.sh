#!/bin/bash
# Test runner script for AI Auto-Annotation Tool

set -e

echo "===================================="
echo "AI Auto-Annotation Tool - Test Runner"
echo "===================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse command line arguments
TEST_TYPE="${1:-all}"  # all, unit, integration, smoke
COVERAGE="${2:-true}"

# Function to print colored output
print_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1${NC}"
        exit 1
    fi
}

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install it with: pip install pytest pytest-cov pytest-asyncio"
    exit 1
fi

# Set test environment
export TESTING=true
export LOG_LEVEL=ERROR
export DATABASE_URL=sqlite:///:memory:

echo "Environment: TESTING=$TESTING"
echo "Test Type: $TEST_TYPE"
echo "Coverage: $COVERAGE"
echo

# Determine pytest options
PYTEST_OPTS="--verbose"

if [ "$COVERAGE" = "true" ]; then
    PYTEST_OPTS="$PYTEST_OPTS --cov=backend --cov=qwen3vl_d --cov-report=term-missing --cov-report=html"
fi

# Run tests based on type
case $TEST_TYPE in
    "unit")
        echo "Running unit tests..."
        pytest tests/unit/ $PYTEST_OPTS -m "unit or not integration"
        print_status "Unit tests completed"
        ;;
    "integration")
        echo "Running integration tests..."
        pytest tests/integration/ $PYTEST_OPTS -m "integration"
        print_status "Integration tests completed"
        ;;
    "smoke")
        echo "Running smoke tests..."
        pytest $PYTEST_OPTS -m "smoke"
        print_status "Smoke tests completed"
        ;;
    "quick")
        echo "Running quick tests (no slow tests)..."
        pytest $PYTEST_OPTS -m "not slow"
        print_status "Quick tests completed"
        ;;
    "all")
        echo "Running all tests..."
        pytest tests/ $PYTEST_OPTS
        print_status "All tests completed"
        ;;
    *)
        echo -e "${RED}Error: Unknown test type '$TEST_TYPE'${NC}"
        echo "Usage: $0 [all|unit|integration|smoke|quick] [true|false]"
        exit 1
        ;;
esac

echo
echo "===================================="
echo -e "${GREEN}Test run completed successfully!${NC}"
echo "===================================="

# Open coverage report if it exists
if [ "$COVERAGE" = "true" ] && [ -f "htmlcov/index.html" ]; then
    echo
    echo "Coverage report generated: htmlcov/index.html"

    # Optionally open in browser (uncomment if desired)
    # if command -v open &> /dev/null; then
    #     open htmlcov/index.html
    # elif command -v xdg-open &> /dev/null; then
    #     xdg-open htmlcov/index.html
    # fi
fi

exit 0
