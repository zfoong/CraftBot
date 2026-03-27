---
name: living-ui-creator
description: Create custom Living UI applications with backend-first architecture. Scaffolds, develops, tests, and launches dynamic web apps with persistent state.
user-invocable: false
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

### Phase 8: Verify and Build

**CRITICAL: Read [VERIFY.md](references/VERIFY.md) and complete the verification checklist.**

You must verify:
1. **Build succeeds** - `npm run build` exits with code 0
2. **Backend works** - Models import without errors
3. **State persists** - Data survives page refresh
4. **UI quality** - Looks good, consistent, no visual bugs
5. **Features complete** - All user requirements met
6. **No errors** - Console is clean

```bash
# Verify backend
cd backend && python -c "from models import *; from routes import *; print('OK')"

# Build frontend
npm run build
```

**DO NOT proceed if build fails.** Fix all errors first.

### Phase 9: Update Documentation

**Edit: `LIVING_UI.md`**

Fill in all sections with implementation details.

### Phase 10: Notify Ready (MANDATORY)

**YOU MUST call `living_ui_notify_ready` to complete the task.**

**CRITICAL - project_id Parameter:**
- The `project_id` is in your **task instruction** (e.g., "Project ID: abc12345")
- **DO NOT use task session ID** - that's different
- The project_id is a short hex string like `c8cda731`

```
living_ui_notify_ready(
  project_id="<PROJECT_ID from task instruction>",
  url="http://localhost:<port from manifest.json>",
  port=<port from manifest.json>
)
```

## Common Mistakes

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

- [ ] Backend models defined in `backend/models.py`
- [ ] Backend routes added in `backend/routes.py`
- [ ] Frontend types defined in `frontend/types.ts`
- [ ] UI components built in `frontend/components/`
- [ ] Controller methods connect UI to backend
- [ ] **[VERIFY.md](references/VERIFY.md) checklist completed**
- [ ] `npm run build` **succeeds with exit code 0**
- [ ] `LIVING_UI.md` documentation updated
- [ ] **Verified project_id from task instruction** (NOT task session ID)
- [ ] **CALLED `living_ui_notify_ready` action**

## FORBIDDEN Actions

- NEVER use `metadata` as a column name in SQLAlchemy
- NEVER leave `npm run dev` or `npm run preview` running
- NEVER store important state only in React (use backend)
- NEVER start the production server yourself
- NEVER use `send_message` - this is a background task
- NEVER skip calling `living_ui_notify_ready`
- NEVER use the task session ID as the project_id parameter
- NEVER call `living_ui_notify_ready` if `npm run build` failed

## References

- [MVC-A Architecture](references/MVC-A.md) - When to use each layer, agent data access methods
- [Quality Standards](references/STANDARDS.md) - Professional standards for Living UIs
- [Code Examples](references/EXAMPLES.md) - Complete code examples for each phase
- [Verification Checklist](references/VERIFY.md) - QA checklist before launch (REQUIRED)
- [Troubleshooting](references/TROUBLESHOOTING.md) - Debug common issues
