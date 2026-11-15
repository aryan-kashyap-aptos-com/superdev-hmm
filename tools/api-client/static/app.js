const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => [...(r || document).querySelectorAll(s)];
const el = (id) => document.getElementById(id);

/* ============ STATE ============ */
let collections = [];
let environments = [];
let activeEnv = null;
let vars = {};
let drafts = {};
let dirty = {};
let activeId = null;
let activeCollectionId = null;
let shut = {};
let tab = "params";
let resTab = "body";
let lastResult = null;
let busy = false;
let skipTls = false;
let cmdResolved = true;
let seq = 1;
let rowIndex = 0;

/* ============ HELPERS ============ */
const VAR_RE = /\{\{\s*([^}]+?)\s*\}\}/g;
const resolve = (s, v) => (s || "").replace(VAR_RE, (m, k) => (v[k] != null ? v[k] : m));
const missingVars = (s, v) => [...new Set([...(s || "").matchAll(VAR_RE)].map((m) => m[1]).filter((k) => v[k] == null))];
const splitUrl = (url) => {
  const i = url.indexOf("?");
  if (i < 0) return { base: url, params: [] };
  return { base: url.slice(0, i), params: url.slice(i + 1).split("&").filter(Boolean).map((p) => { const [k, ...v] = p.split("="); return { key: k, value: v.join("="), disabled: false }; }) };
};
const joinUrl = (base, ps) => { const q = ps.filter((p) => p.key).map((p) => (p.value ? `${p.key}=${p.value}` : p.key)).join("&"); return q ? `${base}?${q}` : base; };
const jsonCheck = (s) => { if (!s.trim()) return "empty"; try { JSON.parse(s); return "ok"; } catch (e) { return e.message; } };
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const markJson = (s) => esc(s).replace(/("(\\u[a-fA-F0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false)\b|\bnull\b|-?\d+(\.\d+)?([eE][+-]?\d+)?)/g, (m) => {
  const c = /^"/.test(m) ? (/:$/.test(m) ? "j-k" : "j-s") : /true|false/.test(m) ? "j-b" : /null/.test(m) ? "j-z" : "j-n";
  return `<span class="${c}">${m}</span>`;
});
const shq = (s) => "'" + String(s).replace(/'/g, "'\\''") + "'";
const fallbackCopy = (t) => {
  const ta = document.createElement("textarea"); ta.value = t; ta.style.position = "fixed"; ta.style.opacity = "0";
  document.body.appendChild(ta); ta.select(); try { document.execCommand("copy"); } catch (e) {} ta.remove();
};
const copyText = (t) => { if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(t).catch(() => fallbackCopy(t)); else fallbackCopy(t); };
const fmtSize = (b) => (b == null ? "?" : b < 1024 ? `${b} B` : `${(b / 1024).toFixed(1)} KB`);
const pad2 = (n) => String(n).padStart(2, "0");
function toast(msg) {
  const t = el("toast");
  t.textContent = msg; t.style.opacity = "1"; t.style.transform = "none";
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { t.style.opacity = "0"; t.style.transform = "translateY(8px)"; }, 2200);
}

function toCmd(req, variables, skip, resolved) {
  const r = (x) => (resolved ? resolve(x, variables) : x);
  const out = [`curl -X ${req.method} ${shq(r(req.url))}`];
  if (skip) out.push("--insecure");
  req.headers.filter((h) => !h.disabled && h.key).forEach((h) => out.push(`-H ${shq(`${h.key}: ${r(h.value)}`)}`));
  if (req.auth.type === "bearer" && req.auth.token) out.push(`-H ${shq(`Authorization: Bearer ${r(req.auth.token)}`)}`);
  if (req.auth.type === "basic" && req.auth.username) out.push(`-u ${shq(`${r(req.auth.username)}:${r(req.auth.password || "")}`)}`);
  if (req.auth.type === "apikey" && req.auth.key) {
    if ((req.auth.in || "header") === "query") out.push(`-G --data-urlencode ${shq(`${req.auth.key}=${r(req.auth.value || "")}`)}`);
    else out.push(`-H ${shq(`${req.auth.key}: ${r(req.auth.value || "")}`)}`);
  }
  if (req.method !== "GET" && req.body.mode === "raw" && req.body.raw && req.body.raw.trim()) {
    let b = req.body.raw; try { b = JSON.stringify(JSON.parse(b)); } catch (e) {}
    out.push(`--data-raw ${shq(r(b))}`);
  }
  return out.join(" \\\n  ");
}

