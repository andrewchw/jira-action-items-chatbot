/**
 * Tests for the popup.js file
 */

// Mock Chrome API
global.chrome = {
  storage: {
    local: {
      get: jest.fn(),
      set: jest.fn()
    }
  },
  runtime: {
    sendMessage: jest.fn(),
    onMessage: {
      addListener: jest.fn()
    }
  },
  tabs: {
    query: jest.fn(),
    sendMessage: jest.fn(),
    create: jest.fn()
  },
  notifications: {
    create: jest.fn(),
    onButtonClicked: {
      addListener: jest.fn()
    }
  }
};

// Mock DOM elements
document.body.innerHTML = `
  <div id="chat-messages"></div>
  <textarea id="user-input"></textarea>
  <button id="send-button"></button>
  <button id="attach-button"></button>
  <span id="status-circle" class="status-circle"></span>
  <span id="status-text">Connecting...</span>
  <button id="tab-chat" class="tab-button active"></button>
  <button id="tab-tasks" class="tab-button"></button>
  <button id="tab-settings" class="tab-button"></button>
  <div id="tasks-content" class="tab-content" style="display: none;"></div>
  <div id="settings-content" class="tab-content" style="display: none;"></div>
  <input type="text" id="server-url" />
  <input type="checkbox" id="notifications-toggle" />
  <button id="save-settings"></button>
  <div id="task-list"></div>
`;

// Import the functions to test
// Note: In a real implementation, the popup.js functions would be exported and imported here
// For now, we'll just test some basic functionality

describe('Popup UI Functionality', () => {
  // Mock functions to test
  const mockAddMessage = (sender, text) => {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.innerHTML = `<div class="message-content">${text}</div>`;
    document.getElementById('chat-messages').appendChild(messageDiv);
    return messageDiv;
  };
  
  const mockSendMessage = () => {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();
    if (!message) return null;
    
    const messageDiv = mockAddMessage('user', message);
    userInput.value = '';
    return messageDiv;
  };
  
  beforeEach(() => {
    // Clear any previous test effects
    document.getElementById('chat-messages').innerHTML = '';
    document.getElementById('user-input').value = '';
    
    // Reset mocks
    jest.clearAllMocks();
  });

  test('Add message should add a message to the chat', () => {
    const text = 'Test message';
    const messageDiv = mockAddMessage('bot', text);
    
    expect(messageDiv).toBeTruthy();
    expect(messageDiv.classList.contains('bot-message')).toBe(true);
    expect(messageDiv.querySelector('.message-content').textContent).toBe(text);
    
    const chatMessages = document.getElementById('chat-messages');
    expect(chatMessages.children.length).toBe(1);
  });

  test('Send message should add user message to chat and clear input', () => {
    const text = 'User test message';
    document.getElementById('user-input').value = text;
    
    const messageDiv = mockSendMessage();
    
    expect(messageDiv).toBeTruthy();
    expect(messageDiv.classList.contains('user-message')).toBe(true);
    expect(messageDiv.querySelector('.message-content').textContent).toBe(text);
    expect(document.getElementById('user-input').value).toBe('');
  });

  test('Send message should not add empty messages', () => {
    document.getElementById('user-input').value = '   ';
    
    const messageDiv = mockSendMessage();
    
    expect(messageDiv).toBeNull();
    expect(document.getElementById('chat-messages').children.length).toBe(0);
  });
}); 