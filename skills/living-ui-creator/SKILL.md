---
name: living-ui-creator
description: Create custom Living UI applications with MVC-A architecture. Scaffolds, develops, tests, and launches dynamic agent-aware user interfaces.
user-invocable: false
action-sets:
  - file_operations
  - code_execution
---

# Living UI Creator

Create dynamic, agent-aware user interfaces that the CraftBot agent can see and interact with.

## Architecture: MVC-A (Model-View-Controller-Agent)

Living UIs extend standard MVC with an Agent layer:
- **Model** (`src/models/`): Data structures and state types
- **View** (`src/views/`): React components that render the UI
- **Controller** (`src/controllers/`): Business logic and user interactions
- **Agent** (`src/agent/`): Bridge to CraftBot for state reporting and commands

## Project Information

The project path is provided in the task instruction. All edits should be within this path.

**Key template files to customize:**
- `config/manifest.json` - Project metadata (already customized)
- `src/models/types.ts` - Data type definitions
- `src/views/MainView.tsx` - Main UI component
- `src/controllers/AppController.ts` - Business logic
- `src/agent/AgentBridge.ts` - Agent connection (pre-configured)
- `src/agent/hooks.ts` - React hooks for agent awareness

## Todo Tracking (REQUIRED)

Use `task_update_todos` to track progress through each phase:

```
1. [pending] Analyze requirements and plan implementation
2. [pending] Design data models (src/models/types.ts)
3. [pending] Create view components (src/views/)
4. [pending] Implement controller logic (src/controllers/)
5. [pending] Configure agent awareness
6. [pending] Test the application
7. [pending] Build for production
8. [pending] Call living_ui_notify_ready action (MUST call this action!)
```

**IMPORTANT:** For step 8, you must ACTUALLY CALL the `living_ui_notify_ready` action.
Do NOT mark it completed until the action has been executed successfully.

## Development Workflow

### Phase 1: Requirements Analysis
1. Read the project description from task instruction
2. Identify key data structures needed
3. Plan the UI layout and components
4. Update todos with implementation plan

### Phase 2: Model Design
1. Open `src/models/types.ts`
2. Define TypeScript interfaces for your data:

```typescript
// Example: News Dashboard
export interface NewsItem {
  id: string
  title: string
  source: string
  summary: string
  url: string
  publishedAt: number
  category: string
}

export interface DashboardState {
  news: NewsItem[]
  selectedCategory: string | null
  loading: boolean
  lastUpdated: number
}
```

### Phase 3: View Development
1. Create React components in `src/views/`
2. Use `useAgentAware` hook for components the agent should track:

```typescript
import { useAgentAware } from '../agent/hooks'

export function NewsList({ items }: { items: NewsItem[] }) {
  // Register this component's state with agent
  useAgentAware('NewsList', {
    itemCount: items.length,
    items: items.map(i => i.title),
  })

  return (
    <ul>
      {items.map(item => (
        <li key={item.id}>{item.title}</li>
      ))}
    </ul>
  )
}
```

3. Follow design guidelines:
   - Use CSS variables from `src/styles/global.css`
   - Responsive design (mobile-first)
   - Loading states for async operations
   - Error handling with user-friendly messages

### Phase 4: Controller Implementation
1. Open `src/controllers/AppController.ts`
2. Implement business logic:

```typescript
export class AppController {
  // Add methods for:
  // - Data fetching
  // - State management
  // - User action handlers

  async fetchNews(): Promise<NewsItem[]> {
    // Fetch from API or generate mock data
  }

  handleCategoryChange(category: string): void {
    // Filter news by category
  }
}
```

### Phase 5: Agent Awareness
1. Configure `AgentBridge` connection (pre-configured in template)
2. Register important components with `useAgentAware`
3. Handle agent commands in `AppController`:

```typescript
handleAgentCommand(command: AgentCommand): void {
  switch (command.type) {
    case 'refresh':
      this.fetchNews()
      break
    case 'action':
      if (command.payload.action === 'selectCategory') {
        this.handleCategoryChange(command.payload.category as string)
      }
      break
  }
}
```

### Phase 6: Testing
1. Install dependencies: Run `npm install` in project directory
2. Start dev server: Run `npm run dev` (in background or check quickly)
3. Verify:
   - UI renders correctly
   - Data loads (mock or real)
   - User interactions work
   - No TypeScript/build errors
