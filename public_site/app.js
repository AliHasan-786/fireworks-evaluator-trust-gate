const cases = [
  {id:"amb-001", source:"authored_ambiguous", message:"Why was I charged extra?", expected:"Ask which transaction or channel the charge concerns; do not force an intent.", detail:"Could refer to a card payment, cash withdrawal, transfer, or exchange. A false pass would make the evaluator too lenient.", model:"pending", evaluator:"pending", human:"pending"},
  {id:"amb-014", source:"authored_ambiguous", message:"My card is not working.", expected:"Ask where or how the card failed; do not force an intent.", detail:"Cash withdrawal, contactless, online, magnetic stripe, and general card issues remain plausible. A forced route can send the case to the wrong workflow.", model:"pending", evaluator:"pending", human:"pending"},
  {id:"dif-003", source:"banking77_difficult", message:"Why was I charged a fee for withdrawing cash?", expected:"Route to cash_withdrawal_charge without clarification.", detail:"The mention of a fee makes this answerable despite similarity to exchange-rate and unrecognized-withdrawal intents. A false fail would make the evaluator too strict.", model:"pending", evaluator:"pending", human:"pending"}
];

const controls = ["model", "source", "eval", "human"].map(name => document.querySelector(`#${name}-filter`));
const list = document.querySelector("#case-list");

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
      <span class="case-id">${item.id}</span>
      <div><h3>${item.message}</h3><p>${item.detail}</p><details><summary>Case detail</summary><dl><dt>Expected behavior</dt><dd>${item.expected}</dd><dt>Model response</dt><dd>Pending Fireworks run</dd><dt>Automated evaluation</dt><dd>Pending model response</dd><dt>Human label</dt><dd>Pending blind review</dd><dt>Why it matters</dt><dd>${item.detail}</dd></dl></details></div>
      <span class="pending">Evidence pending</span>
    </article>`).join("") : '<p class="case-row">No cases match these filters.</p>';
}

controls.forEach(control => control.addEventListener("change", render));
render();
