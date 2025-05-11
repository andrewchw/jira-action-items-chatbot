/**
 * Popup script for the Jira Action Items Chatbot extension
 * Handles the popup UI and communication with the background script
 */

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const attachButton = document.getElementById('attach-button');
const statusCircle = document.getElementById('status-circle');
const statusText = document.getElementById('status-text');
const tabChat = document.getElementById('tab-chat');
const tabTasks = document.getElementById('tab-tasks');
const tabReminders = document.getElementById('tab-reminders');
const tabSettings = document.getElementById('tab-settings');
const tasksContent = document.getElementById('tasks-content');
const remindersContent = document.getElementById('reminders-content');
const settingsContent = document.getElementById('settings-content');
const serverUrlInput = document.getElementById('server-url');
const notificationsToggle = document.getElementById('notifications-toggle');
const reminderToggle = document.getElementById('reminder-toggle');
const checkRemindersButton = document.getElementById('check-reminders-button');
const testReminderButton = document.getElementById('test-reminder-button');
const remindersList = document.getElementById('reminders-list');
const saveSettingsButton = document.getElementById('save-settings');
const taskList = document.getElementById('task-list');

// Chat history
let chatHistory = [];

// Auth state
let isAuthenticated = false;
let currentUser = null;

// Server settings
let serverSettings = {
  DEFAULT_JIRA_PROJECT_KEY: 'JCAI', // Default fallback
  JIRA_URL: 'https://your-domain.atlassian.net'
};

// Input suggestions based on context
const inputSuggestions = {
  default: [
    "Create a task for me to review the documentation by Friday",
    "List my open tasks with high priority",
    "Remind me to follow up with the team tomorrow at 9 AM",
    "Schedule a meeting for next week",
    "Upload evidence for task PROJ-123"
  ],
  jiraIssue: [
    "Add a comment to this issue",
    "Change status to 'In Progress'",
    "Add me as a watcher",
    "Set due date to next Friday",
    "Assign this to John"
  ],
  jiraBoard: [
    "Show tasks assigned to me",
    "Create a new epic for the Q3 deliverables",
    "List blocked tasks in this project",
    "Find tasks without assignees",
    "Show tasks due this week"
  ]
};

// Active context type
let activeContextType = 'default';
let currentJiraContext = {};

// Initialize the popup
document.addEventListener('DOMContentLoaded', () => {
  // Load settings from storage
  loadSettings();
  
  // Check server connection
  checkServerConnection();
  
  // Check authentication status
  checkAuthStatus();
  
  // Load server settings
  loadServerSettings();
  
  // Load chat history
  loadChatHistory();
  
  // Get current context and update suggestions
  updateJiraContext();
  
  // Add welcome message if this is first time
  chrome.storage.local.get('firstOpen', (data) => {
    if (data.firstOpen !== false) {
      // First time opening the extension
      chrome.storage.local.set({ firstOpen: false });
      addMessage('bot', 'Welcome to Jira Action Items Chatbot! How can I help you today?');
      
      // Show sample commands
      setTimeout(() => {
        addMessage('bot', 'You can ask me to do things like:<br>' +
          '• Create tasks in Jira<br>' +
          '• Set reminders for due dates<br>' +
          '• Update task status<br>' +
          '• Find tasks assigned to you<br>' +
          '<br>Try typing a command or click a suggestion below.');
        
        // Show initial suggestions
        showSuggestions();
      }, 1000);
    }
  });

  // Set up event listeners
  setupEventListeners();
});

// Load settings from storage
function loadSettings() {
  chrome.storage.local.get(['serverUrl', 'notificationsEnabled', 'isAuthenticated', 'serverSettings'], (data) => {
    if (data.serverUrl) {
      serverUrlInput.value = data.serverUrl;
    }
    
    if (data.notificationsEnabled !== undefined) {
      notificationsToggle.checked = data.notificationsEnabled;
      reminderToggle.checked = data.notificationsEnabled;
    }
    
    isAuthenticated = data.isAuthenticated || false;
    
    // Load server settings if available
    if (data.serverSettings) {
      serverSettings = {...serverSettings, ...data.serverSettings};
    }
  });
}

// Load server settings from the server
function loadServerSettings() {
  chrome.runtime.sendMessage({
    type: 'API_REQUEST',
    endpoint: '/api/settings',
    method: 'GET'
  }, (response) => {
    if (response.success && response.data.settings) {
      // Store in local variable
      serverSettings = {...serverSettings, ...response.data.settings};
      
      // Store in chrome storage
      chrome.storage.local.set({
        serverSettings: response.data.settings
      });
      
      console.log('Server settings loaded', serverSettings);
    }
  });
}

