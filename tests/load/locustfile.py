"""
Locust load testing configuration for OpenLearn Colombia.
Simulates 1000+ concurrent users testing critical endpoints.
"""

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner
import random
import json
import logging
from typing import Dict, List


# Sample data for testing
SEARCH_QUERIES = [
    'python', 'javascript', 'mathematics', 'science', 'history',
    'programming', 'data science', 'machine learning', 'web development',
    'database', 'algorithms', 'spanish', 'education', 'tutorial'
]

ARTICLE_IDS = list(range(1, 100))  # Will be updated with actual IDs


class OpenLearnUser(HttpUser):
    """Base user class for OpenLearn load testing."""

    # Wait between 1 and 3 seconds between tasks
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a user starts."""
        self.client.headers.update({
            'User-Agent': 'OpenLearn-LoadTest/1.0'
        })
        # Attempt to login
        self.login()

    def login(self):
        """Simulate user login."""
        response = self.client.post('/api/auth/login/', json={
            'username': f'testuser{random.randint(1, 1000)}',
            'password': 'testpassword'
        }, catch_response=True)

        if response.status_code == 200:
            try:
                data = response.json()
                self.token = data.get('token')
                self.client.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                response.success()
            except:
                response.failure("Failed to parse login response")
        elif response.status_code in [400, 401]:
            # Expected for test users
            response.success()
        else:
            response.failure(f"Unexpected status code: {response.status_code}")

    @task(5)
    def view_homepage(self):
        """Load homepage - highest frequency."""
        self.client.get('/', name='/homepage')

    @task(4)
    def browse_articles(self):
        """Browse articles list."""
        self.client.get('/api/articles/', name='/api/articles/')

    @task(3)
    def search_content(self):
        """Search for content."""
        query = random.choice(SEARCH_QUERIES)
        self.client.get(
            '/api/search/',
            params={'q': query},
            name='/api/search/?q=[query]'
        )

    @task(3)
    def view_article(self):
        """View a specific article."""
        article_id = random.choice(ARTICLE_IDS)
        self.client.get(
            f'/api/articles/{article_id}/',
            name='/api/articles/[id]/'
        )

    @task(2)
    def view_dashboard(self):
        """View user dashboard."""
        self.client.get('/api/dashboard/', name='/api/dashboard/')

    @task(2)
    def browse_categories(self):
        """Browse categories."""
        self.client.get('/api/categories/', name='/api/categories/')

    @task(1)
    def view_profile(self):
        """View user profile."""
        self.client.get('/api/users/me/', name='/api/users/me/')


class AuthenticationUser(HttpUser):
    """User focused on authentication flows."""

    wait_time = between(2, 5)
    weight = 2  # Lower weight than regular users

    @task(3)
    def login_attempt(self):
        """Attempt login."""
        self.client.post('/api/auth/login/', json={
            'username': f'user{random.randint(1, 1000)}',
            'password': 'password123'
        }, name='/api/auth/login/')

    @task(1)
    def logout_attempt(self):
        """Attempt logout."""
        self.client.post('/api/auth/logout/', name='/api/auth/logout/')

    @task(1)
    def register_attempt(self):
        """Attempt registration."""
        self.client.post('/api/auth/register/', json={
            'username': f'newuser{random.randint(1, 10000)}',
            'email': f'user{random.randint(1, 10000)}@example.com',
            'password': 'password123'
        }, name='/api/auth/register/')


class SearchHeavyUser(HttpUser):
    """User focused on search operations."""

    wait_time = between(1, 2)
    weight = 3

    @task(10)
    def search_multiple(self):
        """Perform multiple searches."""
        query = random.choice(SEARCH_QUERIES)
        self.client.get(
            '/api/search/',
            params={'q': query},
            name='/api/search/?q=[query]'
        )

    @task(2)
    def advanced_search(self):
        """Perform advanced search."""
        self.client.get(
            '/api/search/',
            params={
                'q': random.choice(SEARCH_QUERIES),
                'category': random.choice(['programming', 'math', 'science']),
                'difficulty': random.choice(['beginner', 'intermediate', 'advanced'])
            },
            name='/api/search/?q=[query]&filters'
        )


class DashboardUser(HttpUser):
    """User focused on dashboard operations."""

    wait_time = between(2, 4)
    weight = 2

    def on_start(self):
        """Login on start."""
        self.client.headers.update({
            'Authorization': 'Bearer test_token'
        })

    @task(5)
    def load_dashboard(self):
        """Load dashboard."""
        self.client.get('/api/dashboard/', name='/api/dashboard/')

    @task(3)
    def load_progress(self):
        """Load user progress."""
        self.client.get('/api/users/progress/', name='/api/users/progress/')

    @task(2)
    def load_recommendations(self):
        """Load recommendations."""
        self.client.get('/api/recommendations/', name='/api/recommendations/')

    @task(1)
    def load_analytics(self):
        """Load analytics."""
        self.client.get('/api/analytics/', name='/api/analytics/')


class ApiHeavyUser(HttpUser):
    """User focused on API operations."""

    wait_time = between(0.5, 1.5)
    weight = 2

    @task(4)
    def fetch_articles_batch(self):
        """Fetch articles in batches."""
        page = random.randint(1, 10)
        self.client.get(
            '/api/articles/',
            params={'page': page, 'page_size': 20},
            name='/api/articles/?page=[n]'
        )

    @task(3)
    def fetch_categories(self):
        """Fetch categories."""
        self.client.get('/api/categories/', name='/api/categories/')

    @task(2)
    def fetch_article_detail(self):
        """Fetch article details."""
        article_id = random.choice(ARTICLE_IDS)
        self.client.get(
            f'/api/articles/{article_id}/',
            name='/api/articles/[id]/'
        )

    @task(1)
    def fetch_related_articles(self):
        """Fetch related articles."""
        article_id = random.choice(ARTICLE_IDS)
        self.client.get(
            f'/api/articles/{article_id}/related/',
            name='/api/articles/[id]/related/'
        )


# Event hooks for reporting
@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Called when Locust is initialized."""
    if isinstance(environment.runner, MasterRunner):
        print("Locust master initialized")
    elif isinstance(environment.runner, WorkerRunner):
        print("Locust worker initialized")
    else:
        print("Locust standalone initialized")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("\n" + "="*60)
    print("🚀 OPENLEARN COLOMBIA - LOAD TEST STARTING")
    print("="*60)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count}")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    stats = environment.runner.stats

    print("\n" + "="*60)
    print("📊 LOAD TEST SUMMARY")
    print("="*60)
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failures: {stats.total.num_failures}")
    print(f"Failure rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min response time: {stats.total.min_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    print(f"p50 response time: {stats.total.get_response_time_percentile(0.5):.2f}ms")
    print(f"p95 response time: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"p99 response time: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    print("="*60)

    # Check if p95 meets target
    p95 = stats.total.get_response_time_percentile(0.95)
    if p95 < 500:
        print("✅ P95 RESPONSE TIME TARGET MET (<500ms)")
    else:
        print(f"❌ P95 RESPONSE TIME TARGET MISSED ({p95:.2f}ms)")

    print("="*60 + "\n")


# Custom load shape for ramping
from locust import LoadTestShape

class StepLoadShape(LoadTestShape):
    """
    A step load shape that ramps up users gradually.

    Step 1: 100 users for 2 minutes
    Step 2: 300 users for 2 minutes
    Step 3: 600 users for 2 minutes
    Step 4: 1000 users for 3 minutes
    Step 5: 500 users for 2 minutes (cool down)
    """

    step_time = 120  # 2 minutes per step
    step_load = 100
    spawn_rate = 10
    time_limit = 660  # 11 minutes total

    def tick(self):
        run_time = self.get_run_time()

        if run_time < self.time_limit:
            if run_time < 120:  # 0-2 min
                user_count = 100
            elif run_time < 240:  # 2-4 min
                user_count = 300
            elif run_time < 360:  # 4-6 min
                user_count = 600
            elif run_time < 540:  # 6-9 min
                user_count = 1000
            else:  # 9-11 min (cool down)
                user_count = 500

            return (user_count, self.spawn_rate)

        return None
