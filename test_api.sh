#!/bin/bash
# Rhône Risk Policy Analysis API - Test Script
# Run this script to verify the API is working correctly

API_URL="${API_URL:-http://localhost:8000}"

echo "=============================================="
echo "Rhône Risk Policy Analysis API - Test Suite"
echo "=============================================="
echo ""
echo "Target: $API_URL"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo "1. Testing Health Check..."
HEALTH=$(curl -s "$API_URL/health")
if echo "$HEALTH" | grep -q '"status":"healthy"'; then
    echo -e "   ${GREEN}✓ Health check passed${NC}"
    echo "   Response: $HEALTH"
else
    echo -e "   ${RED}✗ Health check failed${NC}"
    echo "   Response: $HEALTH"
fi
echo ""

# Test 2: Root Endpoint
echo "2. Testing Root Endpoint..."
ROOT=$(curl -s "$API_URL/")
if echo "$ROOT" | grep -q '"status":"operational"'; then
    echo -e "   ${GREEN}✓ Root endpoint passed${NC}"
else
    echo -e "   ${RED}✗ Root endpoint failed${NC}"
fi
echo ""

# Test 3: Webhook Test Endpoint
echo "3. Testing Webhook Connectivity..."
WEBHOOK_TEST=$(curl -s -X POST "$API_URL/webhook/test")
if echo "$WEBHOOK_TEST" | grep -q '"status":"connected"'; then
    echo -e "   ${GREEN}✓ Webhook endpoint reachable${NC}"

    # Check API key configuration
    if echo "$WEBHOOK_TEST" | grep -q '"anthropic_configured":true'; then
        echo -e "   ${GREEN}✓ Anthropic API key configured${NC}"
    else
        echo -e "   ${YELLOW}⚠ Anthropic API key NOT configured${NC}"
        echo "     Add ANTHROPIC_API_KEY to .env file for live analysis"
    fi
else
    echo -e "   ${RED}✗ Webhook test failed${NC}"
fi
echo ""

# Test 4: API Documentation
echo "4. Testing API Documentation..."
DOCS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/docs")
if [ "$DOCS" = "200" ]; then
    echo -e "   ${GREEN}✓ API docs available at $API_URL/docs${NC}"
else
    echo -e "   ${RED}✗ API docs not accessible${NC}"
fi
echo ""

# Test 5: Analysis List Endpoint
echo "5. Testing Analysis List..."
ANALYSIS_LIST=$(curl -s "$API_URL/analysis/")
if echo "$ANALYSIS_LIST" | grep -q '"analyses"'; then
    echo -e "   ${GREEN}✓ Analysis list endpoint working${NC}"
else
    echo -e "   ${RED}✗ Analysis list failed${NC}"
fi
echo ""

echo "=============================================="
echo "Test Summary"
echo "=============================================="
echo ""
echo "API is running at: $API_URL"
echo "Documentation: $API_URL/docs"
echo ""
echo "Next Steps:"
echo "  1. Configure ANTHROPIC_API_KEY in .env"
echo "  2. Upload a test policy PDF via POST /analysis/upload"
echo "  3. Check analysis status via GET /analysis/{id}/status"
echo ""
