/******/ (() => { // webpackBootstrap
/*!************************!*\
  !*** ./popup/popup.js ***!
  \************************/
function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
function _regeneratorRuntime() { "use strict"; /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ _regeneratorRuntime = function _regeneratorRuntime() { return r; }; var t, r = {}, e = Object.prototype, n = e.hasOwnProperty, o = "function" == typeof Symbol ? Symbol : {}, i = o.iterator || "@@iterator", a = o.asyncIterator || "@@asyncIterator", u = o.toStringTag || "@@toStringTag"; function c(t, r, e, n) { return Object.defineProperty(t, r, { value: e, enumerable: !n, configurable: !n, writable: !n }); } try { c({}, ""); } catch (t) { c = function c(t, r, e) { return t[r] = e; }; } function h(r, e, n, o) { var i = e && e.prototype instanceof Generator ? e : Generator, a = Object.create(i.prototype); return c(a, "_invoke", function (r, e, n) { var o = 1; return function (i, a) { if (3 === o) throw Error("Generator is already running"); if (4 === o) { if ("throw" === i) throw a; return { value: t, done: !0 }; } for (n.method = i, n.arg = a;;) { var u = n.delegate; if (u) { var c = d(u, n); if (c) { if (c === f) continue; return c; } } if ("next" === n.method) n.sent = n._sent = n.arg;else if ("throw" === n.method) { if (1 === o) throw o = 4, n.arg; n.dispatchException(n.arg); } else "return" === n.method && n.abrupt("return", n.arg); o = 3; var h = s(r, e, n); if ("normal" === h.type) { if (o = n.done ? 4 : 2, h.arg === f) continue; return { value: h.arg, done: n.done }; } "throw" === h.type && (o = 4, n.method = "throw", n.arg = h.arg); } }; }(r, n, new Context(o || [])), !0), a; } function s(t, r, e) { try { return { type: "normal", arg: t.call(r, e) }; } catch (t) { return { type: "throw", arg: t }; } } r.wrap = h; var f = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} var l = {}; c(l, i, function () { return this; }); var p = Object.getPrototypeOf, y = p && p(p(x([]))); y && y !== e && n.call(y, i) && (l = y); var v = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(l); function g(t) { ["next", "throw", "return"].forEach(function (r) { c(t, r, function (t) { return this._invoke(r, t); }); }); } function AsyncIterator(t, r) { function e(o, i, a, u) { var c = s(t[o], t, i); if ("throw" !== c.type) { var h = c.arg, f = h.value; return f && "object" == _typeof(f) && n.call(f, "__await") ? r.resolve(f.__await).then(function (t) { e("next", t, a, u); }, function (t) { e("throw", t, a, u); }) : r.resolve(f).then(function (t) { h.value = t, a(h); }, function (t) { return e("throw", t, a, u); }); } u(c.arg); } var o; c(this, "_invoke", function (t, n) { function i() { return new r(function (r, o) { e(t, n, r, o); }); } return o = o ? o.then(i, i) : i(); }, !0); } function d(r, e) { var n = e.method, o = r.i[n]; if (o === t) return e.delegate = null, "throw" === n && r.i["return"] && (e.method = "return", e.arg = t, d(r, e), "throw" === e.method) || "return" !== n && (e.method = "throw", e.arg = new TypeError("The iterator does not provide a '" + n + "' method")), f; var i = s(o, r.i, e.arg); if ("throw" === i.type) return e.method = "throw", e.arg = i.arg, e.delegate = null, f; var a = i.arg; return a ? a.done ? (e[r.r] = a.value, e.next = r.n, "return" !== e.method && (e.method = "next", e.arg = t), e.delegate = null, f) : a : (e.method = "throw", e.arg = new TypeError("iterator result is not an object"), e.delegate = null, f); } function w(t) { this.tryEntries.push(t); } function m(r) { var e = r[4] || {}; e.type = "normal", e.arg = t, r[4] = e; } function Context(t) { this.tryEntries = [[-1]], t.forEach(w, this), this.reset(!0); } function x(r) { if (null != r) { var e = r[i]; if (e) return e.call(r); if ("function" == typeof r.next) return r; if (!isNaN(r.length)) { var o = -1, a = function e() { for (; ++o < r.length;) if (n.call(r, o)) return e.value = r[o], e.done = !1, e; return e.value = t, e.done = !0, e; }; return a.next = a; } } throw new TypeError(_typeof(r) + " is not iterable"); } return GeneratorFunction.prototype = GeneratorFunctionPrototype, c(v, "constructor", GeneratorFunctionPrototype), c(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = c(GeneratorFunctionPrototype, u, "GeneratorFunction"), r.isGeneratorFunction = function (t) { var r = "function" == typeof t && t.constructor; return !!r && (r === GeneratorFunction || "GeneratorFunction" === (r.displayName || r.name)); }, r.mark = function (t) { return Object.setPrototypeOf ? Object.setPrototypeOf(t, GeneratorFunctionPrototype) : (t.__proto__ = GeneratorFunctionPrototype, c(t, u, "GeneratorFunction")), t.prototype = Object.create(v), t; }, r.awrap = function (t) { return { __await: t }; }, g(AsyncIterator.prototype), c(AsyncIterator.prototype, a, function () { return this; }), r.AsyncIterator = AsyncIterator, r.async = function (t, e, n, o, i) { void 0 === i && (i = Promise); var a = new AsyncIterator(h(t, e, n, o), i); return r.isGeneratorFunction(e) ? a : a.next().then(function (t) { return t.done ? t.value : a.next(); }); }, g(v), c(v, u, "Generator"), c(v, i, function () { return this; }), c(v, "toString", function () { return "[object Generator]"; }), r.keys = function (t) { var r = Object(t), e = []; for (var n in r) e.unshift(n); return function t() { for (; e.length;) if ((n = e.pop()) in r) return t.value = n, t.done = !1, t; return t.done = !0, t; }; }, r.values = x, Context.prototype = { constructor: Context, reset: function reset(r) { if (this.prev = this.next = 0, this.sent = this._sent = t, this.done = !1, this.delegate = null, this.method = "next", this.arg = t, this.tryEntries.forEach(m), !r) for (var e in this) "t" === e.charAt(0) && n.call(this, e) && !isNaN(+e.slice(1)) && (this[e] = t); }, stop: function stop() { this.done = !0; var t = this.tryEntries[0][4]; if ("throw" === t.type) throw t.arg; return this.rval; }, dispatchException: function dispatchException(r) { if (this.done) throw r; var e = this; function n(t) { a.type = "throw", a.arg = r, e.next = t; } for (var o = e.tryEntries.length - 1; o >= 0; --o) { var i = this.tryEntries[o], a = i[4], u = this.prev, c = i[1], h = i[2]; if (-1 === i[0]) return n("end"), !1; if (!c && !h) throw Error("try statement without catch or finally"); if (null != i[0] && i[0] <= u) { if (u < c) return this.method = "next", this.arg = t, n(c), !0; if (u < h) return n(h), !1; } } }, abrupt: function abrupt(t, r) { for (var e = this.tryEntries.length - 1; e >= 0; --e) { var n = this.tryEntries[e]; if (n[0] > -1 && n[0] <= this.prev && this.prev < n[2]) { var o = n; break; } } o && ("break" === t || "continue" === t) && o[0] <= r && r <= o[2] && (o = null); var i = o ? o[4] : {}; return i.type = t, i.arg = r, o ? (this.method = "next", this.next = o[2], f) : this.complete(i); }, complete: function complete(t, r) { if ("throw" === t.type) throw t.arg; return "break" === t.type || "continue" === t.type ? this.next = t.arg : "return" === t.type ? (this.rval = this.arg = t.arg, this.method = "return", this.next = "end") : "normal" === t.type && r && (this.next = r), f; }, finish: function finish(t) { for (var r = this.tryEntries.length - 1; r >= 0; --r) { var e = this.tryEntries[r]; if (e[2] === t) return this.complete(e[4], e[3]), m(e), f; } }, "catch": function _catch(t) { for (var r = this.tryEntries.length - 1; r >= 0; --r) { var e = this.tryEntries[r]; if (e[0] === t) { var n = e[4]; if ("throw" === n.type) { var o = n.arg; m(e); } return o; } } throw Error("illegal catch attempt"); }, delegateYield: function delegateYield(r, e, n) { return this.delegate = { i: x(r), r: e, n: n }, "next" === this.method && (this.arg = t), f; } }, r; }
function asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function _asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
/**
 * Popup script for the Jira Action Items Chatbot extension
 * Handles the popup UI and communication with the background script
 */

// DOM Elements
var chatMessages = document.getElementById('chat-messages');
var userInput = document.getElementById('user-input');
var sendButton = document.getElementById('send-button');
var attachButton = document.getElementById('attach-button');
var statusCircle = document.getElementById('status-circle');
var statusText = document.getElementById('status-text');
var tabChat = document.getElementById('tab-chat');
var tabTasks = document.getElementById('tab-tasks');
var tabReminders = document.getElementById('tab-reminders');
var tabSettings = document.getElementById('tab-settings');
var tasksContent = document.getElementById('tasks-content');
var remindersContent = document.getElementById('reminders-content');
var settingsContent = document.getElementById('settings-content');
var serverUrlInput = document.getElementById('server-url');
var notificationsToggle = document.getElementById('notifications-toggle');
var reminderToggle = document.getElementById('reminder-toggle');
var checkRemindersButton = document.getElementById('check-reminders-button');
var testReminderButton = document.getElementById('test-reminder-button');
var remindersList = document.getElementById('reminders-list');
var saveSettingsButton = document.getElementById('save-settings');
var taskList = document.getElementById('task-list');

// Chat history
var chatHistory = [];

// Auth state
var isAuthenticated = false;
var currentUser = null;

// Input suggestions based on context
var inputSuggestions = {
  "default": ["Create a task for me to review the documentation by Friday", "List my open tasks with high priority", "Remind me to follow up with the team tomorrow at 9 AM", "Schedule a meeting for next week", "Upload evidence for task PROJ-123"],
  jiraIssue: ["Add a comment to this issue", "Change status to 'In Progress'", "Add me as a watcher", "Set due date to next Friday", "Assign this to John"],
  jiraBoard: ["Show tasks assigned to me", "Create a new epic for the Q3 deliverables", "List blocked tasks in this project", "Find tasks without assignees", "Show tasks due this week"]
};

// Active context type
var activeContextType = 'default';
var currentJiraContext = {};

// Initialize the popup
document.addEventListener('DOMContentLoaded', function () {
  // Load settings from storage
  loadSettings();

  // Check server connection
  checkServerConnection();

  // Check authentication status
  checkAuthStatus();

  // Load chat history
  loadChatHistory();

  // Get current context and update suggestions
  updateJiraContext();

  // Add welcome message if this is first time
  chrome.storage.local.get('firstOpen', function (data) {
    if (data.firstOpen !== false) {
      // First time opening the extension
      chrome.storage.local.set({
        firstOpen: false
      });
      addMessage('bot', 'Welcome to Jira Action Items Chatbot! How can I help you today?');

      // Show sample commands
      setTimeout(function () {
        addMessage('bot', 'You can ask me to do things like:<br>' + '• Create tasks in Jira<br>' + '• Set reminders for due dates<br>' + '• Update task status<br>' + '• Find tasks assigned to you<br>' + '<br>Try typing a command or click a suggestion below.');

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
  chrome.storage.local.get(['serverUrl', 'notificationsEnabled', 'isAuthenticated'], function (data) {
    if (data.serverUrl) {
      serverUrlInput.value = data.serverUrl;
    }
    if (data.notificationsEnabled !== undefined) {
      notificationsToggle.checked = data.notificationsEnabled;
      reminderToggle.checked = data.notificationsEnabled;
    }
    isAuthenticated = data.isAuthenticated || false;
  });
}

// Check authentication status
function checkAuthStatus() {
  chrome.runtime.sendMessage({
    type: 'AUTH_STATUS'
  }, function (response) {
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
    var authGroup = document.createElement('div');
    authGroup.id = 'auth-settings';
    authGroup.className = 'settings-group auth-settings';
    authGroup.innerHTML = "\n      <label>Authentication</label>\n      <div id=\"auth-status\" class=\"auth-status\"></div>\n      <div id=\"auth-buttons\" class=\"auth-buttons\"></div>\n    ";

    // Insert before save button
    var saveGroup = document.querySelector('.settings-group:last-child');
    settingsContent.insertBefore(authGroup, saveGroup);
  }

  // Update auth status display
  var authStatus = document.getElementById('auth-status');
  var authButtons = document.getElementById('auth-buttons');
  if (isAuthenticated && currentUser) {
    authStatus.innerHTML = "\n      <div class=\"user-info\">\n        <span class=\"status-circle connected\"></span>\n        <span>Logged in as: <strong>".concat(currentUser.name || currentUser.email || currentUser.account_id, "</strong></span>\n      </div>\n    ");
    authButtons.innerHTML = "\n      <button id=\"logout-button\" class=\"secondary-button\">Log Out</button>\n    ";

    // Add logout event listener
    document.getElementById('logout-button').addEventListener('click', handleLogout);
  } else {
    authStatus.innerHTML = "\n      <div class=\"user-info\">\n        <span class=\"status-circle disconnected\"></span>\n        <span>Not logged in</span>\n      </div>\n    ";
    authButtons.innerHTML = "\n      <button id=\"login-button\" class=\"primary-button\">Log In with Jira</button>\n    ";

    // Add login event listener
    document.getElementById('login-button').addEventListener('click', handleLogin);
  }
}

// Handle login button click
function handleLogin() {
  chrome.runtime.sendMessage({
    type: 'AUTH_LOGIN'
  }, function (response) {
    if (!response.success) {
      console.error('Failed to initiate login:', response.error);
      // Show error in UI
      addMessage('bot', 'Failed to log in. Please try again later.');
    }
  });
}

// Handle logout button click
function handleLogout() {
  chrome.runtime.sendMessage({
    type: 'AUTH_LOGOUT'
  }, function (response) {
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
  chrome.storage.local.get('serverUrl', function (data) {
    var serverUrl = data.serverUrl || 'http://localhost:8000';
    fetch("".concat(serverUrl, "/api/health"), {
      method: 'GET'
    }).then(function (response) {
      if (response.ok) {
        setStatus('connected');
      } else {
        setStatus('error');
      }
    })["catch"](function () {
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
  chrome.storage.local.get('chatHistory', function (data) {
    if (data.chatHistory && data.chatHistory.length > 0) {
      chatHistory = data.chatHistory;

      // Display last 10 messages
      var recentMessages = chatHistory.slice(-10);
      recentMessages.forEach(function (msg) {
        addMessageToUI(msg.sender, msg.text, msg.timestamp);
      });
    }
  });
}

// Add chat message to history and UI
function addMessage(sender, text) {
  var timestamp = new Date().toISOString();

  // Add to chat history
  chatHistory.push({
    sender: sender,
    text: text,
    timestamp: timestamp
  });

  // Save to storage (limited to last 50 messages to save space)
  if (chatHistory.length > 50) {
    chatHistory = chatHistory.slice(-50);
  }
  chrome.storage.local.set({
    chatHistory: chatHistory
  });

  // Add to UI
  addMessageToUI(sender, text, timestamp);

  // If bot message, show suggestions after a brief delay
  if (sender === 'bot') {
    setTimeout(function () {
      showSuggestions();
    }, 500);
  }
}

// Add message to UI
function addMessageToUI(sender, text, timestamp) {
  var messageDiv = document.createElement('div');
  messageDiv.className = "message ".concat(sender, "-message");
  var time = new Date(timestamp);
  var formattedTime = "".concat(time.getHours().toString().padStart(2, '0'), ":").concat(time.getMinutes().toString().padStart(2, '0'));
  messageDiv.innerHTML = "\n    <div class=\"message-content\">".concat(text, "</div>\n    <div class=\"message-time\">").concat(formattedTime, "</div>\n  ");
  chatMessages.appendChild(messageDiv);

  // Scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Update Jira context and suggestions based on current tab
function updateJiraContext() {
  getCurrentTabInfo().then(function (tabInfo) {
    currentJiraContext = tabInfo;

    // Determine context type
    if (tabInfo.issueKey) {
      activeContextType = 'jiraIssue';
      userInput.placeholder = "Ask about ".concat(tabInfo.issueKey, "...");
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
  var existingSuggestions = document.getElementById('chat-suggestions');
  if (existingSuggestions) {
    existingSuggestions.remove();
  }

  // If not authenticated and not in settings tab, show login suggestion
  if (!isAuthenticated && !document.getElementById('tab-settings').classList.contains('active')) {
    var loginButton = document.createElement('button');
    loginButton.className = 'suggestion-button login-suggestion';
    loginButton.textContent = 'Log in with Jira to get started';
    loginButton.onclick = function () {
      switchTab(tabSettings);
      setTimeout(function () {
        var loginBtn = document.getElementById('login-button');
        if (loginBtn) loginBtn.focus();
      }, 100);
    };
    suggestionsDiv.appendChild(loginButton);
    chatMessages.parentNode.insertBefore(suggestionsDiv, document.querySelector('.input-container'));
    return;
  }

  // Get relevant suggestions
  var suggestions = inputSuggestions[activeContextType] || inputSuggestions["default"];

  // Create buttons for each suggestion
  suggestions.slice(0, 3).forEach(function (suggestion) {
    var button = document.createElement('button');
    button.className = 'suggestion-button';
    button.textContent = suggestion;
    button.onclick = function () {
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
  userInput.addEventListener('keydown', function (e) {
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
  tabChat.addEventListener('click', function () {
    return switchTab(tabChat);
  });
  tabTasks.addEventListener('click', function () {
    return switchTab(tabTasks);
  });
  tabReminders.addEventListener('click', function () {
    return switchTab(tabReminders);
  });
  tabSettings.addEventListener('click', function () {
    return switchTab(tabSettings);
  });

  // Reminder buttons
  checkRemindersButton.addEventListener('click', handleCheckReminders);
  testReminderButton.addEventListener('click', handleTestReminder);
  reminderToggle.addEventListener('change', saveReminderSettings);

  // Save settings button
  saveSettingsButton.addEventListener('click', saveSettings);
}

// Show smarter suggestions based on partial typing
function smartSuggestions() {
  var input = userInput.value.toLowerCase();
  if (input.length < 3) return;

  // Get relevant suggestions
  var suggestions = inputSuggestions[activeContextType] || inputSuggestions["default"];

  // Filter suggestions that partially match input
  var matchingSuggestions = suggestions.filter(function (suggestion) {
    return suggestion.toLowerCase().includes(input);
  });

  // Show up to 3 matching suggestions
  if (matchingSuggestions.length > 0) {
    // Remove existing suggestions
    var existingSuggestions = document.getElementById('chat-suggestions');
    if (existingSuggestions) {
      existingSuggestions.remove();
    }

    // Create suggestions container
    var _suggestionsDiv = document.createElement('div');
    _suggestionsDiv.id = 'chat-suggestions';
    _suggestionsDiv.className = 'chat-suggestions';

    // Create buttons for each suggestion
    matchingSuggestions.slice(0, 3).forEach(function (suggestion) {
      var button = document.createElement('button');
      button.className = 'suggestion-button';
      button.textContent = suggestion;
      button.onclick = function () {
        userInput.value = suggestion;
        sendMessage();
      };
      _suggestionsDiv.appendChild(button);
    });

    // Append suggestions to UI
    chatMessages.parentNode.insertBefore(_suggestionsDiv, document.querySelector('.input-container'));
  }
}

// Switch between tabs
function switchTab(tab) {
  // Remove active class from all tabs
  [tabChat, tabTasks, tabReminders, tabSettings].forEach(function (t) {
    return t.classList.remove('active');
  });

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
function sendMessage() {
  return _sendMessage.apply(this, arguments);
} // Get info about current tab
function _sendMessage() {
  _sendMessage = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee() {
    var message, existingSuggestions, typingIndicator, messageData;
    return _regeneratorRuntime().wrap(function _callee$(_context) {
      while (1) switch (_context.prev = _context.next) {
        case 0:
          message = userInput.value.trim();
          if (message) {
            _context.next = 3;
            break;
          }
          return _context.abrupt("return");
        case 3:
          // Clear input
          userInput.value = '';

          // Remove suggestions
          existingSuggestions = document.getElementById('chat-suggestions');
          if (existingSuggestions) {
            existingSuggestions.remove();
          }

          // Add user message to UI
          addMessage('user', message);

          // Add typing indicator
          typingIndicator = document.createElement('div');
          typingIndicator.className = 'message bot-message typing-indicator';
          typingIndicator.innerHTML = '<div class="dots"><span>.</span><span>.</span><span>.</span></div>';
          chatMessages.appendChild(typingIndicator);
          chatMessages.scrollTop = chatMessages.scrollHeight;

          // Check if authenticated
          if (isAuthenticated) {
            _context.next = 16;
            break;
          }
          // Remove typing indicator
          typingIndicator.remove();

          // Add response about authentication
          addMessage('bot', 'Please log in with Jira to use the chatbot. Go to the Settings tab to log in.');
          return _context.abrupt("return");
        case 16:
          try {
            // Prepare message with context
            messageData = {
              text: message,
              context: currentJiraContext
            }; // Send to API
            chrome.runtime.sendMessage({
              type: 'API_REQUEST',
              endpoint: '/api/chat',
              method: 'POST',
              data: messageData
            }, function (response) {
              // Remove typing indicator
              typingIndicator.remove();
              if (response.success) {
                // Add bot response to UI
                addMessage('bot', response.data.response);

                // Handle actions if any
                if (response.data.actions) {
                  handleActions(response.data.actions);
                }
              } else {
                // Add error message to UI
                addMessage('bot', "Sorry, I couldn't process your request. ".concat(response.error));

                // If unauthorized, update auth status
                if (response.error.includes('401') || response.error.includes('unauthorized')) {
                  checkAuthStatus();
                }
              }
            });
          } catch (error) {
            // Remove typing indicator
            typingIndicator.remove();

            // Add error message to UI
            addMessage('bot', "Sorry, something went wrong. ".concat(error.message));
            console.error('Error sending message:', error);
          }
        case 17:
        case "end":
          return _context.stop();
      }
    }, _callee);
  }));
  return _sendMessage.apply(this, arguments);
}
function getCurrentTabInfo() {
  return _getCurrentTabInfo.apply(this, arguments);
} // Handle suggested actions
function _getCurrentTabInfo() {
  _getCurrentTabInfo = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee2() {
    return _regeneratorRuntime().wrap(function _callee2$(_context2) {
      while (1) switch (_context2.prev = _context2.next) {
        case 0:
          return _context2.abrupt("return", new Promise(function (resolve) {
            chrome.tabs.query({
              active: true,
              currentWindow: true
            }, function (tabs) {
              if (tabs.length === 0) {
                resolve({
                  isJiraPage: false
                });
                return;
              }
              var url = tabs[0].url;
              var title = tabs[0].title;

              // Check if this is a Jira page
              var isJiraPage = url.includes('atlassian.net') || url.includes('jira');

              // Extract issue key if present in URL or title
              var issueKeyRegex = /\b([A-Z]+-[0-9]+)\b/;
              var urlMatch = url.match(issueKeyRegex);
              var titleMatch = title.match(issueKeyRegex);
              var issueKey = urlMatch ? urlMatch[1] : titleMatch ? titleMatch[1] : null;

              // Extract project key if found
              var projectKeyRegex = /projects\/([A-Z]+)/;
              var projectMatch = url.match(projectKeyRegex);
              var projectKey = projectMatch ? projectMatch[1] : null;
              resolve({
                isJiraPage: isJiraPage,
                issueKey: issueKey,
                projectKey: projectKey,
                url: url,
                title: title
              });
            });
          }));
        case 1:
        case "end":
          return _context2.stop();
      }
    }, _callee2);
  }));
  return _getCurrentTabInfo.apply(this, arguments);
}
function handleActions(actions) {
  // Remove existing actions
  var existingActions = document.getElementById('suggested-actions');
  if (existingActions) {
    existingActions.remove();
  }

  // Create actions container
  var actionsDiv = document.createElement('div');
  actionsDiv.id = 'suggested-actions';
  actionsDiv.className = 'suggested-actions';

  // Add heading
  var heading = document.createElement('div');
  heading.className = 'actions-heading';
  heading.textContent = 'Suggested Actions:';
  actionsDiv.appendChild(heading);

  // Create buttons for each action
  actions.forEach(function (action) {
    var button = document.createElement('button');
    button.className = 'action-button';
    button.textContent = action.text;
    if (action.url) {
      // Open URL action
      button.onclick = function () {
        chrome.tabs.create({
          url: action.url
        });
      };
    } else if (action.action) {
      // Custom action
      button.onclick = function () {
        // Handle different action types
        // ...
      };
    }
    actionsDiv.appendChild(button);
  });

  // Append actions to UI
  chatMessages.appendChild(actionsDiv);

  // Scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;
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
  }, function (response) {
    if (response.success) {
      displayTasks(response.data.issues || []);
    } else {
      taskList.innerHTML = "<div class=\"error-message\">Failed to load tasks: ".concat(response.error, "</div>");
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
  tasks.forEach(function (task) {
    var _task$fields, _task$fields2, _task$fields3, _task$fields4, _task$fields5;
    var taskElement = document.createElement('div');
    taskElement.className = 'task-item';

    // Get key fields
    var key = task.key;
    var summary = ((_task$fields = task.fields) === null || _task$fields === void 0 ? void 0 : _task$fields.summary) || 'No summary';
    var status = ((_task$fields2 = task.fields) === null || _task$fields2 === void 0 || (_task$fields2 = _task$fields2.status) === null || _task$fields2 === void 0 ? void 0 : _task$fields2.name) || 'Unknown';
    var issuetype = ((_task$fields3 = task.fields) === null || _task$fields3 === void 0 || (_task$fields3 = _task$fields3.issuetype) === null || _task$fields3 === void 0 ? void 0 : _task$fields3.name) || 'Task';
    var priority = ((_task$fields4 = task.fields) === null || _task$fields4 === void 0 || (_task$fields4 = _task$fields4.priority) === null || _task$fields4 === void 0 ? void 0 : _task$fields4.name) || 'Normal';

    // Format due date if available
    var dueDate = 'No due date';
    if ((_task$fields5 = task.fields) !== null && _task$fields5 !== void 0 && _task$fields5.duedate) {
      var date = new Date(task.fields.duedate);
      dueDate = date.toLocaleDateString();
    }

    // Create task HTML
    taskElement.innerHTML = "\n      <div class=\"task-header\">\n        <span class=\"task-key\">".concat(key, "</span>\n        <span class=\"task-status status-").concat(status.toLowerCase().replace(/\s+/g, '-'), "\">").concat(status, "</span>\n      </div>\n      <div class=\"task-summary\">").concat(summary, "</div>\n      <div class=\"task-details\">\n        <span class=\"task-type\">").concat(issuetype, "</span>\n        <span class=\"task-priority\">").concat(priority, "</span>\n        <span class=\"task-due-date\">").concat(dueDate, "</span>\n      </div>\n      <div class=\"task-actions\">\n        <button class=\"task-action-button view-button\">View</button>\n        <button class=\"task-action-button update-button\">Update</button>\n      </div>\n    ");

    // Add click handler for view button
    taskElement.querySelector('.view-button').addEventListener('click', function () {
      chrome.storage.local.get('serverUrl', function (data) {
        var jiraUrl = data.serverUrl ? data.serverUrl.replace(/\/api$/, '') : 'https://your-domain.atlassian.net';
        chrome.tabs.create({
          url: "".concat(jiraUrl, "/browse/").concat(key)
        });
      });
    });

    // Add click handler for update button
    taskElement.querySelector('.update-button').addEventListener('click', function () {
      switchTab(tabChat);
      userInput.value = "Update ".concat(key, " status");
      userInput.focus();
    });
    taskList.appendChild(taskElement);
  });
}

// Save settings
function saveSettings() {
  var serverUrl = serverUrlInput.value.trim();
  var notificationsEnabled = notificationsToggle.checked;

  // Validate server URL
  if (!serverUrl) {
    alert('Please enter a valid server URL');
    return;
  }

  // Save settings
  chrome.storage.local.set({
    serverUrl: serverUrl,
    notificationsEnabled: notificationsEnabled
  }, function () {
    // Show success feedback
    var saveButton = document.getElementById('save-settings');
    saveButton.textContent = 'Saved!';
    saveButton.classList.add('success');

    // Revert button text after 2 seconds
    setTimeout(function () {
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
  var fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = 'image/*,application/pdf,.doc,.docx,.xls,.xlsx,.txt';

  // Trigger file selection
  fileInput.click();

  // Handle file selection
  fileInput.addEventListener('change', function (e) {
    var file = e.target.files[0];
    if (!file) return;

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      addMessage('bot', 'File too large. Maximum size is 10MB.');
      return;
    }

    // Show file selection in UI
    addMessage('user', "\uD83D\uDCCE Selected file: ".concat(file.name));

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
  var loadingItem = document.createElement('div');
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
  chrome.runtime.sendMessage({
    type: 'CHECK_REMINDERS'
  }, function (response) {
    checkRemindersButton.disabled = false;
    checkRemindersButton.textContent = 'Check Now';
    if (response.success) {
      var data = response.data;
      if (data.reminders && data.reminders.length > 0) {
        // Show reminders
        loadRecentReminders(data.reminders);
      } else {
        // No reminders
        remindersList.innerHTML = '<div class="no-reminders">No reminders found.</div>';
      }
    } else {
      // Error
      remindersList.innerHTML = "<div class=\"error-message\">Failed to check reminders: ".concat(response.error, "</div>");
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
  var testMessage = "This is a test reminder created at ".concat(new Date().toLocaleTimeString());
  chrome.runtime.sendMessage({
    type: 'API_REQUEST',
    endpoint: '/api/reminders/test',
    method: 'POST',
    data: {
      message: testMessage
    }
  }, function (response) {
    testReminderButton.disabled = false;
    testReminderButton.textContent = 'Test Notification';
    if (response.success) {
      // Show the reminder
      var reminder = response.data.reminder;

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
      alert("Failed to create test reminder: ".concat(response.error));
    }
  });
}

// Save reminder settings
function saveReminderSettings() {
  chrome.storage.local.set({
    notificationsEnabled: reminderToggle.checked
  }, function () {
    // Update notifications toggle to match
    notificationsToggle.checked = reminderToggle.checked;
  });
}

// Load recent reminders
function loadRecentReminders() {
  var reminders = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : null;
  // Clear list
  remindersList.innerHTML = '';

  // If reminders provided, use them
  if (reminders && reminders.length > 0) {
    displayReminders(reminders);
    return;
  }

  // Otherwise load from storage
  chrome.storage.local.get('recentReminders', function (data) {
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
  chrome.storage.local.set({
    recentReminders: reminders.slice(0, 10)
  });

  // Clear list
  remindersList.innerHTML = '';

  // Add reminders
  reminders.forEach(function (reminder) {
    var reminderItem = document.createElement('div');
    reminderItem.className = "reminder-item urgency-".concat(reminder.urgency);

    // Format timestamp
    var timestamp = new Date(reminder.timestamp);
    var formattedTime = timestamp.toLocaleString();
    reminderItem.innerHTML = "\n      <div class=\"reminder-header\">\n        <span class=\"reminder-key\">".concat(reminder.key, "</span>\n        <span class=\"reminder-time\">").concat(formattedTime, "</span>\n      </div>\n      <div class=\"reminder-title\">").concat(reminder.title, "</div>\n      <div class=\"reminder-message\">").concat(reminder.message, "</div>\n      <div class=\"reminder-details\">\n        <span class=\"reminder-priority\">Priority: ").concat(reminder.priority, "</span>\n        <span class=\"reminder-status\">Status: ").concat(reminder.status, "</span>\n      </div>\n    ");
    remindersList.appendChild(reminderItem);
  });
}
/******/ })()
;
//# sourceMappingURL=popup.js.map