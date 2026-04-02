---
name: living-ui-creator
description: Create custom Living UI applications with backend-first architecture. Scaffolds, develops, tests, and launches dynamic web apps with persistent state.
action-sets:
  - file_operations
  - code_execution
---

# Living UI Creator

Create interactive web applications that persist state and survive page reloads.

## Architecture Overview

Living UI uses a **backend-first, stateless frontend** pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│   BACKEND (FastAPI + SQLite)                                    │
│   Location: backend/                                            │
│   - THE source of truth for ALL application state               │
│   - Persists data to SQLite database                            │
│   - Exposes REST API at http://localhost:<backend_port>         │
│   - State survives page reloads and tab switches                │
├─────────────────────────────────────────────────────────────────┤
│   FRONTEND (React + TypeScript)                                 │
│   Location: frontend/                                           │
│   - Stateless view layer - fetches state FROM backend           │
│   - Sends user actions TO backend                               │
│   - Uses localStorage as cache only (fallback)                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Principle**: Frontend is a dumb view. Backend owns all state.

## Architecture Decision

Before coding, determine what your app needs:

| Need | Solution |
|------|----------|
| Persist user data | Database models (SQLite) |
| Fetch external data | Backend proxy endpoint |
| Agent provides data | `PUT /api/state` to push data |
| Agent reads app data | `GET /api/state` endpoint |
| Agent observes UI | `GET /api/ui-snapshot` (auto-captured) |
| Agent sees visually | `GET /api/ui-screenshot` |
| Agent triggers actions | `POST /api/action` |
| Complex UI state | Multiple frontend components |

**Default:** Most apps need all layers (DB + Backend + Frontend).
**Agent APIs are built-in** - no extra work needed.

See [MVC-A.md](references/MVC-A.md) for detailed architecture guidance.

## Directory Structure

```
project_root/
├── backend/                    # Python FastAPI backend
│   ├── main.py                 # FastAPI app entry point (rarely edit)
│   ├── models.py               # SQLAlchemy models - EDIT THIS for data
│   ├── routes.py               # API endpoints - EDIT THIS for actions
│   ├── database.py             # DB connection (rarely edit)
│   └── living_ui.db            # SQLite database (auto-created)
│
├── frontend/                   # React TypeScript frontend
│   ├── main.tsx                # Entry point (rarely edit)
│   ├── App.tsx                 # Main app component
│   ├── AppController.ts        # State management & backend communication
│   ├── types.ts                # TypeScript interfaces - EDIT THIS
│   ├── components/             # React components - EDIT/ADD HERE
│   │   ├── ui/                 # Pre-built UI components (USE THESE)
│   │   │   └── index.tsx       # Button, Card, Input, Modal, etc.
│   │   └── MainView.tsx        # Main UI component
│   ├── services/               # API & UI capture (rarely edit)
│   │   ├── ApiService.ts       # Backend API client
│   │   └── UICapture.ts        # UI snapshot/screenshot for agent
│   └── styles/global.css       # CraftBot design tokens
│
├── config/manifest.json        # Project metadata (port info here)
├── index.html
├── package.json
├── vite.config.ts
└── LIVING_UI.md                # Project documentation - UPDATE THIS
```

## UI Component Presets (MANDATORY)

**CRITICAL:** Living UI includes pre-built components with professional styling. You MUST use these for ALL standard UI elements. Do NOT create custom buttons, inputs, cards, modals, or alerts. Do NOT write custom CSS for elements that have a preset component. The preset components use CraftBot's design tokens and ensure visual consistency.

**If you need a button, use `<Button>`. If you need a card, use `<Card>`. If you need an input, use `<Input>`. No exceptions.**

### Import
```typescript
import { Button, Card, Input, Alert, Table, Modal } from './components/ui'
```

### Available Components

| Category | Components |
|----------|------------|
| **Forms** | `Input`, `Textarea`, `Select`, `Checkbox`, `Toggle` |
| **Buttons** | `Button` (variants: primary, secondary, danger, ghost) |
| **Layout** | `Card`, `Container`, `Divider` |
| **Feedback** | `Alert`, `Badge`, `EmptyState` |
| **Data** | `Table`, `List`, `ListItem` |
| **Overlays** | `Modal`, `Tabs`, `TabList`, `Tab`, `TabPanel` |

### Quick Examples

```tsx
// Button variants
<Button variant="primary">Save</Button>
<Button variant="danger">Delete</Button>
<Button variant="ghost" size="sm">Cancel</Button>

// Form with validation
<Input label="Email" type="email" error="Invalid email" />
<Select label="Role" options={[{value: 'admin', label: 'Admin'}]} />

// Alert
<Alert variant="success" title="Saved!">Changes have been saved.</Alert>

// Table
<Table
  columns={[
    { key: 'name', header: 'Name' },
    { key: 'status', header: 'Status', render: (item) => <Badge>{item.status}</Badge> }
  ]}
  data={items}
/>

// Modal
<Modal open={show} onClose={() => setShow(false)} title="Confirm">
  Are you sure?
</Modal>
```

