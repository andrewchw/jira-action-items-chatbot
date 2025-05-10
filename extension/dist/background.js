/******/ (() => { // webpackBootstrap
/*!***********************!*\
  !*** ./background.js ***!
  \***********************/
function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
function _regeneratorRuntime() { "use strict"; /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ _regeneratorRuntime = function _regeneratorRuntime() { return r; }; var t, r = {}, e = Object.prototype, n = e.hasOwnProperty, o = "function" == typeof Symbol ? Symbol : {}, i = o.iterator || "@@iterator", a = o.asyncIterator || "@@asyncIterator", u = o.toStringTag || "@@toStringTag"; function c(t, r, e, n) { return Object.defineProperty(t, r, { value: e, enumerable: !n, configurable: !n, writable: !n }); } try { c({}, ""); } catch (t) { c = function c(t, r, e) { return t[r] = e; }; } function h(r, e, n, o) { var i = e && e.prototype instanceof Generator ? e : Generator, a = Object.create(i.prototype); return c(a, "_invoke", function (r, e, n) { var o = 1; return function (i, a) { if (3 === o) throw Error("Generator is already running"); if (4 === o) { if ("throw" === i) throw a; return { value: t, done: !0 }; } for (n.method = i, n.arg = a;;) { var u = n.delegate; if (u) { var c = d(u, n); if (c) { if (c === f) continue; return c; } } if ("next" === n.method) n.sent = n._sent = n.arg;else if ("throw" === n.method) { if (1 === o) throw o = 4, n.arg; n.dispatchException(n.arg); } else "return" === n.method && n.abrupt("return", n.arg); o = 3; var h = s(r, e, n); if ("normal" === h.type) { if (o = n.done ? 4 : 2, h.arg === f) continue; return { value: h.arg, done: n.done }; } "throw" === h.type && (o = 4, n.method = "throw", n.arg = h.arg); } }; }(r, n, new Context(o || [])), !0), a; } function s(t, r, e) { try { return { type: "normal", arg: t.call(r, e) }; } catch (t) { return { type: "throw", arg: t }; } } r.wrap = h; var f = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} var l = {}; c(l, i, function () { return this; }); var p = Object.getPrototypeOf, y = p && p(p(x([]))); y && y !== e && n.call(y, i) && (l = y); var v = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(l); function g(t) { ["next", "throw", "return"].forEach(function (r) { c(t, r, function (t) { return this._invoke(r, t); }); }); } function AsyncIterator(t, r) { function e(o, i, a, u) { var c = s(t[o], t, i); if ("throw" !== c.type) { var h = c.arg, f = h.value; return f && "object" == _typeof(f) && n.call(f, "__await") ? r.resolve(f.__await).then(function (t) { e("next", t, a, u); }, function (t) { e("throw", t, a, u); }) : r.resolve(f).then(function (t) { h.value = t, a(h); }, function (t) { return e("throw", t, a, u); }); } u(c.arg); } var o; c(this, "_invoke", function (t, n) { function i() { return new r(function (r, o) { e(t, n, r, o); }); } return o = o ? o.then(i, i) : i(); }, !0); } function d(r, e) { var n = e.method, o = r.i[n]; if (o === t) return e.delegate = null, "throw" === n && r.i["return"] && (e.method = "return", e.arg = t, d(r, e), "throw" === e.method) || "return" !== n && (e.method = "throw", e.arg = new TypeError("The iterator does not provide a '" + n + "' method")), f; var i = s(o, r.i, e.arg); if ("throw" === i.type) return e.method = "throw", e.arg = i.arg, e.delegate = null, f; var a = i.arg; return a ? a.done ? (e[r.r] = a.value, e.next = r.n, "return" !== e.method && (e.method = "next", e.arg = t), e.delegate = null, f) : a : (e.method = "throw", e.arg = new TypeError("iterator result is not an object"), e.delegate = null, f); } function w(t) { this.tryEntries.push(t); } function m(r) { var e = r[4] || {}; e.type = "normal", e.arg = t, r[4] = e; } function Context(t) { this.tryEntries = [[-1]], t.forEach(w, this), this.reset(!0); } function x(r) { if (null != r) { var e = r[i]; if (e) return e.call(r); if ("function" == typeof r.next) return r; if (!isNaN(r.length)) { var o = -1, a = function e() { for (; ++o < r.length;) if (n.call(r, o)) return e.value = r[o], e.done = !1, e; return e.value = t, e.done = !0, e; }; return a.next = a; } } throw new TypeError(_typeof(r) + " is not iterable"); } return GeneratorFunction.prototype = GeneratorFunctionPrototype, c(v, "constructor", GeneratorFunctionPrototype), c(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = c(GeneratorFunctionPrototype, u, "GeneratorFunction"), r.isGeneratorFunction = function (t) { var r = "function" == typeof t && t.constructor; return !!r && (r === GeneratorFunction || "GeneratorFunction" === (r.displayName || r.name)); }, r.mark = function (t) { return Object.setPrototypeOf ? Object.setPrototypeOf(t, GeneratorFunctionPrototype) : (t.__proto__ = GeneratorFunctionPrototype, c(t, u, "GeneratorFunction")), t.prototype = Object.create(v), t; }, r.awrap = function (t) { return { __await: t }; }, g(AsyncIterator.prototype), c(AsyncIterator.prototype, a, function () { return this; }), r.AsyncIterator = AsyncIterator, r.async = function (t, e, n, o, i) { void 0 === i && (i = Promise); var a = new AsyncIterator(h(t, e, n, o), i); return r.isGeneratorFunction(e) ? a : a.next().then(function (t) { return t.done ? t.value : a.next(); }); }, g(v), c(v, u, "Generator"), c(v, i, function () { return this; }), c(v, "toString", function () { return "[object Generator]"; }), r.keys = function (t) { var r = Object(t), e = []; for (var n in r) e.unshift(n); return function t() { for (; e.length;) if ((n = e.pop()) in r) return t.value = n, t.done = !1, t; return t.done = !0, t; }; }, r.values = x, Context.prototype = { constructor: Context, reset: function reset(r) { if (this.prev = this.next = 0, this.sent = this._sent = t, this.done = !1, this.delegate = null, this.method = "next", this.arg = t, this.tryEntries.forEach(m), !r) for (var e in this) "t" === e.charAt(0) && n.call(this, e) && !isNaN(+e.slice(1)) && (this[e] = t); }, stop: function stop() { this.done = !0; var t = this.tryEntries[0][4]; if ("throw" === t.type) throw t.arg; return this.rval; }, dispatchException: function dispatchException(r) { if (this.done) throw r; var e = this; function n(t) { a.type = "throw", a.arg = r, e.next = t; } for (var o = e.tryEntries.length - 1; o >= 0; --o) { var i = this.tryEntries[o], a = i[4], u = this.prev, c = i[1], h = i[2]; if (-1 === i[0]) return n("end"), !1; if (!c && !h) throw Error("try statement without catch or finally"); if (null != i[0] && i[0] <= u) { if (u < c) return this.method = "next", this.arg = t, n(c), !0; if (u < h) return n(h), !1; } } }, abrupt: function abrupt(t, r) { for (var e = this.tryEntries.length - 1; e >= 0; --e) { var n = this.tryEntries[e]; if (n[0] > -1 && n[0] <= this.prev && this.prev < n[2]) { var o = n; break; } } o && ("break" === t || "continue" === t) && o[0] <= r && r <= o[2] && (o = null); var i = o ? o[4] : {}; return i.type = t, i.arg = r, o ? (this.method = "next", this.next = o[2], f) : this.complete(i); }, complete: function complete(t, r) { if ("throw" === t.type) throw t.arg; return "break" === t.type || "continue" === t.type ? this.next = t.arg : "return" === t.type ? (this.rval = this.arg = t.arg, this.method = "return", this.next = "end") : "normal" === t.type && r && (this.next = r), f; }, finish: function finish(t) { for (var r = this.tryEntries.length - 1; r >= 0; --r) { var e = this.tryEntries[r]; if (e[2] === t) return this.complete(e[4], e[3]), m(e), f; } }, "catch": function _catch(t) { for (var r = this.tryEntries.length - 1; r >= 0; --r) { var e = this.tryEntries[r]; if (e[0] === t) { var n = e[4]; if ("throw" === n.type) { var o = n.arg; m(e); } return o; } } throw Error("illegal catch attempt"); }, delegateYield: function delegateYield(r, e, n) { return this.delegate = { i: x(r), r: e, n: n }, "next" === this.method && (this.arg = t), f; } }, r; }
function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: !0, configurable: !0, writable: !0 }) : e[r] = t, e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == _typeof(i) ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != _typeof(t) || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r || "default"); if ("object" != _typeof(i)) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
function asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function _asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
/**
 * Background script for the Jira Action Items Chatbot extension
 * Handles API communication and notifications
 */