/* ============ DATA LOADING ============ */
async function fetchJSON(url, opts) { const r = await fetch(url, opts); return r.json(); }

async function loadEnvironments() {
  const data = await fetchJSON("/api/environments");
  environments = data.environments; activeEnv = data.active;
  renderEnvSelect(); await loadVars();
}
async function loadCollections() {
  collections = await fetchJSON("/api/collections");
  renderList();
}
async function loadVars() {
  const qs = activeCollectionId ? `?collection_id=${activeCollectionId}` : "";
  vars = await fetchJSON(`/api/variables${qs}`);
  renderVars();
  if (activeId) refreshDerived();
}

/* ============ SIDEBAR ============ */
function renderEnvSelect() {
  const sel = el("envSelect");
  sel.innerHTML = '<option value="">(no environment)</option>' + environments.map((e) => `<option value="${e.id}">${esc(e.name)}</option>`).join("");
  sel.value = activeEnv || "";
}
let varsOpen = false;
function renderVars() {
  const entries = Object.entries(vars);
  const setCount = entries.filter(([, v]) => v).length;
  const summary = el("varsSummary");
  summary.textContent = entries.length ? `${entries.length} variables · ${setCount} set` : "no variables";
  el("varsToggle").setAttribute("aria-expanded", varsOpen);
  el("varsEdit").hidden = !varsOpen;
  if (varsOpen) renderVarsRows();
}
function renderVarsRows() {
  const envObj = environments.find((e) => e.id === activeEnv);
  const rowsEl = el("varsRows");
  const q = (el("varsFilter").value || "").toLowerCase();
  if (!envObj) {
    rowsEl.innerHTML = '<p class="hint">Select an environment above to edit its values.</p>';
    return;
  }
  const keys = Object.keys(envObj.values).filter((k) => k.toLowerCase().includes(q)).sort();
  rowsEl.innerHTML = keys.length
    ? keys.map((k) => `<div class="var-row"><span class="var-key" title="${esc(k)}">${esc(k)}</span><input class="var-val" data-k="${esc(k)}" value="${esc(envObj.values[k] ?? "")}"></div>`).join("")
    : '<p class="hint">No match.</p>';
  $$(".var-val", rowsEl).forEach((input) => {
    input.addEventListener("change", async (e) => {
      envObj.values[e.target.dataset.k] = e.target.value;
      await fetch(`/api/environments/${envObj.id}/values`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ values: envObj.values }) });
      toast("Saved");
      await loadVars();
    });
  });
}
el("varsToggle").addEventListener("click", () => { varsOpen = !varsOpen; renderVars(); });
el("varsFilter").addEventListener("input", renderVarsRows);

function findReqById(id) {
  for (const c of collections) {
    const r = c.requests.find((x) => x.id === id);
    if (r) return { col: c, req: r };
  }
  return null;
}

function renderList() {
  rowIndex = 0;
  const list = el("list");
  const q = el("searchInput").value.trim().toLowerCase();
  list.innerHTML = "";
  if (!collections.length) {
    list.innerHTML = '<div class="wait-note" style="padding:var(--s-6) var(--s-4)">Import a .postman_collection(.json) file below to start.</div>';
    return;
  }
  for (const col of collections) {
    let requests = col.requests;
    if (q) requests = requests.filter((r) => `${r.method} ${r.name} ${r.url} ${r.folder}`.toLowerCase().includes(q));
    if (!requests.length) continue;

    const head = document.createElement("div");
    head.className = "collection";
    head.innerHTML = `<span>${esc(col.name)}</span><button class="rm mono" title="Remove collection">&times;</button>`;
    head.querySelector(".rm").addEventListener("click", async () => {
      await fetch(`/api/collections/${col.id}`, { method: "DELETE" });
      await loadCollections();
    });
    list.appendChild(head);

    let lastFolder = undefined;
    let folderOpen = true;
    for (const r of requests) {
      if (r.folder !== lastFolder) {
        lastFolder = r.folder;
        if (r.folder) {
          const key = col.id + "::" + r.folder;
          folderOpen = !!q || !shut[key];
          const count = requests.filter((x) => x.folder === r.folder).length;
          const fEl = document.createElement("button");
          fEl.className = "folder rise"; fEl.style.setProperty("--i", rowIndex++);
          fEl.setAttribute("aria-expanded", folderOpen);
          fEl.innerHTML = `<span class="tri mono" aria-hidden>&rsaquo;</span><b>${esc(r.folder)}</b><span class="mono">${pad2(count)}</span>`;
          fEl.addEventListener("click", () => { shut[key] = !shut[key]; renderList(); });
          list.appendChild(fEl);
        } else {
          folderOpen = true;
        }
      }
      if (!folderOpen) continue;
      const row = document.createElement("button");
      row.className = "row rise"; row.style.setProperty("--i", rowIndex++);
      row.setAttribute("aria-current", r.id === activeId);
      const live = drafts[r.id] || r;
      row.innerHTML = `<span class="m m-${live.method}">${live.method === "DELETE" ? "DEL" : live.method}</span><span class="nm">${esc(live.name)}</span>${dirty[r.id] ? '<span class="dot"></span>' : ""}`;
      row.title = r.name;
      row.addEventListener("click", () => openRequest(col, r));
      list.appendChild(row);
    }
  }
}

