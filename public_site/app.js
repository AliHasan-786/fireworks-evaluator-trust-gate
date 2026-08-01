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
      <div><h3>${escapeHtml(item.message)}</h3><p>${escapeHtml(item.detail)}</p><details><summary>Saved evidence</summary><dl><dt>Model</dt><dd>${escapeHtml(item.modelId)}</dd><dt>Raw response</dt><dd>${escapeHtml(item.response)}</dd><dt>Automated evaluation</dt><dd>${escapeHtml(item.evaluator.toUpperCase())}</dd><dt>Human label</dt><dd>Pending independent blind review</dd></dl></details></div>
      <span class="${item.evaluator === "pass" ? "verified" : "pending"}">${escapeHtml(item.evaluator.toUpperCase())}</span>
    </article>`).join("") : '<p class="case-row">No cases match these filters.</p>';
}

async function loadEvidence() {
  const response = await fetch("data/model_comparison.json");
  if (!response.ok) throw new Error(`Evidence request failed: ${response.status}`);
  const evidence = await response.json();
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
  cases = evidence.examples.map(example => {
    const automated = example.automated_evaluation;
    return {
      id: example.case_id,
      source: example.source_type,
      message: example.user_message,
      detail: automated ? automated.failure_reasons.join(" ") || "All deterministic checks passed." : "Model response could not be scored.",
      model: "live",
      modelId: example.model_id,
      response: example.model_response,
      evaluator: automated?.passed ? "pass" : "fail",
      human: "pending"
    };
  });
  render();
}

controls.forEach(control => control.addEventListener("change", render));
loadEvidence().catch(error => {
  document.querySelector("#comparison-summary").textContent = `Generated evidence could not be loaded: ${error.message}`;
  list.innerHTML = '<p class="case-row">Evidence unavailable.</p>';
});
