import { BASE_URL } from "./config.js";

export function getToken() {
  return sessionStorage.getItem("access_token");
}

export function setToken(token) {
  sessionStorage.setItem("access_token", token);
}

export function clearToken() {
  sessionStorage.removeItem("access_token");
  sessionStorage.removeItem("user");
}

export function getUser() {
  const raw = sessionStorage.getItem("user");
  try { return raw ? JSON.parse(raw) : null; } catch { return null; }
}

export function setUser(user) {
  sessionStorage.setItem("user", JSON.stringify(user));
}

export async function request(path, { method = "GET", body = null, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };

  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null
  });

  let data = null;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) data = await res.json().catch(() => null);
  else data = await res.text().catch(() => null);

  if (!res.ok) {
    const message =
      (data && typeof data === "object" && data.detail) ? data.detail :
      (typeof data === "string" && data) ? data :
      `HTTP ${res.status}`;

    const err = new Error(message);
    err.status = res.status;
    err.data = data;
    throw err;
  }

  return data;
}
