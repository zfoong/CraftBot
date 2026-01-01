#!/bin/bash

# ==========================================
# Firecracker Background Controller & Web Viewer v8.2 (Read-Only)
# ==========================================
# This script manages a Firecracker VM in the background and exposes its
# live boot logs via a web browser.
#
# NOTE: The web terminal is READ-ONLY. You can view boot progress but cannot log in.
#
# Usage: sudo ./fc-manage.sh [start|stop|restart|pause|resume|purge|status|tail]
# ==========================================

set -e

# Make sure we are root
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Must be run as root."
    exit 1
fi

# --- Configuration ---
if [ -n "$SUDO_USER" ]; then
    REAL_USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
    REAL_USER_HOME=$HOME
fi
WORKDIR="${REAL_USER_HOME}/fc-workdir"
DATA_DIR="$WORKDIR/data"

# Networking
TAP_DEV="tap0"
HOST_IP="172.16.0.1"
VM_IP="172.16.0.2"
NETMASK_LEN="/24"
FC_MAC="02:FC:00:00:00:01"

# VM Config
VCpuCount=1
MemSizeMib=512

# Versions & Ports
FC_VERSION="v1.7.0"
TTYD_VERSION="1.7.7"
TTYD_PORT=7681

# Paths
API_SOCKET="/tmp/firecracker.socket"
LOG_FILE="$WORKDIR/fc-vm.log"
FC_PID_FILE="$WORKDIR/fc.pid"
TTYD_PID_FILE="$WORKDIR/ttyd.pid"
SNAPSHOT_DIR="$WORKDIR/snapshots"
MEM_FILE_PATH="$SNAPSHOT_DIR/vm.mem"
SNAPSHOT_FILE_PATH="$SNAPSHOT_DIR/vm.snap"

# Binaries & Images
FC_BINARY="$DATA_DIR/firecracker"
TTYD_BINARY="$DATA_DIR/ttyd"
KERNEL_PATH="$DATA_DIR/vmlinux.bin"
ROOTFS_PATH="$DATA_DIR/bionic.rootfs.ext4"

# URLs
ARCH="$(uname -m)"
FC_URL="https://github.com/firecracker-microvm/firecracker/releases/download/${FC_VERSION}/firecracker-${FC_VERSION}-${ARCH}.tgz"
TTYD_URL="https://github.com/tsl0922/ttyd/releases/download/${TTYD_VERSION}/ttyd.x86_64"
KERNEL_URL="https://s3.amazonaws.com/spec.ccfc.min/img/quickstart_guide/x86_64/kernels/vmlinux.bin"
ROOTFS_URL="https://s3.amazonaws.com/spec.ccfc.min/img/quickstart_guide/x86_64/rootfs/bionic.rootfs.ext4"


# ==========================================
# === Helper Functions ===
# ==========================================

setup_workspace() {
    mkdir -p "$WORKDIR" "$DATA_DIR" "$SNAPSHOT_DIR"
    if [ -n "$SUDO_USER" ]; then
        chown -R "$SUDO_USER:" "$WORKDIR"
    fi

    # 0. Check CPU virtualization support
    if ! grep -E 'vmx|svm' /proc/cpuinfo > /dev/null; then
        echo "ERROR: CPU virtualization (vmx/svm) not found in /proc/cpuinfo."
        exit 1
    fi
    if [ ! -w "/dev/kvm" ]; then
        echo "ERROR: /dev/kvm not writeable. KVM enabled?"
        exit 1
    fi

    # 1. Download TTYD
    if [ ! -f "$TTYD_BINARY" ]; then
        echo "Downloading ttydViewer..."
        curl -L --fail -o "$TTYD_BINARY" "$TTYD_URL" && chmod +x "$TTYD_BINARY"
    fi

    # 2. Download Firecracker
    if [ ! -f "$FC_BINARY" ] || [ -d "$FC_BINARY" ]; then
        if [ -d "$FC_BINARY" ]; then
            rm -rf "$FC_BINARY"
        fi
        echo "Downloading Firecracker $FC_VERSION..."
        TMP=$(mktemp -d)
        curl -L --fail "$FC_URL" | tar -xz -C "$TMP"
        FOUND=$(find "$TMP" -type f -name "firecracker*" | head -n 1)
        if [ -z "$FOUND" ]; then
            echo "ERROR: FC binary not found in download."
            rm -rf "$TMP"
            exit 1
        fi
        mv "$FOUND" "$FC_BINARY" && chmod +x "$FC_BINARY" && rm -rf "$TMP"
    fi

    # 3. Download Images
    if [ ! -f "$KERNEL_PATH" ]; then
        echo "Downloading Kernel..."
        curl -L --fail -o "$KERNEL_PATH" "$KERNEL_URL"
    fi
    if [ ! -f "$ROOTFS_PATH" ] || [ ! -s "$ROOTFS_PATH" ]; then
        echo "Downloading Rootfs..."
        curl -L --fail -o "$ROOTFS_PATH" "$ROOTFS_URL"
    fi
}

