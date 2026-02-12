import { apiRequest } from "./api.js";

let currentPage = 1;
const pageSize = 20;
let userCompanyId = null; // Globally available for this page instance

/**
 * Entry point: Fetches profile first to get the required company_id,
 * then triggers the data load.
 */
async function initialize() {
  const loadingEl = document.getElementById("loading");
  try {
    // 1. Fetch user profile to get company_id
    const userData = await apiRequest('/auth/me', 'GET');
    userCompanyId = userData.company_id;

    if (!userCompanyId) {
      throw new Error("User profile is missing a Company ID.");
    }

    // 2. Load the actual response data
    await loadResponses();
  } catch (err) {
    loadingEl.innerHTML = `
      <div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded">
        Initialization Error: ${err.message || "Could not verify user identity."}
      </div>
    `;
  }
}

/**
 * Fetches and displays the list of AI responses.
 */
async function loadResponses() {
  const loadingEl = document.getElementById("loading");
  const tableBody = document.getElementById("responsesTableBody");

  // Show loading state if we are navigating pages
  loadingEl.classList.remove("hidden");
  loadingEl.innerHTML = '<div class="text-gray-600">Loading responses...</div>';

  try {
    // 1. Map frontend pagination to backend skip/limit
    const limit = pageSize;
    const skip = (currentPage - 1) * pageSize;

    // 2. Call the search endpoint with required company_id and corrected path
    const data = await apiRequest(
      `/responses/search?company_id=${userCompanyId}&limit=${limit}&skip=${skip}`,
      "GET",
    );

    loadingEl.classList.add("hidden");
    tableBody.innerHTML = "";

    // 3. Backend returns a List (Array) directly
    if (Array.isArray(data) && data.length > 0) {
      data.forEach((response) => {
        renderResponseRow(response);
      });
      
      // Since backend doesn't return total count, we estimate for UI logic
      const estimatedTotal = data.length === limit ? currentPage * pageSize + 1 : (currentPage - 1) * pageSize + data.length;
      updatePagination(estimatedTotal);
    } else {
      tableBody.innerHTML = `
        <tr>
          <td colspan="6" class="px-6 py-8 text-center text-gray-500">
            No responses found
          </td>
        </tr>
      `;
      updatePagination(0);
    }
  } catch (err) {
    // Handle the error object properly to avoid displaying [object Object]
    const errorMsg = err.message || "An unexpected error occurred.";
    loadingEl.innerHTML = `
      <div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded">
        Error loading responses: ${errorMsg}
      </div>
    `;
    loadingEl.classList.remove("hidden");
  }
}

function renderResponseRow(response) {
  const tableBody = document.getElementById("responsesTableBody");
  const row = document.createElement("tr");
  row.className = "border-b border-gray-200 hover:bg-gray-50";

  const statusColors = {
    candidate: "bg-yellow-100 text-yellow-800",
    canonical: "bg-green-100 text-green-800",
    quarantine: "bg-red-100 text-red-800",
  };

  row.innerHTML = `
    <td class="px-6 py-4 text-sm text-gray-900">${response.id || response._id}</td>
    <td class="px-6 py-4 text-sm text-gray-900 max-w-xs truncate" title="${escapeHtml(response.canonical_prompt || "")}">
      ${escapeHtml(response.canonical_prompt || "N/A")}
    </td>
    <td class="px-6 py-4">
      <span class="px-2 py-1 text-xs rounded ${statusColors[response.status] || "bg-gray-100 text-gray-800"}">
        ${response.status}
      </span>
    </td>
    <td class="px-6 py-4 text-sm text-gray-900">
      ${response.bayesian_score ? response.bayesian_score.toFixed(3) : "0.000"}
    </td>
    <td class="px-6 py-4 text-sm text-gray-900">${response.reuse_count || 0}</td>
    <td class="px-6 py-4 text-sm">
      <button onclick="viewDetails('${response.id || response._id}')" class="text-blue-600 hover:underline mr-3">View</button>
      ${response.status === "candidate" ? 
        `<button onclick="promoteToCanonical('${response.id || response._id}')" class="text-green-600 hover:underline mr-3">Promote</button>` : ""
      }
      <button onclick="deleteResponse('${response.id || response._id}')" class="text-red-600 hover:underline">Delete</button>
    </td>
  `;
  tableBody.appendChild(row);
}

function updatePagination(total) {
  const paginationEl = document.getElementById("pagination");
  const totalPages = Math.ceil(total / pageSize) || 1;

  paginationEl.innerHTML = `
    <div class="flex items-center justify-between">
      <div class="text-sm text-gray-600">
        Page ${currentPage} ${total > 0 ? `of ${totalPages}` : ""}
      </div>
      <div class="flex gap-2">
        <button 
          ${currentPage === 1 ? "disabled" : ""} 
          onclick="changePage(${currentPage - 1})"
          class="px-4 py-2 bg-slate-800 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
        >Previous</button>
        <button 
          ${(total <= currentPage * pageSize) ? "disabled" : ""} 
          onclick="changePage(${currentPage + 1})"
          class="px-4 py-2 bg-slate-800 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
        >Next</button>
      </div>
    </div>
  `;
}

window.changePage = function (page) {
  currentPage = page;
  loadResponses();
};

window.promoteToCanonical = async function (id) {
  if (!confirm("Promote this response to canonical status?")) return;
  try {
    await apiRequest(`/responses/${id}/status`, "PATCH", { status: "canonical" });
    alert("Response promoted!");
    loadResponses();
  } catch (err) {
    alert("Promotion failed: " + err.message);
  }
};

window.deleteResponse = async function (id) {
  if (!confirm("Are you sure you want to delete this response?")) return;
  try {
    await apiRequest(`/responses/${id}`, "DELETE");
    alert("Response deleted");
    loadResponses();
  } catch (err) {
    alert("Deletion failed: " + err.message);
  }
};

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Start the initialization when the page loads
document.addEventListener("DOMContentLoaded", initialize);

export { loadResponses };