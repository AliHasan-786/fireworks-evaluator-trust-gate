# Design-partner readout - one-week foundation pilot

## What we learned

The highest-risk evaluator error is not a slightly lower average score; it is a false pass on behavior a human rejects. Ambiguous support requests make that concrete: forcing a plausible intent can look operationally convenient while routing the customer incorrectly. Deterministic checks cover ground-truth behavior cheaply; an LLM judge is only justified for whether the explanation names the real ambiguity.

This week verified the evaluation set, scorer contracts, error separation, analysis math, and fail-closed gate. It did not verify Fireworks model performance or evaluator-human alignment because no API key or completed human labels were available.

## What should ship now

- The versioned dataset and manifest.
- Deterministic scorer and Eval Protocol package.
- Resilient, resumable runner and capped smoke-first workflow.
- Blind review packet and explicit leniency/failure-recall report.
- `INSUFFICIENT_EVIDENCE` as the current gate state.

## What should not be automated yet

Do not trigger retraining, promote a model, select the fast model as default, or claim evaluator trust. There is no empirical model comparison and no human calibration denominator.

## Information needed next

1. Valid `FIREWORKS_API_KEY` and current fast, strong, and judge model IDs.
2. Confirmed per-token prices, a conservative retry-inclusive per-case cost bound for those exact models, and approval of the USD 8 hard cap.
3. One primary domain reviewer and preferably a second reviewer for the 30-case blind packet.
4. Customer-specific costs of false route, unnecessary clarification, and abstention.
5. Production failure samples, data-residency constraints, and the rollback owner for any future automation.
