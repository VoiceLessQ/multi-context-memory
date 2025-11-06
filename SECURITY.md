# Security Guidelines

## Overview

This document outlines security best practices and requirements for the MCP Multi-Context Memory System.

## Critical Security Requirements

### 1. Environment Variables

All sensitive configuration MUST be set via environment variables. Never hardcode secrets in source code.

#### Required Variables

These environment variables MUST be set in production:

```bash
# JWT Authentication (REQUIRED)
JWT_SECRET_KEY=<generate-secure-key>
API_SECRET_KEY=<generate-secure-key>

# Database Configuration (REQUIRED)
DATABASE_URL=sqlite:///./data/sqlite/memory.db
```

#### Optional Variables

These are required only if using specific features:

```bash
# Email Configuration (if using email features)
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=<your-secure-password>
APP_BASE_URL=https://your-domain.com

# Redis Configuration (if using Redis)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=<secure-password-if-required>

# OpenAI Configuration (if using OpenAI embeddings)
OPENAI_API_KEY=sk-<your-key>
```

### 2. Generating Secure Keys

Generate cryptographically secure keys using Python:

```bash
# Generate a secure JWT secret key
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Generate multiple keys at once
python -c 'import secrets; print("JWT_SECRET_KEY=" + secrets.token_urlsafe(32)); print("API_SECRET_KEY=" + secrets.token_urlsafe(32))'
```

Or using OpenSSL:

```bash
openssl rand -base64 32
```

### 3. Environment File Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set all required variables with secure values

3. Verify `.env` is in `.gitignore` (it is by default)

4. Never commit `.env` files to version control

### 4. Docker Security

When using Docker Compose:

1. Create a `.env` file in the project root
2. Set environment variables in `.env`:
   ```bash
   JWT_SECRET_KEY=<your-secure-key>
   API_SECRET_KEY=<your-secure-key>
   EMAIL_HOST_PASSWORD=<your-email-password>
   ```

3. Docker Compose will automatically load these variables

4. For production, use Docker secrets or your orchestration platform's secret management

### 5. Password Security

- All passwords are hashed using bcrypt before storage
- Minimum password length: 8 characters
- Password hashing is handled automatically by the application
- Never log or store plaintext passwords

### 6. JWT Token Security

- Access tokens expire after 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Refresh tokens expire after 7 days
- Tokens are signed using HS256 algorithm
- The `JWT_SECRET_KEY` must be kept secure and never exposed

### 7. API Security

- All authentication endpoints use OAuth2 with password flow
- Protected endpoints require valid JWT tokens
- Use HTTPS in production (configure with reverse proxy like nginx)
- Rate limiting should be implemented at the reverse proxy level

## Security Checklist

Before deploying to production:

- [ ] All environment variables are set with secure values
- [ ] `JWT_SECRET_KEY` and `API_SECRET_KEY` are unique and cryptographically secure (32+ chars)
- [ ] `.env` files are not committed to version control
- [ ] Database files have appropriate file permissions (600 or 640)
- [ ] HTTPS is configured and enforced
- [ ] Email credentials are secure and use app-specific passwords
- [ ] Redis is configured with authentication if exposed to network
- [ ] Backup procedures are in place for database files
- [ ] Log files do not contain sensitive information
- [ ] Application is running as non-root user
- [ ] File upload limits are configured (if applicable)
- [ ] CORS settings are properly configured for your domain

## Reporting Security Issues

If you discover a security vulnerability, please report it to the repository maintainers. Do not create public issues for security vulnerabilities.

Contact: GitHub @VoiceLessQ or open a private security advisory on GitHub.

## Reporting Copyright Violations & Code Theft

This project is protected by copyright and licensed under MIT License.
Copyright (c) 2024 VoiceLessQ

If you discover unauthorized use, copyright violations, or code theft:

1. **What constitutes a violation:**
   - Removal of copyright notices or attribution
   - Claiming authorship of this code
   - Distribution without including LICENSE and NOTICE files
   - Using project name or branding without permission

2. **How to report:**
   - Contact: GitHub @VoiceLessQ
   - Open an issue: https://github.com/VoiceLessQ/multi-context-memory/issues
   - Include: URL of violation, screenshots, evidence

3. **Project authentication:**
   - Original repository: https://github.com/VoiceLessQ/multi-context-memory
   - Copyright holder: VoiceLessQ
   - Project fingerprint: 7a8f9b3c-mcpmem-voicelessq-2024
   - First published: 2024

Any repository claiming to be the "original" without this fingerprint and earlier commit history is unauthorized.

## Regular Security Maintenance

1. Keep dependencies up to date:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. Review security advisories for Python packages:
   ```bash
   pip-audit
   ```

3. Rotate secrets periodically (especially after team member changes)

4. Review access logs for suspicious activity

5. Keep Docker images updated

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)

## Compliance Notes

- Passwords are hashed using bcrypt (OWASP recommended)
- JWT tokens use HS256 signing algorithm
- No hardcoded credentials in source code
- Environment variables for sensitive configuration
- Secure token generation using Python's secrets module
