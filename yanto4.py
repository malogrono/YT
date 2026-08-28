from beam import function, Image
import subprocess
import time

image = (
    Image(base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04")
    .add_commands([
        "apt-get update -y",
        "apt-get install -y wget ca-certificates xz-utils procps openssh-client",
    ])
)

@function(
    name="gpu-tmate",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=30 * 60 * 60,
)
def run_script():
    print("==========================================")
    print("       BEAM RTX4090 + TMATE")
    print("==========================================")
    subprocess.run(["nvidia-smi"], check=False)

    cmd = r"""
set -u

TMATE_DIR="/opt/tmate"
TMATE_BIN="$TMATE_DIR/tmate"
TMATE_SOCKET="/tmp/tmate.sock"
mkdir -p "$TMATE_DIR"

echo "=== DOWNLOAD TMATE ==="
cd /tmp
wget -q "https://github.com/tmate-io/tmate/releases/download/2.4.0/tmate-2.4.0-static-linux-amd64.tar.xz" -O /tmp/tmate.tar.xz || exit 1

rm -rf /tmp/tmate-2.4.0-static-linux-amd64
tar -xf /tmp/tmate.tar.xz -C /tmp || exit 1
cp /tmp/tmate-2.4.0-static-linux-amd64/tmate "$TMATE_BIN"
chmod +x "$TMATE_BIN"

echo "=== TMATE VERSION ==="
"$TMATE_BIN" -V

echo "=== START TMATE ==="
rm -f "$TMATE_SOCKET"

"$TMATE_BIN" -S "$TMATE_SOCKET" new-session -d -s beam
RC=$?

if [ "$RC" -ne 0 ]; then
    echo "ERROR: TMATE SESSION CREATION FAILED"
    exit "$RC"
fi

echo "TMATE SESSION CREATED"
echo "=== SEARCHING FOR SSH ==="

SSH_COMMAND=""

for i in $(seq 1 90); do
    echo "TMATE CHECK $i/90"

    OUTPUT=$("$TMATE_BIN" -S "$TMATE_SOCKET" display -p '#{tmate_ssh}' 2>&1 || true)
    echo "$OUTPUT"

    SSH_COMMAND=$(printf '%s
' "$OUTPUT" | grep -Eo 'ssh [^[:space:]]+@[^[:space:]]+' | head -n 1 || true)

    if [ -z "$SSH_COMMAND" ]; then
        OUTPUT=$("$TMATE_BIN" -S "$TMATE_SOCKET" display -p '#{tmate_ssh_ro}' 2>&1 || true)
        echo "$OUTPUT"
        SSH_COMMAND=$(printf '%s
' "$OUTPUT" | grep -Eo 'ssh [^[:space:]]+@[^[:space:]]+' | head -n 1 || true)
    fi

    if [ -n "$SSH_COMMAND" ]; then
        break
    fi

    sleep 2
done

if [ -z "$SSH_COMMAND" ]; then
    echo "=========================================="
    echo "       TMATE SSH NOT FOUND"
    echo "=========================================="
    echo "=== SESSIONS ==="
    "$TMATE_BIN" -S "$TMATE_SOCKET" list-sessions 2>&1 || true
    echo "=== MESSAGES ==="
    "$TMATE_BIN" -S "$TMATE_SOCKET" show-messages 2>&1 || true
    echo "=== DISPLAY SSH ==="
    "$TMATE_BIN" -S "$TMATE_SOCKET" display -p '#{tmate_ssh}' 2>&1 || true
    exit 1
fi

echo "=========================================="
echo "             SSH READY"
echo "=========================================="
echo "$SSH_COMMAND"
echo "=========================================="

echo "=== GPU STATUS ==="
nvidia-smi

echo "=========================================="
echo "       CONTAINER IS RUNNING"
echo "             FOR 30 HOURS"
echo "=========================================="

while true; do
    echo "=== HEARTBEAT ==="
    date
    nvidia-smi --query-gpu=name,temperature.gpu,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>/dev/null || true
    echo ""
    sleep 600
done
"""

    result = subprocess.run(["bash", "-lc", cmd], check=False)
    print("BASH PROCESS EXITED")
    print("Exit code:", result.returncode)

    while True:
        time.sleep(3600)