// Server connection settings
var API_BASE_URL = 'http://localhost:8000';

// Auth state for storing CSRF protection
var authState = null;

// Notification state
var lastNotificationCheck = 0;
var NOTIFICATION_CHECK_INTERVAL = 5 * 60 * 1000; // 5 minutes in milliseconds
var notificationQueue = [];
var isProcessingQueue = false;
var checkRemindersTimeout = null;

// Listen for installation
chrome.runtime.onInstalled.addListener(function () {
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
chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
  if (message.type === 'API_REQUEST') {
    handleApiRequest(message.endpoint, message.method, message.data).then(function (response) {
      return sendResponse({
        success: true,
        data: response
      });
    })["catch"](function (error) {
      return sendResponse({
        success: false,
        error: error.message
      });
    });
    return true; // Required for async sendResponse
  }
  if (message.type === 'SHOW_NOTIFICATION') {
    showNotification(message.title, message.message, message.actions);
    sendResponse({
      success: true
    });
    return true;
  }
  if (message.type === 'AUTH_LOGIN') {
    initiateLogin().then(function (result) {
      return sendResponse({
        success: true,
        data: result
      });
    })["catch"](function (error) {
      return sendResponse({
        success: false,
        error: error.message
      });
    });
    return true;
  }
  if (message.type === 'AUTH_LOGOUT') {
    logout().then(function (result) {
      return sendResponse({
        success: true,
        data: result
      });
    })["catch"](function (error) {
      return sendResponse({
        success: false,
        error: error.message
      });
    });
    return true;
  }
  if (message.type === 'AUTH_STATUS') {
    checkAuthStatus().then(function (status) {
      return sendResponse({
        success: true,
        data: status
      });
    })["catch"](function (error) {
      return sendResponse({
        success: false,
        error: error.message
      });
    });
    return true;
  }
  if (message.type === 'CHECK_REMINDERS') {
    checkReminders().then(function (result) {
      return sendResponse({
        success: true,
        data: result
      });
    })["catch"](function (error) {
      return sendResponse({
        success: false,
        error: error.message
      });
    });
    return true;
  }
  if (message.type === 'HANDLE_NOTIFICATION_ACTION') {
    handleNotificationAction(message.notificationId, message.action, message.issueKey).then(function (result) {
      return sendResponse({
        success: true,
        data: result
      });
    })["catch"](function (error) {
      return sendResponse({
        success: false,
        error: error.message
      });
    });
    return true;
  }
  if (message.type === 'SEND_REPLY') {
    handleConversationalReply(message.issueKey, message.message).then(function (result) {
      return sendResponse({
        success: true,
        data: result
      });
    })["catch"](function (error) {
      return sendResponse({
        success: false,
        error: error.message
      });
    });
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
    checkRemindersTimeout = setTimeout(function () {
      checkReminders()["finally"](function () {
        schedulNextCheck();
      });
    }, NOTIFICATION_CHECK_INTERVAL);
  }
  schedulNextCheck();
}

// Check for reminders from the server
function checkReminders() {
  return _checkReminders.apply(this, arguments);
} // Process the notification queue one at a time with delay
function _checkReminders() {
  _checkReminders = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee() {
    var authStatus, _yield$Promise, notificationsEnabled, result;
    return _regeneratorRuntime().wrap(function _callee$(_context) {
      while (1) switch (_context.prev = _context.next) {
        case 0:
          _context.prev = 0;
          _context.next = 3;
          return checkAuthStatus();
        case 3:
          authStatus = _context.sent;
          if (authStatus.authenticated) {
            _context.next = 7;
            break;
          }
          console.log('Not authenticated, skipping reminder check');
          return _context.abrupt("return", {
            reminders: [],
            count: 0
          });
        case 7:
          _context.next = 9;
          return new Promise(function (resolve) {
            chrome.storage.local.get('notificationsEnabled', function (result) {
              resolve(result);
            });
          });
        case 9:
          _yield$Promise = _context.sent;
          notificationsEnabled = _yield$Promise.notificationsEnabled;
          if (notificationsEnabled) {
            _context.next = 14;
            break;
          }
          console.log('Notifications disabled, skipping reminder check');
          return _context.abrupt("return", {
            reminders: [],
            count: 0
          });
        case 14:
          // Check for reminders
          console.log('Checking for reminders...');
          _context.next = 17;
          return handleApiRequest('/api/reminders/check');
        case 17:
          result = _context.sent;
          // Update last check time
          lastNotificationCheck = Date.now();

          // Process reminders
          if (result.reminders && result.reminders.length > 0) {
            console.log("Found ".concat(result.reminders.length, " reminders"));

            // Queue reminders for display
            notificationQueue = notificationQueue.concat(result.reminders);

            // Process the queue (one at a time)
            if (!isProcessingQueue) {
              processNotificationQueue();
            }
          } else {
            console.log('No reminders found');
          }
          return _context.abrupt("return", result);
        case 23:
          _context.prev = 23;
          _context.t0 = _context["catch"](0);
          console.error('Failed to check reminders:', _context.t0);
          throw _context.t0;
        case 27:
        case "end":
          return _context.stop();
      }
    }, _callee, null, [[0, 23]]);
  }));
  return _checkReminders.apply(this, arguments);
}
function processNotificationQueue() {
  return _processNotificationQueue.apply(this, arguments);
} // Show a reminder notification
function _processNotificationQueue() {
  _processNotificationQueue = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee2() {
    var reminder;
    return _regeneratorRuntime().wrap(function _callee2$(_context2) {
      while (1) switch (_context2.prev = _context2.next) {
        case 0:
          if (!(notificationQueue.length === 0)) {
            _context2.next = 3;
            break;
          }
          isProcessingQueue = false;
          return _context2.abrupt("return");
        case 3:
          isProcessingQueue = true;

          // Get the next reminder
          reminder = notificationQueue.shift(); // Show notification
          showReminderNotification(reminder);

          // Wait before showing the next notification
          setTimeout(function () {
            processNotificationQueue();
          }, 5000); // 5 second delay between notifications
        case 7:
        case "end":
          return _context2.stop();
      }
    }, _callee2);
  }));
  return _processNotificationQueue.apply(this, arguments);
}
function showReminderNotification(reminder) {
  var notificationId = "reminder-".concat(reminder.key, "-").concat(Date.now());

  // Store reminder data for action handling
  chrome.storage.local.set(_defineProperty({}, notificationId, reminder));

  // Add Reply action if not already present
  if (!reminder.actions.includes('Reply')) {
    reminder.actions.push('Reply');
  }

  // Create notification
  chrome.notifications.create(notificationId, {
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: "".concat(reminder.key, ": ").concat(reminder.title),
    message: reminder.message,
    contextMessage: "Priority: ".concat(reminder.priority, " | Status: ").concat(reminder.status),
    buttons: reminder.actions.slice(0, 2).map(function (action) {
      return {
        title: action
      };
    }),
    requireInteraction: true
  });
}

