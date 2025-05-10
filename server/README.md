# Jira Action Items Chatbot Server

This is the backend server for the Jira Action Items Chatbot Edge extension.

## Environment Setup

Copy the `.env.example` file to `.env` and fill in the following variables:

```
# Jira Configuration
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-api-token
DEFAULT_JIRA_PROJECT_KEY=JCAI

# OpenRouter LLM Configuration
OPENROUTER_API_KEY=your-openrouter-api-key
DEFAULT_LLM_MODEL=meta-llama/llama-3-8b-instruct
LLM_MAX_TOKENS=4096
```

## OpenRouter Model Configuration

### LLM Model Selection

The application supports various OpenRouter models. You can configure which model to use by updating the `DEFAULT_LLM_MODEL` in the `.env` file. Some recommended options:

- `mistralai/mistral-7b-instruct` - Fast, 7B parameter model
- `meta-llama/llama-3-8b-instruct` - Good balance of performance and speed
- `meta-llama/llama-3-70b-instruct` - More powerful, but slower and more expensive

There are no truly "free" models on OpenRouter - all models pass through provider pricing. While there are open-source models available, you still pay for the API usage according to OpenRouter's pricing model.

### Token Limits

Most LLMs on OpenRouter support large context windows (8K-128K tokens). The application is configured with:

- Default max tokens: `4096`
- Context window: Depends on the model (see below)

Common context windows by model:
- Mistral models: 8K tokens
- Llama-3 models: 8K tokens
- Claude models: 48K-128K tokens
- GPT-4 models: 8K-128K tokens

Note: Even though models support larger context windows, setting too high of a max token count can lead to very slow responses and higher costs. The default `4096` provides a good balance.

To change the token limit:
1. Update the `LLM_MAX_TOKENS` value in your `.env` file
2. Restart the server for changes to take effect

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