// Check authentication status
function checkAuthStatus() {
  chrome.runtime.sendMessage({ type: 'AUTH_STATUS' }, (response) => {
    if (response.success) {
      isAuthenticated = response.data.authenticated;
      currentUser = response.data.user;
      updateAuthUI();
    } else {
      console.error('Failed to check authentication status:', response.error);
      isAuthenticated = false;
      updateAuthUI();
    }
  });
}

// Update UI based on authentication status
function updateAuthUI() {
  // Add Auth UI to settings tab if it doesn't exist
  if (!document.getElementById('auth-settings')) {
    const authGroup = document.createElement('div');
    authGroup.id = 'auth-settings';
    authGroup.className = 'settings-group auth-settings';
    authGroup.innerHTML = `
      <label>Authentication</label>
      <div id="auth-status" class="auth-status"></div>
      <div id="auth-buttons" class="auth-buttons"></div>
    `;
    
    // Insert before save button
    const saveGroup = document.querySelector('.settings-group:last-child');
    settingsContent.insertBefore(authGroup, saveGroup);
  }
  
  // Update auth status display
  const authStatus = document.getElementById('auth-status');
  const authButtons = document.getElementById('auth-buttons');
  
  if (isAuthenticated && currentUser) {
    authStatus.innerHTML = `
      <div class="user-info">
        <span class="status-circle connected"></span>
        <span>Logged in as: <strong>${currentUser.name || currentUser.email || currentUser.account_id}</strong></span>
      </div>
    `;
    
    authButtons.innerHTML = `
      <button id="logout-button" class="secondary-button">Log Out</button>
    `;
    
    // Add logout event listener
    document.getElementById('logout-button').addEventListener('click', handleLogout);
  } else {
    authStatus.innerHTML = `
      <div class="user-info">
        <span class="status-circle disconnected"></span>
        <span>Not logged in</span>
      </div>
    `;
    
    authButtons.innerHTML = `
      <button id="login-button" class="primary-button">Log In with Jira</button>
    `;
    
    // Add login event listener
    document.getElementById('login-button').addEventListener('click', handleLogin);
  }
}

// Handle login button click
function handleLogin() {
  chrome.runtime.sendMessage({ type: 'AUTH_LOGIN' }, (response) => {
    if (!response.success) {
      console.error('Failed to initiate login:', response.error);
      // Show error in UI
      addMessage('bot', 'Failed to log in. Please try again later.');
    }
  });
}

// Handle logout button click
function handleLogout() {
  chrome.runtime.sendMessage({ type: 'AUTH_LOGOUT' }, (response) => {
    if (response.success) {
      isAuthenticated = false;
      currentUser = null;
      updateAuthUI();
      // Show logout message
      addMessage('bot', 'You have been logged out successfully.');
    } else {
      console.error('Failed to logout:', response.error);
      // Show error in UI
      addMessage('bot', 'Failed to log out. Please try again later.');
    }
  });
}

// Check if server is available
function checkServerConnection() {
  chrome.storage.local.get('serverUrl', (data) => {
    const serverUrl = data.serverUrl || 'http://localhost:8000';
    
    fetch(`${serverUrl}/api/health`, { method: 'GET' })
      .then(response => {
        if (response.ok) {
          setStatus('connected');
        } else {
          setStatus('error');
        }
      })
      .catch(() => {
        setStatus('disconnected');
      });
  });
}

// Set connection status display
function setStatus(status) {
  statusCircle.className = 'status-circle';
  
  switch (status) {
    case 'connected':
      statusCircle.classList.add('connected');
      statusText.textContent = 'Connected';
      break;
    case 'disconnected':
      statusCircle.classList.add('disconnected');
      statusText.textContent = 'Disconnected';
      break;
    case 'error':
      statusCircle.classList.add('error');
      statusText.textContent = 'Error';
      break;
    default:
      statusCircle.classList.add('connecting');
      statusText.textContent = 'Connecting...';
  }
}

// Load chat history from storage
function loadChatHistory() {
  chrome.storage.local.get('chatHistory', (data) => {
    if (data.chatHistory && data.chatHistory.length > 0) {
      chatHistory = data.chatHistory;
      
      // Display last 10 messages
      const recentMessages = chatHistory.slice(-10);
      recentMessages.forEach(msg => {
        addMessageToUI(msg.sender, msg.text, msg.timestamp);
      });
    }
  });
}

