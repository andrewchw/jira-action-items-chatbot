/**
 * Content script for the Jira Action Items Chatbot extension
 * This runs in the context of web pages to detect Jira content
 */

// Check if we're on a Jira page
const isJiraPage = document.location.href.includes('atlassian.net') || 
                   document.location.href.includes('jira');

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
  if (isJiraPage) {
    console.log('Jira page detected, initializing content script');
    initializeJiraIntegration();
  }
});

// Initialize Jira specific functionality
function initializeJiraIntegration() {
  // Try to extract issue information if on a specific issue page
  const issueKey = extractIssueKey();
  if (issueKey) {
    // Notify the background script about the current issue
    chrome.runtime.sendMessage({
      type: 'JIRA_CONTEXT',
      data: {
        issueKey: issueKey,
        issueUrl: window.location.href,
        pageTitle: document.title
      }
    });
  }

  // Add sidebar button if needed
  addSidebarButton();
}

// Extract Jira issue key from the page (e.g., "PROJ-123")
function extractIssueKey() {
  // Try to find the issue key in the URL
  const urlMatch = window.location.href.match(/[A-Z]+-\d+/);
  if (urlMatch) return urlMatch[0];
  
  // Try to find it in the page title
  const titleMatch = document.title.match(/[A-Z]+-\d+/);
  if (titleMatch) return titleMatch[0];
  
  // Try to find it in specific page elements
  const issueKeyElements = document.querySelectorAll('[data-issue-key]');
  if (issueKeyElements.length > 0) {
    return issueKeyElements[0].getAttribute('data-issue-key');
  }
  
  return null;
}

// Add a button to open our sidebar
function addSidebarButton() {
  // Check if our button already exists
  if (document.getElementById('jira-action-items-button')) return;
  
  // Create button element
  const button = document.createElement('button');
  button.id = 'jira-action-items-button';
  button.innerText = 'Action Items';
  button.style.cssText = `
    position: fixed;
    right: 20px;
    top: 100px;
    z-index: 9999;
    background-color: #0052CC;
    color: white;
    border: none;
    border-radius: 3px;
    padding: 8px 12px;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  `;
  
  // Add click event to open extension popup
  button.addEventListener('click', () => {
    chrome.runtime.sendMessage({ type: 'OPEN_POPUP' });
  });
  
  // Add to page
  document.body.appendChild(button);
}

// Listen for messages from the background script or popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_JIRA_CONTEXT') {
    const issueKey = extractIssueKey();
    sendResponse({
      issueKey: issueKey,
      issueUrl: window.location.href,
      pageTitle: document.title,
      isJiraPage: isJiraPage
    });
    return true;
  }
}); 