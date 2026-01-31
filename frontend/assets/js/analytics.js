import { request } from "./api.js";
import { requireAuth, loadMe } from "./auth.js";

requireAuth();

const cards = document.getElementById("cards");
const topicsTable = document.getElementById("topicsTable");
const cacheBox = document.getElementById("cacheBox");

function card(title, value) {
  const div = document.createElement("div");
  div.className = "p-4 rounded-2xl border border-slate-800 bg-slate-900";
  div.innerHTML = `<div class="text-sm text-slate-400">${title}</div><div class="text-2xl font-semibold">${value}</div>`;
  return div;
}

async function init() {
  const me = await loadMe();
  if (me.role !== "admin") {
    window.location.href = "./profile.html";
    return;
  }

  const [company, topics, cache] = await Promise.all([
    request(`/analytics/company/${me.company_id}`),
    request("/analytics/topics"),
    request("/analytics/cache-efficiency")
  ]);

  cards.innerHTML = "";
  cards.appendChild(card("Total prompts", company.total_prompts));
  cards.appendChild(card("Avg rating", company.avg_rating));
  cards.appendChild(card("Cache hit ratio", company.cache_hit_ratio));

  topicsTable.innerHTML = "";
  topics.forEach(t => {
    const tr = document.createElement("tr");
    tr.className = "border-t border-slate-800";
    tr.innerHTML = `
      <td class="p-3">${t.topic}</td>
      <td class="p-3 text-center">${t.total_uses}</td>
      <td class="p-3 text-center">${t.avg_rating}</td>
    `;
    topicsTable.appendChild(tr);
  });

  cacheBox.innerHTML = `
    <div class="p-4 rounded-2xl border border-slate-800 bg-slate-900 space-y-1">
      <div>cache_hits: <b>${cache.cache_hits}</b></div>
      <div>cache_misses: <b>${cache.cache_misses}</b></div>
      <div>estimated_token_savings: <b>${cache.estimated_token_savings}</b></div>
    </div>
  `;
}

init();
