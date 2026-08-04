const treeRoot = document.getElementById("tree");
const gridBody = document.querySelector("#signal-grid tbody");
const detail = document.getElementById("detail");
const search = document.getElementById("search");
const consoleOutput = document.getElementById("console");
let allSignals = [];

function log(message, error = false) {
  consoleOutput.textContent += `\n${error ? "ERROR" : "INFO"} ${new Date().toLocaleTimeString()} ${message}`;
  consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

function setDetails(signal) {
  detail.replaceChildren();
  const heading = document.createElement("h2");
  heading.textContent = signal.path;
  detail.append(heading);
  const fields = [["Type", signal.type], ["Owner", signal.owner], ["Since", signal.since], ["Datatype", signal.datatype], ["Unit", signal.unit], ["Range", `${signal.minimum ?? "-"} .. ${signal.maximum ?? "-"}`], ["Description", signal.description]];
  const list = document.createElement("dl");
  fields.forEach(([label, value]) => { const term = document.createElement("dt"); term.textContent = label; const definition = document.createElement("dd"); definition.textContent = value || "-"; list.append(term, definition); });
  detail.append(list);
}

function renderGrid(signals) {
  gridBody.replaceChildren();
  document.getElementById("grid-status").textContent = `${signals.length} nodes`;
  signals.forEach(signal => { const row = document.createElement("tr"); [signal.path, signal.type, signal.datatype || "branch", signal.unit || "-", signal.owner || "-", signal.since || "-", `${signal.minimum ?? "-"}..${signal.maximum ?? "-"}`].forEach(value => { const cell = document.createElement("td"); cell.textContent = value; row.append(cell); }); row.onclick = () => { document.querySelectorAll("tbody tr.active").forEach(active => active.classList.remove("active")); row.classList.add("active"); setDetails(signal); }; gridBody.append(row); });
}

function renderNode(node, depth = 0) {
  const container = document.createElement("div");
  const button = document.createElement("button");
  button.style.paddingLeft = `${depth * 14 + 4}px`;
  button.textContent = `${node.type === "branch" ? "▸" : "•"} ${node.name}`;
  button.onclick = () => { if (node.type !== "branch") { const signal = allSignals.find(item => item.path === node.path); if (signal) setDetails(signal); } else { container.classList.toggle("collapsed"); } };
  container.append(button);
  node.children.forEach(child => container.append(renderNode(child, depth + 1)));
  return container;
}

async function load() {
  const [treeResponse, signalsResponse] = await Promise.all([fetch("/api/v1/tree"), fetch("/api/v1/signals")]);
  if (!treeResponse.ok || !signalsResponse.ok) throw new Error("Unable to load catalog data.");
  const tree = await treeResponse.json();
  allSignals = await signalsResponse.json();
  treeRoot.replaceChildren(renderNode(tree));
  document.getElementById("node-count").textContent = `${allSignals.length}`;
  renderGrid(allSignals);
  log(`Loaded ${allSignals.length} catalog nodes.`);
}

search.addEventListener("input", () => { const tokens = search.value.toLowerCase().trim().split(/\s+/).filter(Boolean); const type = tokens.find(token => token.startsWith("type:"))?.slice(5); const node = tokens.find(token => token.startsWith("node:"))?.slice(5); const text = tokens.filter(token => !token.startsWith("type:") && !token.startsWith("node:")).join(" "); const matches = allSignals.filter(signal => (!type || (signal.datatype || "branch").toLowerCase() === type) && (!node || signal.path.toLowerCase().includes(node)) && (!text || [signal.path, signal.description, signal.owner, signal.datatype, signal.unit].join(" ").toLowerCase().includes(text))); renderGrid(matches); });
document.getElementById("validate").onclick = async () => { log("Running catalog validation…"); const response = await fetch("/api/v1/validate", { method: "POST" }); const result = await response.json(); if (result.valid) log(`Validation passed (${result.checked} signals).`); else result.issues.forEach(issue => log(`${issue.path}: ${issue.error}`, true)); };
async function runAction(name, label) { log(`${label} started…`); const response = await fetch(`/api/v1/actions/${name}`, { method: "POST" }); const result = await response.json(); if (!response.ok || !result.ok) log(result.error || `${label} failed.`, true); else log(result.message); }
document.getElementById("generate").onclick = () => runAction("generate", "Generation");
document.getElementById("build").onclick = () => { if (window.confirm("Build the container image using the configured engine?")) runAction("build", "Container build"); };
document.getElementById("clear-console").onclick = () => { consoleOutput.textContent = "Console cleared."; };
const dialog = document.getElementById("add-dialog");
document.getElementById("add-signal").onclick = () => dialog.showModal();
document.getElementById("add-form").addEventListener("submit", async event => { event.preventDefault(); const form = new FormData(event.currentTarget); const payload = Object.fromEntries(form.entries()); payload.writable = form.get("writable") === "on"; const response = await fetch("/api/v1/signals", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }); const result = await response.json(); if (!response.ok) { log(result.error || "Signal could not be added.", true); return; } dialog.close(); log(`Added ${result.path}.`); await load(); });
load().catch(error => log(error.message, true));
