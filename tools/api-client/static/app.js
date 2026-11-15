const el = (id) => document.getElementById(id);
const toastEl = el("toast");
function toast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  setTimeout(() => toastEl.classList.remove("show"), 2400);
}

let collections = [];
let environments = [];
let activeEnv = null;
let current = { collectionId: null, method: "GET", url: "", headers: [], query: [], body: { mode: "none", raw: "" }, auth: { type: "noauth" }, name: "" };
let lastResult = null;

// ---------- environments ----------
async function loadEnvironments() {
  const res = await fetch("/api/environments");
  const data = await res.json();
  environments = data.environments;
  activeEnv = data.active;
  const sel = el("envSelect");
  sel.innerHTML = '<option value="">(no environment)</option>' + environments.map((e) => `<option value="${e.id}">${e.name}</option>`).join("");
  sel.value = activeEnv || "";
}
el("envSelect").addEventListener("change", async (e) => {
  await fetch("/api/environments/active", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ env_id: e.target.value || null }) });
  activeEnv = e.target.value || null;
});
el("envInput").addEventListener("change", async () => {
  if (!el("envInput").files.length) return;
  const form = new FormData();
  for (const f of el("envInput").files) form.append("files", f);
  const res = await fetch("/api/environments/import", { method: "POST", body: form });
  const data = await res.json();
  toast(`Imported ${data.added.length} environment(s)`);
  el("envInput").value = "";
  await loadEnvironments();
});

// ---------- collections ----------
async function loadCollections() {
  const res = await fetch("/api/collections");
  collections = await res.json();
  renderTree();
}

function renderTree() {
  const tree = el("tree");
  tree.innerHTML = "";
  if (!collections.length) {
    tree.innerHTML = '<div class="empty">Import a .postman_collection(.json) file to start.</div>';
    return;
  }
  for (const col of collections) {
    const head = document.createElement("div");
    head.className = "collection";
    head.innerHTML = `<span>${col.name}</span><button class="rm" title="Remove collection">&times;</button>`;
    head.querySelector(".rm").addEventListener("click", async () => {
      await fetch(`/api/collections/${col.id}`, { method: "DELETE" });
      await loadCollections();
    });
    tree.appendChild(head);
    let lastFolder = null;
    for (const r of col.requests) {
      if (r.folder && r.folder !== lastFolder) {
        const f = document.createElement("div");
        f.className = "folder";
        f.textContent = r.folder;
        tree.appendChild(f);
        lastFolder = r.folder;
      }
      const row = document.createElement("div");
      row.className = "req";
      row.innerHTML = `<span class="m ${r.method.toLowerCase()}">${r.method}</span><span class="n">${r.name}</span>`;
      row.addEventListener("click", () => loadRequest(col, r));
      tree.appendChild(row);
    }
  }
}

el("colInput").addEventListener("change", async () => {
  if (!el("colInput").files.length) return;
  const form = new FormData();
  for (const f of el("colInput").files) form.append("files", f);
  const res = await fetch("/api/collections/import", { method: "POST", body: form });
  const data = await res.json();
  toast(`Imported ${data.added.length} collection(s), ${data.added.reduce((a, c) => a + c.count, 0)} requests`);
  el("colInput").value = "";
  await loadCollections();
});

// ---------- request editor ----------
function loadRequest(col, r) {
  document.querySelectorAll(".tree .req").forEach((n) => n.classList.remove("active"));
  event?.currentTarget?.classList.add("active");
  current = {
    collectionId: col.id,
    method: r.method,
    url: r.url,
    headers: r.headers.map((h) => ({ ...h })),
    query: r.query.map((q) => ({ ...q })),
    body: { ...r.body },
    auth: { ...r.auth },
    name: r.name,
  };
  el("method").value = current.method;
  el("url").value = current.url;
  renderRows("headerRows", current.headers);
  renderRows("paramRows", current.query);
  el("bodyText").value = current.body.mode === "raw" ? current.body.raw || "" : "";
  el("authType").value = ["noauth", "bearer", "basic", "apikey"].includes(current.auth.type) ? current.auth.type : "noauth";
  renderAuthFields();
}

function renderRows(containerId, rows) {
  const c = el(containerId);
  c.innerHTML = "";
  for (const row of rows) c.appendChild(makeRow(row, rows));
}
function makeRow(row, rows) {
  const div = document.createElement("div");
  div.className = "row-kv";
  div.innerHTML = `<input class="k" placeholder="key" value="${row.key || ""}"><input class="v" placeholder="value" value="${row.value || ""}"><button class="rm">&times;</button>`;
  div.querySelector(".k").addEventListener("input", (e) => (row.key = e.target.value));
  div.querySelector(".v").addEventListener("input", (e) => (row.value = e.target.value));
  div.querySelector(".rm").addEventListener("click", () => {
    rows.splice(rows.indexOf(row), 1);
    div.remove();
  });
  return div;
}
el("addHeader").addEventListener("click", () => {
  const row = { key: "", value: "" };
  current.headers.push(row);
  el("headerRows").appendChild(makeRow(row, current.headers));
});
el("addParam").addEventListener("click", () => {
  const row = { key: "", value: "" };
  current.query.push(row);
  el("paramRows").appendChild(makeRow(row, current.query));
});
el("bodyText").addEventListener("input", (e) => {
  current.body = { mode: "raw", raw: e.target.value, language: "json" };
});
el("method").addEventListener("change", (e) => (current.method = e.target.value));
el("url").addEventListener("input", (e) => (current.url = e.target.value));

