/**
 * Background script for the Jira Action Items Chatbot extension
 * Handles API communication and notifications
 */

// Server connection settings
const API_BASE_URL = 'http://localhost:8000';

// Auth state for storing CSRF protection
let authState = null;

// Notification state
let lastNotificationCheck = 0;
const NOTIFICATION_CHECK_INTERVAL = 5 * 60 * 1000; // 5 minutes in milliseconds
let notificationQueue = [];
let isProcessingQueue = false;
let checkRemindersTimeout = null;

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
  
  // Start reminder checks
  startReminderChecks();
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
  
  if (message.type === 'CHECK_REMINDERS') {
    checkReminders()
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  
  if (message.type === 'HANDLE_NOTIFICATION_ACTION') {
    handleNotificationAction(message.notificationId, message.action, message.issueKey)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  
  if (message.type === 'SEND_REPLY') {
    handleConversationalReply(message.issueKey, message.message)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
});

// Start periodic reminder checks
function startReminderChecks() {
  console.log('Starting reminder checks...');
  // Initial check
  checkReminders();
  
  // Check for notifications at regular intervals
  function schedulNextCheck() {
    if (checkRemindersTimeout) {
      clearTimeout(checkRemindersTimeout);
    }
    
    checkRemindersTimeout = setTimeout(() => {
      checkReminders().finally(() => {
        schedulNextCheck();
      });
    }, NOTIFICATION_CHECK_INTERVAL);
  }
  
  schedulNextCheck();
}

// Check for reminders from the server
async function checkReminders() {
  try {
    // First check if authenticated
    const authStatus = await checkAuthStatus();
    if (!authStatus.authenticated) {
      console.log('Not authenticated, skipping reminder check');
      return { reminders: [], count: 0 };
    }
    
    // Get notifications enabled setting
    const { notificationsEnabled } = await new Promise(resolve => {
      chrome.storage.local.get('notificationsEnabled', (result) => {
        resolve(result);
      });
    });
    
    if (!notificationsEnabled) {
      console.log('Notifications disabled, skipping reminder check');
      return { reminders: [], count: 0 };
    }
    
    // Check for reminders
    console.log('Checking for reminders...');
    const result = await handleApiRequest('/api/reminders/check');
    
    // Update last check time
    lastNotificationCheck = Date.now();
    
    // Process reminders
    if (result.reminders && result.reminders.length > 0) {
      console.log(`Found ${result.reminders.length} reminders`);
      
      // Queue reminders for display
      notificationQueue = notificationQueue.concat(result.reminders);
      
      // Process the queue (one at a time)
      if (!isProcessingQueue) {
        processNotificationQueue();
      }
    } else {
      console.log('No reminders found');
    }
    
    return result;
  } catch (error) {
    console.error('Failed to check reminders:', error);
    throw error;
  }
}

// Process the notification queue one at a time with delay
async function processNotificationQueue() {
  if (notificationQueue.length === 0) {
    isProcessingQueue = false;
    return;
  }
  
  isProcessingQueue = true;
  
  // Get the next reminder
  const reminder = notificationQueue.shift();
  
  // Show notification
  showReminderNotification(reminder);
  
  // Wait before showing the next notification
  setTimeout(() => {
    processNotificationQueue();
  }, 5000); // 5 second delay between notifications
}

// Show a reminder notification
function showReminderNotification(reminder) {
  const notificationId = `reminder-${reminder.key}-${Date.now()}`;
  
  // Store reminder data for action handling
  chrome.storage.local.set({
    [notificationId]: reminder
  });
  
  // Add Reply action if not already present
  if (!reminder.actions.includes('Reply')) {
    reminder.actions.push('Reply');
  }
  
  // Create notification
  chrome.notifications.create(notificationId, {
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: `${reminder.key}: ${reminder.title}`,
    message: reminder.message,
    contextMessage: `Priority: ${reminder.priority} | Status: ${reminder.status}`,
    buttons: reminder.actions.slice(0, 2).map(action => ({ title: action })),
    requireInteraction: true
  });
}

// Handle notification button clicks
chrome.notifications.onButtonClicked.addListener((notificationId, buttonIndex) => {
  // Get the reminder data
  chrome.storage.local.get(notificationId, (result) => {
    if (result[notificationId]) {
      const reminder = result[notificationId];
      const action = reminder.actions[buttonIndex];
      
      // Handle action
      handleNotificationAction(notificationId, action, reminder.key)
        .then(() => {
          // Clear notification data
          chrome.storage.local.remove(notificationId);
        })
        .catch(error => {
          console.error(`Failed to handle notification action: ${error}`);
        });
    }
  });
});

// Handle a notification action
async function handleNotificationAction(notificationId, action, issueKey) {
  try {
    console.log(`Handling notification action: ${action} for ${issueKey}`);
    
    switch (action) {
      case 'Done':
        // Mark issue as done
        await handleApiRequest('/api/reminders/mark-done', 'POST', { issue_key: issueKey });
        break;
      
      case 'Snooze':
        // Snooze issue for 1 day
        await handleApiRequest('/api/reminders/snooze', 'POST', { 
          issue_key: issueKey,
          days: 1
        });
        break;
      
      case 'View':
        // Open Jira issue in new tab
        const serverUrl = await getServerUrl();
        const baseUrl = serverUrl.replace('/api', '');
        chrome.tabs.create({ url: `${baseUrl}/browse/${issueKey}` });
        break;
      
      case 'Reply':
        // Show input popup for replying to the notification
        showReplyPopup(notificationId, issueKey);
        return { success: true, action }; // Early return to keep notification open
    }
    
    // Close the notification
    chrome.notifications.clear(notificationId);
    
    return { success: true, action };
  } catch (error) {
    console.error(`Failed to handle action ${action} for ${issueKey}:`, error);
    throw error;
  }
}

// Show reply popup for conversational responses
function showReplyPopup(notificationId, issueKey) {
  // Create popup with input field
  chrome.windows.create({
    url: `popup/reply.html?id=${notificationId}&key=${issueKey}`,
    type: 'popup',
    width: 400,
    height: 200,
    focused: true
  });
}

// Handle conversational reply
async function handleConversationalReply(issueKey, message) {
  try {
    console.log(`Handling conversational reply for ${issueKey}: ${message}`);
    
    // Send the reply to the server
    const result = await handleApiRequest('/api/reminders/reply', 'POST', {
      issue_key: issueKey,
      message: message
    });
    
    // Show feedback notification based on intent
    const intent = result.intent || 'UNKNOWN';
    
    // Create an appropriate feedback message
    let feedbackTitle = 'Reply Sent';
    let feedbackMessage = '';
    
    switch (intent) {
      case 'COMPLETE':
        feedbackTitle = 'Task Completed';
        feedbackMessage = `Task ${issueKey} has been marked as done`;
        break;
      
      case 'SNOOZE':
        feedbackTitle = 'Task Snoozed';
        feedbackMessage = `Task ${issueKey} has been snoozed for ${result.days || 1} day(s)`;
        break;
      
      case 'UPDATE':
        feedbackTitle = 'Comment Added';
        feedbackMessage = `Comment added to ${issueKey}`;
        break;
      
      case 'VIEW':
        feedbackTitle = 'Opening Task';
        feedbackMessage = `Opening ${issueKey} for viewing`;
        
        // Open task in a new tab
        const serverUrl = await getServerUrl();
        const baseUrl = serverUrl.replace('/api', '');
        chrome.tabs.create({ url: `${baseUrl}/browse/${issueKey}` });
        break;
      
      default:
        feedbackTitle = 'Reply Processed';
        feedbackMessage = `Your message was added as a comment to ${issueKey}`;
    }
    
    // Show feedback notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: feedbackTitle,
      message: feedbackMessage
    });
    
    return result;
  } catch (error) {
    console.error(`Failed to process conversational reply for ${issueKey}:`, error);
    
    // Show error notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'Error Processing Reply',
      message: `Failed to process your reply: ${error.message}`
    });
    
    throw error;
  }
}

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