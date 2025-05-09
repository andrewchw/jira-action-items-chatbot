# Jira Action Items Chatbot Server

This is the FastAPI server component for the Jira Action Items Chatbot extension.

## Features

- RESTful API for the Edge extension to communicate with
- Jira API integration for task management
- LLM integration via OpenRouter for natural language processing
- Reminder system for task due dates
- Evidence upload and attachment to Jira issues

## Getting Started

### Prerequisites

- Python 3.x
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/deencat/jira-action-items-chatbot.git
   cd jira-action-items-chatbot/server
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.template` and configure your environment variables:
   ```
   cp .env.template .env
   # Edit .env with your specific settings
   ```

### Running the Server

Development mode:
```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Production mode:
```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, you can access:
- Interactive API documentation: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc

## Testing

Run tests using pytest:
```
pytest
```

## Project Structure

```
server/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   └── endpoints.py
│   ├── models/
│   │   └── schemas.py
│   └── core/
│       └── config.py
├── tests/
│   └── test_endpoints.py
└── requirements.txt
```

## License

This project is licensed under the MIT License. 