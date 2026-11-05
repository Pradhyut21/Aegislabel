# Contributing

Use synthetic data exclusively. Keep deterministic safety rules separate from AI suggestions; passing validation must never automatically grant human approval.

1. Install the locked Python dependencies and run `npm ci` in `frontend/`.
2. Use a topic branch. Keep domain changes, interface changes and documentation reviewable.
3. Run Ruff checks, pytest, TypeScript checking, ESLint, formatting, Vitest and the production build. Changes affecting workflow or accessibility also need Playwright.
4. Add meaningful failure cases for changes to release eligibility, evidence, extraction, authentication or mutation controls.
5. Update OpenAPI/generated types when request interfaces change. Never hand-edit generated definitions.
6. Record actually executed checks. Do not fabricate benchmark percentages, screenshots, certification claims or provider usage.

API tests use temporary SQLite storage. PostgreSQL tests require an explicitly named isolated database ending in `_test`; those tests clear and reseed that database. Browser tests deliberately change their synthetic workspace.

No clinical or proprietary source material, database snapshots, session records, uploaded documents, caches, browser traces or credentials belong in commits. Run `python -m scripts.check_repository` before pushing. See SECURITY.md for private vulnerability reporting.
