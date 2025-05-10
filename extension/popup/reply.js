// DOM Elements
const taskKeyElement = document.getElementById('task-key');
const replyInput = document.getElementById('reply-input');
const sendButton = document.getElementById('send-button');
const cancelButton = document.getElementById('cancel-button');

// Parse URL parameters
const urlParams = new URLSearchParams(window.location.search);
const notificationId = urlParams.get('id');
const issueKey = urlParams.get('key');

// Initialize the reply popup
document.addEventListener('DOMContentLoaded', () => {
  // Set task key
  taskKeyElement.textContent = issueKey || 'Unknown Task';
  
  // Focus input
  replyInput.focus();
  
  // Add event listeners
  setupEventListeners();
});

// Set up event listeners
function setupEventListeners() {
  // Send button
  sendButton.addEventListener('click', sendReply);
  
  // Cancel button
  cancelButton.addEventListener('click', () => {
    // Close the popup
    window.close();
  });
  
  // Enter key
  replyInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendReply();
    }
  });
}

// Send reply to background script
function sendReply() {
  const message = replyInput.value.trim();
  
  // Validate message
  if (!message) {
    // Flash the input field
    replyInput.classList.add('error');
    setTimeout(() => {
      replyInput.classList.remove('error');
    }, 300);
    return;
  }
  
  // Disable the input and button
  replyInput.disabled = true;
  sendButton.disabled = true;
  sendButton.textContent = 'Sending...';
  
  // Close notification if it exists
  if (notificationId) {
    chrome.notifications.clear(notificationId);
  }
  
  // Send message to background script
  chrome.runtime.sendMessage({
    type: 'SEND_REPLY',
    issueKey: issueKey,
    message: message
  }, (response) => {
    // Close the popup after sending (regardless of response)
    window.close();
  });
} 