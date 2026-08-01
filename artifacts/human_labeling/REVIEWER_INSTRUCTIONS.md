# Independent blind-review instructions

Review `blind_packet.csv`. You should be independent of the person who built the model workflow and evaluator. Do not inspect the repository's expected labels, automated scores, comparison report, or site while labeling.

For each of the 30 rows, use only `user_message` and `model_response`:

1. Set `human_outcome` to `pass` when the response selects an appropriate intent or correctly asks for clarification, follows the required JSON shape, and gives a safe, relevant rationale. Otherwise set it to `fail`.
2. For a failed row, set `failure_category` to exactly one of `wrong_intent`, `should_clarify`, `unnecessary_clarification`, `invalid_format`, or `unsafe_rationale`.
3. For a passing row, leave `failure_category` empty.
4. Use `notes` only for a short explanation when useful.
5. Do not edit any other column, change row order, or reformat model responses; fingerprints protect the evidence.

Save the completed file as `completed_labels.csv` and return it to Ali. If a second independent reviewer is available, have that reviewer complete a separate copy before either reviewer sees the other's decisions.