// Add chat message to history and UI
function addMessage(sender, text) {
  const timestamp = new Date().toISOString();
  
  // Add to chat history
  chatHistory.push({ sender, text, timestamp });
  
  // Save to storage (limited to last 50 messages to save space)
  if (chatHistory.length > 50) {
    chatHistory = chatHistory.slice(-50);
  }
  chrome.storage.local.set({ chatHistory });
  
  // Add to UI
  addMessageToUI(sender, text, timestamp);
  
  // If bot message, show suggestions after a brief delay
  if (sender === 'bot') {
    setTimeout(() => {
      showSuggestions();
    }, 500);
  }
}

// Add message to UI
function addMessageToUI(sender, text, timestamp) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${sender}-message`;
  
  const time = new Date(timestamp);
  const formattedTime = `${time.getHours().toString().padStart(2, '0')}:${time.getMinutes().toString().padStart(2, '0')}`;
  
  messageDiv.innerHTML = `
    <div class="message-content">${text}</div>
    <div class="message-time">${formattedTime}</div>
  `;
  
  chatMessages.appendChild(messageDiv);
  
  // Scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Update Jira context and suggestions based on current tab
function updateJiraContext() {
  getCurrentTabInfo().then(tabInfo => {
    currentJiraContext = tabInfo;
    
    // Determine context type
    if (tabInfo.issueKey) {
      activeContextType = 'jiraIssue';
      userInput.placeholder = `Ask about ${tabInfo.issueKey}...`;
    } else if (tabInfo.isJiraPage) {
      activeContextType = 'jiraBoard';
      userInput.placeholder = 'Ask about Jira board or project...';
    } else {
      activeContextType = 'default';
      userInput.placeholder = 'Type your message here... (e.g., "Create a task for John to review docs by Monday")';
    }
    
    // Update suggestions
    showSuggestions();
  });
}

// Show context-aware suggestions
function showSuggestions() {
  // Remove existing suggestions
  const existingSuggestions = document.getElementById('chat-suggestions');
  if (existingSuggestions) {
    existingSuggestions.remove();
  }
  
  // If not authenticated and not in settings tab, show login suggestion
  if (!isAuthenticated && !document.getElementById('tab-settings').classList.contains('active')) {
    const loginButton = document.createElement('button');
    loginButton.className = 'suggestion-button login-suggestion';
    loginButton.textContent = 'Log in with Jira to get started';
    loginButton.onclick = () => {
      switchTab(tabSettings);
      setTimeout(() => {
        const loginBtn = document.getElementById('login-button');
        if (loginBtn) loginBtn.focus();
      }, 100);
    };
    
    suggestionsDiv.appendChild(loginButton);
    chatMessages.parentNode.insertBefore(suggestionsDiv, document.querySelector('.input-container'));
    return;
  }
  
  // Get relevant suggestions
  const suggestions = inputSuggestions[activeContextType] || inputSuggestions.default;
  
  // Create buttons for each suggestion
  suggestions.slice(0, 3).forEach(suggestion => {
    const button = document.createElement('button');
    button.className = 'suggestion-button';
    button.textContent = suggestion;
    button.onclick = () => {
      userInput.value = suggestion;
      sendMessage();
    };
    
    suggestionsDiv.appendChild(button);
  });
  
  // Append suggestions to UI
  if (suggestions.length > 0) {
    chatMessages.parentNode.insertBefore(suggestionsDiv, document.querySelector('.input-container'));
  }
}

// Set up event listeners
function setupEventListeners() {
  // Send button
  sendButton.addEventListener('click', sendMessage);
  
  // User input
  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  
  // User input for suggestions
  userInput.addEventListener('input', smartSuggestions);
  
  // Attach button
  attachButton.addEventListener('click', handleAttachment);
  
  // Tab buttons
  tabChat.addEventListener('click', () => switchTab(tabChat));
  tabTasks.addEventListener('click', () => switchTab(tabTasks));
  tabReminders.addEventListener('click', () => switchTab(tabReminders));
  tabSettings.addEventListener('click', () => switchTab(tabSettings));
  
  // Reminder buttons
  checkRemindersButton.addEventListener('click', handleCheckReminders);
  testReminderButton.addEventListener('click', handleTestReminder);
  reminderToggle.addEventListener('change', saveReminderSettings);
  
  // Save settings button
  saveSettingsButton.addEventListener('click', saveSettings);
}

// Show smarter suggestions based on partial typing
function smartSuggestions() {
  const input = userInput.value.toLowerCase();
  if (input.length < 3) return;
  
  // Get relevant suggestions
  const suggestions = inputSuggestions[activeContextType] || inputSuggestions.default;
  
  // Filter suggestions that partially match input
  const matchingSuggestions = suggestions.filter(
    suggestion => suggestion.toLowerCase().includes(input)
  );
  
  // Show up to 3 matching suggestions
  if (matchingSuggestions.length > 0) {
    // Remove existing suggestions
    const existingSuggestions = document.getElementById('chat-suggestions');
    if (existingSuggestions) {
      existingSuggestions.remove();
    }
    
    // Create suggestions container
    const suggestionsDiv = document.createElement('div');
    suggestionsDiv.id = 'chat-suggestions';
    suggestionsDiv.className = 'chat-suggestions';
    
    // Create buttons for each suggestion
    matchingSuggestions.slice(0, 3).forEach(suggestion => {
      const button = document.createElement('button');
      button.className = 'suggestion-button';
      button.textContent = suggestion;
      button.onclick = () => {
        userInput.value = suggestion;
        sendMessage();
      };
      
      suggestionsDiv.appendChild(button);
    });
    
    // Append suggestions to UI
    chatMessages.parentNode.insertBefore(suggestionsDiv, document.querySelector('.input-container'));
  }
}

// Switch between tabs
function switchTab(tab) {
  // Remove active class from all tabs
  [tabChat, tabTasks, tabReminders, tabSettings].forEach(t => t.classList.remove('active'));
  
  // Add active class to selected tab
  tab.classList.add('active');
  
  // Hide all content
  chatMessages.parentNode.style.display = 'none';
  tasksContent.style.display = 'none';
  remindersContent.style.display = 'none';
  settingsContent.style.display = 'none';
  
  // Show content based on selected tab
  if (tab === tabChat) {
    chatMessages.parentNode.style.display = 'flex';
    showSuggestions();
  } else if (tab === tabTasks) {
      tasksContent.style.display = 'block';
    loadTasks();
  } else if (tab === tabReminders) {
    remindersContent.style.display = 'block';
    loadRecentReminders();
  } else if (tab === tabSettings) {
      settingsContent.style.display = 'block';
    updateAuthUI();
  }
}

// Send message to API
async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;
  
  // Clear input
  userInput.value = '';
  
  // Remove suggestions
  const existingSuggestions = document.getElementById('chat-suggestions');
  if (existingSuggestions) {
    existingSuggestions.remove();
  }
  
  // Add user message to UI
  addMessage('user', message);
  
  // Add typing indicator
  const typingIndicator = document.createElement('div');
  typingIndicator.className = 'message bot-message typing-indicator';
  typingIndicator.innerHTML = '<div class="dots"><span>.</span><span>.</span><span>.</span></div>';
  chatMessages.appendChild(typingIndicator);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  
  // Check if authenticated
  if (!isAuthenticated) {
    // Remove typing indicator
    typingIndicator.remove();
    
    // Add response about authentication
    addMessage('bot', 'Please log in with Jira to use the chatbot. Go to the Settings tab to log in.');
    return;
  }

  // Check if this is a Jira issue creation request (pattern matching before sending to API)
  let isJiraCreationRequest = /create.*task|create.*issue|add.*task|add.*issue|new.*task|new.*issue/i.test(message.toLowerCase());
  
  try {
    // Prepare message with context
    const messageData = {
      text: message,
      context: currentJiraContext
    };

    // If it appears to be a Jira creation request, check if we have enough information
    if (isJiraCreationRequest && !message.includes("project key")) {
      // First check if we can extract key details
      const summaryMatch = message.match(/summary.*?[:"']([^"']+)[:"']/i) || 
                         message.match(/title.*?[:"']([^"']+)[:"']/i);
      const descriptionMatch = message.match(/description.*?[:"']([^"']+)[:"']/i) ||
                              message.match(/details.*?[:"']([^"']+)[:"']/i);

      // If we don't have at least a summary, ask for complete information
      if (!summaryMatch) {
        // Remove typing indicator
        typingIndicator.remove();

        // Provide a template response for creating Jira issues
        const projectKey = serverSettings.DEFAULT_JIRA_PROJECT_KEY || "JCAI";
        const templateResponse = `To create a Jira issue, I need some details. You can provide them all at once like this:

