import { request, setToken, setUser } from "./api.js";

const form = document.getElementById("loginForm");
const errorBox = document.getElementById("error");
const submitBtn = document.getElementById("submitBtn");

function showError(msg) {
  errorBox.textContent = msg;
  errorBox.classList.remove("hidden");
}

function clearError() {
  errorBox.textContent = "";
  errorBox.classList.add("hidden");
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError();

  submitBtn.disabled = true;
  submitBtn.classList.add("opacity-60", "cursor-not-allowed");

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  try {
    const data = await request("/auth/login", {
      method: "POST",
      auth: false,
      body: { email, password }
    });

    setToken(data.access_token);
    setUser(data.user);

    window.location.href = "./chat.html";
  } catch (err) {
    showError(err.message || "Login failed");
  } finally {
    submitBtn.disabled = false;
    submitBtn.classList.remove("opacity-60", "cursor-not-allowed");
  }
});