function renderAuthFields() {
  const c = el("authFields");
  c.innerHTML = "";
  const t = current.auth.type;
  const field = (key, placeholder) => {
    const input = document.createElement("input");
    input.placeholder = placeholder;
    input.value = current.auth[key] || "";
    input.addEventListener("input", (e) => (current.auth[key] = e.target.value));
    return input;
  };
  if (t === "bearer") c.appendChild(field("token", "token"));
  if (t === "basic") { c.appendChild(field("username", "username")); c.appendChild(field("password", "password")); }
  if (t === "apikey") { c.appendChild(field("key", "header/param name")); c.appendChild(field("value", "value")); c.appendChild(field("in", "header or query")); }
}
el("authType").addEventListener("change", (e) => {
  current.auth = { type: e.target.value };
  renderAuthFields();
});

document.querySelectorAll(".tab").forEach((t) => {
  t.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((x) => x.classList.remove("on"));
    document.querySelectorAll(".pane").forEach((x) => x.classList.remove("on"));
    t.classList.add("on");
    el(`pane-${t.dataset.tab}`).classList.add("on");
  });
});

// ---------- send ----------
el("sendBtn").addEventListener("click", async () => {
  const reqBody = {
    method: current.method,
    url: current.url,
    headers: current.headers,
    query: current.query,
    body: current.body,
    auth: current.auth,
  };
  el("resp").innerHTML = '<div class="empty">Sending...</div>';
  const res = await fetch("/api/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ request: reqBody, collection_id: current.collectionId, skip_tls_verify: el("skipTls").checked }),
  });
  lastResult = await res.json();
  renderResponse(lastResult);
});

function renderResponse(result) {
  const container = el("resp");
  if (!result.ok) {
    container.innerHTML = `<div class="resp-head"><span class="status" style="color:var(--bad)">Failed</span></div><pre>${escapeHtml(result.error || "unknown error")}</pre>`;
    return;
  }
  const bodyText = result.body_text !== null && result.body_text !== undefined
    ? result.body_text
    : JSON.stringify(result.body_json, null, 2);
  const statusColor = result.status < 400 ? "var(--ok)" : "var(--bad)";
  container.innerHTML = `
    <div class="resp-head">
      <span class="status" style="color:${statusColor}">${result.status} ${escapeHtml(result.reason || "")}</span>
      <span class="time">${result.elapsed_ms} ms &middot; ${result.size_bytes} bytes</span>
      <div class="resp-actions">
        <button class="btn sm" id="evidenceBtn">Save evidence</button>
      </div>
    </div>
    <h4>Response headers</h4><pre>${escapeHtml(JSON.stringify(result.headers, null, 2))}</pre>
    <h4>Body</h4><pre>${escapeHtml(bodyText)}</pre>
    <div id="evidenceOut"></div>
  `;
  el("evidenceBtn").addEventListener("click", captureEvidence);
}

function escapeHtml(s) {
  return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}

// ---------- evidence ----------
async function captureEvidence() {
  const name = current.name || `${current.method}-${current.url}`.slice(0, 60);
  const res = await fetch("/api/evidence", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ entry: lastResult, name }),
  });
  const data = await res.json();
  const out = el("evidenceOut");
  const runsRes = await fetch("/api/qa-runs");
  const runs = await runsRes.json();
  const runOpts = runs.map((r) => `<option value="${r.run}">${r.run}</option>`).join("");
  out.innerHTML = `
    <h4>Evidence captured</h4>
    <img src="/api/evidence/${data.file}" style="max-width:100%;border-radius:10px;border:1px solid var(--line)">
    <div class="row-kv" style="margin-top:10px">
      <select id="runSel">${runOpts}</select>
      <select id="taskSel"></select>
      <button class="btn sm primary" id="saveToRunBtn">Save to QA run</button>
    </div>
  `;
  const runSel = el("runSel");
  const taskSel = el("taskSel");
  const fillTasks = () => {
    const r = runs.find((x) => x.run === runSel.value);
    taskSel.innerHTML = (r ? r.tasks : []).map((t) => `<option value="${t}">${t}</option>`).join("");
  };
  runSel.addEventListener("change", fillTasks);
  fillTasks();
  el("saveToRunBtn").addEventListener("click", async () => {
    await fetch("/api/evidence/save-to-run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file: data.file, run: runSel.value, task: taskSel.value, label: name }),
    });
    toast("Saved into QA run screenshots");
  });
}

document.getElementById("appear").addEventListener("click", (e) => {
  const v = e.target.dataset.v;
  if (!v) return;
  document.documentElement.dataset.theme = v;
  try { localStorage.setItem("api_client_theme", v); } catch (err) {}
});

loadEnvironments();
loadCollections();
