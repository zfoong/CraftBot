---
name: cli-anything
description: "Generate agent-native CLI harnesses for any GUI application using the CLI-Anything methodology, or discover and install pre-built CLIs via CLI-Hub."
metadata: {"clawdbot":{"emoji":"⚡","os":["darwin","linux","windows"],"requires":{"bins":["python"]}}}
---

# CLI-Anything Skill

CLI-Anything transforms any GUI application into an agent-native command-line interface. Use this skill when the user asks to:
- Generate a CLI harness for any software (GIMP, Blender, LibreOffice, etc.)
- Install or discover CLIs via CLI-Hub
- Refine or test an existing generated harness

---

## Quick Install (CLI-Hub)

For software that already has a pre-built harness:

```bash
pip install cli-anything-hub
cli-hub install <name>
```

Browse the full catalog: https://hkuds.github.io/CLI-Anything/

---

## Generate a New CLI Harness

Follow the **7-Phase Methodology** below. Work sequentially — each phase depends on the prior.

### Phase 1 — Codebase Analysis

Before writing code, study the target application:

```
- Identify the backend engine (separate from the GUI presentation layer)
- Map each GUI action to its underlying API or Python call
- Understand the data model and native file formats (e.g., .blend, ODF, SVG)
- Locate any existing CLI entry points or scripting interfaces
- Catalog the undo/redo and session management system
```

### Phase 2 — CLI Architecture Design

Choose one of:
- **Stateful REPL** — for interactive, session-based workflows
- **Subcommand CLI** — for scriptable, one-shot invocations
- **Both** — recommended; REPL wraps the subcommand interface

Design command groups that mirror the app's logical domains (e.g., `image`, `layer`, `export` for GIMP). Plan dual output: human-readable text and machine-readable `--json`.

### Phase 3 — Implementation

Directory layout:
```
cli_anything/              # Namespace package — NO __init__.py here
└── <software>/           # Sub-package — HAS __init__.py
    ├── __main__.py
    ├── README.md
    ├── <software>_cli.py
    ├── core/             # Domain modules wrapping the real software
    ├── utils/            # Shared utilities + repl_skin.py
    └── tests/
        ├── TEST.md
        ├── test_core.py
        └── test_full_e2e.py
```

**Critical rule**: The CLI MUST call the actual software for rendering and export — never reimplement the software's functionality in Python. Generate valid native project files and hand them to the real application backend.

Required patterns for every command:
- `--json` flag for machine-readable output
- Fail loudly with unambiguous error messages
- Introspection commands (`info`, `list`, `status`) for state inspection

Use the unified REPL skin (`repl_skin.py` from `cli-anything-plugin/repl_skin.py`) so all generated CLIs share a consistent interface.

### Phase 4 — Test Planning (write TEST.md Part 1)

Before any test code, document in `tests/TEST.md`:
- Test inventory and what each test covers
- Unit test plans (synthetic data, no external deps)
- E2E test plans (real software backend invoked)
- Realistic end-to-end workflow scenarios

### Phase 5 — Test Implementation

Four layers, all required:
1. **Unit tests** — synthetic data, deterministic, fast
2. **E2E native tests** — verify project file generation and structure
3. **E2E backend tests** — invoke the real software, check output exists with correct format (magic bytes, ZIP structure, pixel analysis, etc.)
4. **CLI subprocess tests** — install the CLI entry point, run full workflows end-to-end

**Never assume an export is correct because it ran without errors.** Validate outputs programmatically and print artifact paths for manual inspection.

### Phase 6 — Test Documentation (write TEST.md Part 2)

Append full `pytest` output and summary statistics to `TEST.md`.

### Phase 6.5 — SKILL.md Generation

Create `cli_anything/<software>/skills/SKILL.md` with:
- YAML frontmatter for agent discovery (`name`, `description`, `tags`, `requires`)
- All command groups and subcommands
- Usage examples for common workflows
- Agent-specific guidance for `--json` output and error handling

The REPL should print the absolute path to `SKILL.md` on startup so agents can find it.

### Phase 7 — Package & Install

```bash
# setup.py uses PEP 420 namespace packaging
cd cli_anything/<software>
pip install -e .

# Verify the CLI is on PATH
which cli-anything-<software>
cli-anything-<software> --help
```

Publish to PyPI when ready:
```bash
python -m build
twine upload dist/*
```

---

## Using a Generated CLI

```bash
# Interactive REPL (default when no subcommand given)
cli-anything-<software>

# One-shot subcommand with JSON output for agent consumption
cli-anything-<software> --json <command> [args]

# Help
cli-anything-<software> --help
cli-anything-<software> <command> --help
```

---

## Refining an Existing Harness

After initial generation, run a gap analysis:

```bash
# Broad refinement
/cli-anything:refine ./<software>

# Focused refinement on specific capabilities
/cli-anything:refine ./<software> "batch processing and filters"
```

Then re-run tests: `/cli-anything:test <software>`

---

## Supported Applications (Pre-built)

CLI-Anything has verified harnesses for 26+ applications:

| Category | Applications |
|---|---|
| Creative | GIMP, Blender, Inkscape, Krita, MuseScore |
| Office | LibreOffice, Zotero |
| Media | Audacity, OBS Studio, Kdenlive, Shotcut, VideoCaptioner |
| Diagramming | Draw.io, Mermaid |
| AI/ML | ComfyUI, Ollama, NotebookLM |
| Web/Cloud | Zoom, AdGuard Home, Exa |
| Dev Tools | Godot Engine, RenderDoc |

---

## Architecture Pitfalls

**The Rendering Gap** — project files may reference filters/effects that simple file readers ignore. Solution priority:
1. Use the app's native renderer
2. Build a translation layer for effect conversion
3. Generate a render script as fallback

**Testing with missing software** — tests MUST NOT skip or fake results when the target software is missing. They should fail loudly so the absence is visible.