### Best Practices

**DO:**
- Use preset components for ALL standard UI needs — buttons, inputs, cards, modals, alerts, tables
- Customize via props (variant, size, etc.), not custom CSS
- Combine preset components for complex layouts
- Use `global.css` design tokens (e.g., `var(--color-primary)`) for any custom styling needed

**DON'T — these will result in an ugly, inconsistent UI:**
- Create custom buttons, inputs, cards, or modals (use the presets)
- Write inline styles or custom CSS for standard elements
- Use raw HTML elements like `<button>` or `<input>` (use `<Button>` and `<Input>`)
- Pick arbitrary colors (use design tokens from `global.css`)
- Build your own alert, notification, or modal system (use presets + react-toastify)

See [COMPONENTS.md](references/COMPONENTS.md) for full component reference.

### Toast Notifications (react-toastify)

Use `react-toastify` for user feedback — it's pre-installed and the `<ToastContainer />` is already in `App.tsx`.

```tsx
import { toast } from 'react-toastify'

// Success — auto-dismisses after 3 seconds
toast.success('Item created successfully')

// Error — auto-dismisses after 3 seconds
toast.error('Failed to save changes')

// Info
toast.info('Changes saved')

// Warning
toast.warn('This action cannot be undone')
```

**Always use toasts for:**
- CRUD operation feedback (created, updated, deleted)
- Error messages from failed API calls
- Important state changes the user should know about

**Don't use toasts for:**
- Validation errors (show inline next to the field instead)
- Loading states (use spinners/skeletons)

## Agent API (Built-in)

