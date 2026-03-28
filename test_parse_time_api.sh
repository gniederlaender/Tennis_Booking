#!/bin/bash
# Test script for /api/parse-time endpoint
# Make sure the Flask app is running on port 5001

BASE_URL="http://localhost:5001"

echo "=========================================="
echo "Testing /api/parse-time endpoint"
echo "=========================================="
echo ""

# Test 1: German - tomorrow morning
echo "Test 1: morgen früh"
curl -s -X POST "$BASE_URL/api/parse-time" \
  -H "Content-Type: application/json" \
  -d '{"query": "morgen früh"}' | python -m json.tool
echo ""
echo "---"
echo ""

# Test 2: German - between times
echo "Test 2: morgen zwischen 10 und 13"
curl -s -X POST "$BASE_URL/api/parse-time" \
  -H "Content-Type: application/json" \
  -d '{"query": "morgen zwischen 10 und 13"}' | python -m json.tool
echo ""
echo "---"
echo ""

# Test 3: English - next Sunday afternoon
echo "Test 3: next Sunday afternoon"
curl -s -X POST "$BASE_URL/api/parse-time" \
  -H "Content-Type: application/json" \
  -d '{"query": "next Sunday afternoon"}' | python -m json.tool
echo ""
echo "---"
echo ""

# Test 4: Weekend (should return 2 windows)
echo "Test 4: am Wochenende"
curl -s -X POST "$BASE_URL/api/parse-time" \
  -H "Content-Type: application/json" \
  -d '{"query": "am Wochenende"}' | python -m json.tool
echo ""
echo "---"
echo ""

# Test 5: Typo correction
echo "Test 5: morgrn nachmitag (with typos)"
curl -s -X POST "$BASE_URL/api/parse-time" \
  -H "Content-Type: application/json" \
  -d '{"query": "morgrn nachmitag"}' | python -m json.tool
echo ""
echo "---"
echo ""

# Test 6: ASAP
echo "Test 6: asap"
curl -s -X POST "$BASE_URL/api/parse-time" \
  -H "Content-Type: application/json" \
  -d '{"query": "asap"}' | python -m json.tool
echo ""
echo "---"
echo ""

# Test 7: Empty query (should fail)
echo "Test 7: Empty query (error test)"
curl -s -X POST "$BASE_URL/api/parse-time" \
  -H "Content-Type: application/json" \
  -d '{"query": ""}' | python -m json.tool
echo ""

echo "=========================================="
echo "Tests complete"
echo "=========================================="
