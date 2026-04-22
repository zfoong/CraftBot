# GUI / Vision mode

GUI mode lets CraftBot **see your desktop** and drive it with mouse and keyboard — like a human operator. The agent takes screenshots, asks a [VLM](../providers/vlm.md) where to click, and executes mouse/keyboard actions via `pyautogui`. It's how you get an agent that can operate apps with no API.

!!! warning "Experimental"
    GUI mode is still being hardened. Expect imprecision, especially on dense UIs. For most tasks, [browser](browser.md) or [TUI](tui.md) mode plus [integrations](../connections/index.md) get the job done without vision.

## Quick start

Install the GUI components (downloads ~4GB of model weights):

```bash
python install.py --gui
```

Then launch:

```bash
python run.py --gui
```

## Enable / disable

```json
// settings.json
{ "gui": { "enabled": true } }
```

When disabled, the agent loop's GUI branch is never entered — vision tasks fall back to text reasoning.

## Two pipelines

### Raw VLM

Send the full screenshot to a VLM (Claude, GPT-4o, Gemini, etc.) with a prompt asking "where should I click to accomplish X?" — the VLM returns pixel coordinates or a structured action.

Simpler to set up, but pricey per call and less accurate on dense UIs.

### OmniParser pipeline

```json
{ "gui": { "use_omniparser": true, "omniparser_url": "http://127.0.0.1:7861" } }
```

[OmniParser](https://github.com/microsoft/OmniParser) runs as a separate Gradio server. Pipeline:

1. Screenshot → OmniParser returns structured elements (buttons, labels, icons with bounding boxes).
2. VLM reasons over the **structured element list** (not raw pixels).
3. VLM returns element id or coordinates.
4. Mouse/keyboard executes.

More accurate, cheaper per VLM call, but needs OmniParser running.

## Workflow

GUI tasks enter a special loop (see [Special workflows](../modes/special-workflows.md)):

1. `_is_gui_task_mode()` — returns true when task is complex AND `STATE.gui_mode == True`
2. Each iteration calls `GUIHandler.gui_module.perform_gui_task_step(...)`
3. Inside `perform_gui_task_step`:
   - Take screenshot
   - Call VLM (raw or OmniParser path)
   - Parse the action: `click(x, y)`, `type("text")`, `drag(x1,y1,x2,y2)`, `scroll`, or `screenshot` (no-op for observing)
   - Execute via `pyautogui`
   - Log `action_start` / `action_end` to the [event stream](../concepts/event-stream.md)
4. Repeat until the task's current todo is complete

## GUI action space

| Action | Inputs |
|---|---|
| `click` | `x`, `y`, `button` (`left`/`right`/`middle`) |
| `double_click` | `x`, `y` |
| `type` | `text` |
| `key` | key name (`enter`, `tab`, `ctrl+c`, …) |
| `drag` | `x1, y1, x2, y2` |
| `scroll` | `direction`, `amount` |
| `screenshot` | — (for observation) |

Defined by `GUI_ACTION_SPACE_PROMPT` in the [prompt registry](../concepts/prompt.md).

## Dependencies

`python install.py --gui` installs:

- `pyautogui` — mouse/keyboard control
- `mss` — fast screenshots
- `Pillow` — image processing
- Platform-specific X11 utils on Linux
- OmniParser weights (~4GB, optional)

Release builds can bundle these. For CPU-only systems: `python install.py --gui --cpu-only`.

## Requirements

- A graphical display (X11 on Linux, native on macOS/Windows, or Xvfb in Docker).
- A VLM-capable provider ([see VLM providers](../providers/vlm.md)).
- **Optional:** OmniParser on port 7861.

## Docker / headless

For running GUI mode in a container, use a virtual framebuffer:

```bash
docker run --rm -it --env-file .env craftbot \
  bash -lc "Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99 && exec python run.py --gui"
```

Or attach to your host display on Linux:

```bash
docker run --rm -it \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  craftbot python run.py --gui
```

## Security considerations

GUI mode gives the agent full control over your mouse and keyboard. Don't leave it running unattended on a desktop with sensitive apps open unless you're sure the task scope is safe.

## Related

- [VLM providers](../providers/vlm.md) — the models that see the screen
- [Special workflows](../modes/special-workflows.md) — the GUI workflow handler
- [settings.json `gui.*`](../configuration/config-json.md) — full config
- [Install](../start/install.md) — `--gui` flag
