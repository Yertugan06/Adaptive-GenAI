import { request, getToken, clearToken } from "./api.js";

export function requireAuth() {
  if (!getToken()) window.location.href = "./login.html";
}

export async function loadMe() {
  return await request("/auth/me", { method: "GET", auth: true });
}

export function logoutHard() {
  clearToken();
  window.location.href = "./login.html";
}
