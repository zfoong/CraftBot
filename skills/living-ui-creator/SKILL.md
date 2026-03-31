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

## UI Component Presets (USE THESE)

Living UI includes **pre-built components** matching CraftBot design. **Use these by default** instead of creating custom styles.

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
- Use preset components for all standard UI needs
- Customize via props, not custom CSS
- Combine components for complex layouts

**DON'T:**
- Create custom buttons, inputs, or cards
- Add inline styles for basic styling
- Build custom modal or alert systems

See [COMPONENTS.md](references/COMPONENTS.md) for full component reference.

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

### Phase 1: Understand Requirements

Read the project description and identify:
- Data entities needed (boards, cards, items, etc.)
- User actions (create, update, delete, etc.)
- UI layout

**IMPORTANT:** document requirement in LIVING_UI.md.

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

### Phase 9: Update Documentation

**Edit: `LIVING_UI.md`**

Fill in all sections with implementation details.

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
- NEVER use `send_message` - this is a background task
- NEVER skip calling `living_ui_notify_ready`
- NEVER use the task session ID as the project_id parameter

## References

- [MVC-A Architecture](references/MVC-A.md) - When to use each layer, agent data access methods
- [Quality Standards](references/STANDARDS.md) - Professional standards for Living UIs
- [Code Examples](references/EXAMPLES.md) - Complete code examples for each phase
- [Verification Checklist](references/VERIFY.md) - QA checklist before launch (REQUIRED)
- [Troubleshooting](references/TROUBLESHOOTING.md) - Debug common issues
