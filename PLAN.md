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
- [x] Repair the real async Fireworks SDK contract and add a transport-boundary SDK regression test.
- [x] Repair Eval Protocol collection, dataset resolution, and its MCP v1 dependency boundary.
- [x] Validate live metadata and official pricing for GPT-OSS 20B and GPT-OSS 120B.
- [x] Complete the capped 5-case-per-model smoke and 120-case-per-model comparison.
- [x] Generate the machine-readable comparison, decision memo, sanitized site data, and exact-record blind packet.
- [x] Receive a completed 30-case packet from a blind reviewer who did not build the evaluator.
- [x] Validate the returned evidence, run the trust gate, and generate the final evaluator-human report.
- [x] Redeploy the merged site to production, confirm the Vercel deployment is ready, and finalize only resume claims traceable to merged public evidence.

## Acceptance boundary

The live comparison is complete and its model decision is `NO_DEPLOY` because neither model meets the ambiguity guardrail. The evaluator trust gate is `FAIL`: a fingerprint-validated 30-case review produced 76.7% agreement against the 85% requirement. Reviewer 1 was a non-expert family member completing a quick informal blind pass, so the result demonstrates the end-to-end workflow rather than domain-expert or inter-rater validation. A separately isolated Reviewer 2 app is available as an optional evidence-strengthening follow-up.
