# Implementation plan

- [x] Audit the six requested Fireworks sources and current SDK/Eval Protocol syntax.
- [ ] Scaffold a Python 3.11+ `uv` project, offline CI, configuration, and schemas.
- [ ] Build and validate the versioned 120-case Banking77-derived dataset and manifest.
- [ ] Implement deterministic evaluation, qualitative judge boundaries, analysis, and the fail-closed trust gate.
- [ ] Implement resilient Fireworks inference with structured output, accounting, retries, concurrency, and resume support.
- [ ] Add the blind 30-case human labeling workflow and validation.
- [ ] Add comprehensive mocked/offline tests and a separately marked live smoke path.
- [ ] Generate sanitized demo artifacts, reports, PRD, readout, and recruiter-ready static site without inventing human or live Fireworks results.
- [ ] Run tests, lint, accessibility checks, secret scan, and desktop/mobile local QA.
- [ ] Deploy and verify publicly if authentication is available; otherwise document the exact blocker without claiming completion.

## Acceptance boundary

The repository may be complete as an offline, deployable artifact while the overall launch remains blocked. The trust gate remains `INSUFFICIENT_EVIDENCE` until valid blind human labels exist, live Fireworks results remain absent without a key, and no public URL is claimed until it has been verified.