Please create a Jira issue with:
- Summary: [Issue title]
- Description: [Detailed description]
- Priority: [High, Medium, or Low]
- Due date: [Optional date]

I'll use the default project key "${projectKey}" unless you specify another one.`;

        addMessage('bot', templateResponse);
        return;
      }
    }
    
    // Get the user's email from storage if available
    chrome.storage.local.get(['userEmail', 'userId'], function(result) {
      const userEmail = result.userEmail || '';
      const userId = result.userId || '';
      
      // Prepare the request
      const requestData = {
        text: message,
        history: chatHistory,
        user_id: userId || userEmail  // Add the user ID or email for OAuth authentication
      };
      
      // Log the request for debugging
      console.log('Sending message to server:', requestData);
      
      // Send the request
      fetch(serverUrlInput.value + '/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      })
        .then(response => {
          // Check for network errors
          if (!response.ok) {
            throw new Error(`Server error: ${response.status} ${response.statusText}`);
          }
          return response.json();
        })
        .then(data => {
          // Handle the response
          handleChatResponse(data, typingIndicator);
        })
        .catch(error => {
          // Handle errors
          console.error('Error:', error);
          updateMessage(typingIndicator, `<p>Error: ${error.message}</p>`);
        });
    });
  } catch (error) {
    // Remove typing indicator
    typingIndicator.remove();
    
    // Add error message to UI
    addMessage('bot', `Sorry, something went wrong. ${error.message}`);
    console.error('Error sending message:', error);
  }
}

