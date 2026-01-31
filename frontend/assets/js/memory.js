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
  if (!query) return;

  const k = Number(topK.value || 5);
  const data = await request(`/responses/search?query=${encodeURIComponent(query)}&top_k=${k}`);

  results.innerHTML = "";
  detail.innerHTML = `<div class="text-slate-400">Select a result to view details.</div>`;
  selectedId = null;

  data.forEach(r => {
    const row = document.createElement("button");
    row.className = "w-full text-left p-3 rounded-xl border border-slate-800 bg-slate-900 hover:border-slate-600";
    row.innerHTML = `
      <div class="font-semibold">${esc(r.canonical_prompt || r.id)}</div>
      <div class="text-sm text-slate-400">avg_rating: ${esc(r.avg_rating ?? "-")}</div>
    `;
    row.addEventListener("click", () => openResponse(r.id));
    results.appendChild(row);
  });
}

async function openResponse(id) {
  selectedId = id;
  const r = await request(`/responses/${encodeURIComponent(id)}`);

  detail.innerHTML = `
    <div class="p-4 rounded-2xl border border-slate-800 bg-slate-900 space-y-2">
      <div class="text-sm text-slate-400">ID: ${esc(r.id)}</div>
      <div class="text-xl font-semibold">${esc(r.canonical_prompt || "")}</div>
      <div class="text-sm text-slate-300">status: <span class="font-semibold">${esc(r.status || "")}</span></div>
      <div class="text-sm text-slate-300">avg_rating: <span class="font-semibold">${esc(r.avg_rating ?? "")}</span></div>
      <div class="text-sm text-slate-300">reuse_count: <span class="font-semibold">${esc(r.reuse_count ?? "")}</span></div>
      <div class="text-sm text-slate-300">topics: ${esc((r.topics || []).join(", "))}</div>
      <hr class="border-slate-800"/>
      <div class="whitespace-pre-wrap">${esc(r.response || "")}</div>
    </div>
  `;

  if (me && me.role === "admin") {
    adminStatus.value = r.status || "canonical";
    adminResponseText.value = r.response || "";
    adminTopics.value = (r.topics || []).join(", ");
  }
}

adminUpdateBtn.addEventListener("click", async () => {
  if (!selectedId) return;

  await request(`/responses/${encodeURIComponent(selectedId)}`, {
    method: "PUT",
    body: {
      response: adminResponseText.value,
      topics: adminTopics.value.split(",").map(s => s.trim()).filter(Boolean)
    }
  });

  await openResponse(selectedId);
});

adminDeleteBtn.addEventListener("click", async () => {
  if (!selectedId) return;
  await request(`/responses/${encodeURIComponent(selectedId)}`, { method: "DELETE" });
  selectedId = null;
  detail.innerHTML = `<div class="text-slate-400">Archived. Search again.</div>`;
});

adminStatusBtn.addEventListener("click", async () => {
  if (!selectedId) return;

  await request(`/responses/${encodeURIComponent(selectedId)}/status`, {
    method: "PATCH",
    body: { status: adminStatus.value }
  });

  await openResponse(selectedId);
});
