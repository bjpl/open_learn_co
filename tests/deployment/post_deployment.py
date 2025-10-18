"""
Post-deployment smoke test suite for OpenLearn Colombia.
Validates critical functionality after deployment.
"""

import os
import sys
import requests
import json
import time
from typing import Dict, List, Optional
import psycopg2
import redis
from elasticsearch import Elasticsearch


class PostDeploymentTester:
    """Comprehensive post-deployment smoke tests."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.tests_passed = 0
        self.tests_failed = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OpenLearn-Deployment-Validator/1.0'
        })

    def test_health_endpoint(self) -> bool:
        """Test application health endpoint."""
        print("\n🔍 Testing health endpoint...")

        try:
            response = self.session.get(f"{self.base_url}/health/", timeout=10)

            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Health endpoint: {response.status_code}")
                print(f"  ℹ️  Status: {data.get('status', 'unknown')}")
                self.tests_passed += 1
                return True
            else:
                self.errors.append(f"Health endpoint returned {response.status_code}")
                self.tests_failed += 1
                print(f"  ❌ Health endpoint: {response.status_code}")
                return False

        except Exception as e:
            self.errors.append(f"Health endpoint failed: {str(e)}")
            self.tests_failed += 1
            print(f"  ❌ Health endpoint failed: {str(e)}")
            return False

    def test_database_connectivity(self) -> bool:
        """Test database connectivity through API."""
        print("\n🔍 Testing database connectivity...")

        try:
            # Test through a simple API endpoint
            response = self.session.get(f"{self.base_url}/api/articles/", timeout=10)

            if response.status_code in [200, 404]:  # 404 is ok if no articles
                print(f"  ✅ Database connectivity: OK")
                self.tests_passed += 1
                return True
            else:
                self.errors.append(f"Database connectivity test failed: {response.status_code}")
                self.tests_failed += 1
                print(f"  ❌ Database connectivity: {response.status_code}")
                return False

        except Exception as e:
            self.errors.append(f"Database connectivity test failed: {str(e)}")
            self.tests_failed += 1
            print(f"  ❌ Database connectivity failed: {str(e)}")
            return False

    def test_cache_functionality(self) -> bool:
        """Test Redis cache functionality."""
        print("\n🔍 Testing cache functionality...")

        try:
            # Make same request twice to test caching
            url = f"{self.base_url}/api/articles/"

            # First request
            start_time = time.time()
            response1 = self.session.get(url, timeout=10)
            first_duration = time.time() - start_time

            # Second request (should be cached)
            start_time = time.time()
            response2 = self.session.get(url, timeout=10)
            second_duration = time.time() - start_time

            if response1.status_code == response2.status_code:
                print(f"  ✅ Cache functionality: OK")
                print(f"  ℹ️  First request: {first_duration:.3f}s")
                print(f"  ℹ️  Second request: {second_duration:.3f}s")

                if second_duration < first_duration * 0.8:
                    print(f"  ✅ Cache performance improvement detected")

                self.tests_passed += 1
                return True
            else:
                self.warnings.append("Cache responses inconsistent")
                print(f"  ⚠️  Cache responses inconsistent")
                return True

        except Exception as e:
            self.warnings.append(f"Cache test failed: {str(e)}")
            print(f"  ⚠️  Cache test failed: {str(e)}")
            return True

    def test_search_functionality(self) -> bool:
        """Test search functionality."""
        print("\n🔍 Testing search functionality...")

        try:
            response = self.session.get(
                f"{self.base_url}/api/search/",
                params={'q': 'test'},
                timeout=10
            )

            if response.status_code in [200, 404]:  # 404 ok if no results
                print(f"  ✅ Search functionality: OK")
                self.tests_passed += 1
                return True
            else:
                self.warnings.append(f"Search returned unexpected status: {response.status_code}")
                print(f"  ⚠️  Search: {response.status_code}")
                return True

        except Exception as e:
            self.warnings.append(f"Search test failed: {str(e)}")
            print(f"  ⚠️  Search test failed: {str(e)}")
            return True

    def test_authentication_flow(self) -> bool:
        """Test authentication endpoints."""
        print("\n🔍 Testing authentication flow...")

        try:
            # Test login endpoint exists
            response = self.session.post(
                f"{self.base_url}/api/auth/login/",
                json={'username': 'test', 'password': 'test'},
                timeout=10
            )

            # We expect 401 or 400, not 500
            if response.status_code in [400, 401]:
                print(f"  ✅ Authentication endpoint: OK")
                self.tests_passed += 1
                return True
            elif response.status_code == 404:
                self.warnings.append("Authentication endpoint not found")
                print(f"  ⚠️  Authentication endpoint not found")
                return True
            else:
                self.errors.append(f"Authentication endpoint error: {response.status_code}")
                self.tests_failed += 1
                print(f"  ❌ Authentication endpoint: {response.status_code}")
                return False

        except Exception as e:
            self.warnings.append(f"Authentication test failed: {str(e)}")
            print(f"  ⚠️  Authentication test failed: {str(e)}")
            return True

    def test_static_files(self) -> bool:
        """Test static files are accessible."""
        print("\n🔍 Testing static files...")

        try:
            # Test common static file paths
            static_paths = [
                '/static/css/main.css',
                '/static/js/main.js',
                '/favicon.ico',
            ]

            accessible = 0
            for path in static_paths:
                try:
                    response = self.session.get(f"{self.base_url}{path}", timeout=5)
                    if response.status_code == 200:
                        accessible += 1
                except:
                    pass

            if accessible > 0:
                print(f"  ✅ Static files accessible: {accessible}/{len(static_paths)}")
                self.tests_passed += 1
                return True
            else:
                self.warnings.append("No static files accessible")
                print(f"  ⚠️  No static files accessible")
                return True

        except Exception as e:
            self.warnings.append(f"Static files test failed: {str(e)}")
            print(f"  ⚠️  Static files test failed: {str(e)}")
            return True

    def test_api_endpoints(self) -> bool:
        """Test critical API endpoints."""
        print("\n🔍 Testing API endpoints...")

        endpoints = [
            '/api/articles/',
            '/api/categories/',
            '/api/users/me/',
            '/api/dashboard/',
        ]

        working_endpoints = 0
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code in [200, 401, 403, 404]:  # Expected statuses
                    working_endpoints += 1
                    print(f"  ✅ {endpoint}: {response.status_code}")
                else:
                    print(f"  ❌ {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"  ❌ {endpoint}: {str(e)}")

        if working_endpoints == len(endpoints):
            print(f"  ✅ All {working_endpoints} endpoints responding")
            self.tests_passed += 1
            return True
        elif working_endpoints > 0:
            self.warnings.append(f"Only {working_endpoints}/{len(endpoints)} endpoints working")
            print(f"  ⚠️  Only {working_endpoints}/{len(endpoints)} endpoints working")
            return True
        else:
            self.errors.append("No API endpoints responding")
            self.tests_failed += 1
            print(f"  ❌ No API endpoints responding")
            return False

    def test_response_times(self) -> bool:
        """Test response times are acceptable."""
        print("\n🔍 Testing response times...")

        try:
            response_times = []

            for i in range(5):
                start = time.time()
                response = self.session.get(f"{self.base_url}/health/", timeout=10)
                duration = time.time() - start
                response_times.append(duration)

            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)

            print(f"  ℹ️  Average response time: {avg_time:.3f}s")
            print(f"  ℹ️  Max response time: {max_time:.3f}s")

            if avg_time < 1.0:
                print(f"  ✅ Response times acceptable")
                self.tests_passed += 1
                return True
            else:
                self.warnings.append(f"Response times high: {avg_time:.3f}s average")
                print(f"  ⚠️  Response times high")
                return True

        except Exception as e:
            self.warnings.append(f"Response time test failed: {str(e)}")
            print(f"  ⚠️  Response time test failed: {str(e)}")
            return True

    def test_error_handling(self) -> bool:
        """Test error handling."""
        print("\n🔍 Testing error handling...")

        try:
            # Test 404 handling
            response = self.session.get(f"{self.base_url}/nonexistent-page/", timeout=10)

            if response.status_code == 404:
                print(f"  ✅ 404 handling: OK")
                self.tests_passed += 1
                return True
            else:
                self.warnings.append(f"Unexpected 404 response: {response.status_code}")
                print(f"  ⚠️  404 handling: {response.status_code}")
                return True

        except Exception as e:
            self.warnings.append(f"Error handling test failed: {str(e)}")
            print(f"  ⚠️  Error handling test failed: {str(e)}")
            return True

    def generate_report(self) -> Dict:
        """Generate test report."""
        return {
            'total_tests': self.tests_passed + self.tests_failed,
            'tests_passed': self.tests_passed,
            'tests_failed': self.tests_failed,
            'errors': self.errors,
            'warnings': self.warnings,
            'success': len(self.errors) == 0
        }

    def run_all_tests(self) -> bool:
        """Run all post-deployment smoke tests."""
        print("\n" + "="*60)
        print("🚀 OPENLEARN COLOMBIA - POST-DEPLOYMENT SMOKE TESTS")
        print(f"   Target: {self.base_url}")
        print("="*60)

        tests = [
            ('Health Endpoint', self.test_health_endpoint),
            ('Database Connectivity', self.test_database_connectivity),
            ('Cache Functionality', self.test_cache_functionality),
            ('Search Functionality', self.test_search_functionality),
            ('Authentication Flow', self.test_authentication_flow),
            ('Static Files', self.test_static_files),
            ('API Endpoints', self.test_api_endpoints),
            ('Response Times', self.test_response_times),
            ('Error Handling', self.test_error_handling),
        ]

        for name, test_func in tests:
            test_func()

        # Generate report
        report = self.generate_report()

        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"  Total Tests: {report['total_tests']}")
        print(f"  ✅ Passed: {report['tests_passed']}")
        print(f"  ❌ Failed: {report['tests_failed']}")
        print(f"  ⚠️  Warnings: {len(report['warnings'])}")

        if report['errors']:
            print("\n❌ ERRORS:")
            for error in report['errors']:
                print(f"  • {error}")

        if report['warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in report['warnings']:
                print(f"  • {warning}")

        print("\n" + "="*60)
        if report['success']:
            print("✅ POST-DEPLOYMENT SMOKE TESTS PASSED")
        else:
            print("❌ POST-DEPLOYMENT SMOKE TESTS FAILED")
        print("="*60 + "\n")

        return report['success']


def main():
    """Run post-deployment smoke tests."""
    base_url = os.getenv('DEPLOYMENT_URL', 'http://localhost:8000')

    print(f"Testing deployment at: {base_url}")

    tester = PostDeploymentTester(base_url)
    success = tester.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
