import { apiRequest } from "./api.js";

async function loadDashboard() {
  const loadingEl = document.getElementById("loading");
  const contentEl = document.getElementById("dashboardContent");

  try {
    // 1. Get user info to retrieve company_id
    const userInfo = await apiRequest("/auth/me", "GET");
    const companyId = userInfo.company_id;

    // 2. Fetch analytics using the correct company ID
    const data = await apiRequest(`/analytics/company/${companyId}`, "GET");

    loadingEl.classList.add("hidden");
    contentEl.classList.remove("hidden");

    // 3. Update stats cards (Backend: total_reviews, global_average_rating)
    document.getElementById("totalReviews").textContent = data.total_reviews ?? 0;
    
    const avgRating = data.global_average_rating;
    document.getElementById("avgRating").textContent = 
      (avgRating !== undefined && avgRating !== null) 
        ? avgRating.toFixed(2) 
        : "0.00";

    // 4. Render status breakdown (Backend: status_distribution)
    renderStatusBreakdown(data.status_distribution || {});

    // 5. Render top performer (Backend: top_performing_response_id)
    renderTopPerformer(data.top_performing_response_id);

  } catch (err) {
    loadingEl.innerHTML = `
      <div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded">
        Error loading dashboard: ${err.message || "Unknown error"}
      </div>
    `;
  }
}

function renderStatusBreakdown(distribution) {
  const container = document.getElementById("statusBreakdown");
  container.innerHTML = "";

  // Backend StatusBreakdown model uses these exact keys:
  const statuses = ["candidate", "canonical", "quarantine"];
  const colors = {
    candidate: "bg-yellow-500",
    canonical: "bg-green-500",
    quarantine: "bg-red-500", // Mapping 'quarantine' to the red bar
  };

  const total = Object.values(distribution).reduce((sum, val) => sum + val, 0);

  statuses.forEach((status) => {
    const count = distribution[status] || 0;
    const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : 0;

    const statusDiv = document.createElement("div");
    statusDiv.className = "mb-3";
    statusDiv.innerHTML = `
      <div class="flex justify-between text-sm mb-1">
        <span class="capitalize">${status}</span>
        <span class="font-medium">${count} (${percentage}%)</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div class="${colors[status]} h-2 rounded-full" style="width: ${percentage}%"></div>
      </div>
    `;
    container.appendChild(statusDiv);
  });
}

/**
 * Since the backend only returns a single ID for the top performer,
 * we update the UI to display that specific ID.
 */
function renderTopPerformer(responseId) {
  const container = document.getElementById("topResponses");
  container.innerHTML = "";

  if (!responseId) {
    container.innerHTML = '<p class="text-gray-500 text-sm">No top performing response identified yet</p>';
    return;
  }

  const responseDiv = document.createElement("div");
  responseDiv.className = "bg-blue-50 border border-blue-100 p-4 rounded-lg";
  responseDiv.innerHTML = `
    <div class="flex items-center gap-3">
      <div class="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold">1</div>
      <div>
        <div class="text-sm font-semibold text-slate-800">Top Performing Response ID</div>
        <div class="text-xs text-blue-600 font-mono mt-1">${responseId}</div>
      </div>
    </div>
    <div class="mt-3">
      <a href="./responses.html" class="text-xs text-blue-700 hover:underline">View in Response Management →</a>
    </div>
  `;
  container.appendChild(responseDiv);
}

document.addEventListener("DOMContentLoaded", loadDashboard);
export { loadDashboard };