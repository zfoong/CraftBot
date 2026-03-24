#!/bin/bash
# E2B Sandbox Startup Script for CraftBot
# Called after sandbox creation to launch the agent process.
# Env vars (AGENT_ID, TEAM_ID, etc.) are injected by E2B at sandbox creation time.

set -e

AGENT_DIR="/home/user/agent"
LOG_FILE="/tmp/agent.log"
ENV_FILE="${AGENT_DIR}/.env"

echo "[e2b-start] Starting CraftBot setup..." | tee -a "$LOG_FILE"

# Write .env file from environment variables so python-dotenv picks them up
cat > "$ENV_FILE" <<EOF
AGENT_ID=${AGENT_ID:-}
AGENT_NAME=${AGENT_NAME:-}
TEAM_ID=${TEAM_ID:-}
CHATSERVER_URL=${CHATSERVER_URL:-http://localhost:9000}
MONGO_URI=${MONGO_URI:-mongodb://localhost:27017/}
DB_NAME=${DB_NAME:-agent}
OMNIPARSER_BASE_URL=${OMNIPARSER_BASE_URL:-}
WATCHER_MANAGER_URL=${WATCHER_MANAGER_URL:-}
USE_REMOTE_CREDENTIALS=true
E2B_SANDBOX=true
DISPLAY=${DISPLAY:-:0}
OPENAI_API_KEY=${OPENAI_API_KEY:-}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
GOOGLE_API_KEY=${GOOGLE_API_KEY:-}
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-}
AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}
S3_MEMORY_BUCKET=${S3_MEMORY_BUCKET:-}
S3_MEMORY_REGION=${S3_MEMORY_REGION:-us-east-1}
S3_MEMORY_PREFIX=${S3_MEMORY_PREFIX:-teams}
EOF

echo "[e2b-start] .env written with AGENT_ID=${AGENT_ID}" | tee -a "$LOG_FILE"
echo "[e2b-start] CHATSERVER_URL=${CHATSERVER_URL:-http://localhost:9000}" | tee -a "$LOG_FILE"

# Export all env vars so they're available to the python process
export AGENT_ID="${AGENT_ID:-}"
export AGENT_NAME="${AGENT_NAME:-}"
export TEAM_ID="${TEAM_ID:-}"
export CHATSERVER_URL="${CHATSERVER_URL:-http://localhost:9000}"
export MONGO_URI="${MONGO_URI:-mongodb://localhost:27017/}"
export DB_NAME="${DB_NAME:-agent}"
export WATCHER_MANAGER_URL="${WATCHER_MANAGER_URL:-}"
export USE_REMOTE_CREDENTIALS=true
export E2B_SANDBOX=true
export DISPLAY="${DISPLAY:-:0}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"
export GOOGLE_API_KEY="${GOOGLE_API_KEY:-}"
export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
export S3_MEMORY_BUCKET="${S3_MEMORY_BUCKET:-}"
export S3_MEMORY_REGION="${S3_MEMORY_REGION:-us-east-1}"
export S3_MEMORY_PREFIX="${S3_MEMORY_PREFIX:-teams}"

# Generate proper Xauthority so python-xlib doesn't print warnings to stdout
export XAUTHORITY=/home/user/.Xauthority
touch "$XAUTHORITY"
if command -v xauth >/dev/null 2>&1; then
    xauth generate :0 . trusted 2>/dev/null || true
fi

# Ensure X11 file socket exists for pyautogui (python-xlib needs /tmp/.X11-unix/X0)
echo "[e2b-start] Checking X11 display ${DISPLAY}..." | tee -a "$LOG_FILE"
mkdir -p /tmp/.X11-unix

if [ -e /tmp/.X11-unix/X0 ]; then
    echo "[e2b-start] X11 file socket already exists" | tee -a "$LOG_FILE"
else
    if command -v socat >/dev/null 2>&1; then
        echo "[e2b-start] Bridging abstract X11 socket to file socket via socat..." | tee -a "$LOG_FILE"
        socat UNIX-LISTEN:/tmp/.X11-unix/X0,fork ABSTRACT-CONNECT:/tmp/.X11-unix/X0 &
        sleep 1
        echo "[e2b-start] socat bridge started" | tee -a "$LOG_FILE"
    else
        echo "[e2b-start] socat not available, starting Xvfb..." | tee -a "$LOG_FILE"
        Xvfb :0 -ac -screen 0 1024x768x24 &
        sleep 2
    fi

    if [ -e /tmp/.X11-unix/X0 ]; then
        echo "[e2b-start] X11 file socket ready" | tee -a "$LOG_FILE"
    else
        echo "[e2b-start] WARNING: X11 file socket still not available" | tee -a "$LOG_FILE"
    fi
fi

# Launch the agent in the background
cd "$AGENT_DIR"
export GUI_MODE_ENABLED=False
echo "[e2b-start] Launching python3 run.py --browser ..." | tee -a "$LOG_FILE"
nohup python3 run.py --browser >> "$LOG_FILE" 2>&1 &
AGENT_PID=$!
echo "[e2b-start] Agent started with PID ${AGENT_PID}" | tee -a "$LOG_FILE"
