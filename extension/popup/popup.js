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
const tabSettings = document.getElementById('tab-settings');
const tasksContent = document.getElementById('tasks-content');
const settingsContent = document.getElementById('settings-content');
const serverUrlInput = document.getElementById('server-url');
const notificationsToggle = document.getElementById('notifications-toggle');
const saveSettingsButton = document.getElementById('save-settings');
const taskList = document.getElementById('task-list');

// Chat history
let chatHistory = [];

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
  chrome.storage.local.get(['serverUrl', 'notificationsEnabled'], (data) => {
    if (data.serverUrl) {
      serverUrlInput.value = data.serverUrl;
    }
    
    if (data.notificationsEnabled !== undefined) {
      notificationsToggle.checked = data.notificationsEnabled;
    }
  });
}

// Check if server is available
function checkServerConnection() {
  chrome.storage.local.get('serverUrl', (data) => {
    const serverUrl = data.serverUrl || 'http://localhost:8000';
    
    fetch(`${serverUrl}/health`, { method: 'GET' })
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
  
  // Create suggestions container
  const suggestionsDiv = document.createElement('div');
  suggestionsDiv.id = 'chat-suggestions';
  suggestionsDiv.className = 'chat-suggestions';
  
  // Get relevant suggestions
  const suggestions = inputSuggestions[activeContextType] || inputSuggestions.default;
  
  // Create buttons for each suggestion
  suggestions.slice(0, 3).forEach(suggestion => {
    const button = document.createElement('button');
    button.className = 'suggestion-button';
    button.textContent = suggestion;
    button.addEventListener('click', () => {
      userInput.value = suggestion;
      sendMessage();
    });
    suggestionsDiv.appendChild(button);
  });
  
  // Add to chat container
  const chatContainer = document.querySelector('.chat-container');
  chatContainer.insertBefore(suggestionsDiv, document.querySelector('.input-container'));
}

// Set up event listeners
function setupEventListeners() {
  // Send message when button clicked
  sendButton.addEventListener('click', sendMessage);
  
  // Send message when Enter pressed (but allow Shift+Enter for new lines)
  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  
  // Tab switching
  tabChat.addEventListener('click', () => switchTab('chat'));
  tabTasks.addEventListener('click', () => {
    switchTab('tasks');
    loadTasks();
  });
  tabSettings.addEventListener('click', () => switchTab('settings'));
  
  // Save settings
  saveSettingsButton.addEventListener('click', saveSettings);
  
  // Attachment button
  attachButton.addEventListener('click', handleAttachment);
  
  // Focus input when chat tab is active
  tabChat.addEventListener('click', () => {
    setTimeout(() => userInput.focus(), 100);
  });
  
  // Update context when extension is opened
  chrome.tabs.onActivated.addListener(() => {
    updateJiraContext();
  });
  
  // Input changes - smart suggestions during typing
  userInput.addEventListener('input', smartSuggestions);
}

// Provide smart suggestions while typing
function smartSuggestions() {
  const input = userInput.value.toLowerCase().trim();
  
  // Only suggest if at least 3 characters
  if (input.length < 3) return;
  
  // Common action words to detect
  const createActions = ['create', 'add', 'make', 'new'];
  const reminderActions = ['remind', 'notification', 'alert'];
  const updateActions = ['update', 'change', 'modify', 'edit'];
  const listActions = ['list', 'find', 'show', 'get', 'display'];
  
  // Set placeholder based on detected intent
  if (createActions.some(action => input.includes(action)) && input.includes('task')) {
    userInput.placeholder = 'Creating a task: Specify assignee, title, due date...';
  } else if (reminderActions.some(action => input.includes(action))) {
    userInput.placeholder = 'Setting a reminder: Specify date, time, and details...';
  } else if (updateActions.some(action => input.includes(action)) && input.includes('status')) {
    userInput.placeholder = 'Updating status: Specify task key and new status...';
  } else if (listActions.some(action => input.includes(action))) {
    userInput.placeholder = 'Finding tasks: Specify criteria (assignee, status, etc.)...';
  }
}

// Switch between tabs
function switchTab(tab) {
  // Hide all tabs
  document.querySelector('.chat-container').style.display = 'none';
  tasksContent.style.display = 'none';
  settingsContent.style.display = 'none';
  
  // Remove active class from all tab buttons
  tabChat.classList.remove('active');
  tabTasks.classList.remove('active');
  tabSettings.classList.remove('active');
  
  // Show selected tab
  switch (tab) {
    case 'tasks':
      tasksContent.style.display = 'block';
      tabTasks.classList.add('active');
      break;
    case 'settings':
      settingsContent.style.display = 'block';
      tabSettings.classList.add('active');
      break;
    default:
      document.querySelector('.chat-container').style.display = 'block';
      tabChat.classList.add('active');
  }
}

// Send message to the server and process response
function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;
  
  // Add user message to UI
  addMessage('user', message);
  
  // Clear input
  userInput.value = '';
  
  // Reset placeholder
  if (activeContextType === 'jiraIssue') {
    userInput.placeholder = `Ask about ${currentJiraContext.issueKey}...`;
  } else if (activeContextType === 'jiraBoard') {
    userInput.placeholder = 'Ask about Jira board or project...';
  } else {
    userInput.placeholder = 'Type your message here... (e.g., "Create a task for John to review docs by Monday")';
  }
  
  // Remove suggestions
  const existingSuggestions = document.getElementById('chat-suggestions');
  if (existingSuggestions) {
    existingSuggestions.remove();
  }
  
  // Get current Jira context if available
  getCurrentTabInfo()
    .then(tabInfo => {
      // Show typing indicator
      addMessageToUI('bot', '<div class="typing-indicator"><span></span><span></span><span></span></div>', new Date().toISOString());
      
      // Send to server via background script
      chrome.runtime.sendMessage({
        type: 'API_REQUEST',
        endpoint: '/chat',
        method: 'POST',
        data: {
          message,
          context: tabInfo
        }
      }, response => {
        // Remove typing indicator
        chatMessages.removeChild(chatMessages.lastChild);
        
        if (response && response.success) {
          // Add bot response to chat
          addMessage('bot', response.data.response);
          
          // Handle actions if any were returned
          handleActions(response.data.actions);
          
          // Update context in case it changed
          updateJiraContext();
        } else {
          // Show error message
          addMessage('bot', 'Sorry, I encountered an error while processing your request. Please try again later.');
        }
      });
    });
}

// Get info about the current tab for context
async function getCurrentTabInfo() {
  return new Promise((resolve) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs.length === 0) {
        resolve({});
        return;
      }
      
      const currentTab = tabs[0];
      
      // If it's a Jira page, try to get additional context
      if (currentTab.url.includes('atlassian.net') || currentTab.url.includes('jira')) {
        chrome.tabs.sendMessage(currentTab.id, { type: 'GET_JIRA_CONTEXT' }, response => {
          if (chrome.runtime.lastError || !response) {
            // If content script not available or no response
            resolve({
              url: currentTab.url,
              title: currentTab.title
            });
          } else {
            resolve(response);
          }
        });
      } else {
        // Not a Jira page
        resolve({
          url: currentTab.url,
          title: currentTab.title
        });
      }
    });
  });
}

