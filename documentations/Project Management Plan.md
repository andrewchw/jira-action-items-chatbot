# Project Management Plan: Microsoft Edge Chatbot Extension for Jira Action Items

## 1. Project Overview

**Project Name:** Intelligent Microsoft Edge Chatbot Extension for Jira Action Item Management

**Project Description:**  
An Edge extension with an intelligent chatbot interface that enables teams to manage Jira action items through natural language commands, automating task creation, reminders, and evidence tracking while maintaining firewall compliance. The solution leverages OpenRouter's free LLM API and reduces manual Jira updates by 80%.

**Project Goal:**  
Create a seamless, conversational task management solution that integrates directly with Microsoft Edge and Jira, enabling teams to create, update, and track tasks without leaving their browser.

## 2. Project Phases and Timeline

| Phase | Focus | Duration | Timeline |
|-------|-------|----------|----------|
| **Phase 1** | Core functionality: Edge extension, chat UI, LLM/Jira API integration, reminders | 3 weeks | Weeks 1-3 |
| **Phase 2** | Enhanced features: File upload with OCR, advanced queries, custom reminders | 5 weeks | Weeks 4-8 |
| **Phase 3** | Advanced features: Performance optimization, analytics dashboard, firewall testing | 8 weeks | Weeks 9-16 |

**Total Project Duration:** 16 weeks

## 3. Project Organization

### 3.1 Team Roles & Responsibilities

- **Developer(s):** Implement Edge extension and Python server components
- **Jira Admin:** Configure Jira API access and permissions
- **IT Support:** Set up intranet server and firewall configuration
- **Edge Admin:** Configure extension deployment policies
- **QA Engineer:** Test functionality across different scenarios and environments

### 3.2 Communication Plan

- **Daily Stand-ups:** 15-minute check-ins on progress and blockers
- **Weekly Sprint Reviews:** Demo completed functionality and gather feedback
- **Bi-weekly Task Reviews:** Review Taskmaster task status and adjust priorities
- **Monthly Stakeholder Updates:** Present progress against success metrics

## 4. Task Management Methodology

We will use Taskmaster for task management, following the development workflow outlined in the cursor rules.

### 4.1 Initial Setup

1. **Initialize Project:**
   ```bash
   task-master init --name "Jira-Action-Items-Chatbot" --description "Microsoft Edge extension for Jira item management via chatbot"
   ```

2. **Parse PRD to Generate Tasks:**
   ```bash
   task-master parse-prd --input="documentations/PRD_ Microsoft Edge Chatbot Extension for Jira Action Items2.md"
   ```

3. **Analyze Project Complexity:**
   ```bash
   task-master analyze-complexity --research
   task-master complexity-report
   ```

4. **Expand Complex Tasks:**
   ```bash
   task-master expand --all --research
   ```

### 4.2 Task Workflow Process

For each task:

1. **Task Selection:**
   - Run `task-master next` to identify the next task with satisfied dependencies
   - Review task details with `task-master show <id>`

2. **Task Planning:**
   - Break down complex tasks with `task-master expand --id=<id> --research`
   - Set task to "in-progress" with `task-master set-status --id=<id> --status=in-progress`

3. **Implementation:**
   - Follow iterative subtask implementation process
   - Log progress regularly with `task-master update-subtask`
   - Run comprehensive tests for each completed component

4. **Task Completion:**
   - Verify against test strategy
   - Mark as complete with `task-master set-status --id=<id> --status=done`
   - Commit changes with descriptive messages

5. **Review & Adapt:**
   - Update dependent tasks if implementation deviates from original plan
   - Add new tasks for discovered requirements

### 4.3 Task Tracking Instructions

- Tasks are tagged as Done, In-Progress, ToDo, or Backlog
- Run `task-master list` to see current task statuses
- Update task statuses with `task-master set-status --id=<id> --status=<status>`
- Cross-reference with Jira tickets when applicable

### 4.4 Completed Tasks (Done)

Tasks are ordered chronologically from top to bottom:

- Project management plan creation
- Initial environment configuration 
- Project documentation structure setup
- Taskmaster project initialization
- Task #1.1: Set up Node.js environment and Edge extension structure
- Root package.json and publishing setup

### 4.5 In-Progress Tasks

Tasks currently being worked on:

- Task #1: Set up development environment and project structure (Main task)
- PRD parsing and initial task generation

### 4.6 Pending Tasks (ToDo)

Tasks are prioritized by their order in the list:

- Task #1.2: Set up Python environment and FastAPI server structure
- Task #1.3: Initialize Git repository and project configuration
- Task #2: Implement basic Edge extension with chat UI
- Task #3: Create Python server with FastAPI endpoints
- Task #4: Implement LLM integration with OpenRouter API
- Task #5: Develop Jira API integration for task management
- Task #6: Connect Edge extension to Python server
- Task #7: Implement reminder system with browser notifications
- Task #8: Add evidence upload functionality
- Task #9: Implement SQLite database for caching
- Task #10: Prepare deployment package and documentation

