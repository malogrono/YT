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

echo "=== START TMATE SESSION ==="

rm -f "$TMATE_SOCKET"

"$TMATE_BIN" \
    -S "$TMATE_SOCKET" \
    new-session \
    -d \
    -s beam

echo "TMATE session created."

echo ""
echo "=== WAITING FOR TMATE SSH ==="
echo ""

TMATE_SSH=""

for i in $(seq 1 60); do

    TMATE_SSH=$(
        "$TMATE_BIN" \
        -S "$TMATE_SOCKET" \
        display -p '#{tmate_ssh}' 2>/dev/null || true
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

    echo "Waiting for TMATE SSH... $i/60"
    sleep 2
done

if [ -z "$TMATE_SSH" ]; then

    echo ""
    echo "=========================================="
    echo "       TMATE SSH NOT AVAILABLE"
    echo "=========================================="
    echo ""

    "$TMATE_BIN" \
        -S "$TMATE_SOCKET" \
        show-messages || true

    exit 1
fi

echo "=== TMATE WEB ==="

"$TMATE_BIN" \
    -S "$TMATE_SOCKET" \
    display -p '#{tmate_web}' || true

echo ""
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
