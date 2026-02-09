import { request, getUser, clearToken } from "./api.js";
import { requireAuth, loadMe, logoutHard } from "./auth.js";

requireAuth();

const userBadge = document.getElementById("userBadge");
const logoutBtn = document.getElementById("logoutBtn");

const banner = document.getElementById("banner");
const chatEl = document.getElementById("chat");

const promptInput = document.getElementById("promptInput");
const sendPromptBtn = document.getElementById("sendPromptBtn");

const feedbackBox = document.getElementById("feedbackBox");
const fbTarget = document.getElementById("fbTarget");
const ratingEl = document.getElementById("rating");
const sendFeedbackBtn = document.getElementById("sendFeedbackBtn");
const fbError = document.getElementById("fbError");

let feedbackPending = false;
let lastEventId = null;

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function setBanner(msg, isError = false) {
  banner.textContent = msg;
  banner.classList.remove("hidden");
  banner.className = isError ? 
    "px-4 py-3 mb-4 rounded-xl border border-red-800 bg-red-900/30 text-red-300" :
    "px-4 py-3 mb-4 rounded-xl border border-blue-800 bg-blue-900/30 text-blue-300";
}

function clearBanner() {
  banner.textContent = "";
  banner.classList.add("hidden");
}

function lockInput() {
  feedbackPending = true;
  promptInput.disabled = true;
  sendPromptBtn.disabled = true;
  promptInput.classList.add("opacity-60", "cursor-not-allowed");
  sendPromptBtn.classList.add("opacity-60", "cursor-not-allowed");
}

function unlockInput() {
  feedbackPending = false;
  promptInput.disabled = false;
  sendPromptBtn.disabled = false;
  promptInput.classList.remove("opacity-60", "cursor-not-allowed");
  sendPromptBtn.classList.remove("opacity-60", "cursor-not-allowed");
}

function addMessage(role, text, meta = "") {
  const wrap = document.createElement("div");
  wrap.className = "p-4 rounded-2xl border border-slate-800 bg-slate-900";
  wrap.innerHTML = `
    <div class="flex items-center justify-between mb-2">
      <div class="font-semibold">${escapeHtml(role)}</div>
      <div class="text-xs text-slate-400">${escapeHtml(meta)}</div>
    </div>
    <div class="whitespace-pre-wrap">${escapeHtml(text)}</div>
  `;
  chatEl.appendChild(wrap);
  wrap.scrollIntoView({ behavior: "smooth", block: "end" });
}

function showFeedbackWidget(eventId) {
  lastEventId = eventId;
  fbTarget.textContent = `Event: ${eventId}`;
  feedbackBox.classList.remove("hidden");
  fbError.classList.add("hidden");
  fbError.textContent = "";
}

function hideFeedbackWidget() {
  feedbackBox.classList.add("hidden");
  ratingEl.value = "5";
}

async function syncFeedbackState() {
  try {
    const me = await loadMe();
    if (me) {
      userBadge.textContent = `${me.name} • ${me.role}`;
    }
  } catch (error) {
    console.error("Failed to sync user state:", error);
  }
}

logoutBtn.addEventListener("click", async () => {
  try {
    await request("/auth/logout", { method: "POST" });
  } catch (_) {}
  logoutHard();
});

sendPromptBtn.addEventListener("click", submitPrompt);
promptInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    submitPrompt();
  }
});

sendFeedbackBtn.addEventListener("click", submitFeedback);

async function init() {
  await syncFeedbackState();
}
init();

async function submitPrompt() {
  if (feedbackPending) {
    setBanner("Please provide feedback on the previous response before sending a new prompt.", true);
    return;
  }

  const promptText = promptInput.value.trim();
  if (!promptText) return;

  addMessage("You", promptText);
  promptInput.value = "";

  sendPromptBtn.disabled = true;
  sendPromptBtn.classList.add("opacity-60", "cursor-not-allowed");

  try {
    const data = await request("/prompts/submit", {
      method: "POST",
      body: { prompt_text: promptText }
    });

    addMessage(
      "AI",
      data.response_text,
      `${data.model || "model-unknown"}`
    );

    // Show feedback widget if required
    if (data.feedback_required) {
      lockInput();
      showFeedbackWidget(data.ai_response_id);
      setBanner("Please rate this response to continue.");
    } else {
      unlockInput();
      hideFeedbackWidget();
      clearBanner();
    }
  } catch (err) {
    console.error("Prompt error:", err);
    if (err.status === 403) {
      lockInput();
      setBanner(err.detail || "Feedback required for previous response before submitting a new prompt.", true);
    } else if (err.status === 401) {
      clearToken();
      window.location.href = "./login.html";
    } else {
      setBanner(err.message || "Failed to submit prompt.", true);
      unlockInput();
    }
  } finally {
    if (!feedbackPending) {
      sendPromptBtn.disabled = false;
      sendPromptBtn.classList.remove("opacity-60", "cursor-not-allowed");
    }
  }
}

async function submitFeedback() {
  fbError.classList.add("hidden");
  fbError.textContent = "";

  if (!lastEventId) {
    fbError.textContent = "Missing event ID.";
    fbError.classList.remove("hidden");
    return;
  }

  sendFeedbackBtn.disabled = true;
  sendFeedbackBtn.classList.add("opacity-60", "cursor-not-allowed");

  try {
    await request("/feedback/submit", {
      method: "POST",
      body: {
        event_id: lastEventId,
        rating: Number(ratingEl.value)
      }
    });
    
    hideFeedbackWidget();
    lastEventId = null;
    unlockInput();
    clearBanner();
  } catch (err) {
    console.error("Feedback error:", err);
    fbError.textContent = err.message || "Failed to submit feedback.";
    fbError.classList.remove("hidden");
  } finally {
    sendFeedbackBtn.disabled = false;
    sendFeedbackBtn.classList.remove("opacity-60", "cursor-not-allowed");
  }
}