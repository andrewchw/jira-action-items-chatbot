# Jira Action Items Chatbot

A Microsoft Edge extension with an intelligent chatbot interface that enables teams to manage Jira action items through natural language commands.

This is a hybrid project consisting of:
- A Microsoft Edge extension (JavaScript/Node.js)
- A Python backend server (FastAPI)

## Features

- Create and manage Jira tasks through natural language commands
- Get reminders about upcoming deadlines
- Attach evidence and documentation directly to Jira tickets
- Firewall-compliant integration with Jira
- Intelligent context-aware responses

## Installation for Development

1. Clone the repository:
```bash
git clone https://github.com/deencat/jira-action-items-chatbot.git
cd jira-action-items-chatbot
```

### Extension Setup (JavaScript/Node.js)

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

### Server Setup (Python)

5. Navigate to the server directory where the pre-configured virtual environment exists:
```bash
cd server
```

6. Activate the existing virtual environment:
```bash
# On Windows with Git Bash or similar
source venv_proper/Scripts/activate
# OR on Windows with cmd
# .\venv_proper\Scripts\activate.bat
# OR on Windows with PowerShell
# .\venv_proper\Scripts\Activate.ps1
```

7. Verify you're using the virtual environment Python:
```bash
# Should show the path to the virtual environment Python
which python  # On Unix-like systems or Git Bash
# OR
where python  # On Windows cmd
```

8. (Optional) If you need to create a fresh environment or update dependencies:
```bash
# Only if needed - the venv_proper environment should already be set up
pip install -r requirements.txt
pip install pydantic-settings  # Additional dependency required
```

9. (Optional) Clean up unused virtual environments if present:
```bash
# Only if you have these directories and want to remove them
rm -rf venv venv_local
```

## Environment Configuration

The Python server requires environment variables to be properly set up. Create a `.env` file in the server directory based on the template provided in `.env.template`.

```bash
# Make sure you're in the server directory with an activated virtual environment
cp .env.template .env
# Edit .env with your specific configuration
```

Common environment variables include:
- Jira API credentials
- Database connection settings
- API keys for authentication
- Server configuration parameters

10. Download necessary NLTK data (required for natural language processing):
```bash
# Make sure your virtual environment is activated
python -c "import nltk; nltk.download('punkt')"
```

11. Run the FastAPI server:
```bash
# Make sure your virtual environment is activated
python -m uvicorn app.main:app --reload
```

You should see output indicating that the server has started successfully and is listening on http://127.0.0.1:8000.

## Development Workflow

### Extension Development

1. Start the extension development server with hot reloading:
```bash
npm run dev
```

2. Make your changes to the extension code
3. The extension will automatically rebuild when files change
4. Reload the extension in Edge to see your changes

### Server Development

1. Navigate to the server directory and activate the virtual environment (if not already activated)
```bash
cd server
source venv_proper/Scripts/activate  # Adjust command based on your shell
```

2. Run the FastAPI server with auto-reload enabled:
```bash
# Make sure your virtual environment is activated
python -m uvicorn app.main:app --reload
```

3. Make changes to the server code
4. The server will automatically restart when changes are detected

## Testing

### Extension Tests

Run the Jest tests for the browser extension:
```bash
npm test
```

### Server Tests

Run the Python tests for the backend server:
```bash
cd server
source venv_proper/Scripts/activate  # Adjust command based on your shell
# Make sure your virtual environment is activated
python -m pytest
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

## Server Deployment

For production deployment of the Python server:

1. Set up a production environment with Python 3.x
2. Clone the repository and navigate to the server directory
3. Create and activate a virtual environment for isolation:
```bash
python -m venv prod_env  # Using a different name to distinguish from development environments
source prod_env/Scripts/activate  # Adjust command based on your shell
```
4. Install production dependencies in the virtual environment:
```bash
pip install -r requirements.txt
pip install pydantic-settings gunicorn
```
5. Configure your production environment variables
6. Run the server using a production ASGI server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For more robust deployment, consider using Gunicorn with Uvicorn workers:
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

You may also want to set up a reverse proxy such as Nginx in front of the application server.

## Publishing to Edge Add-ons Store

1. Go to the [Edge Add-ons Developer Dashboard](https://partner.microsoft.com/en-us/dashboard/microsoftedge/overview)
2. Sign in with your Microsoft account
3. Click "Submit a new extension"
4. Fill in the required information and upload the zip file created by the `pack:extension` command
5. Submit for review

## License

This project is licensed under the MIT License - see the LICENSE file for details.