/* ============ REQUEST OPEN / CREATE ============ */
function openRequest(col, r) {
  if (!drafts[r.id]) drafts[r.id] = JSON.parse(JSON.stringify(r));
  activeId = r.id; activeCollectionId = col.id;
  tab = drafts[r.id].method === "GET" ? "params" : "body";
  resTab = "body"; lastResult = null;
  closeDrawer();
  loadVars();
  renderList();
  renderMain();
}
function createScratch() {
  const id = "new-" + seq++;
  drafts[id] = { id, name: "Untitled request", method: "GET", url: "", headers: [], query: [], body: { mode: "none", raw: "" }, auth: { type: "noauth" } };
  activeId = id; activeCollectionId = null;
  tab = "params"; resTab = "body"; lastResult = null;
  closeDrawer();
  loadVars();
  renderList();
  renderMain();
  setTimeout(() => el("urlInput") && el("urlInput").focus(), 0);
}
function update(patch) {
  drafts[activeId] = { ...drafts[activeId], ...patch };
  dirty[activeId] = true;
  renderList();
}

/* ============ MOBILE DRAWER ============ */
function openDrawer() { el("side").classList.add("open"); el("scrim").classList.add("open"); }
function closeDrawer() { el("side").classList.remove("open"); el("scrim").classList.remove("open"); }
el("scrim").addEventListener("click", closeDrawer);

/* ============ MAIN RENDER ============ */
function currentReq() { return activeId ? drafts[activeId] : null; }

function refreshDerived() {
  const req = currentReq();
  if (!req) return;
  const missing = missingVars(req.url + " " + req.headers.filter((h) => !h.disabled).map((h) => h.value).join(" "), vars);
  const resolveLine = el("resolveLine");
  if (resolveLine) {
    if (!req.url.trim()) resolveLine.innerHTML = '<span class="t">Enter a URL to send</span>';
    else if (missing.length) resolveLine.innerHTML = `<span class="err">Not defined in ${esc(activeEnv ? (environments.find((e) => e.id === activeEnv) || {}).name || "" : "(no environment)")}: ${missing.map((m) => `{{${m}}}`).join(", ")}</span>`;
    else resolveLine.innerHTML = `<span class="t">&rarr; ${esc(resolve(req.url, vars))}</span>`;
  }
  const mirror = el("urlMirror");
  if (mirror) {
    mirror.innerHTML = req.url.split(/(\{\{[^}]*\}\})/g).map((p) => {
      const m = p.match(/^\{\{\s*(.*?)\s*\}\}$/);
      if (!m) return esc(p);
      return `<span class="${vars[m[1]] != null ? "var-ok" : "var-bad"}">${esc(p)}</span>`;
    }).join("");
  }
  const bodyState = req.method !== "GET" ? jsonCheck(req.body.mode === "raw" ? req.body.raw : "") : "empty";
  const bodyBroken = req.method !== "GET" && req.body.mode === "raw" && bodyState !== "ok" && bodyState !== "empty";
  const sendBtn = el("sendBtn");
  if (sendBtn) sendBtn.disabled = busy || !req.url.trim() || bodyBroken;
  if (tab === "cmd") renderCmdPane();
  if (tab === "body") {
    const bad = el("bodyBad");
    if (bad) bad.textContent = bodyBroken ? bodyState : "";
    const code = el("bodyText");
    if (code) code.classList.toggle("is-bad", !!bodyBroken);
  }
}