// Handle notification button clicks
chrome.notifications.onButtonClicked.addListener(function (notificationId, buttonIndex) {
  // Get the reminder data
  chrome.storage.local.get(notificationId, function (result) {
    if (result[notificationId]) {
      var reminder = result[notificationId];
      var action = reminder.actions[buttonIndex];

      // Handle action
      handleNotificationAction(notificationId, action, reminder.key).then(function () {
        // Clear notification data
        chrome.storage.local.remove(notificationId);
      })["catch"](function (error) {
        console.error("Failed to handle notification action: ".concat(error));
      });
    }
  });
});

// Handle a notification action
function handleNotificationAction(_x, _x2, _x3) {
  return _handleNotificationAction.apply(this, arguments);
} // Show reply popup for conversational responses
function _handleNotificationAction() {
  _handleNotificationAction = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee3(notificationId, action, issueKey) {
    var serverUrl, baseUrl;
    return _regeneratorRuntime().wrap(function _callee3$(_context3) {
      while (1) switch (_context3.prev = _context3.next) {
        case 0:
          _context3.prev = 0;
          console.log("Handling notification action: ".concat(action, " for ").concat(issueKey));
          _context3.t0 = action;
          _context3.next = _context3.t0 === 'Done' ? 5 : _context3.t0 === 'Snooze' ? 8 : _context3.t0 === 'View' ? 11 : _context3.t0 === 'Reply' ? 17 : 19;
          break;
        case 5:
          _context3.next = 7;
          return handleApiRequest('/api/reminders/mark-done', 'POST', {
            issue_key: issueKey
          });
        case 7:
          return _context3.abrupt("break", 19);
        case 8:
          _context3.next = 10;
          return handleApiRequest('/api/reminders/snooze', 'POST', {
            issue_key: issueKey,
            days: 1
          });
        case 10:
          return _context3.abrupt("break", 19);
        case 11:
          _context3.next = 13;
          return getServerUrl();
        case 13:
          serverUrl = _context3.sent;
          baseUrl = serverUrl.replace('/api', '');
          chrome.tabs.create({
            url: "".concat(baseUrl, "/browse/").concat(issueKey)
          });
          return _context3.abrupt("break", 19);
        case 17:
          // Show input popup for replying to the notification
          showReplyPopup(notificationId, issueKey);
          return _context3.abrupt("return", {
            success: true,
            action: action
          });
        case 19:
          // Close the notification
          chrome.notifications.clear(notificationId);
          return _context3.abrupt("return", {
            success: true,
            action: action
          });
        case 23:
          _context3.prev = 23;
          _context3.t1 = _context3["catch"](0);
          console.error("Failed to handle action ".concat(action, " for ").concat(issueKey, ":"), _context3.t1);
          throw _context3.t1;
        case 27:
        case "end":
          return _context3.stop();
      }
    }, _callee3, null, [[0, 23]]);
  }));
  return _handleNotificationAction.apply(this, arguments);
}
function showReplyPopup(notificationId, issueKey) {
  // Create popup with input field
  chrome.windows.create({
    url: "popup/reply.html?id=".concat(notificationId, "&key=").concat(issueKey),
    type: 'popup',
    width: 400,
    height: 200,
    focused: true
  });
}

