const fileInput = document.getElementById("fileInput");
const fileListEl = document.getElementById("fileList");
const readerEl = document.getElementById("reader");
const currentNameEl = document.getElementById("currentName");
const toastEl = document.getElementById("toast");

let files = [];
let activeId = null;
let dragId = null;

function toast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  setTimeout(() => toastEl.classList.remove("show"), 2200);
}

async function refreshList() {
  const res = await fetch("/api/files");
  files = await res.json();
  renderList();
  if (!activeId && files.length) openFile(files[0].id);
}

function renderList() {
  fileListEl.innerHTML = "";
  for (const f of files) {
    const row = document.createElement("div");
    row.className = "file-item" + (f.id === activeId ? " active" : "");
    row.draggable = true;
    row.dataset.id = f.id;
    row.innerHTML = `<span class="drag">::</span><span class="name">${f.name}</span><button class="rm" title="Remove">&times;</button>`;
    row.addEventListener("click", (e) => {
      if (e.target.classList.contains("rm")) return;
      openFile(f.id);
    });
    row.querySelector(".rm").addEventListener("click", async (e) => {
      e.stopPropagation();
      await fetch(`/api/files/${f.id}`, { method: "DELETE" });
      if (activeId === f.id) { activeId = null; readerEl.innerHTML = '<div class="empty">Select a file to read.</div>'; currentNameEl.textContent = "Select a file"; }
      await refreshList();
    });
    row.addEventListener("dragstart", () => { dragId = f.id; row.classList.add("dragging"); });
    row.addEventListener("dragend", () => row.classList.remove("dragging"));
    row.addEventListener("dragover", (e) => e.preventDefault());
    row.addEventListener("drop", async (e) => {
      e.preventDefault();
      if (!dragId || dragId === f.id) return;
      const ids = files.map((x) => x.id);
      const from = ids.indexOf(dragId);
      const to = ids.indexOf(f.id);
      ids.splice(to, 0, ids.splice(from, 1)[0]);
      await fetch("/api/files/order", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order: ids }),
      });
      await refreshList();
    });
    fileListEl.appendChild(row);
  }
}

async function openFile(id) {
  activeId = id;
  renderList();
  const f = files.find((x) => x.id === id);
  currentNameEl.textContent = f ? f.name : "";
  const res = await fetch(`/api/files/${id}/html`);
  const data = await res.json();
  readerEl.innerHTML = data.html || `<div class="empty">${data.error || "Could not render file."}</div>`;
}

fileInput.addEventListener("change", async () => {
  if (!fileInput.files.length) return;
  const form = new FormData();
  for (const f of fileInput.files) form.append("files", f);
  const res = await fetch("/api/files", { method: "POST", body: form });
  const data = await res.json();
  toast(`Added ${data.added.length} file(s)`);
  fileInput.value = "";
  await refreshList();
  if (data.added.length) openFile(data.added[0].id);
});

async function doExport(kind) {
  const all = document.getElementById("exportAll").checked;
  const ids = all ? null : activeId ? [activeId] : null;
  if (!ids && !all) { toast("Select a file first"); return; }
  const res = await fetch(`/api/export/${kind}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids, filename: all ? `notes.${kind === "docx" ? "docx" : "pdf"}` : undefined }),
  });
  if (!res.ok) { toast("Export failed"); return; }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = all ? `notes.${kind}` : `${(files.find((x) => x.id === activeId) || {}).name || "notes"}.${kind}`;
  a.click();
  URL.revokeObjectURL(url);
  toast("Exported");
}

document.getElementById("exportPdf").addEventListener("click", () => doExport("pdf"));
document.getElementById("exportDocx").addEventListener("click", () => doExport("docx"));

document.getElementById("appear").addEventListener("click", (e) => {
  const v = e.target.dataset.v;
  if (!v) return;
  document.documentElement.dataset.theme = v;
  try { localStorage.setItem("md_reader_theme", v); } catch (err) {}
});

refreshList();