function renderCmdPane() {
  const req = currentReq(); if (!req) return;
  const pane = el("pane-cmd"); if (!pane) return;
  const cmd = toCmd(req, vars, skipTls, cmdResolved);
  const missing = missingVars(req.url, vars);
  pane.innerHTML = `
    <div class="body-bar">
      <div class="seg" role="group" aria-label="Variables in command">
        <button id="cmdResolvedBtn" aria-pressed="${cmdResolved}">Resolved</button>
        <button id="cmdRawBtn" aria-pressed="${!cmdResolved}">{{vars}}</button>
      </div>
      <button class="link" id="copyCmdBtn" ${req.url.trim() ? "" : "disabled"}>Copy</button>
    </div>
    ${req.url.trim() ? `<pre class="code" style="min-height:auto" aria-label="cURL command">${esc(cmd)}</pre>` : '<p class="hint">Enter a URL to generate the command.</p>'}
    ${cmdResolved && missing.length ? `<p class="hint" style="color:var(--signal)">Still contains undefined ${missing.map((m) => `{{${m}}}`).join(", ")}.</p>` : ""}
    ${skipTls ? '<p class="hint">Includes --insecure because TLS verify is off.</p>' : ""}
  `;
  el("cmdResolvedBtn").addEventListener("click", () => { cmdResolved = true; renderCmdPane(); });
  el("cmdRawBtn").addEventListener("click", () => { cmdResolved = false; renderCmdPane(); });
  el("copyCmdBtn").addEventListener("click", () => { copyText(cmd); toast("Copied"); });
}

function renderKV(rows, opts) {
  const { toggle = true, keyLabel = "Key", onChange } = opts;
  const table = document.createElement("table");
  table.className = "kv";
  const build = () => {
    const list = [...rows, { key: "", value: "", disabled: false, ghost: true }];
    table.innerHTML = `<colgroup>${toggle ? "<col style='width:32px'>" : ""}<col style="width:38%"><col><col style="width:32px"></colgroup>
      <thead><tr>${toggle ? "<th></th>" : ""}<th class="cap">${keyLabel}</th><th class="cap">Value</th><th></th></tr></thead>
      <tbody></tbody>`;
    const tbody = table.querySelector("tbody");
    list.forEach((r, i) => {
      const tr = document.createElement("tr");
      if (!r.disabled) tr.className = ""; else tr.className = "off";
      tr.innerHTML = `${toggle ? `<td style="text-align:center">${!r.ghost ? `<input type="checkbox" ${!r.disabled ? "checked" : ""}>` : ""}</td>` : ""}
        <td><input type="text" value="${esc(r.key)}" placeholder="${r.ghost ? `+ ${keyLabel.toLowerCase()}` : ""}"></td>
        <td><input type="text" value="${esc(r.value)}" placeholder="${r.ghost ? "value" : ""}"></td>
        <td>${!r.ghost ? '<button class="x mono">&times;</button>' : ""}</td>`;
      const kInput = tr.children[toggle ? 1 : 0].querySelector("input");
      const vInput = tr.children[toggle ? 2 : 1].querySelector("input");
      const commit = (patch) => {
        if (r.ghost) {
          if (!patch.key && !patch.value) return;
          rows.push({ key: patch.key || "", value: patch.value || "", disabled: false });
          onChange(rows); build(); refreshDerived();
        } else {
          Object.assign(r, patch);
          onChange(rows); refreshDerived();
        }
      };
      kInput.addEventListener("input", (e) => commit({ key: e.target.value }));
      vInput.addEventListener("input", (e) => commit({ value: e.target.value }));
      if (toggle && !r.ghost) {
        tr.querySelector('input[type=checkbox]').addEventListener("change", (e) => { r.disabled = !e.target.checked; onChange(rows); build(); refreshDerived(); });
      }
      if (!r.ghost) {
        tr.querySelector(".x").addEventListener("click", () => { rows.splice(rows.indexOf(r), 1); onChange(rows); build(); refreshDerived(); });
      }
      tbody.appendChild(tr);
    });
  };
  build();
  return table;
}

