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
UPTERM_PRIVATE_KEY="$SSH_DIR/upterm_host_ed25519"
KNOWN_HOSTS="$SSH_DIR/known_hosts"
AUTHORIZED_KEYS="$SSH_DIR/authorized_keys"

CLIENT_PUBLIC_KEY='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC09jbMQE1HHbdV2R18EvBqztYgmkP/K4sOEUeLbkjC+aQd6zH4RaWMA50hBksjdPPcFY4qjmw9vxvaT6R/lQiQkxT43/geoauopzh30TSDNpJMccU276VJqwzSFU+a7WnThG/snJJJtFTcjFDcQu1XW0hKKdE8Pc+dQRlgmRIl+9PsKraPn1E0XdMUqK+opj153LNI5Bhw4DxjBFd9ztwkHBi+R0Cq6/oHReJfGKWWNwdnOU0W5AhygOYym9Y5+sS08QqjqQVfYhu8n67SOBfjjeHVur4tyjQlQuumMKkuDzSjOw0OU0o1MhluGSQkRdHQLN/Ryn4vUne6dc6+a+Bd rsa-key-20260828'

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


echo "=== CREATE UPTERM HOST KEY ==="

if [ ! -f "$UPTERM_PRIVATE_KEY" ]; then
    ssh-keygen \
        -t ed25519 \
        -f "$UPTERM_PRIVATE_KEY" \
        -N "" \
        -C "beam-upterm-host"
fi

chmod 600 "$UPTERM_PRIVATE_KEY"


echo "=== CREATE AUTHORIZED KEYS ==="

printf '%s\\n' "$CLIENT_PUBLIC_KEY" > "$AUTHORIZED_KEYS"

chmod 600 "$AUTHORIZED_KEYS"

echo "Authorized client key:"
cat "$AUTHORIZED_KEYS"


echo "=== PREPARE KNOWN HOSTS ==="

touch "$KNOWN_HOSTS"
chmod 644 "$KNOWN_HOSTS"


echo "=== STARTING UPTERM ==="

rm -f /tmp/upterm.log

"$UPTERM_BIN" host \
    --accept \
    --private-key "$UPTERM_PRIVATE_KEY" \
    --authorized-keys "$AUTHORIZED_KEYS" \
    --known-hosts "$KNOWN_HOSTS" \
    --skip-host-key-check \
    > /tmp/upterm.log 2>&1 &

UPTERM_PID=$!

echo "Upterm PID: $UPTERM_PID"


echo "=== WAITING FOR UPTERM SSH ==="

SSH_COMMAND=""

for i in $(seq 1 60); do

    if ! kill -0 "$UPTERM_PID" 2>/dev/null; then
        echo "ERROR: UPTERM PROCESS EXITED"
        echo "=== UPTERM LOG ==="
        cat /tmp/upterm.log || true
        exit 1
    fi

    SSH_COMMAND=$(
        grep -E '^[[:space:]]*ssh [^[:space:]]+@uptermd\\.upterm\\.dev' \
        /tmp/upterm.log |
        head -n 1 |
        sed 's/^[[:space:]]*//'
    )

    if [ -n "$SSH_COMMAND" ]; then

        echo ""
        echo "=========================================="
        echo "             SSH READY"
        echo "=========================================="
        echo ""
        echo "COPY THIS COMMAND:"
        echo ""
        echo "$SSH_COMMAND"
        echo ""
        echo "=========================================="
        echo ""

        break
    fi

    echo "Waiting for Upterm... $i/60"
    sleep 2
done


if [ -z "$SSH_COMMAND" ]; then

    echo ""
    echo "=========================================="
    echo "       UPTERM SSH NOT AVAILABLE"
    echo "=========================================="
    echo ""

    cat /tmp/upterm.log || true

    exit 1
fi


echo "=== GPU STATUS ==="
nvidia-smi


echo "=== SYSTEM STATUS ==="
hostname
echo "CPU:"
nproc
echo "Memory:"
free -h
echo "Disk:"
df -h /


echo ""
echo "=========================================="
echo "       CONTAINER IS RUNNING"
echo "=========================================="
echo ""
echo "GPU       : RTX4090"
echo "CPU       : 2"
echo "RAM       : 4Gi"
echo "TIMEOUT   : 30 HOURS"
echo ""
echo "Upterm status: RUNNING"
echo ""


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

    echo ""

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
