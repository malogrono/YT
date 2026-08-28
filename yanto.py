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

    cmd = r"""
set -e

TMATE_DIR="/opt/tmate"
TMATE_BIN="$TMATE_DIR/tmate"
TMATE_SOCKET="/tmp/tmate.sock"
AUTHORIZED_KEYS="/root/.tmate_authorized_keys"

mkdir -p "$TMATE_DIR"

echo "=== INSTALL TMATE ==="

cd /tmp

wget -q \
    https://github.com/tmate-io/tmate/releases/download/2.4.0/tmate-2.4.0-static-linux-amd64.tar.xz \
    -O /tmp/tmate.tar.xz

rm -rf /tmp/tmate-2.4.0-static-linux-amd64
tar -xf /tmp/tmate.tar.xz -C /tmp
cp /tmp/tmate-2.4.0-static-linux-amd64/tmate "$TMATE_BIN"
chmod +x "$TMATE_BIN"

echo "=== TMATE VERSION ==="
"$TMATE_BIN" -V

echo "=== CREATE TMATE AUTHORIZED KEY FILE ==="

cat > "$AUTHORIZED_KEYS" <<'KEYEOF'
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICIncgE5CCVHMLsEukl5ED4pgL4UTRhWrTgRmPOe0Tb9 beam2
KEYEOF

chmod 600 "$AUTHORIZED_KEYS"

echo ""
echo "Authorized public key fingerprint:"
ssh-keygen -lf "$AUTHORIZED_KEYS" || true

echo ""
echo "=== START TMATE SESSION ==="

rm -f "$TMATE_SOCKET"

"$TMATE_BIN" \
    -S "$TMATE_SOCKET" \
    -a "$AUTHORIZED_KEYS" \
    new-session -d -s beam

echo "=== WAIT FOR TMATE READY ==="

"$TMATE_BIN" \
    -S "$TMATE_SOCKET" \
    wait tmate-ready

echo "=== TMATE READY ==="

echo ""
echo "=========================================="
echo "             TMATE SSH"
echo "=========================================="
echo ""

TMATE_SSH=""

for i in $(seq 1 30); do

    TMATE_SSH=$(
        "$TMATE_BIN" \
        -S "$TMATE_SOCKET" \
        display -p '#{tmate_ssh}' 2>/dev/null || true
    )

    if [ -n "$TMATE_SSH" ]; then
        break
    fi

    echo "Waiting for SSH URL... $i/30"
    sleep 2

done

if [ -z "$TMATE_SSH" ]; then

    echo ""
    echo "ERROR: TMATE SSH URL NOT AVAILABLE"
    echo ""

    "$TMATE_BIN" \
        -S "$TMATE_SOCKET" \
        show-messages || true

    exit 1
fi

echo ""
echo "=========================================="
echo "             SSH READY"
echo "=========================================="
echo ""
echo "$TMATE_SSH"
echo ""
echo "=========================================="
echo ""

echo "Use the private key corresponding to beam2:"
echo ""
echo 'ssh -i ~/.ssh/beam2 <TMATE_SSH_USER>@<TMATE_SSH_HOST>'
echo ""

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

    nvidia-smi \
        --query-gpu=name,temperature.gpu,memory.used,memory.total,utilization.gpu \
        --format=csv,noheader \
        2>/dev/null || true

    echo ""

    if [ -S "$TMATE_SOCKET" ]; then
        echo "TMATE status: RUNNING"
    else
        echo "TMATE socket missing"
    fi

    echo ""

    sleep 600

done
"""

    result = subprocess.run(
        ["bash", "-lc", cmd],
        check=False,
    )

    print("")
    print("BASH PROCESS EXITED")
    print("Exit code:", result.returncode)

    while True:
        time.sleep(3600)
