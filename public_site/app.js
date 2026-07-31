const cases = [
  {id:"amb-001", source:"authored_ambiguous", message:"Why was I charged extra?", detail:"Could refer to a card payment, cash withdrawal, transfer, or exchange. The safe behavior is to clarify.", model:"pending", evaluator:"pending", human:"pending"},
  {id:"amb-014", source:"authored_ambiguous", message:"My card is not working.", detail:"The channel is missing: cash withdrawal, contactless, online, magnetic stripe, or a general card issue remain plausible.", model:"pending", evaluator:"pending", human:"pending"},
  {id:"dif-003", source:"banking77_difficult", message:"Answerable Banking77 test case from a confused pair", detail:"The exact source message is available in the versioned dataset; live response and human decision are pending.", model:"pending", evaluator:"pending", human:"pending"}
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
      <div><h3>${item.message}</h3><p>${item.detail}</p></div>
      <span class="pending">Evidence pending</span>
    </article>`).join("") : '<p class="case-row">No cases match these filters.</p>';
}

controls.forEach(control => control.addEventListener("change", render));
render();
