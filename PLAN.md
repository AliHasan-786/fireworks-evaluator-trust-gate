# Implementation plan

- [x] Audit the six requested Fireworks sources and current SDK/Eval Protocol syntax.
- [x] Scaffold a Python 3.11+ `uv` project, offline CI, configuration, and schemas.
- [x] Build and validate the versioned 120-case Banking77-derived dataset and manifest.
- [x] Implement deterministic evaluation, qualitative judge boundaries, analysis, and the fail-closed trust gate.
- [x] Implement resilient Fireworks inference with structured output, accounting, retries, concurrency, and resume support.
- [x] Add the blind 30-case human labeling workflow and validation.
- [x] Add comprehensive mocked/offline tests and a separately marked live smoke path.
- [x] Generate sanitized demo artifacts, reports, PRD, readout, and recruiter-ready static site without inventing human or live Fireworks results.
- [x] Run tests, lint, accessibility checks, secret scan, and desktop/mobile local QA.
- [x] Deploy and verify publicly; capture live desktop and mobile screenshots.
- [x] Connect saved run records to packet export and completed labels to the executable trust gate.
- [x] Add exact packet-content and SHA-256 evidence validation so modified or stale review evidence fails closed.
- [x] Add end-to-end calibration and provenance regression tests.
- [x] Make live cost accounting retry-complete and enforce resume-aware hard-cap admission control.

## Acceptance boundary

The repository may be complete as an offline, deployable artifact while the overall launch remains blocked. The trust gate remains `INSUFFICIENT_EVIDENCE` until valid blind human labels exist, live Fireworks results remain absent without a key, and no public URL is claimed until it has been verified.
