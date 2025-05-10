/**
 * Background script for the Jira Action Items Chatbot extension
 * Handles API communication and notifications
 */

// Server connection settings
const API_BASE_URL = 'http://localhost:8000';

// Auth state for storing CSRF protection
let authState = null;

// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('Jira Action Items Chatbot extension installed');
  
  // Initialize extension settings
  chrome.storage.local.set({
    serverUrl: API_BASE_URL,
    notificationsEnabled: true,
    lastSyncTime: null,
    isAuthenticated: false
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

  if (message.type === 'AUTH_LOGIN') {
    initiateLogin()
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  if (message.type === 'AUTH_LOGOUT') {
    logout()
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  if (message.type === 'AUTH_STATUS') {
    checkAuthStatus()
      .then(status => sendResponse({ success: true, data: status }))
      .catch(error => sendResponse({ success: false, error: error.message }));
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
    },
    credentials: 'include' // Include cookies for cross-origin requests
  };
  
  if (data && (method === 'POST' || method === 'PUT')) {
    options.body = JSON.stringify(data);
  }
  
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      // If 401 Unauthorized, try to refresh auth
      if (response.status === 401) {
        const isRefreshed = await refreshAuth();
        if (isRefreshed) {
          // Retry the request after successful refresh
          return handleApiRequest(endpoint, method, data);
        }
      }
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
    // Check auth status first
    const authStatus = await checkAuthStatus();
    if (!authStatus.authenticated) {
      console.log('Not authenticated, skipping reminder check');
      return;
    }

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

// OAuth Authentication

// Initiate the OAuth login process
async function initiateLogin() {
  try {
    // Generate a random state to protect against CSRF
    authState = Math.random().toString(36).substring(2, 15);
    
    // Save state to storage for validation later
    chrome.storage.local.set({ 'oauth_state': authState });
    
    const serverUrl = await getServerUrl();
    const loginUrl = `${serverUrl}/api/auth/login`;
    
    // Open a new tab with the login URL
    chrome.tabs.create({ url: loginUrl });
    
    return { message: 'Login initiated' };
  } catch (error) {
    console.error('Failed to initiate login:', error);
    throw error;
  }
}

// Logout the user
async function logout() {
  try {
    const serverUrl = await getServerUrl();
    const logoutUrl = `${serverUrl}/api/auth/logout`;
    
    // Call the logout API
    await fetch(logoutUrl, { 
      method: 'GET',
      credentials: 'include' // Include cookies
    });
    
    // Update local storage auth status
    chrome.storage.local.set({ isAuthenticated: false });
    
    return { message: 'Logged out successfully' };
  } catch (error) {
    console.error('Failed to logout:', error);
    throw error;
  }
}

// Check if the user is authenticated
async function checkAuthStatus() {
  try {
    const serverUrl = await getServerUrl();
    const statusUrl = `${serverUrl}/api/auth/status`;
    
    // Call the status API
    const response = await fetch(statusUrl, { 
      method: 'GET',
      credentials: 'include' // Include cookies
    });
    
    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
    }
    
    const status = await response.json();
    
    // Update local storage auth status
    chrome.storage.local.set({ isAuthenticated: status.authenticated });
    
    return status;
  } catch (error) {
    console.error('Failed to check auth status:', error);
    // In case of error, assume not authenticated
    chrome.storage.local.set({ isAuthenticated: false });
    return { authenticated: false, error: error.message };
  }
}

// Refresh the auth token
async function refreshAuth() {
  try {
    const serverUrl = await getServerUrl();
    const refreshUrl = `${serverUrl}/api/auth/refresh-token`;
    
    // Call the refresh token API
    const response = await fetch(refreshUrl, { 
      method: 'POST',
      credentials: 'include' // Include cookies
    });
    
    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    return result.success;
  } catch (error) {
    console.error('Failed to refresh auth token:', error);
    return false;
  }
}

// Check auth status when extension loads
checkAuthStatus().then(status => {
  console.log('Initial auth status:', status.authenticated ? 'Authenticated' : 'Not authenticated');
}); 