from beam import function, Image
import subprocess
import time

image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y wget ca-certificates openssh-client procps",
    ])
)

@function(
    name="gpu-upterm",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=30 * 60 * 60,
)
def run_script():
    print("=== BEAM RTX4090 + UPTERM ===")
    print("=== GPU ===")
    subprocess.run(["nvidia-smi"], check=False)

    cmd = r"""
set -e

export HOME=/root

UPTERM_VERSION="0.24.0"
UPTERM_DIR="/opt/upterm"
UPTERM_BIN="/opt/upterm/upterm"

SSH_DIR="/root/.ssh"
PRIVATE_KEY="$SSH_DIR/id_ed25519"
PUBLIC_KEY="$SSH_DIR/id_ed25519.pub"
KNOWN_HOSTS="$SSH_DIR/known_hosts"

mkdir -p "$UPTERM_DIR" "$SSH_DIR"
chmod 700 "$SSH_DIR"

echo "=== INSTALLING UPTERM ==="
cd /tmp

wget -q \
    "https://github.com/owenthereal/upterm/releases/download/v${UPTERM_VERSION}/upterm_linux_amd64.tar.gz" \
    -O /tmp/upterm.tar.gz

rm -rf "$UPTERM_DIR"
mkdir -p "$UPTERM_DIR"

tar -xzf /tmp/upterm.tar.gz -C "$UPTERM_DIR"

if [ ! -x "$UPTERM_BIN" ]; then
    FOUND=$(find "$UPTERM_DIR" -type f -name "upterm" -perm -111 | head -n 1)
    if [ -z "$FOUND" ]; then
        echo "ERROR: Upterm binary not found."
        find "$UPTERM_DIR" -maxdepth 3 -type f -print || true
        exit 1
    fi
    UPTERM_BIN="$FOUND"
fi

chmod +x "$UPTERM_BIN"

echo "=== UPTERM VERSION ==="
"$UPTERM_BIN" version || "$UPTERM_BIN" --version || true

echo "=== CREATE SSH KEY ==="

if [ ! -f "$PRIVATE_KEY" ]; then
    ssh-keygen -t ed25519 -f "$PRIVATE_KEY" -N "" -C "beam-upterm"
fi

chmod 600 "$PRIVATE_KEY"
chmod 644 "$PUBLIC_KEY"
touch "$KNOWN_HOSTS"
chmod 644 "$KNOWN_HOSTS"

echo "SSH PUBLIC KEY:"
cat "$PUBLIC_KEY"

echo "=== STARTING UPTERM ==="

rm -f /tmp/upterm.log /tmp/upterm-session

"$UPTERM_BIN" host \
    --accept \
    --skip-host-key-check \
    > /tmp/upterm.log 2>&1 &

UPTERM_PID=$!

echo "Upterm PID: $UPTERM_PID"

echo "=== WAITING FOR UPTERM SSH ==="

SSH_COMMAND=""

for i in $(seq 1 60); do
    if ! kill -0 "$UPTERM_PID" 2>/dev/null; then
        echo "ERROR: UPTERM PROCESS EXITED"
        cat /tmp/upterm.log || true
        exit 1
    fi

    SESSION_OUTPUT=$(
        "$UPTERM_BIN" session current 2>/dev/null || true
    )

    echo "$SESSION_OUTPUT" > /tmp/upterm-session

    SSH_COMMAND=$(
        echo "$SESSION_OUTPUT" |
        grep -E '^[[:space:]]*ssh ' |
        head -n 1 |
        sed 's/^[[:space:]]*//'
    )

    if [ -n "$SSH_COMMAND" ]; then
        echo ""
        echo "=========================================="
        echo "             SSH READY"
        echo "=========================================="
        echo ""
        echo "$SSH_COMMAND"
        echo ""
        echo "=========================================="
        break
    fi

    echo "Waiting for Upterm... $i/60"
    sleep 2
done

if [ -z "$SSH_COMMAND" ]; then
    echo "ERROR: UPTERM SSH NOT AVAILABLE"
    echo "=== UPTERM LOG ==="
    cat /tmp/upterm.log || true
    echo "=== SESSION OUTPUT ==="
    cat /tmp/upterm-session 2>/dev/null || true
    exit 1
fi

echo "=== GPU STATUS ==="
nvidia-smi

echo "=== SYSTEM STATUS ==="
hostname
echo "CPU:"
nproc
echo "MEMORY:"
free -h
echo "DISK:"
df -h /

echo "=== CONTAINER RUNNING ==="
echo "GPU: RTX4090"
echo "TIMEOUT: 30 HOURS"

while true; do
    echo "=== HEARTBEAT ==="
    date

    nvidia-smi \
        --query-gpu=name,temperature.gpu,memory.used,memory.total,utilization.gpu \
        --format=csv,noheader \
        2>/dev/null || true

    if kill -0 "$UPTERM_PID" 2>/dev/null; then
        echo "Upterm status: RUNNING"
    else
        echo "Upterm status: STOPPED"
        cat /tmp/upterm.log || true
    fi

    sleep 600
done
"""

    result = subprocess.run(
        ["bash", "-lc", cmd],
        check=False,
    )

    print("BASH PROCESS EXITED")
    print("Exit code:", result.returncode)

    while True:
        time.sleep(3600)