### 4.7 Backlog Tasks

Tasks for future consideration:

- OCR for document validation
- Analytics dashboard
- Cross-project dependency mapping
- Predictive task prioritization
- Custom reminder templates
- Multi-criteria task queries
- SLA compliance analytics

## 5. Development Environment Setup

### 5.1 Required Tools & Dependencies

- **Development Environment:** VS Code with GitHub Copilot
- **Client-Side:** 
  - Node.js and npm for extension development
  - Chromium extension development tools
- **Server-Side:**
  - Python 3.10 with FastAPI
  - SQLite for database
  - Required libraries: `requests`, `APScheduler`, `jira-python`, `python-dotenv`
- **External APIs:**
  - OpenRouter API key (for LLM access)
  - Jira API tokens

### 5.2 Environment Variables Configuration

Create a `.env` file with the following variables:
```
ANTHROPIC_API_KEY=your_api_key
MODEL=claude-3-opus-20240229
PROJECT_NAME=Jira-Action-Items-Chatbot
PROJECT_VERSION=0.1.0
OPENROUTER_API_KEY=your_api_key
JIRA_API_TOKEN=your_token
JIRA_API_URL=your_jira_instance_url
```

## 6. Technical Architecture & Implementation Plan

### 6.1 System Components

1. **Edge Extension (Client):**
   - Chat UI with sidebar integration
   - Browser notifications using `chrome.notifications` API
   - Local storage using Chrome storage API

2. **Python Server (Middleware):**
   - FastAPI endpoints for LLM and Jira interaction
   - SQLite for caching frequent queries
   - APScheduler for task reminders

3. **External Services:**
   - OpenRouter LLM API for natural language processing
   - Jira REST API for task management

### 6.2 Data Flow Architecture

```
User Command → Edge Extension → Intranet Server → OpenRouter API
                                                → Jira API
                                                → SQLite Cache
```

### 6.3 Implementation Tasks Breakdown (High-Level)

#### Phase 1 (Core Functionality)

1. **Setup Development Environment**
   - Install required tools and dependencies
   - Configure API access for OpenRouter and Jira
   - Set up extension development environment

2. **Server Implementation**
   - Create FastAPI application structure
   - Implement core API endpoints
   - Set up SQLite database schema
   - Implement LLM integration
   - Create Jira API client

3. **Extension Implementation**
   - Design chat UI based on UI document
   - Implement core chat functionality
   - Create API client for server communication
   - Implement browser notifications

4. **Integration & Testing**
   - Connect extension to server
   - Test natural language task creation
   - Verify Jira integration
   - Test notifications and reminders

#### Phase 2 (Enhanced Features)

1. **File Upload Functionality**
   - Implement drag-and-drop interface
   - Create server-side file handling
   - Implement OCR for document validation

2. **Advanced Query Support**
   - Enhance LLM prompts for complex queries
   - Implement multi-criteria search
   - Add suggestion functionality

3. **Custom Reminders**
   - Create template system
   - Implement @mentions support
   - Enhance notification system

#### Phase 3 (Advanced Features)

1. **Performance Optimization**
   - Implement caching strategies
   - Optimize API calls
   - Enhance response times

2. **Analytics Dashboard**
   - Create SLA compliance tracking
   - Implement task prioritization
   - Build dependency mapping

3. **Security & Deployment**
   - Conduct firewall compliance testing
   - Package extension for enterprise deployment
   - Document deployment process

## 7. Testing Strategy

### 7.1 Testing Approaches

- **Unit Testing:** Test individual components in isolation
- **Integration Testing:** Verify component interactions
- **End-to-End Testing:** Test complete workflows
- **User Acceptance Testing:** Validate against user stories

### 7.2 Test Cases (Examples)

- **Natural Language Processing:** Verify chatbot correctly interprets various task creation commands
- **Jira Integration:** Confirm tasks are correctly created, updated, and queried in Jira
- **Notifications:** Test that reminders are delivered on time and response actions work
- **File Upload:** Verify evidence files are properly attached to Jira issues
- **Firewall Compliance:** Ensure all external calls respect firewall restrictions

### 7.3 Automated Testing

- Implement Playwright for UI and integration tests
- Create regression test suite for continuous validation
- Set up CI pipeline for automated testing
- Run full Playwright regression tests after each feature change
- Check and terminate lingering Playwright report server processes before running tests