setup_network() {
    ip link del "$TAP_DEV" 2>/dev/null || true
    ip tuntap add dev "$TAP_DEV" mode tap
    ip addr add "${HOST_IP}${NETMASK_LEN}" dev "$TAP_DEV"
    ip link set dev "$TAP_DEV" up
}

cleanup_network() {
    ip link del "$TAP_DEV" 2>/dev/null || true
}

curl_api() {
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --unix-socket "$API_SOCKET" -X "$1" -H "Content-Type: application/json" -d "$3" "http://localhost/$2")
    if [ "$HTTP_STATUS" -ge 400 ]; then
        echo "Error: API request $1 $2 failed (Status $HTTP_STATUS)"
        return 1
    fi
    return 0
}

check_pid() {
    if [ -f "$1" ]; then
        if ps -p "$(cat "$1")" > /dev/null; then
            return 0
        fi
    fi
    return 1
}

start_firecracker() {
    if check_pid "$FC_PID_FILE"; then
        echo "Firecracker already running."
        exit 1
    fi
    rm -f "$API_SOCKET"
    touch "$LOG_FILE"
    if [ -n "$SUDO_USER" ]; then
        chown "$SUDO_USER" "$LOG_FILE"
    fi

    echo "Starting Firecracker backend..."
    # Start FC directly, redirecting output to log file
    "$FC_BINARY" --api-sock "$API_SOCKET" > "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$FC_PID_FILE"

    tries=0
    while [ ! -S "$API_SOCKET" ]; do
        sleep 0.1
        tries=$((tries+1))
        if [ $tries -gt 50 ]; then
            echo "ERROR: Socket timeout. See $LOG_FILE"
            kill "$PID"
            exit 1
        fi
    done
}

start_ttyd_viewer() {
    # Kills old ttyd if exists
    if check_pid "$TTYD_PID_FILE"; then
        kill "$(cat "$TTYD_PID_FILE")" 2>/dev/null || true
    fi
    
    echo "Starting Web Viewer (ttyd)..."
    # ttyd runs 'tail -f' on the log file to pipe it to the browser
    setsid "$TTYD_BINARY" -p "$TTYD_PORT" -W -b / tail -f "$LOG_FILE" > /dev/null 2>&1 &
    echo $! > "$TTYD_PID_FILE"
}

stop_all() {
    if check_pid "$TTYD_PID_FILE"; then
        kill "$(cat "$TTYD_PID_FILE")" 2>/dev/null || true
    fi
    rm -f "$TTYD_PID_FILE"

    if check_pid "$FC_PID_FILE"; then
        PID=$(cat "$FC_PID_FILE")
        echo "Stopping Firecracker (PID $PID)..."
        curl_api PUT "actions" '{"action_type": "SendCtrlAltDel"}' || true
        count=0
        while ps -p "$PID" > /dev/null; do
            sleep 0.5
            count=$((count+1))
            if [ $count -gt 20 ]; then
                kill -9 "$PID"
                break
            fi
        done
    fi
    rm -f "$FC_PID_FILE" "$API_SOCKET"
}

# ==========================================
# === Main Commands ===
# ==========================================

