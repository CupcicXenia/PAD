#!/bin/bash

echo "=== RUNNING UNIT TESTS ==="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to run tests
run_test() {
    SERVICE=$1
    echo -e "\n${YELLOW}Testing $SERVICE...${NC}"
    
    cd services/$SERVICE
    python test_app.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $SERVICE tests passed${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ $SERVICE tests failed${NC}"
        ((FAILED++))
    fi
    
    cd ../..
}

# Run all tests
run_test "hotel-search-service"
run_test "frontend-service"

# Summary
echo -e "\n${GREEN}=== TEST SUMMARY ===${NC}"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed!${NC}"
    exit 1
fi

