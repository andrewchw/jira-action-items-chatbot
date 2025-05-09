User Interface Design Document
Layout Structure
Persistent right-hand sidebar within Microsoft Edge, always available while browsing.

Header: Project selector, user avatar, and SLA meter.

Main Chat Area: Conversational history between user and bot, with clear task threading.

Task Preview Panel: Collapsible section showing Jira issue details, status, and attachments.

Input Bar: Context-aware text input with auto-suggestions, file upload button, and quick action shortcuts.

Core Components
Conversational Chat Stream: Natural language interactions, bot responses, and actionable prompts.

Task Cards: Inline previews of Jira issues, with status, assignee, and due date.

Evidence Upload: Drag-and-drop or button-triggered file upload, with thumbnail preview.

SLA Meter: Visual progress bar indicating time left until due date.

Notification Center: In-sidebar and browser notifications for reminders and updates.

Interaction Patterns
Type or speak natural language commands to create, update, or query tasks.

Reply directly to reminders within the chat (e.g., “Done”, “Need extension”).

Drag-and-drop files into the chat to attach evidence to Jira issues.

Click task cards to expand for full Jira details or add comments.

Auto-suggestions for project IDs, assignees, and due dates as you type.

Visual Design Elements & Color Scheme
Modern, minimal look with clear separation between chat, tasks, and controls.

Color-coded status: Green (on track), Yellow (upcoming), Red (overdue) for SLA meter and task cards.

Soft blues and grays for backgrounds, with accent colors for actionable items and notifications.

Rounded corners and subtle shadows for cards and input fields to enhance focus.

Mobile, Web App, Desktop Considerations
Primary: Desktop Edge browser sidebar-optimized for vertical space and multitasking.

Responsive: Collapsible sidebar for smaller screens or split views.

Web App: Core chat and task features can be mirrored in a standalone web dashboard if needed.

Mobile: Not a primary focus, but chat and notifications should degrade gracefully if accessed via mobile Edge.

Typography
Sans-serif font (e.g., Segoe UI or Roboto) for clarity and modern feel.

Bold headings for sections (e.g., “Your Tasks Today”), regular weight for chat, and monospace for code snippets or commands.

Consistent sizing: Larger for headers, medium for chat, small for timestamps and metadata.

Accessibility
Keyboard navigation for all chat, input, and upload actions.

Screen reader support: ARIA labels for chat messages, task cards, and buttons.

High-contrast mode for visually impaired users.

Alt text for all uploaded evidence thumbnails.

Notification sounds and visual cues for important events, with user control to mute or adjust.