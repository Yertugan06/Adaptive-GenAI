import { request } from "./api.js";
import { requireAuth, loadMe, logoutHard } from "./auth.js";

requireAuth();

const info = document.getElementById("info");
const logoutBtn = document.getElementById("logoutBtn");

async function init() {
  const me = await loadMe();

  info.innerHTML = `
    <div class="p-4 rounded-2xl border border-slate-800 bg-slate-900 space-y-1">
      <div><span class="text-slate-400">Name:</span> <b>${me.name}</b></div>
      <div><span class="text-slate-400">Role:</span> <b>${me.role}</b></div>
      <div><span class="text-slate-400">Company ID:</span> <b>${me.company_id}</b></div>
      <div><span class="text-slate-400">Feedback required:</span> <b>${me.feedback_required ? "YES" : "NO"}</b></div>
      <hr class="border-slate-800"/>
      <div class="text-sm text-slate-300">
        Rule: feedback is mandatory to continue using chat.
      </div>
    </div>
  `;
}

logoutBtn.addEventListener("click", async () => {
  try { await request("/auth/logout", { method: "POST" }); } catch {}
  logoutHard();
});

init();
