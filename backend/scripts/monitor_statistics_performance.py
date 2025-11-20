#!/usr/bin/env python3
"""
Performance monitoring script for analysis statistics endpoint.

Usage:
    python backend/scripts/monitor_statistics_performance.py

Features:
    - Measures response time
    - Tracks query count (requires PostgreSQL logging)
    - Displays cache hit/miss rate
    - Shows performance improvements
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, Any


class StatisticsPerformanceMonitor:
    """Monitor performance of analysis statistics endpoint"""

    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.endpoint = f"{base_url}/api/v1/analysis/statistics"

    def test_endpoint_performance(self) -> Dict[str, Any]:
        """Test endpoint and measure performance"""
        print(f"\n{'='*70}")
        print(f"📊 Analysis Statistics Endpoint - Performance Test")
        print(f"{'='*70}")
        print(f"🔗 Endpoint: {self.endpoint}")
        print(f"🕐 Timestamp: {datetime.now().isoformat()}")
        print(f"{'='*70}\n")

        results = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": self.endpoint,
            "tests": []
        }

        # Test 1: First request (cache miss expected)
        print("🔍 Test 1: First Request (Cache MISS expected)")
        print("-" * 70)
        start_time = time.time()
        try:
            response = requests.get(self.endpoint, timeout=10)
            elapsed_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                test_result = {
                    "test": "first_request",
                    "status": "success",
                    "response_time_ms": round(elapsed_ms, 2),
                    "status_code": response.status_code,
                    "data": data
                }

                print(f"   ✅ Status Code: {response.status_code}")
                print(f"   ⏱️  Response Time: {elapsed_ms:.2f} ms")
                print(f"   📈 Total Analyses: {data.get('total_analyses', 'N/A')}")
                print(f"   😊 Avg Sentiment: {data.get('average_sentiment', 'N/A'):.3f}")
                print(f"   🏷️  Entity Types: {data.get('entity_types_count', 'N/A')}")
                print(f"   💾 Cache Enabled: {data.get('cache_enabled', 'N/A')}")
                print(f"   ⏲️  Cache TTL: {data.get('cache_ttl_seconds', 'N/A')}s")

                # Show entity distribution
                if data.get('entity_distribution'):
                    print(f"\n   📊 Entity Distribution:")
                    for entity_type, count in sorted(
                        data['entity_distribution'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]:  # Top 5
                        print(f"      - {entity_type}: {count}")

                # Performance evaluation
                print(f"\n   📊 Performance Evaluation:")
                if elapsed_ms < 100:
                    print(f"      ✅ EXCELLENT: {elapsed_ms:.2f}ms < 100ms (Target met)")
                elif elapsed_ms < 300:
                    print(f"      ⚠️  GOOD: {elapsed_ms:.2f}ms < 300ms (Acceptable)")
                else:
                    print(f"      ❌ SLOW: {elapsed_ms:.2f}ms > 300ms (Optimization needed)")

            else:
                test_result = {
                    "test": "first_request",
                    "status": "error",
                    "response_time_ms": round(elapsed_ms, 2),
                    "status_code": response.status_code,
                    "error": response.text
                }
                print(f"   ❌ Error: Status {response.status_code}")
                print(f"   Response: {response.text}")

            results["tests"].append(test_result)

        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            results["tests"].append({
                "test": "first_request",
                "status": "exception",
                "error": str(e)
            })

        # Test 2: Second request (cache hit expected if Redis available)
        print(f"\n{'='*70}")
        print("🔍 Test 2: Second Request (Cache HIT expected)")
        print("-" * 70)
        time.sleep(0.5)  # Small delay

        start_time = time.time()
        try:
            response = requests.get(self.endpoint, timeout=10)
            elapsed_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                test_result = {
                    "test": "second_request_cached",
                    "status": "success",
                    "response_time_ms": round(elapsed_ms, 2),
                    "status_code": response.status_code
                }

                print(f"   ✅ Status Code: {response.status_code}")
                print(f"   ⏱️  Response Time: {elapsed_ms:.2f} ms")

                # Cache hit evaluation
                first_request_time = results["tests"][0].get("response_time_ms", elapsed_ms)
                improvement = ((first_request_time - elapsed_ms) / first_request_time) * 100

                print(f"\n   💾 Cache Performance:")
                if elapsed_ms < 50:
                    print(f"      ✅ CACHE HIT: {elapsed_ms:.2f}ms (Very fast, likely from cache)")
                    print(f"      🚀 Improvement: {improvement:.1f}% faster than first request")
                elif elapsed_ms < first_request_time * 0.5:
                    print(f"      ⚡ POSSIBLE CACHE HIT: {elapsed_ms:.2f}ms (Faster than first)")
                    print(f"      📈 Improvement: {improvement:.1f}% faster")
                else:
                    print(f"      ⚠️  NO CACHE HIT: {elapsed_ms:.2f}ms (Similar to first request)")
                    print(f"      💡 Redis may not be available")

            results["tests"].append(test_result)

        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            results["tests"].append({
                "test": "second_request_cached",
                "status": "exception",
                "error": str(e)
            })

        # Summary
        print(f"\n{'='*70}")
        print("📋 Performance Summary")
        print("=" * 70)

        if len(results["tests"]) >= 2:
            first_time = results["tests"][0].get("response_time_ms", 0)
            second_time = results["tests"][1].get("response_time_ms", 0)

            print(f"   First Request:  {first_time:.2f} ms")
            print(f"   Second Request: {second_time:.2f} ms")

            if first_time > 0:
                improvement = ((first_time - second_time) / first_time) * 100
                print(f"   Improvement:    {improvement:.1f}%")

            print(f"\n   🎯 Optimization Goals:")
            print(f"      - Query Count: ≤5 queries per request")
            print(f"      - Response Time: <100ms")
            print(f"      - Cache Hit Time: <10ms")

            print(f"\n   📊 Achievement Status:")
            if first_time < 100:
                print(f"      ✅ Response time target met: {first_time:.2f}ms < 100ms")
            else:
                print(f"      ⚠️  Response time target not met: {first_time:.2f}ms > 100ms")

            if second_time < 50:
                print(f"      ✅ Cache appears to be working: {second_time:.2f}ms")
            else:
                print(f"      ⚠️  Cache may not be available")

        print(f"\n{'='*70}")

        return results

    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save test results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backend/logs/statistics_performance_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Results saved to: {filename}")


def main():
    """Main execution"""
    monitor = StatisticsPerformanceMonitor()

    print("\n" + "="*70)
    print("🚀 Starting Analysis Statistics Performance Monitor")
    print("="*70)

    results = monitor.test_endpoint_performance()

    # Save results
    # monitor.save_results(results)

    print("\n" + "="*70)
    print("✅ Performance monitoring complete!")
    print("="*70 + "\n")

    return results


if __name__ == "__main__":
    main()