cmd_start() {
    if ! check_pid "$FC_PID_FILE"; then
        cleanup_network
    fi
    setup_workspace
    setup_network
    start_firecracker
    start_ttyd_viewer

    echo "Configuring VM..."
    boot_args="console=ttyS0 reboot=k panic=1 pci=off root=/dev/vda rw ip=$VM_IP::$HOST_IP:$NETMASK_LEN::eth0:off"
    curl_api PUT "boot-source" "{\"kernel_image_path\": \"$KERNEL_PATH\", \"boot_args\": \"$boot_args\"}"
    chmod +r "$ROOTFS_PATH"
    curl_api PUT "drives/rootfs" "{\"drive_id\": \"rootfs\", \"path_on_host\": \"$ROOTFS_PATH\", \"is_root_device\": true, \"is_read_only\": false}"
    curl_api PUT "network-interfaces/eth0" "{\"iface_id\": \"eth0\", \"guest_mac\": \"$FC_MAC\", \"host_dev_name\": \"$TAP_DEV\"}"
    curl_api PUT "machine-config" "{\"vcpu_count\": $VCpuCount, \"mem_size_mib\": $MemSizeMib}"
    curl_api PUT "actions" '{"action_type": "InstanceStart"}'

    echo "---------------------------------------------------"
    echo "VM started! View boot log at: http://localhost:$TTYD_PORT"
    echo "(Note: This web terminal is read-only)"
    echo "---------------------------------------------------"
}

cmd_stop() {
    stop_all
    cleanup_network
    echo "Stopped."
}

cmd_pause() {
    if ! check_pid "$FC_PID_FILE"; then
        echo "VM not running."
        exit 1
    fi
    echo "Pausing and snapshotting..."
    curl_api PATCH "vm/state" '{"state": "Paused"}'
    rm -f "$MEM_FILE_PATH" "$SNAPSHOT_FILE_PATH"
    mkdir -p "$SNAPSHOT_DIR"
    curl_api PUT "snapshot/create" "{\"mem_file_path\": \"$MEM_FILE_PATH\", \"snapshot_path\": \"$SNAPSHOT_FILE_PATH\"}"
    stop_all
    cleanup_network
    echo "Paused and saved to $SNAPSHOT_DIR"
}

cmd_resume() {
    if check_pid "$FC_PID_FILE"; then
        echo "VM already running."
        exit 1
    fi
    if [ ! -f "$SNAPSHOT_FILE_PATH" ]; then
        echo "No snapshot found."
        exit 1
    fi
    cleanup_network
    setup_workspace
    setup_network
    start_firecracker
    start_ttyd_viewer
    echo "Loading snapshot..."
    curl_api PUT "snapshot/load" "{\"mem_file_path\": \"$MEM_FILE_PATH\", \"snapshot_path\": \"$SNAPSHOT_FILE_PATH\"}"
    curl_api PATCH "vm/state" '{"state": "Resumed"}'
    echo "Resumed. View at http://localhost:$TTYD_PORT"
}

cmd_purge() {
    cmd_stop
    if [ -d "$WORKDIR" ]; then
        echo "Deleting $WORKDIR..."
        rm -rf "$WORKDIR"
    fi
    echo "Purged."
}

cmd_status() {
    if check_pid "$FC_PID_FILE"; then
        echo "Firecracker: RUNNING (PID $(cat $FC_PID_FILE))"
    else
        echo "Firecracker: STOPPED"
    fi

    if check_pid "$TTYD_PID_FILE"; then
        echo "Web Viewer : RUNNING (http://localhost:$TTYD_PORT)"
    else
        echo "Web Viewer : STOPPED"
    fi

    if [ -f "$SNAPSHOT_FILE_PATH" ]; then
        echo "Snapshot   : YES"
    else
        echo "Snapshot   : NO"
    fi
}

# ==========================================
# === Dispatch ===
# ==========================================
SELF=$(realpath "$0")
case "$1" in
    start) cmd_start ;;
    stop) cmd_stop ;;
    restart) cmd_stop; sleep 1; "$SELF" start ;;
    pause) cmd_pause ;;
    resume) cmd_resume ;;
    purge) cmd_purge ;;
    status) cmd_status ;;
    tail) tail -f "$LOG_FILE" ;;
    *) echo "Usage: sudo $0 [start|stop|restart|pause|resume|purge|status|tail]"; exit 1 ;;
esac