function renderMain() {
  const main = el("main");
  const req = currentReq();
  if (!req) {
    main.innerHTML = `
      <section class="empty">
        <button class="menu" id="menuBtn">&equiv; Requests</button>
        <h1>No request <b>on the board.</b></h1>
        <p>Pick one from the timetable, or start a blank request. Variables like <span class="mono">{{host}}</span> resolve from the active environment.</p>
        <button class="send" id="emptyNewBtn">New request <small>+</small></button>
        <dl><dt><kbd>Ctrl Enter</kbd></dt><dd>Send the open request</dd><dt><kbd>Ctrl K</kbd></dt><dd>Filter requests</dd><dt><kbd>Esc</kbd></dt><dd>Close the list on mobile</dd></dl>
      </section>`;
    el("menuBtn").addEventListener("click", openDrawer);
    el("emptyNewBtn").addEventListener("click", createScratch);
    return;
  }
  const found = findReqById(req.id);
  const where = found ? { name: found.col.name + (req.folder ? " / " + req.folder : "") } : null;
  const { base, params } = splitUrl(req.url);
  const counts = { params: params.length, headers: req.headers.filter((h) => !h.disabled && h.key).length };
  const METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"];

  main.innerHTML = `
    <header class="head">
      <button class="menu" id="menuBtn">&equiv; Requests</button>
      <div class="crumb"><span class="cap">${where ? esc(where.name) : "Scratch"}</span>${dirty[req.id] ? '<span class="cap">&middot; edited</span>' : ""}</div>
      <div class="title"><input type="text" id="nameInput" value="${esc(req.name)}" aria-label="Request name"></div>
    </header>
    <div>
      <div class="line">
        <select class="meth meth-${req.method}" id="methodSelect" aria-label="HTTP method">
          ${METHODS.map((m) => `<option ${m === req.method ? "selected" : ""}>${m}</option>`).join("")}
        </select>
        <div class="url">
          <div class="url-mirror" id="urlMirror" aria-hidden></div>
          <input type="text" id="urlInput" value="${esc(req.url)}" spellcheck="false" placeholder="https://{{host}}/orders" aria-label="Request URL">
        </div>
        <button class="tls" id="tlsBtn" aria-pressed="${skipTls}" title="Skip TLS certificate verification"><span class="box" aria-hidden></span>Skip TLS</button>
        <button class="send" id="sendBtn">${busy ? "Sending" : "Send"}<small>${busy ? "" : "Ctrl+Enter"}</small></button>
      </div>
      <div class="resolve" id="resolveLine"></div>
    </div>
    <div class="split">
      <section class="cfg">
        <div class="tabs" role="tablist">
          ${["params", "headers", "body", "auth", "cmd"].map((t) => `<button role="tab" class="tab" data-tab="${t}" aria-selected="${tab === t}">${t === "cmd" ? "cURL" : t[0].toUpperCase() + t.slice(1)}${counts[t] ? `<sup>${counts[t]}</sup>` : ""}</button>`).join("")}
        </div>
        <div class="panel" role="tabpanel" id="panel"></div>
      </section>
      <div class="resize-v" id="splitResizer" role="separator" aria-orientation="vertical" aria-label="Resize request/response"></div>
      <section class="res" aria-live="polite" aria-busy="${busy}" id="resSection"></section>
    </div>
  `;

  el("menuBtn").addEventListener("click", openDrawer);
  el("nameInput").addEventListener("input", (e) => update({ name: e.target.value }));
  el("methodSelect").addEventListener("change", (e) => { update({ method: e.target.value }); renderMain(); });
  el("urlInput").addEventListener("input", (e) => { req.url = e.target.value; dirty[req.id] = true; refreshDerived(); });
  el("tlsBtn").addEventListener("click", () => { skipTls = !skipTls; el("tlsBtn").setAttribute("aria-pressed", skipTls); refreshDerived(); });
  el("sendBtn").addEventListener("click", sendCurrent);
  $$(".tabs .tab").forEach((t) => t.addEventListener("click", () => { tab = t.dataset.tab; renderMain(); }));
  initSplitResizer();

  renderPanel();
  renderResponse();
  refreshDerived();
}

