function showError(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) {
    el.textContent = message;
    el.classList.remove("hidden");
  }
}

function hideError(elementId) {
  const el = document.getElementById(elementId);
  if (el) {
    el.classList.add("hidden");
    el.textContent = "";
  }
}

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleString();
}

export { showError, hideError, formatDate };