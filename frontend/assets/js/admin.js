import { request } from "./api.js";
import { requireAuth, loadMe } from "./auth.js";

requireAuth();

const form = document.getElementById("createForm");
const list = document.getElementById("list");

async function init() {
  const me = await loadMe();
  if (me.role !== "admin") {
    window.location.href = "./profile.html";
    return;
  }
  await refresh();
}

async function refresh() {
  const me = await loadMe();
  // Using the correct backend endpoint with company_id
  const data = await request(`/responses/search?company_id=${me.company_id}&limit=10`);
  list.innerHTML = "";

  data.forEach(r => {
    const div = document.createElement("div");
    div.className = "p-4 rounded-2xl border border-slate-800 bg-slate-900";
    div.innerHTML = `
      <div class="text-sm text-slate-400">ID: ${r._id}</div>
      <div class="font-semibold">${r.prompt || r.canonical_prompt || "(no prompt)"}</div>
      <div class="text-sm text-slate-400">Bayesian Score: ${r.bayesian_score ?? "-"}</div>
      <div class="text-sm text-slate-400">Status: ${r.status}</div>
      <div class="mt-3 flex gap-2">
        <button class="statusBtn px-3 py-1 rounded-lg border border-slate-700" data-id="${r._id}" data-status="quarantine">Quarantine</button>
        <button class="statusBtn px-3 py-1 rounded-lg border border-slate-700" data-id="${r._id}" data-status="canonical">Canonical</button>
        <button class="statusBtn px-3 py-1 rounded-lg border border-slate-700" data-id="${r._id}" data-status="candidate">Candidate</button>
        <button class="delBtn px-3 py-1 rounded-lg border border-red-800 text-red-300" data-id="${r._id}">Delete</button>
      </div>
    `;
    list.appendChild(div);
  });

  list.querySelectorAll(".statusBtn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      const status = btn.dataset.status;
      await request(`/responses/${encodeURIComponent(id)}/status?status=${status}`, {
        method: "PATCH"
      });
      await refresh();
    });
  });

  list.querySelectorAll(".delBtn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      await request(`/responses/${encodeURIComponent(id)}`, { method: "DELETE" });
      await refresh();
    });
  });
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const me = await loadMe();

  const prompt = document.getElementById("canonical_prompt").value.trim();
  const response = document.getElementById("response").value.trim();
  const topics = document.getElementById("topics").value.split(",").map(s => s.trim()).filter(Boolean);
  const status = document.getElementById("status").value;

  await request("/responses", {
    method: "POST",
    body: { 
      prompt, 
      response, 
      topics, 
      status,
      company_id: me.company_id,
      bayesian_score: 0,
      reuse_count: 0
    }
  });

  form.reset();
  await refresh();
});

init();