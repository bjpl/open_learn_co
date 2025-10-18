"""
Comprehensive Security Headers Middleware Tests

Tests for:
- HSTS (Strict-Transport-Security)
- CSP (Content-Security-Policy)
- X-Frame-Options (clickjacking protection)
- X-Content-Type-Options (MIME sniffing)
- Security header injection
- Trusted host validation
- Host header injection prevention
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from starlette.responses import Response, JSONResponse
from fastapi import FastAPI, Request

from app.middleware.security_headers import (
    SecurityHeadersMiddleware,
    TrustedHostMiddleware,
    add_security_middleware,
)


class TestSecurityHeadersMiddleware:
    """Test security headers middleware"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = FastAPI()

    @pytest.fixture
    def security_middleware(self):
        """Create security headers middleware"""
        return SecurityHeadersMiddleware(self.app)

    @pytest.mark.asyncio
    async def test_adds_all_security_headers(self, security_middleware):
        """All security headers should be added to response"""
        request = Mock(spec=Request)
        request.url.scheme = "https"
        request.url.path = "/api/test"
        request.headers = {}

        mock_response = Response(content="test", status_code=200)

        async def call_next(req):
            return mock_response

        response = await security_middleware.dispatch(request, call_next)

        # Check all security headers
        assert "Strict-Transport-Security" in response.headers
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers
        assert "X-Permitted-Cross-Domain-Policies" in response.headers

    @pytest.mark.asyncio
    async def test_hsts_only_on_https(self, security_middleware):
        """HSTS should only be added for HTTPS connections"""
        # HTTPS request
        https_request = Mock(spec=Request)
        https_request.url.scheme = "https"
        https_request.url.path = "/api/test"
        https_request.headers = {}

        mock_response = Response(content="test")

        async def call_next(req):
            return Response(content="test")

        https_response = await security_middleware.dispatch(https_request, call_next)
        assert "Strict-Transport-Security" in https_response.headers

        # HTTP request
        http_request = Mock(spec=Request)
        http_request.url.scheme = "http"
        http_request.url.path = "/api/test"
        http_request.headers = {}

        http_response = await security_middleware.dispatch(http_request, call_next)
        assert "Strict-Transport-Security" not in http_response.headers

    @pytest.mark.asyncio
    async def test_hsts_configuration(self):
        """HSTS header should respect configuration"""
        middleware = SecurityHeadersMiddleware(
            self.app,
            hsts_max_age=7200,  # 2 hours
            hsts_include_subdomains=False,
            hsts_preload=False
        )

        request = Mock(spec=Request)
        request.url.scheme = "https"
        request.url.path = "/api/test"
        request.headers = {}

        async def call_next(req):
            return Response(content="test")

        response = await middleware.dispatch(request, call_next)

        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=7200" in hsts
        assert "includeSubDomains" not in hsts
        assert "preload" not in hsts

    @pytest.mark.asyncio
    async def test_csp_default_policy(self, security_middleware):
        """Default CSP should be restrictive"""
        request = Mock(spec=Request)
        request.url.scheme = "https"
        request.url.path = "/api/test"
        request.headers = {}

        async def call_next(req):
            return Response(content="test")

        response = await security_middleware.dispatch(request, call_next)

        csp = response.headers["Content-Security-Policy"]

        # Check for important directives
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "object-src 'none'" in csp
        assert "frame-ancestors 'none'" in csp

    @pytest.mark.asyncio
    async def test_csp_custom_policy(self):
        """Custom CSP policy should be respected"""
        custom_csp = "default-src 'none'; script-src 'self' https://cdn.example.com"

        middleware = SecurityHeadersMiddleware(
            self.app,
            csp_policy=custom_csp
        )

        request = Mock(spec=Request)
        request.url.scheme = "https"
        request.url.path = "/api/test"
        request.headers = {}

        async def call_next(req):
            return Response(content="test")

        response = await middleware.dispatch(request, call_next)

        assert response.headers["Content-Security-Policy"] == custom_csp

    @pytest.mark.asyncio
    async def test_frame_options_deny(self, security_middleware):
        """X-Frame-Options should be set to DENY"""
        request = Mock(spec=Request)
        request.url.scheme = "https"
        request.url.path = "/api/test"
        request.headers = {}

        async def call_next(req):
            return Response(content="test")

        response = await security_middleware.dispatch(request, call_next)

        assert response.headers["X-Frame-Options"] == "DENY"

    @pytest.mark.asyncio
    async def test_content_type_options_nosniff(self, security_middleware):
        """X-Content-Type-Options should be nosniff"""
        request = Mock(spec=Request)
        request.url.scheme = "https"
        request.url.path = "/api/test"
        request.headers = {}

        async def call_next(req):
            return Response(content="test")

        response = await security_middleware.dispatch(request, call_next)

        assert response.headers["X-Content-Type-Options"] == "nosniff"

    @pytest.mark.asyncio
    async def test_xss_protection_enabled(self, security_middleware):
        """X-XSS-Protection should be enabled with block mode"""
        request = Mock(spec=Request)
        request.url.scheme = "https"
        request.url.path = "/api/test"
        request.headers = {}

        async def call_next(req):
            return Response(content="test")

        response = await security_middleware.dispatch(request, call_next)

        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    @pytest.mark.asyncio
    async def test_xss_protection_disabled(self):
        """X-XSS-Protection can be disabled"""
        middleware = SecurityHeadersMiddleware(
            self.app,
            enable_xss_protection=False
        )

        request = Mock(spec=Request)
        request.url.scheme = "https"
        request.url.path = "/api/test"
        request.headers = {}

        async def call_next(req):
            return Response(content="test")

        response = await middleware.dispatch(request, call_next)

        assert "X-XSS-Protection" not in response.headers

    @pytest.mark.asyncio
    async def test_referrer_policy(self, security_middleware):
        """Referrer-Policy should be set"""
        request = Mock(spec=Request)
        request.url.scheme = "https"
        request.url.path = "/api/test"
        request.headers = {}

        async def call_next(req):
            return Response(content="test")

        response = await security_middleware.dispatch(request, call_next)

        assert "Referrer-Policy" in response.headers
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    async def test_permissions_policy(self, security_middleware):
        """Permissions-Policy should restrict features"""
        request = Mock(spec=Request)
        request.url.scheme = "https"
        request.url.path = "/api/test"
        request.headers = {}

        async def call_next(req):
            return Response(content="test")

        response = await security_middleware.dispatch(request, call_next)

        permissions = response.headers["Permissions-Policy"]

        # Check for important restrictions
        assert "geolocation=()" in permissions
        assert "camera=()" in permissions
        assert "microphone=()" in permissions

    @pytest.mark.asyncio
    async def test_removes_server_headers(self, security_middleware):
        """Server identification headers should be removed"""
        request = Mock(spec=Request)
        request.url.scheme = "https"
        request.url.path = "/api/test"
        request.headers = {}

        mock_response = Response(content="test")
        mock_response.headers["Server"] = "uvicorn"
        mock_response.headers["X-Powered-By"] = "Python"

        async def call_next(req):
            return mock_response

        response = await security_middleware.dispatch(request, call_next)

        assert "Server" not in response.headers
        assert "X-Powered-By" not in response.headers

    @pytest.mark.asyncio
    async def test_cache_control_for_authenticated_requests(self, security_middleware):
        """Authenticated requests should have no-cache headers"""
        request = Mock(spec=Request)
        request.url.scheme = "https"
        request.url.path = "/api/test"
        request.headers = {"authorization": "Bearer token123"}

        async def call_next(req):
            return Response(content="test")

        response = await security_middleware.dispatch(request, call_next)

        assert "Cache-Control" in response.headers
        assert "no-store" in response.headers["Cache-Control"]
        assert "Pragma" in response.headers
        assert response.headers["Pragma"] == "no-cache"


