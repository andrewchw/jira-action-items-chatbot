# Jira Action Items Chatbot

A Microsoft Edge extension with an intelligent chatbot interface that enables teams to manage Jira action items through natural language commands.

## Features

- Create and manage Jira tasks through natural language commands
- Get reminders about upcoming deadlines
- Attach evidence and documentation directly to Jira tickets
- Firewall-compliant integration with Jira
- Intelligent context-aware responses

## Installation for Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/jira-action-items-chatbot.git
cd jira-action-items-chatbot
```

2. Install dependencies for both the root project and the extension:
```bash
npm run install:all
```

3. Build the extension:
```bash
npm run build
```

4. Load the extension in Microsoft Edge:
   - Open Edge and navigate to `edge://extensions/`
   - Enable "Developer mode" using the toggle in the bottom-left
   - Click "Load unpacked"
   - Select the `extension/dist` directory from this project

## Development Workflow

1. Start the development server with hot reloading:
```bash
npm run dev
```

2. Make your changes to the extension code
3. The extension will automatically rebuild when files change
4. Reload the extension in Edge to see your changes

## Testing

Run the Jest tests:
```bash
npm test
```

## Building for Production

To create a production build that can be published to the Edge Add-ons store:

```bash
npm run build
```

## Packaging the Extension

To create a zip file for submission to the Edge Add-ons store:

```bash
npm run pack:extension
```

This will create a `jira-action-items-chatbot.zip` file in the root directory.

## Publishing to Edge Add-ons Store

1. Go to the [Edge Add-ons Developer Dashboard](https://partner.microsoft.com/en-us/dashboard/microsoftedge/overview)
2. Sign in with your Microsoft account
3. Click "Submit a new extension"
4. Fill in the required information and upload the zip file created by the `pack:extension` command
5. Submit for review

## License

This project is licensed under the MIT License - see the LICENSE file for details. 