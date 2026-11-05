# Architecture and trust boundaries

AegisLabel-FX is a local, single-process research application. The React client talks to FastAPI through the same origin. Vite proxies `/api` during development; FastAPI serves the built interface in local production mode. No external AI call occurs unless `AI_ENABLED=true` and credentials are configured.

## Reference implementation study

The Celebrate AI repository was read through the GitHub API and raw files without cloning or changing it. The study included App, CSS, Dialog, workspace hooks, planning client, server composition, provider implementation, shared Pydantic-equivalent Zod schemas, pure planning logic, Playwright/axe tests and the verification report. The adopted patterns are small reusable UI components, I/O outside deterministic rules, explicit provider fallback, schema validation at boundaries, independent browser tests and candid verification limits. No event-planning functionality or decorative imagery was copied.

## Storage and transactions

SQLAlchemy stores typed record categories in a `records` table with JSON payloads and an optimistic revision counter. PostgreSQL is the Docker default. SQLite is the zero-infrastructure native fallback. Alembic migration 0001 creates the table and category index. The generic record store intentionally keeps this prototype small; referential integrity is enforced by service functions rather than relational foreign keys. This is a documented prototype tradeoff, not the recommended final production schema.

All write operations run under a process lock and database transaction. Run exactly **one application worker**. Multiple worker or distributed operation needs database row/advisory locking and unique version constraints before use. Source and artwork contents are preserved; edits create new records. Status, validation references and approvals evolve on their existing record. Revision checks reject stale review/edit requests. Historical release packages use frozen release fields rather than current artwork.

Entities: device → label variant → artwork revisions; device → approved source versions; changes → affected label IDs; artwork → validation → approved source; artwork → reviewer approval; release → frozen artwork, evidence and validation. Every event contains the previous event hash.

## Authority and generation

Approved document fields govern product name, identifier, UDI, barcode, warning, IFU, symbols, claims, translation, manufacturer and sterility. The registered label configuration governs variant, market, language and packaging. Each label has explicit `dependency_fields`. Source change propagation intersects changed fields with these edges for that device. Only affected labels advance their applicable source pointer; an unrelated field change does not invalidate other label snapshots. A document's packaging description cannot silently overwrite a controlled label configuration.

Structured templates generate proposals. SVG bytes are shared by the on-screen preview, hash and release download. PDF generation uses the same structured fields with real Code128 bars. PDF bytes are not the approval key: PDF generators may include changing metadata. The canonical approval key is SHA-256 of exact deterministic SVG bytes. The SVG includes every controlled field, including fields not normally prominent on a physical label. Barcode control checks the encoded string against configured authoritative content; this is not comprehensive GS1 carrier validation.

Validation never asks an LLM to decide. Each field is compared against the authoritative snapshot. A critical mismatch gives BLOCKED. A source contradiction without other errors gives ESCALATE. Neither can be submitted or released. PASS FOR REVIEW means only that configured checks passed. Release revalidates current requirements and the exact approval hash, source revision and ruleset. There is no automatic approval path.

## Optional model adapter

`backend/provider.py` supports an explicitly configured HTTPS OpenAI-compatible Meta-model endpoint. It validates a bounded JSON field map with Pydantic, caps outputs, uses 12-second request timeouts and at most two retries. Provider errors return a visible deterministic fallback with a persisted reason. Usage is recorded when supplied. Live provider compatibility and billing have not been tested. The parser for uploaded documents is deterministic by default; optional structured AI extraction is accepted only when proposed values occur literally in the document. AI-assisted drafting is also integrated. Source extraction proposals still require human confirmation.

## Access and audit

Separate local accounts use scrypt password hashes and random server-side sessions. Cookies are HttpOnly and SameSite Strict. Mutations require a per-session CSRF token; untrusted browser origins are rejected. Authors cannot approve their own artwork. Independent reviewer actions are enforced by the server, not by hidden buttons. Demo credentials are for localhost synthetic use only. HTTP is local; production TLS and organization identity management are outside this prototype.

Each audit entry hashes canonical JSON containing sequence, actor, timestamp, action, detail and previous hash. Verification detects altered entries against that chain. A database administrator could rewrite the whole chain or remove its tail; trusted external head anchoring and immutable retention are not implemented. Never describe this as immutable storage.

## Document boundary

Uploads are capped at 10 MB, 100 pages and 250,000 extracted characters. The parser accepts known `field: value` lines, records page/quote/bounding box evidence, preserves contradictory values as a blocked source candidate and rejects encrypted/corrupt files and empty scanned documents, and never uses the supplied filename as a filesystem path. Extracted records remain candidates until a reviewer confirms all controlled fields. OCR, arbitrary prose understanding, external enterprise connectors and live regulatory monitoring are not implemented.


## Publication hardening

`backend/security.py` applies a transport-level 11 MiB request cap independently of Content-Length, a 30-second body-read deadline, eight active body readers and security headers on rejection responses. Trusted hosts default to localhost and 127.0.0.1. Unknown usernames still perform the password hash operation. Successful login expires old sessions and bounds active sessions per account. Optional AI response streams stop at 64 KiB before structured parsing. Cookies can be explicitly configured as Secure behind local HTTPS.

Frontend records use explicit domain interfaces and unknown response defaults. Heterogeneous drawers narrow document, artwork, release and audit data before access; ESLint rejects explicit `any`. Generated request contracts are checked for drift in CI.
