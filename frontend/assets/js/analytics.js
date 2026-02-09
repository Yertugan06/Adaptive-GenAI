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

  try {
    const company = await request(`/analytics/company/${me.company_id}`);
    
    cards.innerHTML = "";
    cards.appendChild(card("Total Reviews", company.total_reviews || 0));
    cards.appendChild(card("Global Avg Rating", company.global_average_rating ? company.global_average_rating.toFixed(2) : "0.0"));
    
    const status = company.status_distribution || {};
    const statusCard = document.createElement("div");
    statusCard.className = "p-4 rounded-2xl border border-slate-800 bg-slate-900";
    statusCard.innerHTML = `
      <div class="text-sm text-slate-400">Status Distribution</div>
      <div class="mt-2 grid grid-cols-3 gap-2">
        <div class="text-center">
          <div class="text-lg font-semibold">${status.candidate || 0}</div>
          <div class="text-xs text-slate-400">Candidate</div>
        </div>
        <div class="text-center">
          <div class="text-lg font-semibold">${status.canonical || 0}</div>
          <div class="text-xs text-slate-400">Canonical</div>
        </div>
        <div class="text-center">
          <div class="text-lg font-semibold">${status.quarantine || 0}</div>
          <div class="text-xs text-slate-400">Quarantine</div>
        </div>
      </div>
    `;
    cards.appendChild(statusCard);

    // Topics and cache endpoints don't exist in backend
    topicsTable.innerHTML = `
      <tr class="border-t border-slate-800">
        <td class="p-3 text-slate-400 text-center" colspan="3">Topics analytics not implemented</td>
      </tr>
    `;
    
    cacheBox.innerHTML = `
      <div class="p-4 rounded-2xl border border-slate-800 bg-slate-900 space-y-1">
        <div class="text-slate-400">Cache efficiency analytics not implemented</div>
      </div>
    `;
  } catch (error) {
    console.error("Failed to load analytics:", error);
    cards.innerHTML = `
      <div class="p-4 rounded-2xl border border-red-800 bg-slate-900 text-red-400">
        Failed to load analytics: ${error.message}
      </div>
    `;
  }
}

init();