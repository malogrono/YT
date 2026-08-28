from beam import function, Image
import subprocess
import time

image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y wget ca-certificates xz-utils procps",
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

    print("=== GPU ===")
    subprocess.run(["nvidia-smi"], check=False)

    cmd = r'''
set -e

TMATE_DIR="/opt/tmate"
TMATE_BIN="$TMATE_DIR/tmate"
TMATE_SOCKET="/tmp/tmate.sock"
TMATE_LOG="/tmp/tmate-messages.log"

mkdir -p "$TMATE_DIR"

echo "=== DOWNLOAD TMATE ==="

cd /tmp

wget -q \
    https://github.com/tmate-io/tmate/releases/download/2.4.0/tmate-2.4.0-static-linux-amd64.tar.xz \
    -O /tmp/tmate.tar.xz

echo "=== EXTRACT TMATE ==="

rm -rf /tmp/tmate-2.4.0-static-linux-amd64

tar -xf /tmp/tmate.tar.xz -C /tmp

cp /tmp/tmate-2.4.0-static-linux-amd64/tmate "$TMATE_BIN"

chmod +x "$TMATE_BIN"

echo "=== TMATE VERSION ==="

"$TMATE_BIN" -V

echo "=== START TMATE ==="

rm -f "$TMATE_SOCKET"
rm -f "$TMATE_LOG"

"$TMATE_BIN" \
    -S "$TMATE_SOCKET" \
    new-session -d -s beam

echo "TMATE SESSION CREATED"

TMATE_SSH=""

echo ""
echo "=========================================="
echo "       SEARCHING FOR TMATE SSH"
echo "=========================================="
echo ""

for i in $(seq 1 90); do

    "$TMATE_BIN" \
        -S "$TMATE_SOCKET" \
        show-messages 2>&1 | tee "$TMATE_LOG" || true

    TMATE_SSH=$(
        grep -Eo 'ssh [^[:space:]]+@[^[:space:]]+\.tmate\.io' "$TMATE_LOG" |
        head -n 1 || true
    )

    if [ -n "$TMATE_SSH" ]; then

        echo ""
        echo "=========================================="
        echo "             SSH READY"
        echo "=========================================="
        echo ""
        echo "$TMATE_SSH"
        echo ""
        echo "=========================================="
        echo ""

        break
    fi

    echo ""
    echo "Waiting for TMATE SSH... $i/90"
    sleep 2
done

if [ -z "$TMATE_SSH" ]; then

    echo ""
    echo "=========================================="
    echo "       TMATE SSH NOT AVAILABLE"
    echo "=========================================="
    echo ""

    echo "=== LAST TMATE MESSAGES ==="

    cat "$TMATE_LOG" 2>/dev/null || true

    echo ""
    echo "=== SOCKET CHECK ==="

    ls -la "$TMATE_SOCKET" 2>/dev/null || true

    exit 1
fi

echo "=== GPU STATUS ==="

nvidia-smi

echo ""
echo "=========================================="
echo "       CONTAINER IS RUNNING"
echo "             FOR 30 HOURS"
echo "=========================================="
echo ""

while true; do

    echo "=== HEARTBEAT ==="
    date

    echo ""

    nvidia-smi \
        --query-gpu=name,temperature.gpu,memory.used,memory.total,utilization.gpu \
        --format=csv,noheader \
        2>/dev/null || true

    echo ""

    if [ -S "$TMATE_SOCKET" ]; then
        echo "TMATE socket: OK"
    else
        echo "TMATE socket: MISSING"
    fi

    echo ""

    sleep 600

done
'''

    result = subprocess.run(
        ["bash", "-lc", cmd],
        check=False,
    )

    print("")
    print("==========================================")
    print("       BASH PROCESS EXITED")
    print("==========================================")
    print("")
    print("Exit code:", result.returncode)

    while True:
        time.sleep(3600)
