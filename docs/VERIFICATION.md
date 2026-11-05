# Executed verification record

Verified **2026-11-05** in the provided Linux workspace using Python 3.12.14, Node 24.22.1, PostgreSQL 16.8 and Chromium through Playwright 1.64.1. Results below were executed, not inferred. The reference repository's results are not counted as AegisLabel-FX results.

| Command / check | Observed result |
| --- | --- |
| `.venv/bin/python -m pytest -q` | **52 passed**, 7 upstream deprecation warnings |
| `TEST_DATABASE_URL=postgresql+psycopg://aegis:local-synthetic-only@127.0.0.1:15432/aegis_test .venv/bin/python -m pytest -q` | **52 passed**, 7 upstream deprecation warnings; isolated PostgreSQL database reseeded per API test |
| `npm test` | **3 passed** on Vitest 5.1.0 |
| `npm run test:e2e` | **2 passed**; the tests contain the complete multi-stage journey and ten-view accessibility/navigation checks |
| Playwright + axe | No reported WCAG A/AA violations on the tested ten views, blocked-warning state, mobile overview and mobile source-change dialog |
| Responsive / keyboard | 390 px and 320 px page-overflow checks passed; native dialog Escape dismissal, mobile navigation and focus handling exercised |
| `npm run typecheck` | Passed |
| `npm run lint` | Passed, zero warnings; TypeScript, React hooks and JSX accessibility rules |
| `npm run format:check` | Passed |
| `.venv/bin/ruff check backend tests scripts` | Passed |
| `.venv/bin/ruff format --check backend tests scripts` | Passed |
| `npm run build` | Passed; Vite 6.4.5 production build |
| `python -m scripts.benchmark` | **24/24** faults detected; **0/5** clean controls blocked |
| Fault-control negative test | Removing the warning control causes warning mutations to escape; confirms results depend on executed controls |
| Barcode verification | Real generated PDF rasterized and independently decoded with zxing-cpp; decoded value matches configured content |
| Artwork preview smoke | Both browser image previews decoded actual server SVGs at 520 × 650; previews share release/hash SVG bytes |
| `alembic upgrade head` and `alembic current` | `0001 (head)` on dedicated PostgreSQL and SQLite migration databases |
| `docker compose config --quiet` | Passed |
| PostgreSQL container | Started from Compose and used for actual integration tests through a localhost-only test port |
| `npm audit --audit-level=high` | **0 known vulnerabilities** after updating tools and a scoped minimatch override; JSON retained |
| `pip-audit --progress-spinner off` | **No known vulnerabilities found** after dependency updates; JSON retained |
| Synthetic fixtures | Actual R1 and R2 specification PDFs generated under `sample-data/` |
| FastAPI / frontend contracts | Actual OpenAPI exported and TypeScript schema definitions generated |

## Verified behavior

The browser journey updates the warning, finds two affected labels, generates actual artwork, edits the warning back to the obsolete content, observes BLOCKED / SAFETY WARNING MISMATCH, inspects the failure, regenerates correct artwork, validates, submits, switches to an independent reviewer, approves the exact version, generates and downloads a ZIP, runs the full and change-targeted mutation suites, verifies audit integrity and reloads persisted workspace records.

Backend coverage includes all configured field controls, source changes, unrelated field dependencies, stale source approvals, approval/hash/ruleset binding, rejection of earlier artwork after a successor exists, optimistic revision conflicts, unauthorized review, CSRF/origin protection, login rate limits, valid/invalid/oversized/encrypted/scanned PDFs, preserved source contradictions, reviewer source confirmation, real PDF generation, decoded barcode, exact source evidence coordinates, mutation isolation, disabled-control escapes and audit tampering.

Dependency scanning initially found vulnerable older development and server packages. Final pins were upgraded and all relevant tests rerun. The scoped npm override updates only the TypeScript parser's minimatch dependency. The known-vulnerability result describes the scanners' current data; it is not a guarantee that the application is vulnerability-free.

## Benchmark observation

For the recorded full synthetic fixture: artwork comparison detected **19/24**, deterministic content checks detected **19/24**, and the full workflow detected **24/24**. Five repeated valid controls produced no blocks for each method. The independent impact fixtures found **4/4** expected impacts and **0** false impacts. These are small synthetic experiments with deliberately different information available to each baseline; no manufacturing or clinical performance claim follows. See `EVALUATION.md`.

## Evidence files

- `artifacts/backend-sqlite-results.txt`
- `artifacts/backend-postgres-results.txt`
- `artifacts/browser-results.txt` and `artifacts/playwright-results.json`
- `artifacts/benchmark.json`
- `artifacts/npm-audit.json` and `artifacts/python-audit.json`

Genuine browser captures were used for layout review. They are verification artifacts, not generated mockups or substitutes for a working application. Browser tests run against `artifacts/e2e.db`, separate from the final demonstration workspace.

## Limits and unexecuted paths