4. Fix any issues found
5. **IMPORTANT: Stop the dev server after testing** - Do NOT leave it running!

### Phase 7: Build for Production
1. Build for production: `npm run build`
2. Verify build succeeds with no errors
3. **DO NOT start the preview server yourself** - The system will launch it automatically

### Phase 8: Notify Ready (MANDATORY)
**YOU MUST call the `living_ui_notify_ready` action to complete this task.**

This is NOT optional. The Living UI will NOT launch until you call this action.
DO NOT mark the "Notify browser UI is ready" todo as completed until you have ACTUALLY CALLED the action.

```
living_ui_notify_ready(
  project_id="<from task instruction>",
  url="http://localhost:<port from manifest.json>",
  port=<port from manifest.json>
)
```

**Example for project with port 3100:**
```
living_ui_notify_ready(
  project_id="b022f7bb",
  url="http://localhost:3100",
  port=3100
)
```

After calling `living_ui_notify_ready`, the system will automatically launch the Living UI server.

**CRITICAL REMINDERS:**
- You MUST call `living_ui_notify_ready` action explicitly - just marking a todo as completed does NOT notify the system
- Do NOT run `npm run preview` or `npm run dev` and leave it running - it blocks the task session
- The system handles server launching - you just need to build and call the notify action

## Code Quality Standards

- TypeScript strict mode
- No `any` types unless absolutely necessary
- Proper error handling with try/catch
- Loading states for all async operations
- Meaningful variable and function names
- Comments for complex logic only

## Agent Awareness Requirements

Every Living UI MUST:
1. Connect to CraftBot WebSocket on startup (pre-configured)
2. Report state at configured interval (default 1s)
3. Include visible text content in state reports
4. Report all user input values
5. Handle agent commands gracefully

## Data Fetching Options

### Option 1: Mock Data
Generate realistic mock data for demonstration:

```typescript
const mockNews: NewsItem[] = [
  {
    id: '1',
    title: 'Breaking: New AI Breakthrough',
    source: 'Tech News',
    summary: 'Researchers announce...',
    url: '#',
    publishedAt: Date.now(),
    category: 'technology',
  },
  // More items...
]
```

### Option 2: Real API
If data source is provided in task:

```typescript
async fetchFromAPI(): Promise<NewsItem[]> {
  const response = await fetch('https://api.example.com/news')
  const data = await response.json()
  return data.articles.map(transformToNewsItem)
}
```

### Option 3: Backend API
If using the Python backend:
1. Uncomment code in `backend/main.py`
2. Run `pip install -r requirements.txt`
3. Start with `python backend/main.py`

## FORBIDDEN Actions

- NEVER hardcode API keys or secrets
- NEVER expose sensitive data in state reports
- NEVER modify files outside the project directory
- NEVER skip testing phase
- NEVER use `send_message` - this is a background task
- NEVER leave `npm run dev` or `npm run preview` running - it blocks the task session!
- NEVER start the production server yourself - the system handles this automatically

## Example: Todo List Living UI

Given: "Create a simple todo list with add, complete, and delete"

**Models:**
```typescript
interface Todo {
  id: string
  text: string
  completed: boolean
}
```

**Views:**
- TodoList.tsx - Renders list
- TodoItem.tsx - Single item with checkbox/delete
- AddTodoForm.tsx - Input form

**Controller:**
- addTodo(text: string)
- toggleTodo(id: string)
- deleteTodo(id: string)

**Agent awareness:**
- Report: todoCount, completedCount, items (titles only)
- Handle: refresh, add, complete, delete commands

## Progress Reporting

Report progress using `living_ui_report_progress`:

```
living_ui_report_progress(
  project_id="<id>",
  phase="coding",
  progress=50,
  message="Implementing view components..."
)
```

Phases: `initializing`, `scaffolding`, `coding`, `testing`, `building`, `launching`

## Completion Checklist

Before calling `living_ui_notify_ready`:

- [ ] All required components implemented
- [ ] Data fetching/mock data working
- [ ] User interactions functional
- [ ] Agent awareness configured
- [ ] No TypeScript errors
- [ ] No console errors
- [ ] Build successful (`npm run build` completed without errors)
- [ ] Dev server stopped (not running)

**FINAL STEP - DO NOT SKIP:**
- [ ] CALLED `living_ui_notify_ready` action with project_id, url, and port
- [ ] Received success response from the action

Only call `task_end` AFTER `living_ui_notify_ready` returns success.
