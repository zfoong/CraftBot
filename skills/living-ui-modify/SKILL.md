---
name: living-ui-modify
description: Modify existing Living UI applications - add features, fix bugs, update UI, change backend logic. Reads existing code, makes targeted changes, verifies, and restarts.
action-sets:
  - file_operations
  - code_execution
  - living_ui
---

# Living UI Modifier

Make changes to existing Living UI applications: add features, fix bugs, update UI components, modify backend logic, or restructure data models.

## Workflow

Follow these phases in order. Use TodoWrite to track progress.

### Phase 1: Identify the Living UI

Read the project registry:

```
File: agent_file_system/workspace/living_ui_projects.json
```

Each entry has: `id`, `name`, `path`, `status`, `port` (frontend), `backendPort` (backend API).

**Match by name** - fuzzy-match user's request against project names. If ambiguous, list projects and ask.

### Phase 2: Understand Current Implementation

Read these files **before making any changes**:

1. **`{project.path}/LIVING_UI.md`** - overview, data models, API endpoints, components
2. **Source files relevant to the change:**

| What to change | Read first |
|----------------|------------|
| Data models / DB schema | `backend/models.py` |
| API endpoints / backend logic | `backend/routes.py` |
| TypeScript types | `frontend/types.ts` |
| UI components | `frontend/components/MainView.tsx` and relevant component files |
| State management / API calls | `frontend/AppController.ts` |
| Port / project config | `config/manifest.json` |

Understand the existing patterns, naming conventions, and code style before editing.

### Phase 3: Plan Changes

Identify all files that need modification. Changes often cascade:

```
New data field  → models.py → routes.py → types.ts → AppController.ts → Component
New feature     → models.py → routes.py → types.ts → AppController.ts → New component → MainView.tsx
UI-only change  → Component file(s) only
Bug fix         → Whichever file has the bug
```

### Phase 4: Make Changes

#### Backend Changes

**Edit: `backend/models.py`**

- Add/modify SQLAlchemy models
- NEVER use `metadata` as column name (SQLAlchemy reserved)
- Always include `to_dict()` method for JSON serialization
- If adding a new model, new table is auto-created on restart

```python
# Adding a field to existing model
class Todo(Base):
    __tablename__ = "todos"
    # ... existing fields ...
    priority = Column(String(20), default="medium")  # NEW FIELD

    def to_dict(self):
        return {
            # ... existing fields ...
            "priority": self.priority,  # ADD TO DICT
        }
```

**Edit: `backend/routes.py`**

- Add/modify API endpoints
- If model name conflicts with Python built-ins, use alias: `from models import List as ListModel`
- Always call `db.commit()` after write operations
- Return proper HTTP status codes (404 for not found, etc.)

```python
# Adding a new endpoint
@router.post("/todos/{todo_id}/archive")
def archive_todo(todo_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo.archived = True
    db.commit()
    return todo.to_dict()
```

#### Frontend Changes

**Edit: `frontend/types.ts`**

- Keep TypeScript interfaces in sync with backend models
- Use camelCase in types (backend `to_dict()` should output camelCase)

```typescript
export interface Todo {
  id: number
  title: string
  priority: string  // NEW FIELD
}
```

**Edit: `frontend/AppController.ts`**

- Add methods for new backend endpoints
- Follow existing patterns for API calls and state updates

```typescript
async archiveTodo(id: number): Promise<void> {
  await fetch(`${this.backendUrl}/todos/${id}/archive`, { method: 'POST' })
  await this.fetchTodos()  // Refresh list
}
```

**Edit: `frontend/components/`**

- Modify existing or create new React components
- **Use preset UI components** - import from `./components/ui`:

