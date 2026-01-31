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
const commentEl = document.getElementById("comment");
const sendFeedbackBtn = document.getElementById("sendFeedbackBtn");
const fbError = document.getElementById("fbError");

let feedbackPending = false;
let lastAiResponseId = null;

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function setBanner(msg) {
  banner.textContent = msg;
  banner.classList.remove("hidden");
}
function clearBanner() {
  banner.textContent = "";
  banner.classList.add("hidden");
}

function lockInput() {
  feedbackPending = true;
  promptInput.disabled = true;
  sendPromptBtn.disabled = true;
  promptInput.classList.add("opacity-60");
  sendPromptBtn.classList.add("opacity-60", "cursor-not-allowed");
}

function unlockInput() {
  feedbackPending = false;
  promptInput.disabled = false;
  sendPromptBtn.disabled = false;
  promptInput.classList.remove("opacity-60");
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

function showFeedbackWidget(aiId) {
  lastAiResponseId = aiId;
  fbTarget.textContent = `response: ${aiId}`;
  feedbackBox.classList.remove("hidden");
  fbError.classList.add("hidden");
  fbError.textContent = "";
}

function hideFeedbackWidget() {
  feedbackBox.classList.add("hidden");
  commentEl.value = "";
  ratingEl.value = "5";
}

async function syncFeedbackState() {
  const me = await loadMe();

  // Badge from session user (fast) — can also update from /auth/me if it includes name/role
  if (me.feedback_required) {
    lockInput();
    setBanner("Feedback is required to continue. Please submit feedback.");
  } else {
    unlockInput();
    clearBanner();
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
  if (e.key === "Enter") submitPrompt();
});

sendFeedbackBtn.addEventListener("click", submitFeedback);

async function init() {
  const user = getUser();
  if (user) userBadge.textContent = `${user.name} • ${user.role}`;
  await syncFeedbackState();
}
init();

async function submitPrompt() {
  if (feedbackPending) {
    setBanner("Feedback is required before sending the next prompt.");
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
      body: { prompt_text: promptText, topics: ["general"] }
    });

    addMessage(
      "AI",
      data.response_text,
      `${data.model || ""}${data.used_cached_answer ? " • cached" : ""}`.trim()
    );

    // According to spec, backend usually sets feedback_required=true after a generation
    if (data.feedback_required) {
      lockInput();
      showFeedbackWidget(data.ai_response_id);
      setBanner("Feedback required. Please rate the answer to continue.");
    } else {
      unlockInput();
      hideFeedbackWidget();
      clearBanner();
    }
  } catch (err) {
    if (err.status === 403) {
      // backend says feedback required
      await syncFeedbackState();
    } else if (err.status === 401) {
      clearToken();
      window.location.href = "./login.html";
    } else {
      setBanner(err.message || "Failed to submit prompt.");
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

  if (!lastAiResponseId) {
    fbError.textContent = "Missing ai_response_id.";
    fbError.classList.remove("hidden");
    return;
  }

  sendFeedbackBtn.disabled = true;
  sendFeedbackBtn.classList.add("opacity-60", "cursor-not-allowed");

  try {
    await request("/feedback/submit", {
      method: "POST",
      body: {
        ai_response_id: lastAiResponseId,
        rating: Number(ratingEl.value),
        comment: commentEl.value.trim()
      }
    });
  } catch (err) {
    // Spec: 400 feedback already exists
    if (!(err.status === 400 && /already exists/i.test(err.message))) {
      fbError.textContent = err.message || "Failed to submit feedback.";
      fbError.classList.remove("hidden");
      sendFeedbackBtn.disabled = false;
      sendFeedbackBtn.classList.remove("opacity-60", "cursor-not-allowed");
      return;
    }
  }

  hideFeedbackWidget();
  lastAiResponseId = null;

  await syncFeedbackState();

  sendFeedbackBtn.disabled = false;
  sendFeedbackBtn.classList.remove("opacity-60", "cursor-not-allowed");
}
