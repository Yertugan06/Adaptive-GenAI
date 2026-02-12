const API_BASE = "http://127.0.0.1:8000/api/v1";

function getToken() {
  return localStorage.getItem("access_token");
}

async function apiRequest(endpoint, method = "GET", body = null) {
  const headers = {
    "Content-Type": "application/json"
  };

  const token = getToken();
  if (token) {
    headers["Authorization"] = "Bearer " + token;
  }

  const options = {
    method,
    headers
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const res = await fetch(API_BASE + endpoint, options);

  if (res.status === 401) {
    localStorage.removeItem("access_token");
    window.location.href = "./login.html";
    return;
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    const errorMessage = error.detail || error.message || "Request failed";
    throw new Error(errorMessage);
  }

  return res.json();
}

export { apiRequest, getToken, API_BASE };