| Category | Components |
|----------|------------|
| **Forms** | `Input`, `Textarea`, `Select`, `Checkbox`, `Toggle` |
| **Buttons** | `Button` (variants: primary, secondary, danger, ghost) |
| **Layout** | `Card`, `Container`, `Divider` |
| **Feedback** | `Alert`, `Badge`, `EmptyState` |
| **Data** | `Table`, `List`, `ListItem` |
| **Overlays** | `Modal`, `Tabs`, `TabList`, `Tab`, `TabPanel` |

```tsx
import { Button, Card, Badge, Modal } from './components/ui'
```

**Edit: `frontend/components/MainView.tsx`**

- Wire new components into the main view
- Connect event handlers to controller methods

### Phase 5: Verify

**CRITICAL: Verify before restarting.**

```bash
# 1. Check backend compiles
cd {project.path}/backend && python -c "from models import *; from routes import *; print('OK')"

# 2. Build frontend
cd {project.path} && npm run build
```

**Both must succeed.** If build fails, read the error, fix it, and retry. Do NOT proceed with a broken build.

### Phase 6: Restart

Use the `living_ui_restart` action to apply changes:

```
living_ui_restart(project_id="{project.id}")
```

This stops and relaunches both backend and frontend on the same ports.

**DO NOT** use `living_ui_notify_ready` - it skips projects that are already running.
**DO NOT** start uvicorn or npm preview manually.

### Phase 7: Update Documentation

**Edit: `{project.path}/LIVING_UI.md`**

Update the relevant sections:
- **Data Model** table if models changed
- **API Endpoints** table if routes changed
- **Frontend Components** table if components added/removed
- **Key Files** table if new files created

## Directory Structure

```
{project.path}/
├── backend/
│   ├── main.py          # FastAPI entry point (rarely edit)
│   ├── models.py        # SQLAlchemy models
│   ├── routes.py        # API endpoints
│   ├── database.py      # DB connection (rarely edit)
│   └── living_ui.db     # SQLite database
├── frontend/
│   ├── App.tsx           # Root component (rarely edit)
│   ├── AppController.ts  # State management & API calls
│   ├── types.ts          # TypeScript interfaces
│   ├── components/
│   │   ├── ui/index.tsx  # Preset components (DO NOT edit)
│   │   └── MainView.tsx  # Main UI component
│   ├── services/
│   │   ├── ApiService.ts # Backend HTTP client
│   │   └── UICapture.ts  # UI capture for agent (rarely edit)
│   └── styles/global.css # Design tokens (rarely edit)
├── config/manifest.json  # Ports and project metadata
└── LIVING_UI.md          # Documentation index
```

## FORBIDDEN Actions

- NEVER use `metadata` as a SQLAlchemy column name
- NEVER leave `npm run dev` or `npm run preview` running
- NEVER store important state only in React (use backend)
- NEVER start servers manually - use `living_ui_restart` action
- NEVER skip build verification before restarting
- NEVER edit `frontend/components/ui/index.tsx` (preset components)
- NEVER use `send_message` - this is a background task

## Quality Checklist

Before calling `living_ui_restart`:

- [ ] Backend imports pass: `python -c "from models import *; from routes import *"`
- [ ] Frontend builds: `npm run build` exits with code 0
- [ ] No TypeScript errors
- [ ] New endpoints handle errors (404 for not found, etc.)
- [ ] `to_dict()` updated if model fields changed
- [ ] Types in `types.ts` match backend output
- [ ] LIVING_UI.md updated with changes

## References

These reference files from the creator skill also apply to modifications:

- [Quality Standards](../living-ui-creator/references/STANDARDS.md) - UI, backend, and code quality standards
- [Code Examples](../living-ui-creator/references/EXAMPLES.md) - Complete code examples for each layer
- [Component Reference](../living-ui-creator/references/COMPONENTS.md) - Full preset component API reference
- [Troubleshooting](../living-ui-creator/references/TROUBLESHOOTING.md) - Common errors and fixes
- [Verification Checklist](../living-ui-creator/references/VERIFY.md) - Detailed QA checklist