// Get info about current tab
async function getCurrentTabInfo() {
  return new Promise((resolve) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs.length === 0) {
        resolve({ isJiraPage: false });
        return;
      }
      
      const url = tabs[0].url;
      const title = tabs[0].title;
      
      // Check if this is a Jira page
      const isJiraPage = url.includes('atlassian.net') || url.includes('jira');
      
      // Extract issue key if present in URL or title
      const issueKeyRegex = /\b([A-Z]+-[0-9]+)\b/;
      const urlMatch = url.match(issueKeyRegex);
      const titleMatch = title.match(issueKeyRegex);
      const issueKey = urlMatch ? urlMatch[1] : (titleMatch ? titleMatch[1] : null);
      
      // Extract project key if found
      const projectKeyRegex = /projects\/([A-Z]+)/;
      const projectMatch = url.match(projectKeyRegex);
      const projectKey = projectMatch ? projectMatch[1] : null;
      
            resolve({
        isJiraPage,
        issueKey,
        projectKey,
        url,
        title
      });
    });
  });
}

// Handle suggested actions
function handleActions(actions) {
  if (!actions || !Array.isArray(actions) || actions.length === 0) {
    return;
  }
  
  // Create action buttons container
  const actionsDiv = document.createElement('div');
  actionsDiv.className = 'message-actions';
  
  // Add action buttons
  actions.forEach(action => {
    // Create the button
    const button = document.createElement('button');
    button.className = 'action-button';
    button.textContent = action.text;
    
    // Add click handler based on action type
    if (action.url) {
      // External URL action
      button.addEventListener('click', () => {
        chrome.tabs.create({ url: action.url });
      });
    } else if (action.action === 'create_task') {
      // Create task action
      button.addEventListener('click', () => {
        // Normalize between title and summary
        const entities = action.params || {};
        if (entities.title && !entities.summary) {
          entities.summary = entities.title;
        } else if (entities.summary && !entities.title) {
          entities.title = entities.summary;
        }
        
        // Extract all available fields
        const taskData = {
          project_key: entities.project_key || serverSettings.DEFAULT_JIRA_PROJECT_KEY,
          summary: entities.summary || entities.title || "Task created via chatbot",
          description: entities.description || "",
          issue_type: entities.issue_type || "Task",
          priority: entities.priority || "Medium"
        };
        
        // Add optional fields if present
        if (entities.assignee) taskData.assignee = entities.assignee;
        if (entities.due_date) taskData.due_date = entities.due_date;
        if (entities.labels) taskData.labels = entities.labels;
        
        // Call the create function
        createJiraIssue(taskData);
      });
    } else if (action.action === 'transition') {
      // Transition task action
      button.addEventListener('click', () => {
        chrome.runtime.sendMessage({
          type: 'API_REQUEST',
          endpoint: `/api/jira/tasks/${action.params.task_id}/transition`,
          method: 'POST',
          data: {
            id: action.params.transition_id
          }
        }, (response) => {
          if (response.success) {
            addMessage('bot', `✅ Successfully moved ${action.params.task_id} to ${action.params.transition_name}`);
          } else {
            addMessage('bot', `❌ Failed to update status: ${response.error || "Unknown error"}`);
          }
        });
      });
    } else {
      // Generic action (handled by extension)
      button.addEventListener('click', () => {
        // Pass action to handler function
        chrome.runtime.sendMessage({
          type: 'HANDLE_ACTION',
          action: action.action,
          params: action.params
        }, (response) => {
          if (response && response.message) {
            addMessage('bot', response.message);
          }
        });
      });
    }
    
    // Add button to container
    actionsDiv.appendChild(button);
  });
  
  // Append actions to UI
  chatMessages.appendChild(actionsDiv);
  
  // Scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Create a Jira issue based on extracted entities
function createJiraIssue(entities) {
  // Create a new message element for response
  const loadingMessageElement = document.createElement('div');
  loadingMessageElement.className = 'message bot-message';
  loadingMessageElement.innerHTML = '<div class="message-content">Creating Jira issue...</div>';
  chatMessages.appendChild(loadingMessageElement);

  // Scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;
  
  // Use default project key if not specified
  const projectKey = entities.project_key || serverSettings?.DEFAULT_JIRA_PROJECT_KEY || 'JCAI';
  
  // Ensure required fields are present
  if (!entities.summary && !entities.title) {
    updateMessage(loadingMessageElement, '❌ Error: Summary/Title is required to create a Jira issue.');
    return;
  }
  
  // Get the user's email from storage if available
  chrome.storage.local.get(['userEmail', 'userId'], function(result) {
    const userEmail = result.userEmail || '';
    const userId = result.userId || '';
    
    // Add user info to entities for OAuth authentication
    entities.user_id = userId || userEmail;
    
    // Normalize title/summary
    if (!entities.summary && entities.title) {
      entities.summary = entities.title;
    } else if (!entities.title && entities.summary) {
      entities.title = entities.summary;
    }
    
    // Ensure project key is set
    entities.project_key = projectKey;
    
    console.log('Creating Jira issue with entities:', entities);
    
    // Send the request
    fetch(`${serverUrl}/api/jira/tasks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(entities),
    })
      .then(response => {
        if (!response.ok) {
          return response.json().then(data => {
            throw new Error(data.message || `Server error: ${response.status}`);
          });
        }
        return response.json();
      })
      .then(data => {
        // Handle success response
        if (data.success && data.key) {
          const issueLink = `${jiraBaseUrl || 'https://your-jira-instance.atlassian.net'}/browse/${data.key}`;
          let responseMessage = `
            ✅ Successfully created Jira issue <a href="${issueLink}" target="_blank">${data.key}</a>:<br>
            <strong>Summary:</strong> ${data.summary || entities.summary}<br>
            <strong>Project:</strong> ${data.project_key || entities.project_key}<br>
            <strong>Type:</strong> ${data.issue_type || entities.issue_type || 'Task'}<br>
          `;
          
          // Add optional fields if present
          if (data.assignee || entities.assignee) {
            responseMessage += `<strong>Assignee:</strong> ${data.assignee || entities.assignee}<br>`;
          }
          
          if (entities.priority) {
            responseMessage += `<strong>Priority:</strong> ${entities.priority}<br>`;
          }
          
          if (entities.due_date) {
            responseMessage += `<strong>Due Date:</strong> ${entities.due_date}<br>`;
          }
          
          updateMessage(loadingMessageElement, responseMessage);
          
          // Add success to chat history
          addChatHistoryItem('system', `Created Jira issue ${data.key}: ${data.summary || entities.summary}`);
        } else {
          // Handle unexpected success response format
          updateMessage(loadingMessageElement, `✅ Jira issue created, but response format was unexpected: ${JSON.stringify(data)}`);
        }
      })
      .catch(error => {
        // Handle error
        console.error('Error creating Jira issue:', error);
        
        // Create retry button
        const retryButton = document.createElement('button');
        retryButton.textContent = 'Retry';
        retryButton.className = 'retry-button';
        retryButton.onclick = function() {
          // Replace error message with loading
          updateMessage(loadingMessageElement, 'Retrying Jira issue creation...');
          // Try again
          setTimeout(() => createJiraIssue(entities), 500);
        };
        
        // Update with error message and retry button
        updateMessage(
          loadingMessageElement, 
          `❌ Error creating Jira issue: ${error.message} <div class="retry-container"></div>`
        );
        
        // Add the retry button
        loadingMessageElement.querySelector('.retry-container').appendChild(retryButton);
        
        // Add failure to chat history
        addChatHistoryItem('system', `Failed to create Jira issue: ${error.message}`);
      });
  });
}

// Load tasks from API
function loadTasks() {
  // Show loading indicator
  taskList.innerHTML = '<div class="loading-indicator">Loading tasks...</div>';
  
  // Check if authenticated
  if (!isAuthenticated) {
    taskList.innerHTML = '<div class="no-tasks">Please log in with Jira to see your tasks.</div>';
    return;
  }
  
  // Fetch tasks
  chrome.runtime.sendMessage({
    type: 'API_REQUEST',
    endpoint: '/api/jira/tasks',
    method: 'GET'
  }, (response) => {
    if (response.success) {
      displayTasks(response.data.issues || []);
    } else {
      taskList.innerHTML = `<div class="error-message">Failed to load tasks: ${response.error}</div>`;
    }
  });
}

// Display tasks in the UI
function displayTasks(tasks) {
  if (tasks.length === 0) {
    taskList.innerHTML = '<div class="no-tasks">No tasks found.</div>';
    return;
  }
  
  taskList.innerHTML = '';
  
  tasks.forEach(task => {
    const taskElement = document.createElement('div');
    taskElement.className = 'task-item';
    
    // Get key fields
    const key = task.key;
    const summary = task.fields?.summary || 'No summary';
    const status = task.fields?.status?.name || 'Unknown';
    const issuetype = task.fields?.issuetype?.name || 'Task';
    const priority = task.fields?.priority?.name || 'Normal';
    
    // Format due date if available
    let dueDate = 'No due date';
    if (task.fields?.duedate) {
      const date = new Date(task.fields.duedate);
      dueDate = date.toLocaleDateString();
    }
    
    // Create task HTML
    taskElement.innerHTML = `
      <div class="task-header">
        <span class="task-key">${key}</span>
        <span class="task-status status-${status.toLowerCase().replace(/\s+/g, '-')}">${status}</span>
      </div>
      <div class="task-summary">${summary}</div>
      <div class="task-details">
        <span class="task-type">${issuetype}</span>
        <span class="task-priority">${priority}</span>
        <span class="task-due-date">${dueDate}</span>
      </div>
      <div class="task-actions">
        <button class="task-action-button view-button">View</button>
        <button class="task-action-button update-button">Update</button>
      </div>
    `;
    
    // Add click handler for view button
    taskElement.querySelector('.view-button').addEventListener('click', () => {
      chrome.storage.local.get('serverUrl', (data) => {
        const jiraUrl = data.serverUrl ? 
          data.serverUrl.replace(/\/api$/, '') : 
          'https://your-domain.atlassian.net';
        chrome.tabs.create({ url: `${jiraUrl}/browse/${key}` });
      });
    });
    
    // Add click handler for update button
    taskElement.querySelector('.update-button').addEventListener('click', () => {
      switchTab(tabChat);
      userInput.value = `Update ${key} status`;
      userInput.focus();
    });
    
    taskList.appendChild(taskElement);
  });
}

// Save settings
function saveSettings() {
  const serverUrl = serverUrlInput.value.trim();
  const notificationsEnabled = notificationsToggle.checked;
  
  // Validate server URL
  if (!serverUrl) {
    alert('Please enter a valid server URL');
    return;
  }
  
  // Save settings
  chrome.storage.local.set({
    serverUrl,
    notificationsEnabled
  }, () => {
    // Show success feedback
    const saveButton = document.getElementById('save-settings');
    saveButton.textContent = 'Saved!';
    saveButton.classList.add('success');
    
    // Revert button text after 2 seconds
    setTimeout(() => {
      saveButton.textContent = 'Save Settings';
      saveButton.classList.remove('success');
    }, 2000);
    
    // Check server connection with new URL
    checkServerConnection();
  });
}

// Handle attachment button click
function handleAttachment() {
  // Check if authenticated
  if (!isAuthenticated) {
    addMessage('bot', 'Please log in with Jira to upload attachments.');
    return;
  }
  
  // Create file input
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = 'image/*,application/pdf,.doc,.docx,.xls,.xlsx,.txt';
  
  // Trigger file selection
  fileInput.click();
  
  // Handle file selection
  fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      addMessage('bot', 'File too large. Maximum size is 10MB.');
      return;
    }
    
    // Show file selection in UI
    addMessage('user', `📎 Selected file: ${file.name}`);
    
    // Here you would upload the file to the server
    // This requires additional implementation in the API
  });
}

// Handle checking for reminders
function handleCheckReminders() {
  // Disable button while checking
  checkRemindersButton.disabled = true;
  checkRemindersButton.textContent = 'Checking...';
  
  // Show checking message
  const loadingItem = document.createElement('div');
  loadingItem.className = 'reminder-item loading';
  loadingItem.innerHTML = '<div class="reminder-title">Checking for reminders...</div>';
  remindersList.innerHTML = '';
  remindersList.appendChild(loadingItem);
  
  // Check authentication
  if (!isAuthenticated) {
    remindersList.innerHTML = '<div class="no-reminders">Please log in with Jira to check reminders.</div>';
    checkRemindersButton.disabled = false;
    checkRemindersButton.textContent = 'Check Now';
    return;
  }
  
  // Call background script to check reminders
  chrome.runtime.sendMessage({ type: 'CHECK_REMINDERS' }, (response) => {
    checkRemindersButton.disabled = false;
    checkRemindersButton.textContent = 'Check Now';
    
    if (response.success) {
      const data = response.data;
      
      if (data.reminders && data.reminders.length > 0) {
        // Show reminders
        loadRecentReminders(data.reminders);
      } else {
        // No reminders
        remindersList.innerHTML = '<div class="no-reminders">No reminders found.</div>';
      }
    } else {
      // Error
      remindersList.innerHTML = `<div class="error-message">Failed to check reminders: ${response.error}</div>`;
    }
  });
}

// Handle test reminder
function handleTestReminder() {
  // Show testing message
  testReminderButton.disabled = true;
  testReminderButton.textContent = 'Sending...';
  
  // Check authentication
  if (!isAuthenticated) {
    alert('Please log in with Jira to test reminders.');
    testReminderButton.disabled = false;
    testReminderButton.textContent = 'Test Notification';
    return;
  }
  
  // Create test reminder
  const testMessage = `This is a test reminder created at ${new Date().toLocaleTimeString()}`;
  
  chrome.runtime.sendMessage({ 
    type: 'API_REQUEST',
    endpoint: '/api/reminders/test',
    method: 'POST',
    data: { message: testMessage }
  }, (response) => {
    testReminderButton.disabled = false;
    testReminderButton.textContent = 'Test Notification';
    
    if (response.success) {
      // Show the reminder
      const reminder = response.data.reminder;
      
      // Create notification
      chrome.runtime.sendMessage({
        type: 'SHOW_NOTIFICATION',
        title: 'Test Reminder',
        message: reminder.message,
        actions: reminder.actions
      });
      
      // Refresh reminder list
      loadRecentReminders([reminder]);
    } else {
      alert(`Failed to create test reminder: ${response.error}`);
    }
  });
}

// Save reminder settings
function saveReminderSettings() {
  chrome.storage.local.set({
    notificationsEnabled: reminderToggle.checked
  }, () => {
    // Update notifications toggle to match
    notificationsToggle.checked = reminderToggle.checked;
  });
}

// Load recent reminders
function loadRecentReminders(reminders = null) {
  // Clear list
  remindersList.innerHTML = '';
  
  // If reminders provided, use them
  if (reminders && reminders.length > 0) {
    displayReminders(reminders);
    return;
  }
  
  // Otherwise load from storage
  chrome.storage.local.get('recentReminders', (data) => {
    if (data.recentReminders && data.recentReminders.length > 0) {
      displayReminders(data.recentReminders);
    } else {
      remindersList.innerHTML = '<div class="no-reminders">No recent reminders</div>';
    }
  });
}

// Display reminders in the UI
function displayReminders(reminders) {
  // Save to storage
  chrome.storage.local.set({ recentReminders: reminders.slice(0, 10) });
  
  // Clear list
  remindersList.innerHTML = '';
  
  // Add reminders
  reminders.forEach(reminder => {
    const reminderItem = document.createElement('div');
    reminderItem.className = `reminder-item urgency-${reminder.urgency}`;
    
    // Format timestamp
    const timestamp = new Date(reminder.timestamp);
    const formattedTime = timestamp.toLocaleString();
    
    reminderItem.innerHTML = `
      <div class="reminder-header">
        <span class="reminder-key">${reminder.key}</span>
        <span class="reminder-time">${formattedTime}</span>
      </div>
      <div class="reminder-title">${reminder.title}</div>
      <div class="reminder-message">${reminder.message}</div>
      <div class="reminder-details">
        <span class="reminder-priority">Priority: ${reminder.priority}</span>
        <span class="reminder-status">Status: ${reminder.status}</span>
      </div>
    `;
    
    remindersList.appendChild(reminderItem);
  });
}

// Update an existing message element
function updateMessage(messageElement, newText) {
  if (!messageElement) return;
  
  // Find the message content element
  const contentElement = messageElement.querySelector('.message-content');
  if (contentElement) {
    contentElement.innerHTML = newText;
  }
  
  // Scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;
} 