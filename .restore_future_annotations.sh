#!/usr/bin/env bash
# Restore `from __future__ import annotations` in files that lost it vs dev.
# For each file: find the line number after the module docstring in the dev version,
# then insert it in the same position in the working tree using Python (cross-platform safe).

set -euo pipefail

FILES=(
  "agent_core/core/impl/llm/cache/config.py"
  "agent_core/core/impl/llm/cache/metrics.py"
  "agent_core/core/impl/llm/errors.py"
  "agent_core/core/impl/llm/types.py"
  "agent_core/core/impl/memory/manager.py"
  "agent_core/core/llm/google_gemini_client.py"
  "agent_core/core/protocols/trigger.py"
  "agent_core/core/task/todo.py"
  "agent_core/core/trigger.py"
  "app/browser/interface.py"
  "app/cli/interface.py"
  "app/credentials/handlers.py"
  "app/external_comms/base.py"
  "app/external_comms/config.py"
  "app/external_comms/integration_settings.py"
  "app/external_comms/manager.py"
  "app/external_comms/platforms/google_workspace.py"
  "app/external_comms/platforms/linkedin.py"
  "app/external_comms/platforms/notion.py"
  "app/external_comms/platforms/outlook.py"
  "app/external_comms/platforms/slack.py"
  "app/external_comms/platforms/telegram_bot.py"
  "app/external_comms/platforms/telegram_user.py"
  "app/external_comms/platforms/twitter.py"
  "app/external_comms/platforms/whatsapp_bridge/client.py"
  "app/external_comms/platforms/whatsapp_business.py"
  "app/external_comms/platforms/whatsapp_web.py"
  "app/external_comms/registry.py"
  "app/ui_layer/commands/base.py"
  "app/ui_layer/commands/builtin/agent_command.py"
  "app/ui_layer/commands/builtin/clear.py"
  "app/ui_layer/commands/builtin/cred.py"
  "app/ui_layer/commands/builtin/exit.py"
  "app/ui_layer/commands/builtin/help.py"
  "app/ui_layer/commands/builtin/integrations.py"
  "app/ui_layer/commands/builtin/mcp.py"
  "app/ui_layer/commands/builtin/menu.py"
  "app/ui_layer/commands/builtin/provider.py"
  "app/ui_layer/commands/builtin/reset.py"
  "app/ui_layer/commands/builtin/skill.py"
  "app/ui_layer/commands/builtin/skill_invoke.py"
  "app/ui_layer/commands/builtin/update.py"
  "app/ui_layer/commands/executor.py"
  "app/ui_layer/events/event_bus.py"
  "app/ui_layer/events/event_types.py"
  "app/ui_layer/events/transformer.py"
  "app/ui_layer/onboarding/controller.py"
  "app/ui_layer/themes/base.py"
  "app/usage/action_storage.py"
  "app/usage/chat_storage.py"
  "app/usage/reporter.py"
  "app/usage/session_storage.py"
  "app/usage/storage.py"
  "app/usage/task_storage.py"
  "diagnostic/action_diagnose.py"
  "diagnostic/environments/create_and_run_python_script.py"
  "diagnostic/environments/create_pdf_file.py"
  "diagnostic/environments/find_file_by_name.py"
  "diagnostic/environments/find_in_file_content.py"
  "diagnostic/environments/ignore.py"
  "diagnostic/environments/keyboard_input.py"
  "diagnostic/environments/keyboard_typing.py"
  "diagnostic/environments/list_folder.py"
  "diagnostic/environments/mouse_drag.py"
  "diagnostic/environments/mouse_move.py"
  "diagnostic/environments/open_application.py"
  "diagnostic/environments/read_pdf_file.py"
  "diagnostic/environments/scroll.py"
  "diagnostic/environments/send_http_requests.py"
  "diagnostic/environments/send_message.py"
  "diagnostic/environments/shell_exec_windows.py"
  "diagnostic/environments/switch_to_cli_mode.py"
  "diagnostic/environments/trace_mouse.py"
  "diagnostic/environments/view_image.py"
  "diagnostic/environments/window_close.py"
  "diagnostic/framework.py"
  "mkdocs/scripts/gen_ref_pages.py"
  "skills/model-usage/scripts/model_usage.py"
  "skills/stock-market-pro/scripts/options_links.py"
)

ANNOTATION="from __future__ import annotations"
RESTORED=0
SKIPPED=0
ERRORS=0

for FILE in "${FILES[@]}"; do
  if [ ! -f "$FILE" ]; then
    echo "SKIP (not found): $FILE"
    ((SKIPPED++)) || true
    continue
  fi

  # Skip if annotation already present (e.g. vlm/interface.py which we kept)
  if grep -q "^from __future__ import annotations" "$FILE"; then
    echo "SKIP (already has it): $FILE"
    ((SKIPPED++)) || true
    continue
  fi

  # Get the line number of from __future__ import annotations in the dev version
  DEV_LINE=$(git show "dev:$FILE" 2>/dev/null | grep -n "^from __future__ import annotations" | head -1 | cut -d: -f1)

  if [ -z "$DEV_LINE" ]; then
    echo "SKIP (not in dev either): $FILE"
    ((SKIPPED++)) || true
    continue
  fi

  # Insert the annotation at that line number in the current file using Python
  python3 - "$FILE" "$DEV_LINE" "$ANNOTATION" <<'PYEOF'
import sys

filepath = sys.argv[1]
insert_at = int(sys.argv[2])  # 1-indexed line number from dev
annotation = sys.argv[3]

with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Insert at insert_at - 1 (0-indexed), preserving newlines
insert_idx = insert_at - 1
lines.insert(insert_idx, annotation + "\n")

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"OK: inserted '{annotation}' at line {insert_at} in {filepath}")
PYEOF

  ((RESTORED++)) || true
done

echo ""
echo "Done: $RESTORED restored, $SKIPPED skipped, $ERRORS errors."
