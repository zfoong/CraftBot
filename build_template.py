"""
Build an E2B desktop template for CraftBot.

Usage:
    pip install e2b python-dotenv

    # Build the CraftBot template:
    python build_template.py

    # Build with a custom name:
    python build_template.py --name my-craftbot

The template will appear in your E2B dashboard under Templates.
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# -- Configuration -----------------------------------------------------------

E2B_API_KEY = "E2B_API_KEY"

CRAFTBOT_DIR = Path(__file__).parent

DEFAULT_TEMPLATE_NAME = "craftbot"

SYSTEM_PACKAGES = [
    "build-essential",
    "pkg-config",
    "tesseract-ocr",
    "libtesseract-dev",
    "libgl1",
    "libglib2.0-0",
    "libsm6",
    "libxext6",
    "libxrender1",
    "scrot",
    "libxi6",
    "libxtst6",
    "x11-apps",
    "fonts-dejavu",
    "python3-tk",
    "socat",
]


# -- MCP npm pre-install helpers ---------------------------------------------

def get_npm_preinstall_cmds(mcp_config_path: Path) -> list[str]:
    """Read mcp_config.json and extract npm pre-install commands."""
    if not mcp_config_path.exists():
        return []
    try:
        data = json.loads(mcp_config_path.read_text())
        mcp_servers = data.get("mcp_servers", [])
    except (json.JSONDecodeError, KeyError):
        return []

    npm_packages = set()
    for server in mcp_servers:
        command = server.get("command", "")
        args = server.get("args", [])
        if command == "npx" and args:
            pkg_args = [a for a in args if not a.startswith("-")]
            if pkg_args:
                npm_packages.add(pkg_args[0])

    return [
        f"npm install -g {pkg} || echo 'WARN: {pkg} pre-install failed'"
        for pkg in sorted(npm_packages)
    ]


# -- Template build ----------------------------------------------------------

def build_template(template_name: str) -> str:
    """Build the CraftBot E2B template. Returns the template ID."""
    try:
        from e2b import Template
    except ImportError:
        print("ERROR: e2b SDK not installed. Run: pip install e2b")
        sys.exit(1)

    req_file = CRAFTBOT_DIR / "requirements.txt"
    if not req_file.exists():
        print("ERROR: requirements.txt not found")
        sys.exit(1)

    packages = [
        line.strip()
        for line in req_file.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    print(f"Building CraftBot template: {template_name}")
    print(f"  System packages: {len(SYSTEM_PACKAGES)}")
    print(f"  Python packages: {len(packages)}")

    # Install Node.js 18 via NodeSource (MCP servers require Node >= 18)
    install_node_cmds = [
        "apt-get update && apt-get install -y ca-certificates curl gnupg",
        "mkdir -p /etc/apt/keyrings",
        "curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg",
        'echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_18.x nodistro main" > /etc/apt/sources.list.d/nodesource.list',
        "apt-get update && apt-get install -y nodejs",
    ]

    template = Template(file_context_path=str(CRAFTBOT_DIR)).from_template("desktop")
    template = template.apt_install(SYSTEM_PACKAGES, no_install_recommends=True)
    for cmd in install_node_cmds:
        template = template.run_cmd(cmd, user="root")
    template = (
        template
        .set_workdir("/home/user/agent")
        .copy("requirements.txt", "/home/user/agent/requirements.txt")
        .run_cmd(
            "pip install --no-cache-dir -r /home/user/agent/requirements.txt 2>&1"
            " || (echo '=== RETRYING FAILED PACKAGES ONE BY ONE ===' "
            " && while IFS= read -r pkg || [ -n \"$pkg\" ]; do"
            "   pkg=$(echo \"$pkg\" | sed 's/#.*//;s/^[[:space:]]*//;s/[[:space:]]*$//');"
            "   [ -z \"$pkg\" ] && continue;"
            "   pip install --no-cache-dir \"$pkg\" 2>&1 || echo \"FAILED: $pkg\";"
            " done < /home/user/agent/requirements.txt)"
        )
        # Playwright needs browser binaries installed separately
        .run_cmd("playwright install chromium --with-deps 2>&1 || echo 'WARN: playwright install failed'")
    )

    # Pre-install MCP npm packages
    npm_cmds = get_npm_preinstall_cmds(CRAFTBOT_DIR / "app" / "config" / "mcp_config.json")
    if npm_cmds:
        for cmd in npm_cmds:
            print(f"  Pre-installing: {cmd}")
            template = template.run_cmd(cmd, user="root")

    # Copy full CraftBot code and build frontend
    template = (
        template
        .copy(".", "/home/user/agent/")
        # Remove credentials/data that should not be in the template
        .run_cmd("rm -rf /home/user/agent/.credentials /home/user/agent/agent_file_system /home/user/agent/chroma_db_memory")
        .run_cmd(
            "cd /home/user/agent/app/ui_layer/browser/frontend"
            " && npm install --legacy-peer-deps"
            " && npm run build"
            " && rm -rf node_modules"
            " && echo 'Frontend built successfully'"
            " || echo 'WARN: Frontend build failed - will use fallback UI'"
        )
        .run_cmd(
            "sed -i 's/\\r$//' /home/user/agent/e2b-start.sh"
            " && chmod +x /home/user/agent/e2b-start.sh"
        )
        .run_cmd("chmod -R 755 /home/user/agent")
        # Install systemd service so the agent starts automatically on sandbox boot
        .run_cmd(
            'cat > /etc/systemd/system/craftbot.service << \'UNIT\'\n'
            '[Unit]\n'
            'Description=CraftBot Agent\n'
            'After=network.target\n'
            '\n'
            '[Service]\n'
            'Type=forking\n'
            'User=user\n'
            'WorkingDirectory=/home/user/agent\n'
            'ExecStart=/bin/bash /home/user/agent/e2b-start.sh\n'
            'Restart=on-failure\n'
            'RestartSec=3\n'
            'EnvironmentFile=-/home/user/agent/.env\n'
            '\n'
            '[Install]\n'
            'WantedBy=multi-user.target\n'
            'UNIT',
            user="root",
        )
        .run_cmd("systemctl daemon-reload && systemctl enable craftbot.service", user="root")
    )

    print("  Building template (this may take several minutes)...")

    build_info = Template.build(
        template,
        template_name,
        cpu_count=2,
        memory_mb=4096,
        api_key=E2B_API_KEY,
    )

    print(f"  Template built successfully!")
    print(f"  Template ID: {build_info.template_id}")
    print(f"  Build ID:    {build_info.build_id}")

    return build_info.template_id


# -- Main --------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Build an E2B desktop template for CraftBot."
    )
    parser.add_argument(
        "--name",
        default=DEFAULT_TEMPLATE_NAME,
        help=f"Template name (default: {DEFAULT_TEMPLATE_NAME})",
    )
    args = parser.parse_args()

    if not E2B_API_KEY:
        print("ERROR: E2B_API_KEY not set.")
        sys.exit(1)

    template_id = build_template(args.name)
    print(f"\nDone! Use template '{args.name}' (ID: {template_id}) to create sandboxes:")
    print(f"  python scripts/e2b_sandbox.py create --template {template_id}")


if __name__ == "__main__":
    main()
