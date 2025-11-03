# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of OpenLearn Colombia seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Where to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to:
- **Security Contact**: [your-security-email@domain.com]
- **Maintainer**: [your-email@domain.com]

### What to Include

To help us better understand the nature and scope of the vulnerability, please include as much of the following information as possible:

- Type of vulnerability (e.g., SQL injection, XSS, authentication bypass)
- Full paths of source file(s) related to the vulnerability
- The location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability
- Suggested remediation (if known)

### What to Expect

- **Acknowledgment**: We will acknowledge your email within 48 hours
- **Investigation**: We will investigate and validate the report
- **Updates**: We will keep you informed about our progress
- **Fix Timeline**:
  - Critical vulnerabilities: 7 days
  - High severity: 14 days
  - Medium severity: 30 days
  - Low severity: 60 days
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous)

### Disclosure Policy

- Please give us reasonable time to address the vulnerability before making it public
- We follow a coordinated disclosure process:
  1. You report the vulnerability privately
  2. We acknowledge and investigate
  3. We develop and test a fix
  4. We release a security patch
  5. We publish a security advisory
  6. You may publicly disclose after the patch is released

### Safe Harbor

We support safe harbor for security researchers who:

- Make a good faith effort to avoid privacy violations, destruction of data, and interruption or degradation of our services
- Only interact with accounts you own or with explicit permission of the account holder
- Do not exploit a security issue you discover for any reason (including demonstrating additional risk)
- Report vulnerabilities as soon as you discover them

When working with us under this policy, you can expect:

- We will respond to your report promptly and work with you to understand and resolve the issue quickly
- We will not pursue or support any legal action related to your research
- We will keep your report confidential and not share your personal information without your permission
- We will publicly acknowledge your responsible disclosure if you wish (after the vulnerability is fixed)

## Known Security Considerations

### Current Security Features

- JWT-based authentication with refresh tokens
- Bcrypt password hashing
- Input validation via Pydantic schemas
- SQL injection protection via SQLAlchemy ORM
- CORS configuration for cross-origin requests
- Rate limiting for API endpoints
- Secure cookie configuration

### Areas for Improvement

We are actively working on:

- Enhanced rate limiting per user/IP
- Two-factor authentication (2FA)
- API key rotation mechanisms
- Comprehensive audit logging
- Enhanced CSP headers

## Security Best Practices for Contributors

If you're contributing to this project, please:

1. **Never commit secrets**: Use `.env` files (which are gitignored)
2. **Validate all inputs**: Use Pydantic schemas for API validation
3. **Use parameterized queries**: Never concatenate user input into SQL
4. **Hash sensitive data**: Use bcrypt for passwords, appropriate encryption for PII
5. **Follow least privilege**: Only request/grant minimum necessary permissions
6. **Keep dependencies updated**: Regularly run `npm audit` and `safety check`
7. **Write security tests**: Include test cases for authentication, authorization, and input validation
8. **Review the security documentation**: See `docs/SECURITY.md` for detailed guidelines

## Security Scanning

This repository uses automated security scanning:

- **Dependabot**: Automatic dependency vulnerability alerts and updates
- **CodeQL**: Code scanning for security vulnerabilities
- **npm audit**: Frontend dependency vulnerability scanning
- **Bandit**: Python code security linting
- **TruffleHog**: Secret scanning in commits

## Security Updates

Security updates will be released as patch versions (e.g., 1.0.1, 1.0.2) and announced via:

- GitHub Security Advisories
- Release notes
- Email to maintainers list

## Contact

For general security questions or concerns (not vulnerability reports), you can:

- Open a discussion in the GitHub Discussions tab
- Email the maintainers at [your-email@domain.com]

## Thank You

We appreciate your efforts to responsibly disclose vulnerabilities and help us keep OpenLearn Colombia secure for everyone!

---

**Last Updated**: November 2025
