# Critical TELIPORT self-review

| Judge question | Evidence and remaining boundary |
| --- | --- |
| Can a judge execute the warning scenario? | Playwright completes source update → faulty warning → blocked validation → correction → independent review → release download. Guided instructions are built into Overview. |
| Is this more than a dashboard? | API-backed persistence, SVG/PDF generation, PDF ingestion, deterministic validation, mutation execution, reviewer state transitions and actual ZIP downloads. |
| Are metrics invented? | No. Mutation and baseline decisions execute against isolated copies. Impact metrics use expected fixtures. Human timing remains unmeasured until review records exist. Small-corpus limits are explicit. |
| Are unrelated labels protected? | Same-device field-dependency intersection controls source propagation. Tests verify both unrelated devices and non-dependent source fields. |
| Does later artwork invalidate release eligibility? | Approval does not transfer to successors; earlier approved revisions cannot release after a newer revision exists. Tested at the API boundary. |
| Is the validation engine genuinely challenged? | 24 distinct faults plus change-targeted selection. A negative test disables warning detection and observes escaped faults. |
| Is the evidence inspectable? | Each configured field maps to a document quote/location or controlled registry record; findings, reviewer and artwork hashes are retained. |
| Is storage immutable? | No. Hash-chain verification is implemented; privileged rewrites and tail truncation need an external trusted anchor. |
| Is this production-ready or certified? | No. Educational research prototype, bounded checks, synthetic identifiers and local accounts. |
| Can another developer reproduce it? | Source, pinned Python/npm dependencies, Alembic, real source fixtures, Compose, local/Windows instructions and executed test report are included. Windows and full app-image builds remain unverified. |

Observed issues fixed during review: omitted hash fields, low-contrast secondary text, a navigation accessible-name conflict, test-runner collection overlap, insufficient barcode raster readability, irrelevant source propagation, stale dashboard readiness and release eligibility for superseded artwork. No test outcome was replaced with a hardcoded success.

Publication review adds strict frontend domain interfaces, bounded HTTP/provider streams, secure rejection responses, trusted hosts, capped/expired sessions, a publication-content scanner, pinned CI actions and real application captures. Public source contains no runtime database, sessions, uploads, credentials or browser traces.
