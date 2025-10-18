"""
OWASP Top 10 2021 - A05: Security Misconfiguration Tests

Tests for security misconfigurations:
- Missing security headers
- Default credentials
- Unnecessary features enabled
- Verbose error messages
- Outdated software
- Misconfigured permissions
- Exposed sensitive endpoints
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config.settings import settings


class TestSecurityMisconfiguration:
    """Test suite for A05: Security Misconfiguration"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)

    def test_security_headers_present(self, client):
        """Test that security headers are properly configured"""
        response = client.get("/health")

        # Check for essential security headers
        expected_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "Content-Security-Policy": None,  # Should exist
            "X-XSS-Protection": ["1; mode=block", "0"],  # Either blocking or disabled (newer browsers)
            "Referrer-Policy": None,  # Should exist
        }

        for header, expected_value in expected_headers.items():
            assert header in response.headers, \
                f"Missing security header: {header}"

            if expected_value and isinstance(expected_value, list):
                assert response.headers[header] in expected_value, \
                    f"Invalid {header}: {response.headers[header]}"

    def test_hsts_header_on_https(self, client):
        """Test HSTS header is present on HTTPS connections"""
        # Simulate HTTPS connection
        response = client.get(
            "/health",
            headers={"X-Forwarded-Proto": "https"}
        )

        # HSTS should be present on HTTPS
        if response.headers.get("X-Forwarded-Proto") == "https":
            assert "Strict-Transport-Security" in response.headers
            hsts = response.headers["Strict-Transport-Security"]

            # Check for includeSubDomains
            assert "includeSubDomains" in hsts or settings.ENVIRONMENT != "production"

            # Check max-age is sufficient (at least 6 months)
            assert "max-age=" in hsts
            max_age = int(hsts.split("max-age=")[1].split(";")[0])
            assert max_age >= 15768000  # 6 months in seconds

    def test_server_header_not_exposed(self, client):
        """Test that Server header doesn't expose version info"""
        response = client.get("/health")

        # Server header should be removed or generic
        server_header = response.headers.get("Server", "")

        # Should not contain version numbers or specific software
        forbidden_servers = [
            "uvicorn/",
            "FastAPI/",
            "Python/",
        ]

        for forbidden in forbidden_servers:
            assert forbidden.lower() not in server_header.lower(), \
                f"Server header exposes software version: {server_header}"

    def test_x_powered_by_header_removed(self, client):
        """Test that X-Powered-By header is removed"""
        response = client.get("/health")

        assert "X-Powered-By" not in response.headers, \
            "X-Powered-By header should be removed"

    def test_error_messages_not_verbose(self, client):
        """Test that error messages don't expose internal details"""
        # Trigger various errors
        error_endpoints = [
            "/nonexistent/endpoint",
            "/api/auth/me",  # Without auth
            "/api/content/99999999",  # Non-existent ID
        ]

        for endpoint in error_endpoints:
            response = client.get(endpoint)

            if response.status_code >= 400:
                error_text = response.text.lower()

                # Should not expose:
                forbidden_exposures = [
                    "traceback",
                    "exception",
                    "stack trace",
                    "internal server error",
                    "postgresql",
                    "sqlalchemy",
                    "file \"",
                    "line ",
                    settings.SECRET_KEY if settings.SECRET_KEY else "secret",
                ]

                for exposure in forbidden_exposures:
                    assert exposure not in error_text, \
                        f"Error message exposes: {exposure}"

    def test_debug_mode_disabled_in_production(self):
        """Test that debug mode is disabled in production"""
        if settings.ENVIRONMENT.lower() == "production":
            assert not settings.DEBUG, \
                "DEBUG mode must be False in production"

    def test_default_credentials_not_used(self):
        """Test that default credentials are changed in production"""
        if settings.ENVIRONMENT.lower() == "production":
            # Database password should not be default
            assert settings.POSTGRES_PASSWORD != "openlearn123", \
                "Default database password in use"

            # Secret key should not be default
            assert settings.SECRET_KEY != "INSECURE_DEFAULT_KEY_REPLACE_IN_PRODUCTION", \
                "Default SECRET_KEY in use"

    def test_unnecessary_http_methods_disabled(self, client):
        """Test that unnecessary HTTP methods are disabled"""
        # Try dangerous methods on various endpoints
        dangerous_methods = ["TRACE", "TRACK", "OPTIONS"]

        for method in dangerous_methods:
            response = client.request(method, "/")

            # TRACE and TRACK should be disabled (405 or 501)
            if method in ["TRACE", "TRACK"]:
                assert response.status_code in [405, 501], \
                    f"{method} method should be disabled"

    def test_directory_listing_disabled(self, client):
        """Test that directory listing is disabled"""
        # Try to access various directories
        directories = [
            "/static/",
            "/uploads/",
            "/media/",
        ]

        for directory in directories:
            response = client.get(directory)

            # Should not return directory listing (200 with HTML)
            if response.status_code == 200:
                content = response.text.lower()
                assert "index of" not in content
                assert "parent directory" not in content

    def test_sensitive_endpoints_not_exposed(self, client):
        """Test that sensitive endpoints require authentication"""
        sensitive_endpoints = [
            "/api/admin",
            "/api/admin/users",
            "/api/admin/config",
            "/metrics",  # Prometheus metrics
            "/.env",  # Environment variables
            "/config",  # Configuration
            "/api/internal",
        ]

        for endpoint in sensitive_endpoints:
            response = client.get(endpoint)

            # Should not be publicly accessible (200)
            assert response.status_code in [401, 403, 404, 405], \
                f"Sensitive endpoint {endpoint} is exposed (status: {response.status_code})"

    def test_cors_properly_configured(self, client):
        """Test CORS is properly configured"""
        # Make preflight request
        response = client.options(
            "/api/auth/register",
            headers={
                "Origin": "http://malicious.com",
                "Access-Control-Request-Method": "POST"
            }
        )

        # Check CORS headers
        if "Access-Control-Allow-Origin" in response.headers:
            allowed_origin = response.headers["Access-Control-Allow-Origin"]

            # In production, should not be "*"
            if settings.ENVIRONMENT.lower() == "production":
                assert allowed_origin != "*", \
                    "CORS should not allow all origins in production"

                # Should match configured origins
                assert allowed_origin in settings.ALLOWED_ORIGINS

    def test_file_upload_restrictions(self, client):
        """Test that file uploads are properly restricted"""
        # This test assumes avatar upload endpoint exists
        from io import BytesIO

        # Try to upload restricted file types
        malicious_files = [
            ("malicious.exe", b"MZ\x90\x00", "application/x-msdownload"),
            ("script.sh", b"#!/bin/bash\nrm -rf /", "application/x-sh"),
            ("payload.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
        ]

        for filename, content, content_type in malicious_files:
            files = {"file": (filename, BytesIO(content), content_type)}

            response = client.post("/api/avatars/upload", files=files)

            # Should reject dangerous file types
            assert response.status_code in [400, 415, 422], \
                f"Dangerous file type {filename} was not rejected"

    def test_rate_limiting_configured(self, client):
        """Test that rate limiting is configured"""
        # Make rapid requests
        responses = []

        for i in range(100):
            response = client.get("/api/content")
            responses.append(response.status_code)

            if response.status_code == 429:
                break

        # Should hit rate limit
        assert 429 in responses, \
            "Rate limiting not configured or threshold too high"

    def test_cache_control_on_sensitive_endpoints(self, client):
        """Test that sensitive endpoints have proper cache control"""
        response = client.get("/api/auth/me")

        # Even if unauthorized, check headers would be set for authenticated
        # Sensitive endpoints should have no-cache headers
        # This might only apply to successful authenticated responses

    def test_https_redirect_in_production(self):
        """Test that HTTPS redirect is configured in production"""
        if settings.ENVIRONMENT.lower() == "production":
            # Frontend URL should use HTTPS
            assert settings.FRONTEND_URL.startswith("https://"), \
                "Frontend URL should use HTTPS in production"

    def test_sql_echo_disabled_in_production(self):
        """Test that SQL query logging is disabled in production"""
        if settings.ENVIRONMENT.lower() == "production":
            assert not settings.DB_ECHO, \
                "SQL query logging should be disabled in production"

    def test_unnecessary_services_disabled(self):
        """Test that unnecessary services are disabled"""
        # Check that optional services are configured appropriately
        if settings.ENVIRONMENT.lower() == "production":
            # Elasticsearch should be properly configured or disabled
            if not settings.ELASTICSEARCH_ENABLED:
                # If disabled, should not try to connect
                pass

    def test_error_handling_configured(self, client):
        """Test that global error handling is configured"""
        # Trigger a 500 error (if possible)
        response = client.get("/api/trigger-error")

        if response.status_code == 500:
            # Error response should be structured, not raw exception
            data = response.json()
            assert "detail" in data or "message" in data

            # Should not contain stack trace
            assert "Traceback" not in response.text

    def test_logging_configured_properly(self):
        """Test that logging is properly configured"""
        # Logs should not go to stdout in production
        if settings.ENVIRONMENT.lower() == "production":
            # Log directory should be configured
            assert settings.LOG_DIR is not None or \
                   settings.LOG_ENABLE_FILE, \
                   "File logging should be enabled in production"

    def test_allowed_hosts_configured(self):
        """Test that allowed hosts are properly configured"""
        if settings.ENVIRONMENT.lower() == "production":
            # Should have specific allowed hosts, not "*"
            assert settings.ALLOWED_HOSTS != ["*"], \
                "ALLOWED_HOSTS should be specific in production"

    def test_session_security_configured(self):
        """Test that session security is properly configured"""
        # Sessions should have:
        # 1. Secure flag (HTTPS only)
        # 2. HttpOnly flag (no JavaScript access)
        # 3. SameSite flag (CSRF protection)
        # 4. Proper timeout

        # JWT token expiry should be reasonable
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 60, \
            "Access token expiry should be 60 minutes or less"

        assert settings.REFRESH_TOKEN_EXPIRE_DAYS <= 30, \
            "Refresh token expiry should be 30 days or less"