// Handle conversational reply
function handleConversationalReply(_x4, _x5) {
  return _handleConversationalReply.apply(this, arguments);
} // Notification handling
function _handleConversationalReply() {
  _handleConversationalReply = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee4(issueKey, message) {
    var result, intent, feedbackTitle, feedbackMessage, serverUrl, baseUrl;
    return _regeneratorRuntime().wrap(function _callee4$(_context4) {
      while (1) switch (_context4.prev = _context4.next) {
        case 0:
          _context4.prev = 0;
          console.log("Handling conversational reply for ".concat(issueKey, ": ").concat(message));

          // Send the reply to the server
          _context4.next = 4;
          return handleApiRequest('/api/reminders/reply', 'POST', {
            issue_key: issueKey,
            message: message
          });
        case 4:
          result = _context4.sent;
          // Show feedback notification based on intent
          intent = result.intent || 'UNKNOWN'; // Create an appropriate feedback message
          feedbackTitle = 'Reply Sent';
          feedbackMessage = '';
          _context4.t0 = intent;
          _context4.next = _context4.t0 === 'COMPLETE' ? 11 : _context4.t0 === 'SNOOZE' ? 14 : _context4.t0 === 'UPDATE' ? 17 : _context4.t0 === 'VIEW' ? 20 : 28;
          break;
        case 11:
          feedbackTitle = 'Task Completed';
          feedbackMessage = "Task ".concat(issueKey, " has been marked as done");
          return _context4.abrupt("break", 30);
        case 14:
          feedbackTitle = 'Task Snoozed';
          feedbackMessage = "Task ".concat(issueKey, " has been snoozed for ").concat(result.days || 1, " day(s)");
          return _context4.abrupt("break", 30);
        case 17:
          feedbackTitle = 'Comment Added';
          feedbackMessage = "Comment added to ".concat(issueKey);
          return _context4.abrupt("break", 30);
        case 20:
          feedbackTitle = 'Opening Task';
          feedbackMessage = "Opening ".concat(issueKey, " for viewing");

          // Open task in a new tab
          _context4.next = 24;
          return getServerUrl();
        case 24:
          serverUrl = _context4.sent;
          baseUrl = serverUrl.replace('/api', '');
          chrome.tabs.create({
            url: "".concat(baseUrl, "/browse/").concat(issueKey)
          });
          return _context4.abrupt("break", 30);
        case 28:
          feedbackTitle = 'Reply Processed';
          feedbackMessage = "Your message was added as a comment to ".concat(issueKey);
        case 30:
          // Show feedback notification
          chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon48.png',
            title: feedbackTitle,
            message: feedbackMessage
          });
          return _context4.abrupt("return", result);
        case 34:
          _context4.prev = 34;
          _context4.t1 = _context4["catch"](0);
          console.error("Failed to process conversational reply for ".concat(issueKey, ":"), _context4.t1);

          // Show error notification
          chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon48.png',
            title: 'Error Processing Reply',
            message: "Failed to process your reply: ".concat(_context4.t1.message)
          });
          throw _context4.t1;
        case 39:
        case "end":
          return _context4.stop();
      }
    }, _callee4, null, [[0, 34]]);
  }));
  return _handleConversationalReply.apply(this, arguments);
}
function showNotification(title, message) {
  var actions = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : [];
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: title,
    message: message,
    buttons: actions.map(function (action) {
      return {
        title: action
      };
    }),
    requireInteraction: true
  });
}

