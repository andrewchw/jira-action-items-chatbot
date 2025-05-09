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
var tabSettings = document.getElementById('tab-settings');
var tasksContent = document.getElementById('tasks-content');
var settingsContent = document.getElementById('settings-content');
var serverUrlInput = document.getElementById('server-url');
var notificationsToggle = document.getElementById('notifications-toggle');
var saveSettingsButton = document.getElementById('save-settings');
var taskList = document.getElementById('task-list');

// Chat history
var chatHistory = [];

// Initialize the popup
document.addEventListener('DOMContentLoaded', function () {
  // Load settings from storage
  loadSettings();

  // Check server connection
  checkServerConnection();

  // Load chat history
  loadChatHistory();

  // Add welcome message if this is first time
  chrome.storage.local.get('firstOpen', function (data) {
    if (data.firstOpen !== false) {
      // First time opening the extension
      chrome.storage.local.set({
        firstOpen: false
      });
      addMessage('bot', 'Welcome to Jira Action Items Chatbot! How can I help you today?');
    }
  });

  // Set up event listeners
  setupEventListeners();
});

// Load settings from storage
function loadSettings() {
  chrome.storage.local.get(['serverUrl', 'notificationsEnabled'], function (data) {
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
  chrome.storage.local.get('serverUrl', function (data) {
    var serverUrl = data.serverUrl || 'http://localhost:8000';
    fetch("".concat(serverUrl, "/health"), {
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

// Set up event listeners
function setupEventListeners() {
  // Send message when button clicked
  sendButton.addEventListener('click', sendMessage);

  // Send message when Enter pressed (but allow Shift+Enter for new lines)
  userInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Tab switching
  tabChat.addEventListener('click', function () {
    return switchTab('chat');
  });
  tabTasks.addEventListener('click', function () {
    switchTab('tasks');
    loadTasks();
  });
  tabSettings.addEventListener('click', function () {
    return switchTab('settings');
  });

  // Save settings
  saveSettingsButton.addEventListener('click', saveSettings);

  // Attachment button
  attachButton.addEventListener('click', handleAttachment);
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
  var message = userInput.value.trim();
  if (!message) return;

  // Add user message to UI
  addMessage('user', message);

  // Clear input
  userInput.value = '';

  // Get current Jira context if available
  getCurrentTabInfo().then(function (tabInfo) {
    // Show loading indicator
    addMessageToUI('bot', '<div class="typing-indicator"><span></span><span></span><span></span></div>', new Date().toISOString());

    // Send to server via background script
    chrome.runtime.sendMessage({
      type: 'API_REQUEST',
      endpoint: '/chat',
      method: 'POST',
      data: {
        message: message,
        context: tabInfo
      }
    }, function (response) {
      // Remove loading indicator
      chatMessages.removeChild(chatMessages.lastChild);
      if (response && response.success) {
        // Add bot response to chat
        addMessage('bot', response.data.response);

        // Handle actions if any were returned
        handleActions(response.data.actions);
      } else {
        // Show error message
        addMessage('bot', 'Sorry, I encountered an error while processing your request. Please try again later.');
      }
    });
  });
}

// Get info about the current tab for context
function getCurrentTabInfo() {
  return _getCurrentTabInfo.apply(this, arguments);
} // Handle any actions returned from the server
function _getCurrentTabInfo() {
  _getCurrentTabInfo = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee() {
    return _regeneratorRuntime().wrap(function _callee$(_context) {
      while (1) switch (_context.prev = _context.next) {
        case 0:
          return _context.abrupt("return", new Promise(function (resolve) {
            chrome.tabs.query({
              active: true,
              currentWindow: true
            }, function (tabs) {
              if (tabs.length === 0) {
                resolve({});
                return;
              }
              var currentTab = tabs[0];

              // If it's a Jira page, try to get additional context
              if (currentTab.url.includes('atlassian.net') || currentTab.url.includes('jira')) {
                chrome.tabs.sendMessage(currentTab.id, {
                  type: 'GET_JIRA_CONTEXT'
                }, function (response) {
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
          }));
        case 1:
        case "end":
          return _context.stop();
      }
    }, _callee);
  }));
  return _getCurrentTabInfo.apply(this, arguments);
}
function handleActions(actions) {
  if (!actions || actions.length === 0) return;
  actions.forEach(function (action) {
    switch (action.type) {
      case 'open_url':
        chrome.tabs.create({
          url: action.data.url
        });
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
  }, function (response) {
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
  tasks.forEach(function (task) {
    var taskElement = document.createElement('div');
    taskElement.className = "task-item ".concat(task.status.toLowerCase());
    var dueDate = task.dueDate ? new Date(task.dueDate).toLocaleDateString() : 'No due date';
    taskElement.innerHTML = "\n      <div class=\"task-header\">\n        <span class=\"task-key\">".concat(task.key, "</span>\n        <span class=\"task-status\">").concat(task.status, "</span>\n      </div>\n      <div class=\"task-summary\">").concat(task.summary, "</div>\n      <div class=\"task-details\">\n        <span class=\"task-assignee\">").concat(task.assignee || 'Unassigned', "</span>\n        <span class=\"task-due-date\">").concat(dueDate, "</span>\n      </div>\n    ");

    // Add click event to open the task
    taskElement.addEventListener('click', function () {
      chrome.tabs.create({
        url: task.url
      });
    });
    taskList.appendChild(taskElement);
  });
}

// Save settings
function saveSettings() {
  var serverUrl = serverUrlInput.value.trim();
  var notificationsEnabled = notificationsToggle.checked;
  chrome.storage.local.set({
    serverUrl: serverUrl,
    notificationsEnabled: notificationsEnabled
  }, function () {
    // Show saved message
    var savedIndicator = document.createElement('div');
    savedIndicator.className = 'saved-indicator';
    savedIndicator.textContent = 'Settings saved!';
    settingsContent.appendChild(savedIndicator);

    // Remove after 2 seconds
    setTimeout(function () {
      settingsContent.removeChild(savedIndicator);
    }, 2000);

    // Check connection with new URL
    checkServerConnection();
  });
}

// Handle file attachment
function handleAttachment() {
  // Create a file input element
  var fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = 'image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt';

  // Trigger click event to open file picker
  fileInput.click();

  // Handle file selection
  fileInput.addEventListener('change', function () {
    if (fileInput.files.length > 0) {
      var file = fileInput.files[0];

      // Add message about the attachment
      addMessage('user', "Attached file: ".concat(file.name));

      // Create FormData and send to server via background script
      var formData = new FormData();
      formData.append('file', file);

      // Preview for certain file types
      if (file.type.startsWith('image/')) {
        var reader = new FileReader();
        reader.onload = function (e) {
          var img = document.createElement('img');
          img.src = e.target.result;
          img.className = 'attachment-preview';
          chatMessages.appendChild(img);
          chatMessages.scrollTop = chatMessages.scrollHeight;
        };
        reader.readAsDataURL(file);
      }

      // TODO: Implement file upload to server (requires additional backend support)
      // For now, just show a message
      setTimeout(function () {
        addMessage('bot', "I've received your file \"".concat(file.name, "\". What would you like me to do with it?"));
      }, 1000);
    }
  });
}
/******/ })()
;
//# sourceMappingURL=popup.js.map