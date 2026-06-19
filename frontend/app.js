// Minimal dashboard: fetches one of the /api views and renders it as a table.
// Columns are derived from the keys of the returned rows, so it adapts to
// whatever shape the backend (and the underlying Acumatica GI) returns.

const VIEWS = {
  "open-po-lines": { label: "Open PO Lines", url: "/api/open-po-lines" },
  "purchase-receipts": { label: "Purchase Receipts", url: "/api/purchase-receipts" },
  "inventory-history": { label: "Inventory History", url: "/api/inventory-history" },
};

let currentView = "open-po-lines";
let autoTimer = null;

const els = {
  status: document.getElementById("status"),
  tableWrap: document.getElementById("tableWrap"),
  health: document.getElementById("health"),
  refresh: document.getElementById("refresh"),
  autoRefresh: document.getElementById("autoRefresh"),
};

function setStatus(text, isError = false) {
  els.status.textContent = text;
  els.status.classList.toggle("err", isError);
}

function humanizeKey(key) {
  return key
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/^./, (c) => c.toUpperCase());
}

function renderTable(rows) {
  if (!Array.isArray(rows) || rows.length === 0) {
    els.tableWrap.innerHTML = '<div class="empty">No rows.</div>';
    return;
  }
  const columns = Array.from(
    rows.reduce((set, r) => {
      Object.keys(r).forEach((k) => set.add(k));
      return set;
    }, new Set())
  );

  const thead = `<thead><tr>${columns
    .map((c) => `<th>${humanizeKey(c)}</th>`)
    .join("")}</tr></thead>`;
  const tbody = `<tbody>${rows
    .map(
      (r) =>
        `<tr>${columns
          .map((c) => `<td>${formatCell(r[c])}</td>`)
          .join("")}</tr>`
    )
    .join("")}</tbody>`;
  els.tableWrap.innerHTML = `<table>${thead}${tbody}</table>`;
}

function formatCell(v) {
  if (v === null || v === undefined) return "";
  const s = String(v);
  return s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}

async function load() {
  const view = VIEWS[currentView];
  setStatus(`Loading ${view.label}…`);
  try {
    const resp = await fetch(view.url);
    const body = await resp.json();
    if (!resp.ok) {
      throw new Error(body.detail || `Request failed (${resp.status})`);
    }
    renderTable(body);
    setStatus(`${view.label}: ${body.length} row(s) · ${new Date().toLocaleTimeString()}`);
  } catch (err) {
    els.tableWrap.innerHTML = "";
    setStatus(`Error: ${err.message}`, true);
  }
}

async function checkHealth() {
  try {
    const resp = await fetch("/api/health");
    const body = await resp.json();
    els.health.textContent = `${body.tenant} @ ${body.instance}`;
    els.health.className = "health ok";
  } catch {
    els.health.textContent = "API unreachable";
    els.health.className = "health err";
  }
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    currentView = tab.dataset.view;
    load();
  });
});

els.refresh.addEventListener("click", load);
els.autoRefresh.addEventListener("change", (e) => {
  if (e.target.checked) {
    autoTimer = setInterval(load, 30000);
  } else {
    clearInterval(autoTimer);
    autoTimer = null;
  }
});

checkHealth();
load();
