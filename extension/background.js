/**
 * Background script for the Jira Action Items Chatbot extension
 * Handles API communication and notifications
 */

// Server connection settings
const API_BASE_URL = 'http://localhost:8000';

// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('Jira Action Items Chatbot extension installed');
  
  // Initialize extension settings
  chrome.storage.local.set({
    serverUrl: API_BASE_URL,
    notificationsEnabled: true,
    lastSyncTime: null
  });
});

// Listen for messages from content scripts or popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'API_REQUEST') {
    handleApiRequest(message.endpoint, message.method, message.data)
      .then(response => sendResponse({ success: true, data: response }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Required for async sendResponse
  }
  
  if (message.type === 'SHOW_NOTIFICATION') {
    showNotification(message.title, message.message, message.actions);
    sendResponse({ success: true });
    return true;
  }
});

// Notification handling
function showNotification(title, message, actions = []) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: title,
    message: message,
    buttons: actions.map(action => ({ title: action })),
    requireInteraction: true
  });
}

// Handle notification button clicks
chrome.notifications.onButtonClicked.addListener((notificationId, buttonIndex) => {
  console.log(`Notification ${notificationId} button ${buttonIndex} clicked`);
  // Implement actions based on which button was clicked
});

// API request handling
async function handleApiRequest(endpoint, method = 'GET', data = null) {
  const serverUrl = await getServerUrl();
  const url = `${serverUrl}${endpoint}`;
  
  const options = {
    method: method,
    headers: {
      'Content-Type': 'application/json'
    }
  };
  
  if (data && (method === 'POST' || method === 'PUT')) {
    options.body = JSON.stringify(data);
  }
  
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}

// Get server URL from storage
async function getServerUrl() {
  return new Promise((resolve) => {
    chrome.storage.local.get('serverUrl', (result) => {
      resolve(result.serverUrl || API_BASE_URL);
    });
  });
}

// Check for reminders periodically
setInterval(async () => {
  try {
    const data = await handleApiRequest('/reminders/check');
    if (data.reminders && data.reminders.length > 0) {
      data.reminders.forEach(reminder => {
        showNotification(
          'Jira Reminder',
          reminder.message,
          ['Done', 'Snooze', 'View Details']
        );
      });
    }
  } catch (error) {
    console.error('Failed to check reminders:', error);
  }
}, 300000); // Check every 5 minutes 