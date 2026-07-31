# Research notes

Accessed 2026-07-31. Product claims below use current primary Fireworks sources only. This project hypothesis is an inference from those sources, not a statement about Fireworks' internal roadmap or a missing product feature.

## Product evidence

1. [Associate Product Manager role](https://job-boards.greenhouse.io/fireworksai/jobs/4235059009)
   - The role combines technical customer advising, developer tooling, inference and fine-tuning workflows, analytical judgment, and concise customer communication.
2. [The Fine-Tuning Bottleneck Isn't the Algorithm](https://fireworks.ai/blog/fine-tuning-bottlenecks)
   - Fireworks describes integration, iteration time, and choosing the right training method as recurring bottlenecks.
   - It says reward functions, graders, and evaluation APIs may need to remain in the customer's environment.
   - It describes a future eval-to-retrain loop in which humans define objectives and guardrails while the system observes failures, trains, validates, and deploys. It also says teams currently stitch pieces of this workflow together manually.
3. [Evaluators](https://docs.fireworks.ai/fine-tuning/evaluators)
   - An evaluator/reward function scores model output from 0 to 1 and defines what good means for RFT.
   - Fireworks recommends starting with rule-based checks, handling malformed outputs, and checking content as well as format to reduce reward hacking.
4. [Create Evaluator API](https://docs.fireworks.ai/api-reference/create-evaluator)
   - Hosted evaluator projects use Eval Protocol, a `requirements.txt`, and pytest files decorated with `@evaluation_test`.
   - Fireworks recommends `ep upload`; the direct API flow creates a resource, uploads an archive, validates it, and polls until active.
5. [Developing Evaluators](https://docs.fireworks.ai/tools-sdks/python-client/developing-evaluators)
   - The Build SDK guide currently documents `fireworks-ai[reward-kit]`, `@reward_function`, `Dataset.from_list`, and `create_evaluation_job`.
   - This guide and the Create Evaluator API show two current integration surfaces. This repository follows the Eval Protocol format requested by the Create Evaluator API and keeps the local scorer framework-independent.
6. [Trilogy customer story](https://fireworks.ai/blog/Trilogy)
   - Fireworks reports that the customer compared open-weight models across latency, quality, and cost, then moved evaluation toward a repeatable production-testing workflow.

## Current implementation references

- [Structured Outputs](https://docs.fireworks.ai/structured-responses/structured-response-formatting): the documented Python pattern is `from fireworks import Fireworks`, then `client.chat.completions.create(...)` with `response_format={"type": "json_schema", ...}`. The prompt must also request JSON.
- [Python SDK reference](https://docs.fireworks.ai/tools-sdks/python-client/sdk-reference): chat completions expose synchronous `create` and asynchronous `acreate` methods plus token usage.
- [Eval Protocol `@evaluation_test`](https://evalprotocol.io/reference/evaluation-test): pointwise evaluators accept and return an `EvaluationRow`; scores belong in `row.evaluation_result.score`, with optional metrics and reason. Local execution is pytest-compatible.

## Product hypothesis

Before a customer automates retraining around an evaluator, it needs evidence that the evaluator reflects human and business judgment. Otherwise the loop can optimize the wrong behavior faster.

That sentence is this project's inference. The sources support the underlying facts - evaluators define the RFT reward, humans set guardrails in the described future loop, and evaluation workflows must balance quality, latency, cost, reliability, and data control - but Fireworks does not state this exact trust-gate proposal.

## Dataset source

- Banking77 source: [PolyAI task-specific datasets](https://github.com/PolyAI-LDN/task-specific-datasets/tree/master/banking_data), pinned by raw file URLs and recorded hashes in the generated manifest.
- Dataset paper: [BANKING77: Intent Detection of Fine-Grained Banking Queries](https://aclanthology.org/2020.coling-main.66/).
- License: CC BY 4.0, as identified by the Hugging Face dataset card and upstream repository metadata. The generated set uses only upstream test examples plus clearly marked original ambiguity cases.

## Design consequence

The gate fails closed. Deterministic correctness comes first; the LLM judge is limited to rationale quality; missing human evidence cannot pass; and failure recall is an explicit condition because average agreement can hide a dangerously lenient evaluator.
