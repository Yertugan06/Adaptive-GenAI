function requireAuth() {
  if (!localStorage.getItem("access_token")) {
    window.location.href = "./login.html";
  }
}

function clearAuth() {
  localStorage.removeItem("access_token");
}

function setAuth(token) {
  localStorage.setItem("access_token", token);
}

export { requireAuth, clearAuth, setAuth };