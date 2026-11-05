# Security policy

AegisLabel-FX is a localhost research prototype using synthetic application data. The separate allowlisted public FDA reference bundle is not imported into labeling workflows. Do not upload real patient information, proprietary specifications or production credentials. No release is regulatory certification or a legally compliant electronic signature.

## Implemented controls

- scrypt password hashes; random, hashed server-side session tokens; HttpOnly / SameSite Strict cookies and per-session CSRF tokens.
- Independent server-enforced reviewer role and exact artwork/source/ruleset approval binding. Superseded artwork cannot release.
- Trusted-host validation, origin checks, login/API rate limits, bounded request bodies even without Content-Length, body-read deadlines and reader limits.
- Bounded PDF parsing, generated internal storage names, controlled field schemas, XML escaping and frozen release packages.
- Explicit opt-in for external AI, server-only credentials, bounded response streaming, timeouts, structured validation and deterministic fallback.
- Security headers on rejected requests; audit hash-chain verification and automated dependency checks.

## Local configuration

Set unique `DEMO_AUTHOR_PASSWORD` and `DEMO_REVIEWER_PASSWORD` before initial seeding. Demo credentials in the README are deliberately public synthetic examples, not secrets. Existing accounts are not changed by editing seed environment variables. `ALLOWED_HOSTS` defaults to localhost and 127.0.0.1. If using a local HTTPS reverse proxy, explicitly set `COOKIE_SECURE=true` and the expected hosts; production hosting itself is outside this prototype.

Keep one application worker. Rate limits, request-reader limits and write serialization are process-local. Database-administrator rewrites and audit-tail truncation need an external trusted anchor to detect. This application has no validated immutable retention, organization SSO or production credential management.

## Reporting a vulnerability

Use GitHub's **Security → Advisories → Report a vulnerability** when private reporting is available. Do not disclose tokens, real documents or exploit details in a public issue. If private reporting is unavailable, submit a minimal issue requesting a private reporting channel without technical exploit details.

Current security fixes are maintained on `main`. Dependency scanner results describe known advisories at the time of a run, not a guarantee of security. The verification report distinguishes executed controls from untested production assumptions.