- Windows setup commands are documented but **not executed on Windows**; this environment has no D: drive.
- The managed workspace did not build the full application image because storage was limited. The complete Docker image was subsequently built and smoke-tested successfully in GitHub Actions; see the remote verification below. Windows Docker Desktop remains untested.
- Live Meta-compatible provider calls were **not executed**. Provider success, invalid output and bounded timeouts use mocks. No credentials or paid services were activated.
- No broad language, clinical or regulatory validation, real GS1 allocation, OCR, live enterprise-system connectors, live regulatory monitoring, immutable external audit anchoring or production electronic signatures are claimed.
- Chromium and automated accessibility checks were tested. Safari, Firefox, real assistive-technology sessions and all possible environments were not.
- The prototype supports one application worker. Distributed concurrency requires additional database locking and relational constraints.

Final workspace smoke: 3 devices, 6 labels, 6 current synthetic seed approvals, no pending source changes, and one actually executed 24/24 mutation run. The backend was stopped and restarted; these records and the valid audit chain persisted. The application remains running on port 8000 in the workspace. PostgreSQL test services were stopped after verification; their local data volume was retained.


## Public repository preparation

Security hardening was followed by **52 passing tests on each database**, including chunked bodies without Content-Length, read deadlines, busy-reader limits, trusted-host rejection, security headers on failures, logout revocation, workspace secret exclusion and bounded provider streaming. Frontend record models are explicitly typed; ESLint now rejects explicit `any`. Blocked artwork cannot be submitted through the interface; the API independently enforces the same release gates.

The repository includes pinned GitHub Actions for quality checks, browser/accessibility tests, PostgreSQL integration, a container smoke test and CodeQL. These remote workflow results are only considered verified after their GitHub runs finish. README images are genuine captures from a separate synthetic preview database; neither that database nor its sessions is included in commits.


## Verified GitHub publication

The public source is hosted at [Pradhyut21/Aegislabel](https://github.com/Pradhyut21/Aegislabel). On commit `3b8c278cae5d028403c04b5bddb0ad068580a16f`:

- [Quality run 41955816757](https://github.com/Pradhyut21/Aegislabel/actions/runs/41955816757) **passed**: backend tests on SQLite and PostgreSQL, migrations, mutation benchmark, repository-content scan, Ruff, frontend type/lint/format/unit/build checks, generated-contract drift checks, npm/Python dependency audits, the browser/accessibility journey, and the complete Docker build and container health smoke.
- [CodeQL run 41955816798](https://github.com/Pradhyut21/Aegislabel/actions/runs/41955816798) **passed** analysis for Python and JavaScript/TypeScript. A successful analysis job is not a guarantee of zero security defects.

The first container smoke attempt exposed a readiness race: Docker accepted the port before the application was ready, producing a connection reset. The health probe now retries bounded startup errors; the corrected run passed without weakening application tests. Nothing was deployed publicly. Repository description/topic updates were denied by the GitHub integration; the source, README and workflows were pushed successfully.

## Narrated demo, Meta adapters and public reference data update

Executed locally on 2026-11-05:

- `pytest -q`: **61 passed**, including current Meta Model API routing/truncation controls, native Llama SDK JSON-schema requests/fallback, and public-reference join/allowlist/missing/ambiguity/conflict checks. Provider tests use mocks; no live inference or paid access.
- `ruff check backend tests scripts` and `ruff format`: passed.
- Frontend ESLint, Vitest (**3 passed**) and production TypeScript/Vite build: passed.
- `pip-audit -r requirements.lock.txt`: no known vulnerabilities found.
- Optional demo `npm audit`: no known vulnerabilities after pinning the transitive `undici` to 7.30.1. This was a real finding and remediation, not a suppressed audit.
- Real Playwright capture executed the complete warning/approval/release/mutation/audit flow in an isolated database, with result assertions. The demo's reviewer actions are scripted role demonstrations, not production human signatures.
- Hyperframes composition check: passed; no layout, contrast, motion, craft or audio errors. Snapshots inspected at 3, 47, 74, 95, 116 and 132 seconds. Intentional still cards use `data-hold`; audio durations use actual measured WAV lengths.
- Public openFDA fetch: **6 unique devices, 8 category joins, 0 unmatched/ambiguous/conflicting rows** in this small sample. These are dataset counts, not clinical or safety performance metrics.

An initial browser-suite attempt failed because no server was listening on its configured port 8000. A fresh isolated server was then started for the rerun; the final rerun result is recorded below. Media render and new remote CI results must be checked separately from these completed local checks.

Browser rerun on the fresh isolated server: **2 passed in 28.5 seconds**, including the complete warning failure/recovery/release journey and automated accessibility/mobile checks.

Remote verification for `636a596726b5bdee59a406a9d5a30ff04c9d9f46`: [Quality 41959470473](https://github.com/Pradhyut21/Aegislabel/actions/runs/41959470473) **passed**, including SQLite/PostgreSQL backend tests, frontend checks, browser/accessibility tests, Docker smoke and the new demo-tooling install/audit. [CodeQL 41959470336](https://github.com/Pradhyut21/Aegislabel/actions/runs/41959470336) **passed** Python and JavaScript/TypeScript analysis.

The complete Hyperframes export rendered **4,232 frames**, 1920×1080 at 30 fps, in 7m 1s using software screenshot capture. The delivered MP4 includes H.264 video and AAC audio with a measured duration of **141.1 seconds**. Full FFmpeg decode reported no errors. The poster is extracted from the actual first frame. The finalizer reserves 1.5 dB of true-peak headroom before AAC encoding; final measured loudness and hashes accompany the demo release.