function renderPanel() {
  const req = currentReq();
  const panel = el("panel");
  panel.innerHTML = "";
  if (tab === "params") {
    const { base, params } = splitUrl(req.url);
    const table = renderKV(params, { toggle: false, keyLabel: "Param", onChange: (rows) => { req.url = joinUrl(base, rows); dirty[req.id] = true; el("urlInput") && (el("urlInput").value = req.url); } });
    panel.appendChild(table);
    const hint = document.createElement("p"); hint.className = "hint"; hint.textContent = "Mirrors the query string. Edit here or in the URL."; panel.appendChild(hint);
  } else if (tab === "headers") {
    panel.appendChild(renderKV(req.headers, { keyLabel: "Header", onChange: () => { dirty[req.id] = true; renderMain(); } }));
  } else if (tab === "body") {
    const bar = document.createElement("div"); bar.className = "body-bar";
    bar.innerHTML = `<span class="cap">application/json</span><span class="bad" id="bodyBad"></span><button class="link" id="fmtBtn">Format</button>`;
    panel.appendChild(bar);
    const ta = document.createElement("textarea");
    ta.className = "code"; ta.id = "bodyText"; ta.spellcheck = false;
    ta.placeholder = req.method === "GET" ? "GET requests usually have no body" : '{ "orderId": "SO-10021" }';
    ta.value = req.body.mode === "raw" ? (req.body.raw || "") : "";
    ta.addEventListener("input", (e) => { req.body = { mode: "raw", raw: e.target.value, language: "json" }; dirty[req.id] = true; refreshDerived(); });
    panel.appendChild(ta);
    el("fmtBtn", panel) && bar.querySelector("#fmtBtn").addEventListener("click", () => { try { ta.value = JSON.stringify(JSON.parse(ta.value), null, 2); req.body.raw = ta.value; } catch (e) {} });
  } else if (tab === "auth") {
    const seg = document.createElement("div"); seg.className = "seg"; seg.setAttribute("role", "group"); seg.setAttribute("aria-label", "Auth type");
    const types = [["noauth", "None"], ["bearer", "Bearer"], ["basic", "Basic"], ["apikey", "API Key"]];
    seg.innerHTML = types.map(([k, l]) => `<button data-k="${k}" aria-pressed="${req.auth.type === k}">${l}</button>`).join("");
    seg.addEventListener("click", (e) => { const k = e.target.dataset.k; if (!k) return; req.auth = { type: k }; dirty[req.id] = true; renderPanel(); refreshDerived(); });
    panel.appendChild(seg);
    const field = (label, key, type) => {
      const l = document.createElement("label"); l.className = "field";
      l.innerHTML = `<span class="cap">${label}</span><input type="${type || "text"}" value="${esc(req.auth[key] || "")}">`;
      l.querySelector("input").addEventListener("input", (e) => { req.auth[key] = e.target.value; dirty[req.id] = true; refreshDerived(); });
      panel.appendChild(l);
    };
    if (req.auth.type === "bearer") field("Token", "token");
    if (req.auth.type === "basic") { field("Username", "username"); field("Password", "password", "password"); }
    if (req.auth.type === "apikey") { field("Header/param name", "key"); field("Value", "value"); field("In (header or query)", "in"); }
    if (req.auth.type === "noauth") { const p = document.createElement("p"); p.className = "hint"; p.style.marginTop = "var(--s-4)"; p.textContent = "Sent without an Authorization header."; panel.appendChild(p); }
  } else if (tab === "cmd") {
    const pane = document.createElement("div"); pane.id = "pane-cmd"; panel.appendChild(pane);
    renderCmdPane();
  }
}