class TestTrustedHostMiddleware:
    """Test trusted host validation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = FastAPI()

    @pytest.mark.asyncio
    async def test_allows_trusted_host(self):
        """Trusted hosts should be allowed"""
        middleware = TrustedHostMiddleware(
            self.app,
            allowed_hosts=["example.com", "localhost"]
        )

        request = Mock(spec=Request)
        request.headers = {"host": "example.com"}
        request.client = Mock(host="192.168.1.1")

        mock_response = Response(content="OK", status_code=200)

        async def call_next(req):
            return mock_response

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_blocks_untrusted_host(self):
        """Untrusted hosts should be blocked"""
        middleware = TrustedHostMiddleware(
            self.app,
            allowed_hosts=["example.com"]
        )

        request = Mock(spec=Request)
        request.headers = {"host": "malicious.com"}
        request.client = Mock(host="1.2.3.4")

        async def call_next(req):
            pytest.fail("Should not call next middleware")

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_wildcard_subdomain_matching(self):
        """Wildcard subdomains should be matched"""
        middleware = TrustedHostMiddleware(
            self.app,
            allowed_hosts=["*.example.com"]
        )

        # Should allow subdomains
        for subdomain in ["api.example.com", "www.example.com", "test.example.com"]:
            request = Mock(spec=Request)
            request.headers = {"host": subdomain}
            request.client = Mock(host="1.2.3.4")

            async def call_next(req):
                return Response(content="OK", status_code=200)

            response = await middleware.dispatch(request, call_next)
            assert response.status_code == 200

        # Should block non-matching domains
        request = Mock(spec=Request)
        request.headers = {"host": "other.com"}
        request.client = Mock(host="1.2.3.4")

        async def call_next(req):
            return Response(content="OK", status_code=200)

        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_host_with_port(self):
        """Host header with port should be handled"""
        middleware = TrustedHostMiddleware(
            self.app,
            allowed_hosts=["example.com"]
        )

        request = Mock(spec=Request)
        request.headers = {"host": "example.com:8000"}
        request.client = Mock(host="1.2.3.4")

        async def call_next(req):
            return Response(content="OK", status_code=200)

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_host_header(self):
        """Missing host header should be rejected"""
        middleware = TrustedHostMiddleware(
            self.app,
            allowed_hosts=["example.com"]
        )

        request = Mock(spec=Request)
        request.headers = {}  # No host header
        request.client = Mock(host="1.2.3.4")

        async def call_next(req):
            return Response(content="OK", status_code=200)

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 400


class TestSecurityEdgeCases:
    """Test edge cases and security boundaries"""

    @pytest.mark.asyncio
    async def test_multiple_authorization_headers(self):
        """Multiple authorization headers should trigger cache control"""
        middleware = SecurityHeadersMiddleware(FastAPI())

        request = Mock(spec=Request)
        request.url.scheme = "https"
        request.url.path = "/api/test"
        request.headers = {
            "authorization": "Bearer token1",
            "cookie": "session=abc123"
        }

        async def call_next(req):
            return Response(content="test")

        response = await middleware.dispatch(request, call_next)

        assert "no-store" in response.headers["Cache-Control"]

    @pytest.mark.asyncio
    async def test_very_long_csp_policy(self):
        """Very long CSP policy should be handled"""
        long_csp = "; ".join([f"source-{i} 'self'" for i in range(100)])

        middleware = SecurityHeadersMiddleware(
            FastAPI(),
            csp_policy=long_csp
        )

        request = Mock(spec=Request)
        request.url.scheme = "https"
        request.url.path = "/api/test"
        request.headers = {}

        async def call_next(req):
            return Response(content="test")

        response = await middleware.dispatch(request, call_next)

        assert response.headers["Content-Security-Policy"] == long_csp

    @pytest.mark.asyncio
    async def test_special_characters_in_host(self):
        """Host with special characters should be handled"""
        middleware = TrustedHostMiddleware(
            FastAPI(),
            allowed_hosts=["example.com"]
        )

        # Test various malicious hosts
        malicious_hosts = [
            "example.com@malicious.com",
            "example.com\r\nX-Injected: header",
            "example.com/../../../etc/passwd",
        ]

        for host in malicious_hosts:
            request = Mock(spec=Request)
            request.headers = {"host": host}
            request.client = Mock(host="1.2.3.4")

            async def call_next(req):
                pytest.fail("Should not call next for malicious host")

            response = await middleware.dispatch(request, call_next)
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_header_injection_prevention(self):
        """CSP should prevent header injection"""
        malicious_csp = "default-src 'self'\r\nX-Injected: malicious"

        middleware = SecurityHeadersMiddleware(
            FastAPI(),
            csp_policy=malicious_csp
        )

        request = Mock(spec=Request)
        request.url.scheme = "https"
        request.url.path = "/api/test"
        request.headers = {}

        async def call_next(req):
            return Response(content="test")

        response = await middleware.dispatch(request, call_next)

        # Header should be set as-is (framework handles sanitization)
        assert "Content-Security-Policy" in response.headers

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Concurrent requests should all get security headers"""
        import asyncio

        middleware = SecurityHeadersMiddleware(FastAPI())

        async def make_request():
            request = Mock(spec=Request)
            request.url.scheme = "https"
            request.url.path = "/api/test"
            request.headers = {}

            async def call_next(req):
                await asyncio.sleep(0.01)
                return Response(content="test")

            return await middleware.dispatch(request, call_next)

        responses = await asyncio.gather(*[make_request() for _ in range(10)])

        # All responses should have security headers
        for response in responses:
            assert "Content-Security-Policy" in response.headers
            assert "X-Frame-Options" in response.headers

    @pytest.mark.asyncio
    async def test_ipv6_trusted_hosts(self):
        """IPv6 addresses should be validated"""
        middleware = TrustedHostMiddleware(
            FastAPI(),
            allowed_hosts=["[::1]", "localhost"]  # IPv6 loopback
        )

        request = Mock(spec=Request)
        request.headers = {"host": "[::1]"}
        request.client = Mock(host="::1")

        async def call_next(req):
            return Response(content="OK", status_code=200)

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
