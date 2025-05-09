# Product Requirements Document: Intelligent Microsoft Edge Chatbot Extension for Jira Action Item Management

## 1. Elevator Pitch
An Edge extension chatbot that enables teams to manage Jira action items through natural language commands, automating task creation, reminders, and evidence tracking while maintaining firewall compliance. This solution leverages a free open-source LLM API (e.g., OpenRouter) and replaces manual task follow-ups, reducing manual Jira updates by 80% and supporting seamless, conversational task management directly in Microsoft Edge.

## 2. Who Is This App For
- Team leads managing distributed agile teams
- Developers/QA engineers needing quick task updates
- Project managers tracking sprint deliverables
- IT departments requiring firewall-compliant solutions
- Organizations restricted to Microsoft Edge browser

## 3. Functional Requirements

### Core Features (Phase 1)
- Conversational Task Management: Natural language commands to create, update, and query Jira issues via REST API.
- LLM Integration: OpenRouter’s free API (e.g., Llama 3, Mistral 7B) for parsing user input and generating context-aware responses.
- Reminders: Browser notifications to task owners based on Jira due dates, with conversational reply support (e.g., “Done”, “Need extension”).
- Evidence Upload: File upload and comment support, attaching evidence to Jira issues.
- Intranet Hosting: Python server hosted internally for all LLM and Jira API interactions, ensuring firewall compliance.
- Edge Extension: Chromium-based sidebar or popup chat interface.

### Enhanced Features (Phase 2)
- Advanced file upload with OCR validation for evidence.
- Multi-criteria task queries (e.g., “Show Sarah’s overdue docs review”).
- Custom reminder templates with @mentions.

### Advanced Features (Phase 3)
- Predictive task prioritization using historical data.
- Cross-project dependency mapping.
- SLA compliance analytics dashboard.

### Technical Requirements
- **Extension (Client):** JavaScript, HTML, CSS; uses Chromium APIs (`chrome.runtime`, `chrome.notifications`).
- **Server:** Python 3.x with FastAPI; libraries include `requests`, `APScheduler`, `jira-python`, `python-dotenv`.
- **Database:** SQLite for local caching of tasks and API responses.
- **Authentication:** OAuth or API tokens for Jira and OpenRouter, stored securely on the server.
- **Hosting:** Intranet server (Linux/Windows), outbound HTTPS only to OpenRouter’s API.
- **Development Environment:** VS Code with GitHub Copilot.

## 4. User Stories

### High-Priority Stories
- As a team lead, I want to type "Create a task for John to review docs by Monday" in the Edge extension, so the bot creates a Jira issue without manual setup.
- As a task owner, I want to receive browser notifications with natural language reminders and confirm completion conversationally in the extension.
- As a team member, I want to ask "What tasks are assigned to me?" in the extension and get a clear response based on Jira data.
- As a Scrum Master, I want to type "Log retrospective action items for Sprint 22" and have tasks auto-created with assignees, so we eliminate manual Jira entry.
- As a Developer, I want to respond "Done" to a chatbot reminder notification to automatically close the Jira ticket.
- As a PMO, I need to ask "Show all unapproved PRDs" and get linked Jira issues with statuses, to track deliverables without Jira navigation.

### Technical Stories
- As a DevOps Engineer, I want CLI deployment of the intranet server with health checks, to maintain firewall compliance.
- As a Security Officer, I require all Jira API calls to use rotating tokens stored exclusively on-prem.

## 5. User Interface

**Chat UI (Edge Sidebar):**
```
[Bot Icon] What would you like to track today?
User: "Assign docs review to Alice due Friday"
Bot: "Created Jira DOC-42 • Due May 10 • Reminders set"
```
**Key Components:**
- Context-aware input with auto-suggestions for project IDs and assignees.
- Visual proof hub: thumbnail grid of uploaded evidence.
- SLA meter: color-coded due date progress bar.
- Browser notifications with actionable replies.

## 6. Success Metrics
- Reduce manual task reminders by 80%.
- 100% of action items tracked in Jira via the extension.
- Users can create, query, or complete tasks in under 30 seconds using natural language.
- Zero missed reminders for due tasks.

## 7. Development Scope

| Phase   | Focus                                         | Timeline |
|---------|-----------------------------------------------|----------|
| Phase 1 | Core: Edge extension, chat UI, LLM/Jira API, reminders | 3 weeks  |
| Phase 2 | File upload, advanced queries, enhanced prompts | 5 weeks  |
| Phase 3 | Performance, firewall testing, analytics, UX   | 8 weeks  |

## 8. Constraints
- Restricted to Microsoft Edge browser per company policy.
- Server must be hosted on intranet due to firewall restrictions, with external calls limited to OpenRouter’s API.
- Limited to OpenRouter’s free API tier to avoid costs, which may impose rate limits.
- Team must have basic familiarity with Jira workflows.

## 9. Assumptions
- OpenRouter’s free API supports sufficient throughput for team usage (can fallback to alternatives like Groq if needed).
- Jira instance is accessible via API with proper authentication.
- Intranet server has Python 3.x, Node.js (for extension build tools), and required dependencies installed.
- Edge browser is managed to allow extension installation via enterprise policies.

## 10. Development Plan

- **Setup:**
  - Configure VS Code with Copilot, install Python and Node.js dependencies.
  - Register for OpenRouter API key and Jira API token.
  - Set up Edge extension development environment with Chromium tools.
- **Code Structure:**
  - Extension: JavaScript for chat UI, API calls to intranet server, and browser notifications.
  - Server: FastAPI endpoints for LLM processing (`/chat`), Jira interactions (`/jira`), and reminder scheduling.
  - Scheduler: APScheduler to poll Jira for due tasks and send notifications via the extension.
- **Testing:**
  - Use VS Code debugging for extension and server.
  - Simulate user inputs and Jira API responses locally.
  - Test notification delivery in Edge.
- **Deployment:**
  - Deploy server on intranet (e.g., Ubuntu server with FastAPI and SQLite).
  - Package extension as a `.crx` file and distribute via enterprise policy (e.g., `ExtensionInstallForceList`).
  - Configure firewall to allow outbound HTTPS to OpenRouter’s API.

## 11. Risks and Mitigation

| Risk                                              | Mitigation                                                                                   |
|---------------------------------------------------|----------------------------------------------------------------------------------------------|
| OpenRouter’s free tier rate limits slow responses | Cache frequent queries in SQLite or fallback to alternative free LLM APIs (e.g., Groq).      |
| Complex natural language confuses the LLM         | Fine-tune prompts with task-specific examples and provide fallback structured inputs.         |
| Firewall blocks OpenRouter API calls              | Work with IT to allow outbound traffic to OpenRouter’s endpoint.                             |
| Enterprise policies restrict extension install    | Use group policies to enable self-hosted extension deployment.                               |

## 12. Timeline & Resources

- **Timeline:** 6-8 weeks for Phase 1 (core functionality), assuming 1-2 developers.
- **Resources:**
  - Developer(s) with Python and JavaScript experience.
  - Jira admin for API setup.
  - IT support for intranet server and firewall configuration.
  - Edge enterprise admin for extension deployment policies.

---