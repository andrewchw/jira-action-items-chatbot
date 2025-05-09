/**
 * Jira Action Items Chatbot
 * 
 * This file serves as the main entry point for the package.
 * It exports information about the extension and provides utility functions.
 */

const path = require('path');

// Export extension metadata
const extensionInfo = {
  name: 'Jira Action Items Chatbot',
  version: require('./package.json').version,
  description: require('./package.json').description,
  distPath: path.join(__dirname, 'extension', 'dist'),
  manifestPath: path.join(__dirname, 'extension', 'manifest.json')
};

// Utility function to get the path to the built extension
function getExtensionPath() {
  return extensionInfo.distPath;
}

// Utility function to get the manifest
function getManifest() {
  return require(extensionInfo.manifestPath);
}

module.exports = {
  extensionInfo,
  getExtensionPath,
  getManifest
}; 