// API request handling
function handleApiRequest(_x6) {
  return _handleApiRequest.apply(this, arguments);
} // Get server URL from storage
function _handleApiRequest() {
  _handleApiRequest = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee5(endpoint) {
    var method,
      data,
      serverUrl,
      url,
      options,
      response,
      isRefreshed,
      _args5 = arguments;
    return _regeneratorRuntime().wrap(function _callee5$(_context5) {
      while (1) switch (_context5.prev = _context5.next) {
        case 0:
          method = _args5.length > 1 && _args5[1] !== undefined ? _args5[1] : 'GET';
          data = _args5.length > 2 && _args5[2] !== undefined ? _args5[2] : null;
          _context5.next = 4;
          return getServerUrl();
        case 4:
          serverUrl = _context5.sent;
          url = "".concat(serverUrl).concat(endpoint);
          options = {
            method: method,
            headers: {
              'Content-Type': 'application/json'
            },
            credentials: 'include' // Include cookies for cross-origin requests
          };
          if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
          }
          _context5.prev = 8;
          _context5.next = 11;
          return fetch(url, options);
        case 11:
          response = _context5.sent;
          if (response.ok) {
            _context5.next = 20;
            break;
          }
          if (!(response.status === 401)) {
            _context5.next = 19;
            break;
          }
          _context5.next = 16;
          return refreshAuth();
        case 16:
          isRefreshed = _context5.sent;
          if (!isRefreshed) {
            _context5.next = 19;
            break;
          }
          return _context5.abrupt("return", handleApiRequest(endpoint, method, data));
        case 19:
          throw new Error("Server responded with ".concat(response.status, ": ").concat(response.statusText));
        case 20:
          _context5.next = 22;
          return response.json();
        case 22:
          return _context5.abrupt("return", _context5.sent);
        case 25:
          _context5.prev = 25;
          _context5.t0 = _context5["catch"](8);
          console.error('API request failed:', _context5.t0);
          throw _context5.t0;
        case 29:
        case "end":
          return _context5.stop();
      }
    }, _callee5, null, [[8, 25]]);
  }));
  return _handleApiRequest.apply(this, arguments);
}
function getServerUrl() {
  return _getServerUrl.apply(this, arguments);
} // OAuth Authentication
// Initiate the OAuth login process
function _getServerUrl() {
  _getServerUrl = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee6() {
    return _regeneratorRuntime().wrap(function _callee6$(_context6) {
      while (1) switch (_context6.prev = _context6.next) {
        case 0:
          return _context6.abrupt("return", new Promise(function (resolve) {
            chrome.storage.local.get('serverUrl', function (result) {
              resolve(result.serverUrl || API_BASE_URL);
            });
          }));
        case 1:
        case "end":
          return _context6.stop();
      }
    }, _callee6);
  }));
  return _getServerUrl.apply(this, arguments);
}
function initiateLogin() {
  return _initiateLogin.apply(this, arguments);
} // Logout the user
function _initiateLogin() {
  _initiateLogin = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee7() {
    var serverUrl, loginUrl;
    return _regeneratorRuntime().wrap(function _callee7$(_context7) {
      while (1) switch (_context7.prev = _context7.next) {
        case 0:
          _context7.prev = 0;
          // Generate a random state to protect against CSRF
          authState = Math.random().toString(36).substring(2, 15);

          // Save state to storage for validation later
          chrome.storage.local.set({
            'oauth_state': authState
          });
          _context7.next = 5;
          return getServerUrl();
        case 5:
          serverUrl = _context7.sent;
          loginUrl = "".concat(serverUrl, "/api/auth/login"); // Open a new tab with the login URL
          chrome.tabs.create({
            url: loginUrl
          });
          return _context7.abrupt("return", {
            message: 'Login initiated'
          });
        case 11:
          _context7.prev = 11;
          _context7.t0 = _context7["catch"](0);
          console.error('Failed to initiate login:', _context7.t0);
          throw _context7.t0;
        case 15:
        case "end":
          return _context7.stop();
      }
    }, _callee7, null, [[0, 11]]);
  }));
  return _initiateLogin.apply(this, arguments);
}
function logout() {
  return _logout.apply(this, arguments);
} // Check if the user is authenticated
function _logout() {
  _logout = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee8() {
    var serverUrl, logoutUrl;
    return _regeneratorRuntime().wrap(function _callee8$(_context8) {
      while (1) switch (_context8.prev = _context8.next) {
        case 0:
          _context8.prev = 0;
          _context8.next = 3;
          return getServerUrl();
        case 3:
          serverUrl = _context8.sent;
          logoutUrl = "".concat(serverUrl, "/api/auth/logout"); // Call the logout API
          _context8.next = 7;
          return fetch(logoutUrl, {
            method: 'GET',
            credentials: 'include' // Include cookies
          });
        case 7:
          // Update local storage auth status
          chrome.storage.local.set({
            isAuthenticated: false
          });
          return _context8.abrupt("return", {
            message: 'Logged out successfully'
          });
        case 11:
          _context8.prev = 11;
          _context8.t0 = _context8["catch"](0);
          console.error('Failed to logout:', _context8.t0);
          throw _context8.t0;
        case 15:
        case "end":
          return _context8.stop();
      }
    }, _callee8, null, [[0, 11]]);
  }));
  return _logout.apply(this, arguments);
}
function checkAuthStatus() {
  return _checkAuthStatus.apply(this, arguments);
} // Refresh the auth token
function _checkAuthStatus() {
  _checkAuthStatus = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee9() {
    var serverUrl, statusUrl, response, status;
    return _regeneratorRuntime().wrap(function _callee9$(_context9) {
      while (1) switch (_context9.prev = _context9.next) {
        case 0:
          _context9.prev = 0;
          _context9.next = 3;
          return getServerUrl();
        case 3:
          serverUrl = _context9.sent;
          statusUrl = "".concat(serverUrl, "/api/auth/status"); // Call the status API
          _context9.next = 7;
          return fetch(statusUrl, {
            method: 'GET',
            credentials: 'include' // Include cookies
          });
        case 7:
          response = _context9.sent;
          if (response.ok) {
            _context9.next = 10;
            break;
          }
          throw new Error("Server responded with ".concat(response.status, ": ").concat(response.statusText));
        case 10:
          _context9.next = 12;
          return response.json();
        case 12:
          status = _context9.sent;
          // Update local storage auth status
          chrome.storage.local.set({
            isAuthenticated: status.authenticated
          });
          return _context9.abrupt("return", status);
        case 17:
          _context9.prev = 17;
          _context9.t0 = _context9["catch"](0);
          console.error('Failed to check auth status:', _context9.t0);
          // In case of error, assume not authenticated
          chrome.storage.local.set({
            isAuthenticated: false
          });
          return _context9.abrupt("return", {
            authenticated: false,
            error: _context9.t0.message
          });
        case 22:
        case "end":
          return _context9.stop();
      }
    }, _callee9, null, [[0, 17]]);
  }));
  return _checkAuthStatus.apply(this, arguments);
}
function refreshAuth() {
  return _refreshAuth.apply(this, arguments);
} // Check auth status when extension loads
function _refreshAuth() {
  _refreshAuth = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee0() {
    var serverUrl, refreshUrl, response, result;
    return _regeneratorRuntime().wrap(function _callee0$(_context0) {
      while (1) switch (_context0.prev = _context0.next) {
        case 0:
          _context0.prev = 0;
          _context0.next = 3;
          return getServerUrl();
        case 3:
          serverUrl = _context0.sent;
          refreshUrl = "".concat(serverUrl, "/api/auth/refresh-token"); // Call the refresh token API
          _context0.next = 7;
          return fetch(refreshUrl, {
            method: 'POST',
            credentials: 'include' // Include cookies
          });
        case 7:
          response = _context0.sent;
          if (response.ok) {
            _context0.next = 10;
            break;
          }
          throw new Error("Server responded with ".concat(response.status, ": ").concat(response.statusText));
        case 10:
          _context0.next = 12;
          return response.json();
        case 12:
          result = _context0.sent;
          return _context0.abrupt("return", result.success);
        case 16:
          _context0.prev = 16;
          _context0.t0 = _context0["catch"](0);
          console.error('Failed to refresh auth token:', _context0.t0);
          return _context0.abrupt("return", false);
        case 20:
        case "end":
          return _context0.stop();
      }
    }, _callee0, null, [[0, 16]]);
  }));
  return _refreshAuth.apply(this, arguments);
}
checkAuthStatus().then(function (status) {
  console.log('Initial auth status:', status.authenticated ? 'Authenticated' : 'Not authenticated');
});
/******/ })()
;
//# sourceMappingURL=background.js.map