"""
Security Headers Middleware

Implements comprehensive security headers to protect against common web vulnerabilities:
- HSTS (HTTP Strict Transport Security)
- CSP (Content Security Policy)
- X-Frame-Options (Clickjacking protection)
- X-Content-Type-Options (MIME sniffing protection)
- X-XSS-Protection (Legacy XSS protection)
- Referrer-Policy (Referrer information control)
- Permissions-Policy (Feature policy)

References:
- OWASP Secure Headers Project
- Mozilla Web Security Guidelines
- CWE-693: Protection Mechanism Failure
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Implements OWASP recommended security headers to mitigate:
    - XSS attacks
    - Clickjacking
    - MIME sniffing
    - Man-in-the-middle attacks
    - Information disclosure
    """

    def __init__(
        self,
        app,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = True,
        csp_policy: str = None,
        frame_options: str = "DENY",
        enable_xss_protection: bool = True,
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: str = None
    ):
        """
        Initialize security headers middleware.

        Args:
            hsts_max_age: HSTS max-age in seconds (default: 1 year)
            hsts_include_subdomains: Include subdomains in HSTS
            hsts_preload: Enable HSTS preload
            csp_policy: Custom CSP policy (None = use default)
            frame_options: X-Frame-Options value (DENY, SAMEORIGIN, or ALLOW-FROM)
            enable_xss_protection: Enable X-XSS-Protection header
            referrer_policy: Referrer-Policy value
            permissions_policy: Custom Permissions-Policy
        """
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.frame_options = frame_options
        self.enable_xss_protection = enable_xss_protection
        self.referrer_policy = referrer_policy

        # Build HSTS header
        self.hsts_header = self._build_hsts_header()

        # Build CSP header
        self.csp_header = csp_policy or self._build_default_csp()

        # Build Permissions Policy
        self.permissions_policy = permissions_policy or self._build_default_permissions_policy()

        logger.info("Security Headers Middleware initialized")

    def _build_hsts_header(self) -> str:
        """Build HSTS header value."""
        hsts = f"max-age={self.hsts_max_age}"

        if self.hsts_include_subdomains:
            hsts += "; includeSubDomains"

        if self.hsts_preload:
            hsts += "; preload"

        return hsts

    def _build_default_csp(self) -> str:
        """
        Build default Content Security Policy.

        This is a strict CSP that:
        - Blocks inline scripts by default
        - Only allows same-origin resources
        - Prevents loading from untrusted sources

        Customize in production based on actual resource needs.
        """
        csp_directives = [
            "default-src 'self'",  # Only same-origin by default
            "script-src 'self'",  # Only same-origin scripts (no inline!)
            "style-src 'self' 'unsafe-inline'",  # Allow inline styles (consider removing)
            "img-src 'self' data: https:",  # Images from same-origin, data URIs, HTTPS
            "font-src 'self'",  # Fonts from same-origin
            "connect-src 'self'",  # AJAX/WebSocket to same-origin
            "media-src 'self'",  # Media from same-origin
            "object-src 'none'",  # No plugins (Flash, etc.)
            "frame-src 'none'",  # No iframes
            "base-uri 'self'",  # Restrict base tag URLs
            "form-action 'self'",  # Forms only submit to same-origin
            "frame-ancestors 'none'",  # Cannot be embedded in iframes
            "upgrade-insecure-requests",  # Upgrade HTTP to HTTPS
            "block-all-mixed-content",  # Block HTTP content on HTTPS pages
        ]

        return "; ".join(csp_directives)

    def _build_default_permissions_policy(self) -> str:
        """
        Build default Permissions Policy (formerly Feature Policy).

        Restricts browser features to prevent abuse:
        - Geolocation
        - Camera/Microphone
        - Payment APIs
        - etc.
        """
        policy_directives = [
            "geolocation=()",  # Block geolocation
            "microphone=()",  # Block microphone
            "camera=()",  # Block camera
            "payment=()",  # Block payment API
            "usb=()",  # Block USB access
            "magnetometer=()",  # Block magnetometer
            "accelerometer=()",  # Block accelerometer
            "gyroscope=()",  # Block gyroscope
            "interest-cohort=()",  # Block FLoC tracking
        ]

        return ", ".join(policy_directives)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process request and add security headers to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            Response with security headers added
        """
        # Process the request
        response = await call_next(request)

        # Add security headers
        headers_added = self._add_security_headers(response, request)

        # Log for monitoring (only in debug mode)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Security headers added to {request.url.path}: {headers_added}"
            )

        return response

    def _add_security_headers(
        self,
        response: Response,
        request: Request
    ) -> dict:
        """
        Add all security headers to the response.

        Args:
            response: HTTP response object
            request: HTTP request object

        Returns:
            Dictionary of headers added
        """
        headers_added = {}

        # 1. Strict-Transport-Security (HSTS)
        # Forces HTTPS connections for specified duration
        # Only add on HTTPS connections
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = self.hsts_header
            headers_added["Strict-Transport-Security"] = self.hsts_header

        # 2. Content-Security-Policy (CSP)
        # Prevents XSS, clickjacking, and other code injection attacks
        response.headers["Content-Security-Policy"] = self.csp_header
        headers_added["Content-Security-Policy"] = "enabled"

        # 3. X-Frame-Options
        # Prevents clickjacking by controlling iframe embedding
        response.headers["X-Frame-Options"] = self.frame_options
        headers_added["X-Frame-Options"] = self.frame_options

        # 4. X-Content-Type-Options
        # Prevents MIME sniffing, forces declared content types
        response.headers["X-Content-Type-Options"] = "nosniff"
        headers_added["X-Content-Type-Options"] = "nosniff"

        # 5. X-XSS-Protection (legacy, but still useful for old browsers)
        # Enables browser XSS filtering
        if self.enable_xss_protection:
            response.headers["X-XSS-Protection"] = "1; mode=block"
            headers_added["X-XSS-Protection"] = "1; mode=block"

        # 6. Referrer-Policy
        # Controls referrer information sent with requests
        response.headers["Referrer-Policy"] = self.referrer_policy
        headers_added["Referrer-Policy"] = self.referrer_policy

        # 7. Permissions-Policy (formerly Feature-Policy)
        # Controls which browser features can be used
        response.headers["Permissions-Policy"] = self.permissions_policy
        headers_added["Permissions-Policy"] = "enabled"

        # 8. X-Permitted-Cross-Domain-Policies
        # Restrict Adobe Flash and PDF cross-domain policies
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        headers_added["X-Permitted-Cross-Domain-Policies"] = "none"

        # 9. Remove server identification header
        # Reduces information disclosure
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)

        # 10. Cache-Control for sensitive pages
        # Prevent caching of authenticated content
        if "authorization" in request.headers or "cookie" in request.headers:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            headers_added["Cache-Control"] = "no-store"

        return headers_added


class TrustedHostMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate Host header and prevent Host header injection attacks.

    Protects against:
    - Host header injection
    - Cache poisoning
    - Password reset poisoning
    - Server-Side Request Forgery (SSRF)

    Reference: CWE-644 (Improper Neutralization of HTTP Headers)
    """

    def __init__(self, app, allowed_hosts: list[str] = None):
        """
        Initialize trusted host middleware.

        Args:
            allowed_hosts: List of allowed host patterns
                          Examples: ["example.com", "*.example.com", "192.168.1.100"]
        """
        super().__init__(app)
        self.allowed_hosts = allowed_hosts or ["localhost", "127.0.0.1"]
        logger.info(f"Trusted Host Middleware initialized: {self.allowed_hosts}")

    def _is_valid_host(self, host: str) -> bool:
        """
        Check if host is in allowed list.

        Args:
            host: Host header value

        Returns:
            True if host is allowed
        """
        # Remove port if present
        if ":" in host:
            host = host.split(":")[0]

        # Check exact matches
        if host in self.allowed_hosts:
            return True

        # Check wildcard patterns (e.g., *.example.com)
        for allowed in self.allowed_hosts:
            if allowed.startswith("*."):
                domain = allowed[2:]
                if host.endswith(domain):
                    return True

        return False

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Validate Host header before processing request.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            Response or 400 error if host is invalid
        """
        host = request.headers.get("host", "")

        if not self._is_valid_host(host):
            logger.warning(
                f"Invalid Host header detected: {host} "
                f"from {request.client.host if request.client else 'unknown'}"
            )

            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid host header"}
            )

        response = await call_next(request)
        return response


# Utility function to apply all security middleware
def add_security_middleware(app, settings):
    """
    Add all security middleware to FastAPI application.

    Args:
        app: FastAPI application instance
        settings: Application settings object
    """
    from app.config.settings import is_production

    # 1. Trusted Host validation
    allowed_hosts = settings.ALLOWED_HOSTS if hasattr(settings, 'ALLOWED_HOSTS') else ["*"]
    if is_production():
        # In production, enforce explicit host whitelist
        if allowed_hosts == ["*"]:
            logger.warning(
                "ALLOWED_HOSTS is '*' in production! "
                "This is insecure. Configure explicit allowed hosts."
            )
        else:
            app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    # 2. Security Headers
    csp_policy = None
    if is_production():
        # Strict CSP for production
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

    app.add_middleware(
        SecurityHeadersMiddleware,
        hsts_max_age=31536000,  # 1 year
        hsts_include_subdomains=True,
        hsts_preload=True,
        csp_policy=csp_policy,
        frame_options="DENY",
        enable_xss_protection=True,
        referrer_policy="strict-origin-when-cross-origin"
    )

    logger.info("All security middleware applied successfully")
