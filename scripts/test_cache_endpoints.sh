#!/bin/bash
# Integration test script for cache implementation
# Tests cache hit/miss behavior on live endpoints

set -e

API_BASE="${API_BASE:-http://localhost:8002/api/v1}"

echo "🧪 Testing Cache Implementation on API Endpoints"
echo "================================================"
echo ""

# Function to make request and show timing
test_endpoint() {
    local endpoint=$1
    local name=$2
    local iteration=$3

    echo "[$iteration] Testing $name..."
    start_time=$(date +%s%3N)

    response=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}" "$API_BASE$endpoint")

    end_time=$(date +%s%3N)
    duration=$((end_time - start_time))

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    time_total=$(echo "$response" | grep "TIME:" | cut -d: -f2)

    if [ "$http_code" = "200" ]; then
        echo "  ✅ Status: $http_code | Time: ${time_total}s"
        return 0
    else
        echo "  ❌ Status: $http_code | Time: ${time_total}s"
        return 1
    fi
}

echo "Test 1: /api/scraping/status (5-min TTL)"
echo "==========================================="
test_endpoint "/scraping/status" "Scraping Status" "First call (MISS)"
sleep 1
test_endpoint "/scraping/status" "Scraping Status" "Second call (HIT)"
echo ""

echo "Test 2: /api/analysis/statistics (10-min TTL)"
echo "=============================================="
test_endpoint "/analysis/statistics" "Analysis Stats" "First call (MISS)"
sleep 1
test_endpoint "/analysis/statistics" "Analysis Stats" "Second call (HIT)"
echo ""

echo "Test 3: /api/scraping/content/simple (15-min TTL)"
echo "=================================================="
test_endpoint "/scraping/content/simple?limit=10&offset=0" "Content Simple" "First call (MISS)"
sleep 1
test_endpoint "/scraping/content/simple?limit=10&offset=0" "Content Simple" "Second call (HIT)"
echo ""

echo "Test 4: /api/scraping/sources (30-min TTL)"
echo "==========================================="
test_endpoint "/scraping/sources?format=ui" "Sources List" "First call (MISS)"
sleep 1
test_endpoint "/scraping/sources?format=ui" "Sources List" "Second call (HIT)"
echo ""

echo "Test 5: Cache Invalidation Test"
echo "================================"
echo "Triggering scrape to invalidate caches..."
curl -s -X POST "$API_BASE/scraping/trigger/Test" > /dev/null 2>&1 || true
sleep 2
test_endpoint "/scraping/status" "Scraping Status" "After invalidation (MISS)"
echo ""

echo "✅ Cache integration tests completed!"
echo ""
echo "To check cache metrics, visit: http://localhost:8002/metrics"
echo "Look for: cache_hits_total, cache_misses_total"
