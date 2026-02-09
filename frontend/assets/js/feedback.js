import { request } from "./api.js";
import { requireAuth, loadMe } from "./auth.js";

requireAuth();

const tbody = document.getElementById("rows");

function esc(s) {
  return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
}

async function loadHistory() {
  try {
    const me = await loadMe();
    // Note: Backend doesn't have this exact endpoint, but we can use what's available
    // or implement it in backend
    const data = await request(`/feedback/history?user_id=${me.id}&limit=10`);
    tbody.innerHTML = "";

    if (data && data.length > 0) {
      data.forEach(item => {
        const tr = document.createElement("tr");
        tr.className = "border-t border-slate-800";
        tr.innerHTML = `
          <td class="p-3">${esc(item.event_id || "")}</td>
          <td class="p-3 text-center">${esc(item.rating ?? "")}</td>
          <td class="p-3 text-center">${esc(new Date(item.created_at || Date.now()).toLocaleString())}</td>
        `;
        tbody.appendChild(tr);
      });
    } else {
      tbody.innerHTML = `
        <tr class="border-t border-slate-800">
          <td class="p-3 text-slate-400 text-center" colspan="3">No feedback history yet</td>
        </tr>
      `;
    }
  } catch (error) {
    console.error("Failed to load history:", error);
    tbody.innerHTML = `
      <tr class="border-t border-slate-800">
        <td class="p-3 text-red-400 text-center" colspan="3">Error loading history: ${error.message}</td>
      </tr>
    `;
  }
}

loadHistory();