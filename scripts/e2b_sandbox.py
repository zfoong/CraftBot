#!/usr/bin/env python3
"""
E2B Sandbox Manager - Create and manage E2B desktop sandbox instances
CLI tool for spinning up WhiteCollarAgent sandboxes on demand.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime


def require_e2b():
    """Import e2b_desktop or exit with install instructions."""
    try:
        from e2b_desktop import Sandbox
        return Sandbox
    except ImportError:
        print("Error: e2b_desktop package not installed.")
        print("Install with: pip install e2b-desktop")
        sys.exit(1)


def get_api_key():
    """Get E2B API key from environment."""
    key = (os.environ.get("E2B_API_KEY") or "").strip()
    if not key:
        print("Error: E2B_API_KEY environment variable not set.")
        sys.exit(1)
    return key


def create_sandbox(args):
    """Create a new E2B sandbox instance."""
    Sandbox = require_e2b()
    api_key = get_api_key()

    template = args.template or os.environ.get("E2B_TEMPLATE_ID", "craftbot")
    timeout = args.timeout
    agent_id = args.agent_id or f"craftbot-{int(time.time())}"
    agent_name = args.agent_name or "CraftBot Agent"
    team_id = args.team_id or ""

    # Build environment variables
    envs = {
        "AGENT_ID": agent_id,
        "AGENT_NAME": agent_name,
        "TEAM_ID": team_id,
        "CHATSERVER_URL": args.chatserver_url or os.environ.get("CHATSERVER_URL", "http://localhost:9000"),
        "MONGO_URI": os.environ.get("MONGO_URI", "mongodb://localhost:27017/"),
        "DB_NAME": os.environ.get("DB_NAME", "agent"),
        "USE_REMOTE_CREDENTIALS": "true",
        "E2B_SANDBOX": "true",
        "OMNIPARSER_BASE_URL": os.environ.get("OMNIPARSER_BASE_URL", ""),
        "WATCHER_MANAGER_URL": os.environ.get("WATCHER_MANAGER_URL", ""),
        # LLM keys
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
        "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", ""),
        # S3
        "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID", ""),
        "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
        "S3_MEMORY_BUCKET": os.environ.get("S3_MEMORY_BUCKET", ""),
        "S3_MEMORY_REGION": os.environ.get("S3_MEMORY_REGION", "us-east-1"),
        "S3_MEMORY_PREFIX": os.environ.get("S3_MEMORY_PREFIX", "teams"),
    }

    # Allow extra env vars via --env KEY=VALUE
    if args.env:
        for pair in args.env:
            if "=" in pair:
                k, v = pair.split("=", 1)
                envs[k] = v

    print(f"Creating sandbox...")
    print(f"  Template:  {template}")
    print(f"  Timeout:   {timeout}s")
    print(f"  Agent ID:  {agent_id}")
    print(f"  Agent:     {agent_name}")

    try:
        sandbox = Sandbox.create(
            api_key=api_key,
            template=template,
            timeout=timeout,
            envs=envs,
        )
        print(f"  Sandbox:   {sandbox.sandbox_id}")

        # Launch agent process
        if not args.no_start:
            print("Starting agent process...")
            sandbox.commands.run(
                "bash /home/user/agent/e2b-start.sh",
                background=True,
                envs=envs,
            )
            # Wait for the startup script to finish and verify the agent is running
            import time as _time
            _time.sleep(6)
            check = sandbox.commands.run(
                "cat /tmp/agent.log 2>/dev/null | tail -3; "
                "ps aux | grep -q '[p]ython3 -m app.main' && echo 'AGENT_OK' || echo 'AGENT_FAIL'"
            )
            if "AGENT_OK" in (check.stdout or ""):
                print("  Agent process launched.")
            else:
                print("  WARNING: Agent may not have started. Check logs:")
                print(f"    {check.stdout}")
                print(f"  Debug: python e2b_sandbox.py exec {sandbox.sandbox_id} cat /tmp/agent.log")

        # Start desktop stream
        stream_url = None
        if not args.no_stream:
            try:
                sandbox.stream.start()
                stream_url = sandbox.stream.get_url()
                print(f"  Stream:    {stream_url}")
            except Exception as e:
                print(f"  Stream failed: {e}")

        # Get browser URL
        browser_url = None
        try:
            host = sandbox.get_host(7926)
            browser_url = f"https://{host}"
            print(f"  Browser:   {browser_url}")
        except Exception:
            pass

        # Output summary as JSON for programmatic use
        result = {
            "sandbox_id": sandbox.sandbox_id,
            "template_id": template,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "status": "running",
            "stream_url": stream_url,
            "browser_url": browser_url,
            "created_at": datetime.utcnow().isoformat(),
        }

        print(f"\nSandbox ready.")
        if args.json:
            print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"Error creating sandbox: {e}")
        sys.exit(1)


def list_sandboxes(args):
    """List running E2B sandboxes."""
    Sandbox = require_e2b()
    api_key = get_api_key()

    try:
        pager = Sandbox.list(api_key=api_key)
        all_sandboxes = []
        while True:
            items = pager.next_items()
            if not items:
                break
            all_sandboxes.extend(items)
            if not pager.has_next:
                break

        if not all_sandboxes:
            print("No running sandboxes.")
            return

        print(f"{'Sandbox ID':<26} {'Name':<22} {'State':<10} {'Started':<25}")
        print("-" * 83)
        for sb in all_sandboxes:
            print(f"{sb.sandbox_id:<26} {sb.name or '?':<22} {sb.state.value:<10} {str(sb.started_at):<25}")

        print(f"\nTotal: {len(all_sandboxes)}")

    except Exception as e:
        print(f"Error listing sandboxes: {e}")
        sys.exit(1)


def stop_sandbox(args):
    """Stop a running sandbox."""
    Sandbox = require_e2b()
    api_key = get_api_key()

    sandbox_id = args.sandbox_id
    print(f"Stopping sandbox {sandbox_id}...")

    try:
        sandbox = Sandbox.connect(sandbox_id, api_key=api_key)
        sandbox.kill()
        print("Sandbox stopped.")
    except Exception as e:
        print(f"Error stopping sandbox: {e}")
        sys.exit(1)


def status_sandbox(args):
    """Check if a sandbox is alive."""
    Sandbox = require_e2b()
    api_key = get_api_key()

    sandbox_id = args.sandbox_id
    try:
        sandbox = Sandbox.connect(sandbox_id, api_key=api_key)
        print(f"Sandbox {sandbox_id}: running")

        # Try to get stream URL
        try:
            url = sandbox.stream.get_url()
            print(f"Stream: {url}")
        except Exception:
            pass

    except Exception:
        print(f"Sandbox {sandbox_id}: not found or stopped")
        sys.exit(1)


def extend_sandbox(args):
    """Extend a sandbox's timeout."""
    Sandbox = require_e2b()
    api_key = get_api_key()

    sandbox_id = args.sandbox_id
    timeout_ms = args.timeout * 1000

    print(f"Extending sandbox {sandbox_id} by {args.timeout}s...")
    try:
        Sandbox.set_timeout(sandbox_id, timeout_ms, api_key=api_key)
        print("Timeout extended.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def exec_command(args):
    """Execute a command inside a running sandbox."""
    Sandbox = require_e2b()
    api_key = get_api_key()

    sandbox_id = args.sandbox_id
    cmd = " ".join(args.command)

    try:
        sandbox = Sandbox.connect(sandbox_id, api_key=api_key)
        result = sandbox.commands.run(cmd)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(result.exit_code)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="E2B Sandbox Manager - Create and manage E2B desktop sandboxes"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = subparsers.add_parser("create", help="Create a new sandbox")
    p_create.add_argument("--template", "-t", help="E2B template ID (default: from E2B_TEMPLATE_ID or 'white-collar-agent')")
    p_create.add_argument("--timeout", type=int, default=300, help="Sandbox timeout in seconds (default: 300)")
    p_create.add_argument("--agent-id", help="Agent ID (default: auto-generated)")
    p_create.add_argument("--agent-name", default="CraftBot Agent", help="Agent display name")
    p_create.add_argument("--team-id", default="", help="Team ID")
    p_create.add_argument("--chatserver-url", help="Chat server URL (default: from CHATSERVER_URL or localhost:9000)")
    p_create.add_argument("--env", "-e", action="append", help="Extra env vars as KEY=VALUE (repeatable)")
    p_create.add_argument("--no-start", action="store_true", help="Don't auto-start the agent process")
    p_create.add_argument("--no-stream", action="store_true", help="Don't start desktop streaming")
    p_create.add_argument("--json", action="store_true", help="Output result as JSON")
    p_create.set_defaults(func=create_sandbox)

    # list
    p_list = subparsers.add_parser("list", help="List running sandboxes")
    p_list.set_defaults(func=list_sandboxes)

    # stop
    p_stop = subparsers.add_parser("stop", help="Stop a sandbox")
    p_stop.add_argument("sandbox_id", help="Sandbox ID to stop")
    p_stop.set_defaults(func=stop_sandbox)

    # status
    p_status = subparsers.add_parser("status", help="Check sandbox status")
    p_status.add_argument("sandbox_id", help="Sandbox ID to check")
    p_status.set_defaults(func=status_sandbox)

    # extend
    p_extend = subparsers.add_parser("extend", help="Extend sandbox timeout")
    p_extend.add_argument("sandbox_id", help="Sandbox ID")
    p_extend.add_argument("--timeout", type=int, default=300, help="Additional seconds (default: 300)")
    p_extend.set_defaults(func=extend_sandbox)

    # exec
    p_exec = subparsers.add_parser("exec", help="Run a command inside a sandbox")
    p_exec.add_argument("sandbox_id", help="Sandbox ID")
    p_exec.add_argument("command", nargs="+", help="Command to execute")
    p_exec.set_defaults(func=exec_command)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