// Handle any actions returned from the server
function handleActions(actions) {
  if (!actions || actions.length === 0) return;
  
  actions.forEach(action => {
    switch (action.type) {
      case 'open_url':
        chrome.tabs.create({ url: action.data.url });
        break;
      case 'show_notification':
        chrome.runtime.sendMessage({
          type: 'SHOW_NOTIFICATION',
          title: action.data.title,
          message: action.data.message,
          actions: action.data.actions
        });
        break;
      case 'refresh_tasks':
        if (tabTasks.classList.contains('active')) {
          loadTasks();
        }
        break;
    }
  });
}

// Load tasks from server
function loadTasks() {
  taskList.innerHTML = '<div class="loading-indicator">Loading tasks...</div>';
  
  chrome.runtime.sendMessage({
    type: 'API_REQUEST',
    endpoint: '/tasks',
    method: 'GET'
  }, response => {
    if (response && response.success) {
      displayTasks(response.data.tasks);
    } else {
      taskList.innerHTML = '<div class="error-message">Failed to load tasks. Please try again later.</div>';
    }
  });
}

// Display tasks in the UI
function displayTasks(tasks) {
  if (!tasks || tasks.length === 0) {
    taskList.innerHTML = '<div class="empty-message">No tasks found.</div>';
    return;
  }
  
  taskList.innerHTML = '';
  
  tasks.forEach(task => {
    const taskElement = document.createElement('div');
    taskElement.className = `task-item ${task.status.toLowerCase()}`;
    
    const dueDate = task.dueDate ? new Date(task.dueDate).toLocaleDateString() : 'No due date';
    
    taskElement.innerHTML = `
      <div class="task-header">
        <span class="task-key">${task.key}</span>
        <span class="task-status">${task.status}</span>
      </div>
      <div class="task-summary">${task.summary}</div>
      <div class="task-details">
        <span class="task-assignee">${task.assignee || 'Unassigned'}</span>
        <span class="task-due-date">${dueDate}</span>
      </div>
    `;
    
    // Add click event to open the task
    taskElement.addEventListener('click', () => {
      chrome.tabs.create({ url: task.url });
    });
    
    taskList.appendChild(taskElement);
  });
}

// Save settings
function saveSettings() {
  const serverUrl = serverUrlInput.value.trim();
  const notificationsEnabled = notificationsToggle.checked;
  
  chrome.storage.local.set({
    serverUrl,
    notificationsEnabled
  }, () => {
    // Show saved message
    const savedIndicator = document.createElement('div');
    savedIndicator.className = 'saved-indicator';
    savedIndicator.textContent = 'Settings saved!';
    
    settingsContent.appendChild(savedIndicator);
    
    // Remove after 2 seconds
    setTimeout(() => {
      settingsContent.removeChild(savedIndicator);
    }, 2000);
    
    // Check connection with new URL
    checkServerConnection();
  });
}

// Handle file attachment
function handleAttachment() {
  // Create a file input element
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = 'image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt';
  
  // Trigger click event to open file picker
  fileInput.click();
  
  // Handle file selection
  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      const file = fileInput.files[0];
      
      // Add message about the attachment
      addMessage('user', `Attached file: ${file.name}`);
      
      // Create FormData and send to server via background script
      const formData = new FormData();
      formData.append('file', file);
      
      // Preview for certain file types
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          const img = document.createElement('img');
          img.src = e.target.result;
          img.className = 'attachment-preview';
          chatMessages.appendChild(img);
          chatMessages.scrollTop = chatMessages.scrollHeight;
        };
        reader.readAsDataURL(file);
      }
      
      // TODO: Implement file upload to server (requires additional backend support)
      // For now, just show a message
      setTimeout(() => {
        addMessage('bot', `I've received your file "${file.name}". What would you like me to do with it?`);
      }, 1000);
    }
  });
} 