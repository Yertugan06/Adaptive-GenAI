import { apiRequest } from './api.js';

let feedbackRequired = false;
let lastAIResponseId = null;
let tempUserInput = "";

const messagesContainer = document.getElementById('messagesContainer');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const ratingSection = document.getElementById('ratingSection');
const warningMessage = document.getElementById('warningMessage');

function addUserMessage(text) {
  const messageDiv = document.createElement('div');
  messageDiv.className = 'flex justify-end mb-4';
  messageDiv.innerHTML = `
    <div class="bg-blue-600 text-white p-3 rounded-lg max-w-md">
      ${escapeHtml(text)}
    </div>
  `;
  messagesContainer.appendChild(messageDiv);
  scrollToBottom();
}

function addAIMessage(text, responseId) {
  const messageDiv = document.createElement('div');
  messageDiv.className = 'flex justify-start mb-4';

  // 1. Parse Markdown to HTML
  const rawHtml = marked.parse(text);

  // 2. Sanitize the HTML (Prevents XSS attacks)
  const safeHtml = DOMPurify.sanitize(rawHtml);

  // 3. Add the 'prose' class. This tells Tailwind to style h1, ul, li, bolding, etc.
  messageDiv.innerHTML = `
    <div class="bg-white border border-gray-200 p-4 rounded-lg max-w-2xl prose prose-sm prose-slate">
      ${safeHtml}
    </div>
  `;
  
  messagesContainer.appendChild(messageDiv);
  scrollToBottom();
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showRatingSection() {
  ratingSection.classList.remove('hidden');
  updateSendButtonState();
}

function hideRatingSection() {
  ratingSection.classList.add('hidden');
  updateSendButtonState();
}

function updateSendButtonState() {
  sendBtn.disabled = feedbackRequired;
  if (feedbackRequired) {
    sendBtn.classList.add('opacity-50', 'cursor-not-allowed');
  } else {
    sendBtn.classList.remove('opacity-50', 'cursor-not-allowed');
  }
}

function showWarning(message) {
  warningMessage.textContent = message;
  warningMessage.classList.remove('hidden');
  setTimeout(() => {
    warningMessage.classList.add('hidden');
  }, 3000);
}

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  if (feedbackRequired) {
    tempUserInput = message;
    showWarning('Please rate the previous response before sending a new prompt.');
    return;
  }

  userInput.value = '';
  addUserMessage(message);

  try {
    const data = await apiRequest('/prompts/submit', 'POST', { 
      prompt_text: message 
    });

    // Backend returns: response_text, ai_response_id, model, feedback_required
    if (data.response_text) {
      addAIMessage(data.response_text, data.ai_response_id);

      // Backend tells us if feedback is required
      if (data.feedback_required) {
        feedbackRequired = true;
        lastAIResponseId = data.ai_response_id;
        showRatingSection();
      }
    } else {
      // Handle unexpected response structure
      const errorDiv = document.createElement('div');
      errorDiv.className = 'flex justify-start mb-4';
      errorDiv.innerHTML = `
        <div class="bg-yellow-50 border border-yellow-200 text-yellow-700 p-3 rounded-lg max-w-md">
          Response received but no AI answer found. Please try again.
        </div>
      `;
      messagesContainer.appendChild(errorDiv);
      scrollToBottom();
    }

  } catch (err) {
    // Check if this is a 403 feedback required error
    if (err.message && err.message.includes('Feedback required')) {
      feedbackRequired = true;
      showRatingSection();
      showWarning('Please rate the previous response first.');
      // Put the message back in the input
      userInput.value = message;
    } else {
      const errorDiv = document.createElement('div');
      errorDiv.className = 'flex justify-start mb-4';
      errorDiv.innerHTML = `
        <div class="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg max-w-md">
          Error: ${escapeHtml(err.message)}
        </div>
      `;
      messagesContainer.appendChild(errorDiv);
      scrollToBottom();
    }
  }
}

async function submitRating(rating) {
  if (!lastAIResponseId) return;

  try {
    await apiRequest('/feedback/submit', 'POST', {
      event_id: lastAIResponseId,
      rating: rating
    });

    feedbackRequired = false;
    lastAIResponseId = null;
    hideRatingSection();

    if (tempUserInput !== "") {
      const savedInput = tempUserInput;
      tempUserInput = "";
      userInput.value = savedInput;
      await sendMessage();
    }

  } catch (err) {
    showWarning('Failed to submit rating: ' + err.message);
  }
}

// Initialize chat state on page load
async function initializeChat() {
  try {
    // Start with clean state
    feedbackRequired = false;
    lastAIResponseId = null;
    hideRatingSection();
    updateSendButtonState();
    
    // Note: If backend has a /feedback/status endpoint, check it here
    // to see if there's pending feedback from a previous session
  } catch (err) {
    console.error('Failed to initialize chat:', err);
  }
}

sendBtn.addEventListener('click', sendMessage);

userInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

document.querySelectorAll('.rating-star').forEach((star, index) => {
  star.addEventListener('click', () => {
    submitRating(index + 1);
  });
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', initializeChat);

export { sendMessage, submitRating };