## 8. Risk Management

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| OpenRouter's free tier rate limits | Medium | High | Cache frequent queries in SQLite; implement fallback to alternative free LLM APIs |
| Complex natural language confusion | High | Medium | Fine-tune prompts with task-specific examples; provide structured fallback inputs |
| Firewall blocking OpenRouter API | Medium | Critical | Work with IT to allow outbound traffic or implement proxy solution |
| Enterprise policies restricting extension | Medium | High | Use group policies for self-hosted extension deployment |
| Jira API changes | Low | Medium | Implement version-aware client with graceful degradation |

## 9. Success Metrics & Evaluation

- **Efficiency:** Reduce manual task reminders by 80%
- **Adoption:** 100% of action items tracked via the extension
- **Usability:** Users can create, query, or complete tasks in under 30 seconds
- **Reliability:** Zero missed reminders for due tasks
- **Performance:** Chat response time under 2 seconds (with caching)

## 10. Deployment Plan

### 10.1 Server Deployment

- Deploy FastAPI server on intranet (Ubuntu or Windows server)
- Configure SQLite database
- Set up environment variables for API keys
- Implement health checks and monitoring

### 10.2 Extension Deployment

- Package extension as `.crx` file
- Configure enterprise policies for installation (`ExtensionInstallForceList`)
- Document installation process for end users

### 10.3 Post-Deployment

- Conduct user training sessions
- Monitor usage and performance
- Gather feedback for improvements
- Plan for maintenance and updates

## 11. Documentation Requirements

- **Technical Documentation:**
  - System architecture
  - API specifications
  - Database schema
  - Deployment instructions

- **User Documentation:**
  - Installation guide
  - User manual with examples
  - Common phrases and commands
  - Troubleshooting guide

## 12. Project Tracking & Reporting

- Use Taskmaster to track task status and progress
- Generate weekly status reports
- Conduct sprint reviews with demos
- Update project documentation as development progresses

## 13. Quality Assurance & Continuous Integration

- Implement pre-commit hooks for code quality checks
- Set up automated Playwright testing for UI components
- Run regression tests after each feature implementation
- Check and terminate lingering Playwright report server processes before running tests
- Address and fix any negative test results immediately
- Always check the problems window for issues and fix them before committing

## 14. Component Navigation & Responsiveness

- Ensure all UI components are properly linked for smooth navigation
- Implement responsive design for all buttons and interface elements
- Test UI across different screen sizes and resolutions
- Validate browser compatibility (primarily for Edge)
- Make all buttons and interactive elements responsive and user-friendly

## 15. Regular Plan Updates

This Project Management Plan is a living document that will be:
- Updated weekly to reflect task progress
- Revised as new tasks are discovered
- Expanded with learned implementation details
- Modified to address changing requirements or technical constraints
- Refreshed after each sprint review to capture new insights

## Appendix: Project Requirements References

- Product Requirements Document
- Software Requirements Specification
- User Interface Design Document
- Taskmaster Development Workflow Guide

## 8. Deployment & Publishing Plan

### 8.1 Extension Packaging Process

1. **Prepare for Deployment:**
   - Update version numbers in manifest.json and package.json
   - Run `npm run build` to create production build
   - Run `npm run pack:extension` to create distribution ZIP file

2. **Quality Checks:**
   - Run all tests with `npm test`
   - Validate manifest entries match Microsoft Edge requirements
   - Check that all permissions are properly declared
   - Verify icons are present in required sizes

3. **Edge Add-ons Store Submission:**
   - Create developer account on [Edge Add-ons Developer Dashboard](https://partner.microsoft.com/en-us/dashboard/microsoftedge/overview)
   - Submit extension package with required metadata
     - Title: Jira Action Items Chatbot
     - Description: Extended version of description from package.json
     - Privacy policy URL
     - Support URL
     - Screenshots of key features
     - Promo images
   - Submit for review
   - Address any feedback from Microsoft review team

4. **Post-Publication:**
   - Monitor usage statistics through dashboard
   - Collect user feedback for future improvements
   - Plan update schedule for feature enhancements

### 8.2 Server Deployment

1. **Server Requirements:**
   - Python 3.10+ environment
   - Port 8000 open on internal network
   - Access to Jira API from deployment server
   - Environment variables configured

2. **Deployment Options:**
   - On-premises deployment for high-security environments
   - Docker-based deployment for easier scaling
   - Cloud deployment for testing and public access

3. **Configuration:**
   - URL configuration in extension settings
   - Firewall access rules
   - API rate limiting and security measures

### 8.3 Maintenance Plan

- Regular updates to address security vulnerabilities
- Compatibility testing with Edge browser updates
- Performance monitoring and optimization
- Documentation updates with each new feature

---

This Project Management Plan will be updated as the project progresses, with special attention to implementation details, task management, and adapting to any changing requirements or technical constraints discovered during development. 