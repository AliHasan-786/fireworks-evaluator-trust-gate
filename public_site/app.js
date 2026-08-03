let cases = [];

const controls = ["model", "source", "eval", "human"].map(name => document.querySelector(`#${name}-filter`));
const list = document.querySelector("#case-list");

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[character]);
}

function percent(value) {
  return value == null ? "Undefined" : `${(value * 100).toFixed(1)}%`;
}

function setText(id, value) {
  document.querySelector(`#${id}`).textContent = value;
}

function render() {
  const [model, source, evaluator, human] = controls.map(control => control.value);
  const filtered = cases.filter(item =>
    (model === "all" || item.model === model) &&
    (source === "all" || item.source === source) &&
    (evaluator === "all" || item.evaluator === evaluator) &&
    (human === "all" || item.human === human)
  );
  list.innerHTML = filtered.length ? filtered.map(item => `
    <article class="case-row">
      <span class="case-id">${escapeHtml(item.id)}</span>
      <div><h3>${escapeHtml(item.message)}</h3><p>${escapeHtml(item.detail)}</p><details><summary>Saved evidence</summary><dl><dt>Model</dt><dd>${escapeHtml(item.modelId)}</dd><dt>Raw response</dt><dd>${escapeHtml(item.response)}</dd><dt>Automated evaluation</dt><dd>${escapeHtml(item.evaluator.toUpperCase())}</dd><dt>Human label</dt><dd>${escapeHtml(item.human.toUpperCase())}</dd><dt>Direction</dt><dd>${escapeHtml(item.direction)}</dd></dl></details></div>
      <span class="pending">TOO STRICT</span>
    </article>`).join("") : '<p class="case-row">No cases match these filters.</p>';
}

async function loadEvidence() {
  const [comparisonResponse, trustResponse] = await Promise.all([
    fetch("data/model_comparison.json"),
    fetch("data/evaluator_trust.json")
  ]);
  if (!comparisonResponse.ok || !trustResponse.ok) throw new Error("Generated evidence request failed");
  const evidence = await comparisonResponse.json();
  const trust = await trustResponse.json();
  const models = evidence.comparison.models;
  const fast = models["accounts/fireworks/models/gpt-oss-20b"];
  const strong = models["accounts/fireworks/models/gpt-oss-120b"];
  setText("fast-accuracy", percent(fast.intent_accuracy));
  setText("strong-accuracy", percent(strong.intent_accuracy));
  setText("fast-ambiguity", percent(fast.ambiguity_detection));
  setText("strong-ambiguity", percent(strong.ambiguity_detection));
  setText("fast-json", percent(fast.json_reliability));
  setText("strong-json", percent(strong.json_reliability));
  setText("fast-latency", `${fast.p50_latency_ms.toFixed(0)} / ${fast.p95_latency_ms.toFixed(0)} ms`);
  setText("strong-latency", `${strong.p50_latency_ms.toFixed(0)} / ${strong.p95_latency_ms.toFixed(0)} ms`);
  setText("fast-cost", `$${fast.estimated_cost_per_1000_cases_usd.toFixed(4)}`);
  setText("strong-cost", `$${strong.estimated_cost_per_1000_cases_usd.toFixed(4)}`);
  document.querySelector("#comparison-summary").textContent = `${evidence.comparison.recommendation} Complete coverage: 120 cases per model; recorded comparison spend $${evidence.coverage.total_recorded_spend_usd.toFixed(6)}.`;
  const metrics = trust.analysis.overall;
  setText("gate-decision", trust.gate.decision);
  setText("gate-agreement", percent(metrics.agreement));
  setText("gate-recall", percent(metrics.failure_recall));
  setText("gate-leniency", percent(metrics.leniency_rate));
  setText("gate-coverage", `${metrics.n} / ${trust.thresholds.minimum_human_cases}`);
  setText("gate-failures", `${metrics.human_failures} human failures`);
  document.querySelector("#gate-summary").textContent = `The complete blind review is sufficient for a decision, but agreement was ${percent(metrics.agreement)} against an ${percent(trust.thresholds.minimum_agreement)} requirement. All ${trust.disagreements.length} disagreements were evaluator-too-strict.`;
  cases = trust.disagreements.map(example => {
    return {
      id: example.case_id,
      source: example.source_type,
      message: example.user_message,
      detail: example.automated_failure_reasons.join(" "),
      model: "live",
      modelId: example.model_id,
      response: example.model_response,
      evaluator: example.automated_pass ? "pass" : "fail",
      human: example.human_outcome,
      direction: example.direction
    };
  });
  render();
}

controls.forEach(control => control.addEventListener("change", render));
loadEvidence().catch(error => {
  document.querySelector("#comparison-summary").textContent = `Generated evidence could not be loaded: ${error.message}`;
  list.innerHTML = '<p class="case-row">Evidence unavailable.</p>';
});
