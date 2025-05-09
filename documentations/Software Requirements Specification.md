# Software Requirements Specification  

## System Design  
- **Client**: Edge extension (Chromium-based) with chat UI, notifications, and local storage.  
- **Server**: Python FastAPI middleware handling LLM processing, Jira API calls, and scheduling.  
- **External Services**: OpenRouter LLM API, Jira Cloud/Server REST API.  

## Architecture Pattern  
**Client-Server** with middleware:  
- Extension → Intranet Server → Jira/OpenRouter APIs  
- Server acts as firewall-compliant proxy and task coordinator.  

## State Management  
- **Client**: Chromium storage API for user preferences/context.  
- **Server**: SQLite for caching frequent queries/Jira responses.  
- **Jira**: Source of truth for task state.  

## Data Flow  
1. User command → Extension → Server `/chat` endpoint  
2. Server → OpenRouter API → Parse intent → Jira API  
3. Jira response → Server → Extension + Browser notification  
4. APScheduler polls Jira hourly for due tasks → Notifications.  

## Technical Stack  
| Component        | Technology                  |  
|------------------|-----------------------------|  
| Extension        | JavaScript, Chrome APIs     |  
| Server           | Python 3.10, FastAPI, SQLite|  
| LLM              | OpenRouter (Llama 3/Mistral)|  
| Notifications    | `chrome.notifications` API  |  
| Scheduler        | APScheduler                 |  

## Authentication Process  
- **Jira**: OAuth 2.0 with token rotation (server-side storage).  
- **OpenRouter**: API key in server environment variables.  
- **Extension**: Enterprise policy-enforced installation.  

## Route Design  
**Server Endpoints**:  
- `POST /chat` - Process natural language input  
- `POST /jira/create` - Create Jira issues  
- `GET /jira/search` - Query tasks  
- `POST /upload` - Handle evidence files  

## API Design  
**Extension ↔ Server**:  
```json  
// Request  
{ "text": "Assign docs review to Alice", "user": "john@company.com" }  

// Response  
{  
  "jira_id": "DOC-42",  
  "summary": "Documentation Review",  
  "due": "2025-05-12",  
  "actions": ["Done", "Request Extension"]  
}  
```

## Database Design ERD  
**SQLite Schema**:  
- **Tasks**  
  - task_id (PK)  
  - jira_id  
  - user_email  
  - last_updated  

- **Users**  
  - email (PK)  
  - jira_project_default  

- **API_Cache**  
  - query_hash (PK)  
  - response  
  - expires_at  

---

Need me to elaborate on any component or adjust technical constraints?

Citations:
[1] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/9841353/db3457a6-b125-460c-b1a3-f56e3cc7b5a4/PRD_-Microsoft-Edge-Chatbot-Extension-for-Jira-Action-Items.md
[2] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/9841353/065ad3fe-37f0-41e9-ae61-47eb7321ff0a/PRD_-Microsoft-Edge-Chatbot-Extension-for-Jira-Action-Items2.md
[3] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/9841353/bfa9078a-6753-4bb3-acce-c4bf563a39da/PRD_-Microsoft-Edge-Chatbot-Extension-for-Jira-Action-Items2.md
[4] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/9841353/32ea5b0a-8338-4a9c-9e28-487ff578a26b/User-Interface-Design-Document.txt

---
Answer from Perplexity: pplx.ai/share