function renderResponse() {
  const res = el("resSection");
  const req = currentReq();
  const statusDigits = busy || !lastResult ? ["0", "0", "0"] : lastResult.ok ? String(lastResult.status).split("") : ["E", "R", "R"];
  const statusClass = busy ? "status wait loading" : !lastResult ? "status wait" : !lastResult.ok ? "status fail" : lastResult.status >= 400 ? "status fail" : "status pass";

  res.innerHTML = `
    <div class="board">
      <div class="${statusClass}" aria-label="${busy ? "Sending" : lastResult ? "Response status" : "No response yet"}">
        ${statusDigits.map((d, i) => `<span style="--i:${i}">${d}</span>`).join("")}
      </div>
      ${lastResult && !busy ? `<div class="meta">
          <b class="${!lastResult.ok || lastResult.status >= 400 ? "fail" : ""}">${lastResult.ok ? esc(lastResult.reason || "") : "Failed"}</b>
          <span>${lastResult.ok ? `${lastResult.elapsed_ms} ms &middot; ${fmtSize(lastResult.size_bytes)}` : esc(lastResult.error || "")}</span>
        </div>` : ""}
      ${busy ? `<div class="meta"><b>Sending</b><span>${req.method}</span></div>` : ""}
    </div>
    <div id="resBody"></div>
  `;
  const body = el("resBody");
  if (!lastResult) {
    body.innerHTML = '<p class="wait-note">Nothing has arrived yet. Send to see status, timing and body here.</p>';
    return;
  }
  if (!lastResult.ok) {
    body.innerHTML = `<div class="res-out"><pre>${esc(lastResult.error || "unknown error")}</pre></div>`;
    return;
  }
  const bodyText = lastResult.body_text != null ? lastResult.body_text : JSON.stringify(lastResult.body_json, null, 2);
  body.innerHTML = `
    <div class="res-bar" role="tablist">
      <button role="tab" class="tab" data-rt="body" aria-selected="${resTab === "body"}">Body</button>
      <button role="tab" class="tab" data-rt="headers" aria-selected="${resTab === "headers"}">Headers</button>
      <button class="link" id="copyRespBtn">Copy</button>
      <button class="link" id="downloadRespBtn">Download</button>
    </div>
    <div class="res-out" id="resOut"></div>
  `;
  $$('[data-rt]', body).forEach((b) => b.addEventListener("click", () => { resTab = b.dataset.rt; renderResponse(); }));
  el("copyRespBtn").addEventListener("click", () => { copyText(bodyText); toast("Copied"); });
  el("downloadRespBtn").addEventListener("click", () => {
    const isJson = lastResult.body_json !== null && lastResult.body_json !== undefined;
    const ext = isJson ? "json" : "txt";
    const slug = (currentReq().name || "response").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
    const blob = new Blob([bodyText], { type: isJson ? "application/json" : "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${slug || "response"}-${Date.now()}.${ext}`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    toast("Downloaded");
  });
  const out = el("resOut");
  if (resTab === "body") {
    out.innerHTML = `<pre>${markJson(bodyText)}</pre>`;
  } else {
    out.innerHTML = `<dl class="hdrs">${Object.entries(lastResult.headers || {}).flatMap(([k, v]) => [`<dt>${esc(k)}</dt>`, `<dd>${esc(v)}</dd>`]).join("")}</dl>`;
  }
  renderEvidenceSection(out);
}

function renderEvidenceSection(container) {
  const box = document.createElement("div");
  box.className = "evidence";
  box.innerHTML = `<button class="btn-line" style="flex:none;padding:var(--s-2) var(--s-3)" id="evidenceBtn">Save evidence</button><div id="evidenceOut"></div>`;
  container.appendChild(box);
  el("evidenceBtn").addEventListener("click", captureEvidence);
}

async function captureEvidence() {
  const req = currentReq();
  const name = req.name || `${req.method}-${req.url}`.slice(0, 60);
  const data = await fetchJSON("/api/evidence", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ entry: lastResult, name }) });
  const runs = await fetchJSON("/api/qa-runs");
  const out = el("evidenceOut");
  const runOpts = runs.map((r) => `<option value="${esc(r.run)}">${esc(r.run)}</option>`).join("");
  out.innerHTML = `
    <img src="/api/evidence/${data.file}?t=${Date.now()}" alt="Evidence screenshot">
    <div class="row-pick">
      <select id="runSel">${runOpts}</select>
      <select id="taskSel"></select>
      <button class="btn-line" style="flex:none;padding:var(--s-2) var(--s-3)" id="saveRunBtn">Save to QA run</button>
    </div>
  `;
  const runSel = el("runSel"), taskSel = el("taskSel");
  const fillTasks = () => { const r = runs.find((x) => x.run === runSel.value); taskSel.innerHTML = (r ? r.tasks : []).map((t) => `<option value="${esc(t)}">${esc(t)}</option>`).join(""); };
  runSel.addEventListener("change", fillTasks); fillTasks();
  el("saveRunBtn").addEventListener("click", async () => {
    await fetch("/api/evidence/save-to-run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ file: data.file, run: runSel.value, task: taskSel.value, label: name }) });
    toast("Saved into QA run screenshots");
  });
}

