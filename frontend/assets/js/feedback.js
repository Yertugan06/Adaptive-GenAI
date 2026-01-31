import { request } from "./api.js";
import { requireAuth } from "./auth.js";

requireAuth();

const tbody = document.getElementById("rows");

function esc(s) {
  return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
}

async function loadHistory() {
  const data = await request("/feedback/history");
  tbody.innerHTML = "";

  data.forEach(item => {
    const tr = document.createElement("tr");
    tr.className = "border-t border-slate-800";
    tr.innerHTML = `
      <td class="p-3">${esc(item.prompt_text || "")}</td>
      <td class="p-3 text-center">${esc(item.rating ?? "")}</td>
      <td class="p-3 text-center">${esc(new Date(item.created_at).toLocaleString())}</td>
    `;
    tbody.appendChild(tr);
  });
}

loadHistory();
