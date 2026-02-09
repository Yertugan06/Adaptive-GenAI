import { request } from "./api.js";
import { requireAuth, loadMe } from "./auth.js";

requireAuth();

const qInput = document.getElementById("query");
const topK = document.getElementById("topK");
const btn = document.getElementById("searchBtn");
const results = document.getElementById("results");
const detail = document.getElementById("detail");

const adminBox = document.getElementById("adminBox");
const adminStatus = document.getElementById("adminStatus");
const adminUpdateBtn = document.getElementById("adminUpdateBtn");
const adminDeleteBtn = document.getElementById("adminDeleteBtn");
const adminResponseText = document.getElementById("adminResponseText");
const adminTopics = document.getElementById("adminTopics");
const adminStatusBtn = document.getElementById("adminStatusBtn");

let me = null;
let selectedId = null;

function esc(s){ return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;"); }

async function init() {
  me = await loadMe();
  adminBox.classList.toggle("hidden", me.role !== "admin");
}
init();

btn.addEventListener("click", search);

async function search() {
  const query = qInput.value.trim();
  const k = Number(topK.value || 5);
  
  try {
    // Using the correct backend search endpoint
    const data = await request(`/responses/search?company_id=${me.company_id}&limit=${k}&skip=0`);
    results.innerHTML = "";
    detail.innerHTML = `<div class="text-slate-400">Select a result to view details.</div>`;
    selectedId = null;

    if (data && data.length > 0) {
      data.forEach(r => {
        const row = document.createElement("button");
        row.className = "w-full text-left p-3 rounded-xl border border-slate-800 bg-slate-900 hover:border-slate-600";
        row.innerHTML = `
          <div class="font-semibold">${esc(r.prompt || r.canonical_prompt || r._id)}</div>
          <div class="text-sm text-slate-400">Status: ${esc(r.status || "-")} | Score: ${esc(r.bayesian_score ?? "-")}</div>
        `;
        row.addEventListener("click", () => openResponse(r._id));
        results.appendChild(row);
      });
    } else {
      results.innerHTML = `<div class="p-4 text-slate-400 text-center">No responses found</div>`;
    }
  } catch (error) {
    console.error("Search error:", error);
    results.innerHTML = `<div class="p-4 text-red-400 text-center">Error: ${error.message}</div>`;
  }
}

async function openResponse(id) {
  try {
    selectedId = id;
    const r = await request(`/responses/${encodeURIComponent(id)}`);

    detail.innerHTML = `
      <div class="p-4 rounded-2xl border border-slate-800 bg-slate-900 space-y-2">
        <div class="text-sm text-slate-400">ID: ${esc(r._id)}</div>
        <div class="text-xl font-semibold">${esc(r.prompt || r.canonical_prompt || "")}</div>
        <div class="text-sm text-slate-300">Status: <span class="font-semibold ${r.status === 'canonical' ? 'text-green-400' : r.status === 'quarantine' ? 'text-red-400' : 'text-yellow-400'}">${esc(r.status || "")}</span></div>
        <div class="text-sm text-slate-300">Bayesian Score: <span class="font-semibold">${esc(r.bayesian_score ?? "")}</span></div>
        <div class="text-sm text-slate-300">Reuse Count: <span class="font-semibold">${esc(r.reuse_count ?? "")}</span></div>
        <div class="text-sm text-slate-300">Topics: ${esc((r.topics || []).join(", "))}</div>
        <hr class="border-slate-800"/>
        <div class="whitespace-pre-wrap">${esc(r.response || "")}</div>
      </div>
    `;

    if (me && me.role === "admin") {
      adminStatus.value = r.status || "candidate";
      adminResponseText.value = r.response || "";
      adminTopics.value = (r.topics || []).join(", ");
    }
  } catch (error) {
    console.error("Open response error:", error);
    detail.innerHTML = `<div class="p-4 text-red-400">Error loading response: ${error.message}</div>`;
  }
}

adminUpdateBtn.addEventListener("click", async () => {
  if (!selectedId) return;

  try {
    await request(`/responses/${encodeURIComponent(selectedId)}`, {
      method: "PUT",
      body: {
        response: adminResponseText.value,
        topics: adminTopics.value.split(",").map(s => s.trim()).filter(Boolean)
      }
    });
    await openResponse(selectedId);
  } catch (error) {
    alert(`Update failed: ${error.message}`);
  }
});

adminDeleteBtn.addEventListener("click", async () => {
  if (!selectedId) return;
  if (!confirm("Are you sure you want to delete this response?")) return;
  
  try {
    await request(`/responses/${encodeURIComponent(selectedId)}`, { method: "DELETE" });
    selectedId = null;
    detail.innerHTML = `<div class="text-slate-400">Deleted. Search again.</div>`;
    await search();
  } catch (error) {
    alert(`Delete failed: ${error.message}`);
  }
});

adminStatusBtn.addEventListener("click", async () => {
  if (!selectedId) return;

  try {
    await request(`/responses/${encodeURIComponent(selectedId)}/status?status=${adminStatus.value}`, {
      method: "PATCH"
    });
    await openResponse(selectedId);
  } catch (error) {
    alert(`Status update failed: ${error.message}`);
  }
});