Living UI provides standard HTTP endpoints for agent observation:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ui-snapshot` | GET | UI state (DOM, text, form values) |
| `/api/ui-screenshot` | GET | Visual screenshot (PNG base64) |
| `/api/state` | GET/PUT | Application data |
| `/api/action` | POST | Trigger actions |

Frontend auto-captures UI state on meaningful events (page load, state changes, user interactions). See [MVC-A.md](references/MVC-A.md) for details.

## Development Workflow

Follow these phases in order. Use TodoWrite to track progress.

### Before You Start: Read Global Config

Read `agent_file_system/GLOBAL_LIVING_UI.md` for global design preferences and rules that apply to ALL Living UI projects. Apply all enabled rules (`[x]`) as requirements. Per-project requirements from Phase 0 Q&A override global settings when they conflict.

### Phase 0: Requirement Gathering (MANDATORY — minimum 2 batches)

Before coding, gather requirements from the user through a conversational interview.
Use `send_message` with `wait_for_user_reply=True` to ask questions and wait for answers.

**Reference:** Read [QUESTIONNAIRE.md](references/QUESTIONNAIRE.md) for question categories and examples.

**CRITICAL RULES:**
- You MUST ask at least 2 batches of questions. Never skip to coding after just 1 batch.
- Batch 1 MUST cover data/features. Batch 2 MUST cover design/visual preferences.
- If the user gives short or vague answers, DO NOT skip Batch 2. Instead, offer specific choices (e.g., "Would you prefer a card grid or a kanban column layout?").
- If the user explicitly says "just build it" or "skip the questions" — then and ONLY then can you stop early. A short answer to one question is NOT "skip."

**Process:**

1. **Analyze the project description** — identify what's clear and what's ambiguous
2. **Batch 1: Data & Features (REQUIRED)** — ask 2-4 questions:
   - Open with a warm acknowledgment of the project idea
   - Focus on: what entities/items exist, how they relate, what operations are needed
   - Use `send_message` with `wait_for_user_reply=True`
3. **Batch 2: Design & Layout (REQUIRED)** — always ask this, even if Batch 1 answers were short:
   - Acknowledge Batch 1 answers briefly
   - Focus on: layout style (grid/kanban/list/freeform), visual style, color preferences, detail views vs modals
   - Offer concrete choices rather than open-ended questions (e.g., "Card grid like Pinterest, or columns like Trello?")
   - Use `send_message` with `wait_for_user_reply=True`
4. **Batch 3 (optional)** — only if significant gaps remain after Batch 2
5. **Fill gaps with assumptions** — after gathering answers:
   - State your assumptions explicitly to the user
   - See "Safe Assumptions" in QUESTIONNAIRE.md for defaults
6. **Document in LIVING_UI.md (MANDATORY)** — you MUST fill in the Requirements section NOW, before moving to Phase 1:
   - Fill in ALL subsections: Entities & Data Model, Layout & Design, Features, Assumptions
   - Replace ALL HTML comments (`<!-- ... -->`) with actual content
   - Replace ALL example/placeholder data with real data
   - This becomes the source of truth for all subsequent phases
   - **DO NOT proceed to Phase 1 until LIVING_UI.md has real content**

**When to stop asking:**
- After Batch 2, unless there are major gaps (then do Batch 3)
- If user explicitly says "just build it" or "skip" — stop and assume the rest
- Never ask more than 3 batches total

**Tone:** Warm and conversational. Offer concrete choices, not just open-ended questions. Acknowledge answers before asking more.

**Example Batch 1 (Data & Features):**
> "Love the idea! Before I start building, a few quick questions about what goes on the board:
> 1. What kinds of items will you add? (notes, images, videos, links, docs — all of these?)
> 2. What info should each item have? (just the content, or also title, description, tags, status?)
> 3. Do you need to organize items into categories or groups?"

**Example Batch 2 (Design & Layout):**
> "Thanks! Now a couple questions about how it should look:
> 1. Layout preference — card grid (like Pinterest), columns (like Trello), or a list view?
> 2. When you click an item, should it open in a detail panel on the side, a full modal, or expand in place?
> 3. Any color/visual preference? (dark theme, light, colorful, minimal — or I'll use a clean modern default)"

### Phase 1: Plan Implementation

Read the requirements documented in LIVING_UI.md (from Phase 0) and plan:
- Data entities needed (models, fields, relationships)
- User actions (create, update, delete, etc.)
- UI layout and component structure

If Phase 0 was skipped (e.g., requirements are already very detailed in the description),
document them in LIVING_UI.md now before proceeding.

### Phase 2: Define Backend Models

**Edit: `backend/models.py`**

- Define SQLAlchemy models for your data
- NEVER use `metadata` as column name (reserved by SQLAlchemy)
- Always include `to_dict()` method for JSON serialization
- Use `extra_data` for flexible JSON columns

### Phase 3: Define Backend Routes

**Edit: `backend/routes.py`**

- Add API endpoints for CRUD operations
- If model name conflicts with Python built-ins, use alias:
  ```python
  from models import List as ListModel  # Avoid shadowing typing.List
  ```

### Phase 4: Define Frontend Types

**Edit: `frontend/types.ts`**

Define TypeScript interfaces matching backend models.

### Phase 5: Build UI Components

**Edit: `frontend/components/`**

Create React components. Main entry point is `MainView.tsx`.

### Phase 6: Connect Frontend to Backend

**Edit: `frontend/AppController.ts`**

Add methods to call your backend APIs.

### Phase 7: Update MainView

**Edit: `frontend/components/MainView.tsx`**

Wire up UI to use the controller.

### Phase 8: Review Code

Review your code for correctness before proceeding:
- Backend routes use **absolute imports** (`from models import ...` NOT `from . import ...`)
- Backend `routes.py` does NOT add `/api` prefix to route paths (the `main.py` router prefix handles this)
- All `to_dict()` methods return all fields
- TypeScript types in `types.ts` match backend model output
- Components import correctly from relative paths

**DO NOT run:** `npm run dev`, `npm run build`, `npm run preview`, or `uvicorn` manually.
The launch pipeline handles all building, testing, and serving automatically.

### Phase 9: Update Documentation (MANDATORY)

**Edit: `LIVING_UI.md`** — you MUST update ALL sections with real implementation details:

- **Overview**: What the app does, who it's for
- **Data Model table**: List every SQLAlchemy model with purpose and key fields (replace example rows)
- **API Endpoints table**: List every custom route with method, path, description (replace example rows)
- **Frontend Components table**: List every component with purpose
- **Key Files table**: Update if you added new files
- Remove ALL HTML comments (`<!-- ... -->`) and placeholder/example data
- **DO NOT proceed to Phase 10 if LIVING_UI.md still has placeholder content**

### Phase 10: Launch (MANDATORY)

**YOU MUST call `living_ui_notify_ready` to complete the task.**

This action runs the full launch pipeline automatically:
- Installs backend dependencies (`pip install -r requirements.txt`)
- Runs import validation, unit tests, and frontend-backend compatibility checks
- Starts the backend server and verifies health
- Runs external smoke tests against the running backend
- Installs frontend dependencies and builds (`npm install && npm run build`)
- Starts the frontend server

If any step fails, the action returns the specific errors. Fix them and call again.

**CRITICAL - project_id Parameter:**
- The `project_id` is in your **task instruction** (e.g., "Project ID: abc12345")
- **DO NOT use task session ID** - that's different
- The project_id is a short hex string like `c8cda731`

```
living_ui_notify_ready(project_id="<PROJECT_ID from task instruction>")
```

## Debugging & Logs

When something goes wrong, check these log files in the project directory:

| Log File | Contains |
|----------|----------|
| `backend/logs/subprocess_output.log` | Uvicorn startup output, crashes, stack traces |
| `backend/logs/backend_*.log` | Backend app-level logs (requests, errors, SQL) |
| `backend/logs/frontend_console.log` | Frontend console errors, warnings, app logs, and network requests (fetch method, URL, status, request/response bodies) |
| `backend/logs/health_status.json` | Health checker status (last check, failures) |
| `backend/logs/test_discovery.json` | Pre-launch test results (imports, routes, models) |
| `backend/logs/test_results.json` | External smoke test results |
| `logs/frontend_output.log` | Vite preview server output |

**Read these logs first** when debugging launch failures or runtime issues.

## Common Mistakes

- **Relative imports** — NEVER use `from . import models` or `from .models import ...` in backend code. Use absolute imports: `from models import ...`
- **Double /api prefix** — Routes in `routes.py` should NOT have `/api` prefix (e.g., use `@router.get("/items")` not `@router.get("/api/items")`). The prefix is added by `main.py`'s `include_router`.
- **Running servers manually** — NEVER start uvicorn, npm run dev, or npm run preview. The pipeline handles this.

See [TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) for more debugging help.

## Files Summary

| File | Purpose | When to Edit |
|------|---------|--------------|
| `backend/models.py` | Database models | Define data entities |
| `backend/routes.py` | API endpoints | Add CRUD operations |
| `frontend/types.ts` | TypeScript types | Match backend models |
| `frontend/components/` | UI components | Build the interface |
| `frontend/AppController.ts` | State management | Connect UI to backend |
| `LIVING_UI.md` | Documentation | Document your app |

## Quality Standards

Every Living UI must meet these standards:

### Must Have (Blocking)
- [ ] Data persists across page refreshes
- [ ] UI is responsive (works at 320px mobile width)
- [ ] Loading states for async operations
- [ ] Error handling with user feedback
- [ ] No console errors
- [ ] Build succeeds (exit code 0)

### Should Have (Quality)
- [ ] Empty states when no data
- [ ] Confirmation for destructive actions
- [ ] Keyboard navigation works
- [ ] Consistent visual design

See [STANDARDS.md](references/STANDARDS.md) for complete quality checklist.

## Completion Checklist

Before calling `living_ui_notify_ready`:

- [ ] Backend models defined in `backend/models.py` (absolute imports only)
- [ ] Backend routes added in `backend/routes.py` (no `/api` prefix on route paths)
- [ ] Frontend types defined in `frontend/types.ts`
- [ ] UI components built in `frontend/components/`
- [ ] Controller methods connect UI to backend
- [ ] `LIVING_UI.md` documentation updated
- [ ] **Verified project_id from task instruction** (NOT task session ID)
- [ ] **CALLED `living_ui_notify_ready` action** (pipeline handles build/test/launch)

## FORBIDDEN Actions

- NEVER use `metadata` as a column name in SQLAlchemy
- NEVER use relative imports in backend code (`from . import` or `from .models import`)
- NEVER add `/api` prefix to route paths in `routes.py` (the router prefix handles this)
- NEVER run `npm run dev`, `npm run build`, `npm run preview`, or `uvicorn` manually
- NEVER store important state only in React (use backend)
- NEVER use raw HTML elements (`<button>`, `<input>`, `<select>`) — use preset components (`<Button>`, `<Input>`, `<Select>`)
- NEVER write custom CSS for buttons, cards, inputs, modals, or alerts — use the preset component props
- NEVER pick arbitrary colors — use design tokens from `global.css` (e.g., `var(--color-primary)`)
- NEVER skip Phase 0 Batch 2 (design questions) — minimum 2 batches required
- ONLY use `send_message` during Phase 0 (Requirement Gathering) with `wait_for_user_reply=True`. NEVER use it during development phases (Phase 1-10).
- NEVER edit `config/manifest.json` (managed by the system, contains pipeline config)
- NEVER edit `backend/main.py` (managed by the system, contains server setup)
- NEVER edit `frontend/main.tsx` (managed by the system, contains service initialization)
- NEVER leave LIVING_UI.md with placeholder content, HTML comments, or example data
- NEVER skip calling `living_ui_notify_ready`
- NEVER use the task session ID as the project_id parameter

## References

- [Requirement Questionnaire](references/QUESTIONNAIRE.md) - Reference questions for Phase 0
- [MVC-A Architecture](references/MVC-A.md) - When to use each layer, agent data access methods
- [Quality Standards](references/STANDARDS.md) - Professional standards for Living UIs
- [Code Examples](references/EXAMPLES.md) - Complete code examples for each phase
- [Verification Checklist](references/VERIFY.md) - QA checklist before launch (REQUIRED)
- [Troubleshooting](references/TROUBLESHOOTING.md) - Debug common issues