/* ============ SEND ============ */
async function sendCurrent() {
  const req = currentReq();
  if (!req || busy || !req.url.trim()) return;
  busy = true; renderMain();
  const body = req.body.mode === "raw" ? { ...req.body } : req.body;
  const payload = {
    request: { method: req.method, url: req.url, headers: req.headers, query: req.query || splitUrl(req.url).params, body, auth: req.auth },
    collection_id: activeCollectionId,
    skip_tls_verify: skipTls,
  };
  try {
    lastResult = await fetchJSON("/api/send", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  } finally {
    busy = false;
    renderMain();
  }
}

/* ============ IMPORT ============ */
el("colInput").addEventListener("change", async () => {
  if (!el("colInput").files.length) return;
  const form = new FormData();
  for (const f of el("colInput").files) form.append("files", f);
  const data = await fetchJSON("/api/collections/import", { method: "POST", body: form });
  toast(`Imported ${data.added.length} collection(s), ${data.added.reduce((a, c) => a + c.count, 0)} requests`);
  el("colInput").value = "";
  await loadCollections();
});
el("envInput").addEventListener("change", async () => {
  if (!el("envInput").files.length) return;
  const form = new FormData();
  for (const f of el("envInput").files) form.append("files", f);
  const data = await fetchJSON("/api/environments/import", { method: "POST", body: form });
  toast(`Imported ${data.added.length} environment(s)`);
  el("envInput").value = "";
  await loadEnvironments();
});
el("envSelect").addEventListener("change", async (e) => {
  activeEnv = e.target.value || null;
  await fetch("/api/environments/active", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ env_id: activeEnv }) });
  await loadVars();
});
el("newReqBtn").addEventListener("click", createScratch);
el("searchInput").addEventListener("input", renderList);

/* ============ KEYBOARD ============ */
window.addEventListener("keydown", (e) => {
  const mod = e.metaKey || e.ctrlKey;
  if (mod && e.key === "Enter") { e.preventDefault(); sendCurrent(); }
  if (mod && e.key.toLowerCase() === "k") { e.preventDefault(); openDrawer(); el("searchInput").focus(); }
  if (e.key === "Escape") closeDrawer();
});

/* ============ THEME ============ */
function setApiTheme(v) {
  $(".ac").classList.toggle("light", v === "light");
  $$("#themeSeg button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.v === v)));
  try { localStorage.setItem("api_client_theme", v); } catch (e) {}
}
el("themeSeg").addEventListener("click", (e) => { const v = e.target.dataset.v; if (v) setApiTheme(v); });

/* ============ RESIZABLE PANELS ============ */
const AC_ZOOM = 0.88;
function makeResizer(handle, { getRect, min, max, cssVar, target, storeKey }) {
  let dragging = false;
  const onMove = (e) => {
    if (!dragging) return;
    const rect = getRect();
    const raw = (e.clientX - rect.left) / AC_ZOOM;
    const val = Math.min(max(), Math.max(min(), raw));
    target.style.setProperty(cssVar, val + "px");
  };
  const onUp = (e) => {
    if (!dragging) return;
    dragging = false;
    handle.classList.remove("dragging");
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
    try { handle.releasePointerCapture(e.pointerId); } catch (err) {}
    try { localStorage.setItem(storeKey, target.style.getPropertyValue(cssVar)); } catch (err) {}
  };
  handle.addEventListener("pointerdown", (e) => {
    dragging = true;
    handle.classList.add("dragging");
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    try { handle.setPointerCapture(e.pointerId); } catch (err) {}
  });
  handle.addEventListener("pointermove", onMove);
  handle.addEventListener("pointerup", onUp);
  handle.addEventListener("pointercancel", onUp);
}
function initSideResizer() {
  const handle = el("sideResizer");
  const ac = $(".ac");
  if (!handle || !ac) return;
  try { const saved = localStorage.getItem("api_client_side_w"); if (saved) ac.style.setProperty("--side-w", saved); } catch (e) {}
  makeResizer(handle, {
    getRect: () => ac.getBoundingClientRect(),
    min: () => 200,
    max: () => 460,
    cssVar: "--side-w",
    target: ac,
    storeKey: "api_client_side_w",
  });
}
function initSplitResizer() {
  const handle = el("splitResizer");
  const splitEl = $(".split");
  if (!handle || !splitEl) return;
  try { const saved = localStorage.getItem("api_client_cfg_w"); if (saved) splitEl.style.setProperty("--cfg-w", saved); } catch (e) {}
  makeResizer(handle, {
    getRect: () => splitEl.getBoundingClientRect(),
    min: () => 320,
    max: () => Math.max(320, splitEl.getBoundingClientRect().width / AC_ZOOM - 366),
    cssVar: "--cfg-w",
    target: splitEl,
    storeKey: "api_client_cfg_w",
  });
}

/* ============ BOOT ============ */
(async function boot() {
  try { setApiTheme(localStorage.getItem("api_client_theme") || "dark"); } catch (e) {}
  initSideResizer();
  await loadEnvironments();
  await loadCollections();
  renderMain();
})();
