"""
OWASP Top 10 2021 - A03: Injection Tests

Tests for injection vulnerabilities:
- SQL Injection (SQLi)
- NoSQL Injection
- Command Injection
- LDAP Injection
- XPath Injection
- Expression Language Injection
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.main import app
from app.core.security import create_access_token, hash_password
from app.database.models import User, ScrapedContent
from app.database.connection import get_db


class TestInjectionVulnerabilities:
    """Test suite for A03: Injection"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)

    @pytest.fixture
    def auth_token(self, db: Session):
        """Create authenticated user and return token"""
        user = User(
            email="injection@test.com",
            password_hash=hash_password("Test123!"),
            full_name="Injection Test",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token({"sub": user.email, "user_id": user.id})
        return token, user

    def test_sql_injection_in_search(self, client, auth_token):
        """Test SQL injection prevention in search endpoints"""
        token, user = auth_token
        headers = {"Authorization": f"Bearer {token}"}

        # Common SQL injection payloads
        sql_injections = [
            "' OR '1'='1",
            "'; DROP TABLE users--",
            "' UNION SELECT * FROM users--",
            "admin'--",
            "' OR 1=1--",
            "' OR 'x'='x",
            "1' AND '1' = '1",
            "1' AND '1' = '2' UNION SELECT * FROM users--"
        ]

        for payload in sql_injections:
            # Test search endpoint (if exists)
            response = client.get(
                f"/api/search?q={payload}",
                headers=headers
            )

            # Should not execute SQL, should either:
            # 1. Return empty results (safe handling)
            # 2. Return 400 (rejected)
            # 3. Return 422 (validation error)
            # Never 500 (server error from SQL injection)
            assert response.status_code in [200, 400, 404, 422]

            if response.status_code == 200:
                # If successful, should be safe results, not error
                data = response.json()
                # Should not contain SQL error messages
                response_text = str(data).lower()
                assert "syntax error" not in response_text
                assert "sql" not in response_text
                assert "postgresql" not in response_text

    def test_sql_injection_in_user_registration(self, client):
        """Test SQL injection prevention in registration"""
        sql_payloads = {
            "email": "test' OR '1'='1'@test.com",
            "password": "Test123!",
            "full_name": "'; DROP TABLE users--"
        }

        response = client.post("/api/auth/register", json=sql_payloads)

        # Should handle gracefully, not execute SQL
        assert response.status_code in [201, 400, 422]

    def test_sql_injection_in_login(self, client):
        """Test SQL injection prevention in authentication"""
        # Try SQL injection in email field
        response = client.post(
            "/api/auth/token",
            data={
                "username": "admin' OR '1'='1'--",
                "password": "anything"
            }
        )

        # Should reject, not bypass authentication
        assert response.status_code == 401

        # Try in password field
        response = client.post(
            "/api/auth/token",
            data={
                "username": "admin@test.com",
                "password": "' OR '1'='1'--"
            }
        )

        assert response.status_code == 401

    def test_sql_injection_in_filter_parameters(self, client, auth_token, db):
        """Test SQL injection in query parameters and filters"""
        token, user = auth_token
        headers = {"Authorization": f"Bearer {token}"}

        # Create test content
        content = ScrapedContent(
            source="Test Source",
            source_url="https://test.com/article1",
            title="Test Article",
            content="Test content",
            difficulty_score=3.0
        )
        db.add(content)
        db.commit()

        # Try SQL injection in filter parameters
        injection_params = [
            {"source": "Test' OR '1'='1"},
            {"difficulty_min": "1' OR '1'='1"},
            {"category": "'; DROP TABLE scraped_content--"},
        ]

        for params in injection_params:
            response = client.get("/api/content", params=params, headers=headers)

            # Should handle safely
            assert response.status_code in [200, 400, 422]

            if response.status_code == 200:
                # Should not show error messages
                assert "error" not in response.text.lower() or \
                       "sql" not in response.text.lower()

    def test_command_injection_prevention(self, client, auth_token):
        """Test that system commands cannot be injected"""
        token, user = auth_token
        headers = {"Authorization": f"Bearer {token}"}

        # Command injection payloads
        command_injections = [
            "; ls -la",
            "| cat /etc/passwd",
            "& whoami",
            "`id`",
            "$(cat /etc/passwd)",
            "; rm -rf /",
        ]

        # Test in various inputs
        for payload in command_injections:
            # If there's a file upload or processing endpoint
            response = client.get(
                f"/api/content?search={payload}",
                headers=headers
            )

            # Should not execute commands
            assert response.status_code in [200, 400, 404, 422]

            if response.status_code == 200:
                response_text = response.text.lower()
                # Should not contain command output
                assert "root:" not in response_text  # /etc/passwd
                assert "uid=" not in response_text   # id command
                assert "total" not in response_text[:20]  # ls output

    def test_nosql_injection_in_json_filters(self, client, auth_token):
        """Test NoSQL injection prevention in JSON fields"""
        token, user = auth_token
        headers = {"Authorization": f"Bearer {token}"}

        # NoSQL injection payloads (MongoDB-style)
        nosql_payloads = [
            {"$ne": None},
            {"$gt": ""},
            {"$regex": ".*"},
            {"$where": "1==1"},
        ]

        for payload in nosql_payloads:
            response = client.get(
                "/api/content",
                params={"tags": str(payload)},
                headers=headers
            )

            # Should handle safely
            assert response.status_code in [200, 400, 422]

    def test_xpath_injection_prevention(self, client):
        """Test XPath injection prevention"""
        xpath_payloads = [
            "' or '1'='1",
            "' or ''='",
            "x' or 1=1 or 'x'='y",
        ]

        for payload in xpath_payloads:
            response = client.get(f"/api/search?q={payload}")

            # Should not expose XML/XPath errors
            assert response.status_code != 500

    def test_orm_properly_parameterizes_queries(self, db: Session):
        """Test that SQLAlchemy ORM uses parameterized queries"""
        # This test verifies ORM usage rather than raw SQL

        # Safe ORM query
        user = db.query(User).filter(User.email == "test' OR '1'='1").first()
        assert user is None  # Should safely return None, not all users

        # Verify that ORM escapes special characters
        test_user = User(
            email="sql'injection@test.com",
            password_hash=hash_password("Test123!"),
            full_name="SQL'; DROP TABLE users--",
            is_active=True
        )
        db.add(test_user)
        db.commit()

        # Should store safely without executing SQL
        retrieved = db.query(User).filter(
            User.email == "sql'injection@test.com"
        ).first()
        assert retrieved is not None
        assert retrieved.full_name == "SQL'; DROP TABLE users--"

        # Clean up
        db.delete(test_user)
        db.commit()

    def test_raw_sql_uses_parameters(self, db: Session):
        """Test that any raw SQL uses proper parameterization"""
        # If raw SQL is used, it should use parameters

        # UNSAFE (this is what we're testing AGAINST):
        # db.execute(f"SELECT * FROM users WHERE email = '{email}'")

        # SAFE (this is what should be used):
        email = "test'; DROP TABLE users--"
        result = db.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": email}
        )

        # Should safely handle without SQL injection
        users = result.fetchall()
        # Should not execute the DROP TABLE

    def test_html_input_sanitization(self, client, auth_token):
        """Test that HTML/script tags are sanitized in user input"""
        token, user = auth_token
        headers = {"Authorization": f"Bearer {token}"}

        # XSS payloads in user inputs
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg/onload=alert('XSS')>",
        ]

        for payload in xss_payloads:
            response = client.put(
                "/api/auth/me",
                params={"full_name": payload},
                headers=headers
            )

            if response.status_code == 200:
                # Get user data
                user_response = client.get("/api/auth/me", headers=headers)
                data = user_response.json()

                # Script tags should be escaped or removed
                full_name = data.get("full_name", "")
                assert "<script>" not in full_name.lower()
                assert "onerror=" not in full_name.lower()

    def test_template_injection_prevention(self, client):
        """Test that template injection is prevented"""
        # Template injection payloads (Jinja2-style)
        template_injections = [
            "{{7*7}}",
            "{{config}}",
            "{{''.__class__.__mro__[1].__subclasses__()}}",
            "${7*7}",
        ]

        for payload in template_injections:
            response = client.post(
                "/api/auth/register",
                json={
                    "email": f"{payload}@test.com",
                    "password": "Test123!",
                    "full_name": payload
                }
            )

            if response.status_code in [200, 201]:
                # Template should not be executed
                assert "49" not in response.text  # 7*7 = 49
                assert "config" not in response.json().values()

    def test_expression_language_injection_prevention(self, client):
        """Test EL injection prevention"""
        el_payloads = [
            "${7*7}",
            "#{7*7}",
            "*{7*7}",
        ]

        for payload in el_payloads:
            response = client.get(f"/api/search?q={payload}")

            if response.status_code == 200:
                # Expression should not be evaluated
                assert "49" not in response.text
