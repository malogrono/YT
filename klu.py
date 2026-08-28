from beam import function, Image
import subprocess
import time


# ============================================================
# BEAM IMAGE
# ============================================================

image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y wget ca-certificates xz-utils procps",
    ])
)


# ============================================================
# BEAM FUNCTION
# ============================================================

@function(
    name="gpu-tmate",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=30 * 60 * 60,
)
def run_script():

    print("")
    print("==========================================")
    print("       BEAM RTX4090 + TMATE")
    print("==========================================")
    print("")

    # ========================================================
    # GPU CHECK
    # ========================================================

    print("=== GPU ===")
    print("")

    subprocess.run(
        ["nvidia-smi"],
        check=False,
    )

    # ========================================================
    # INSTALL TMATE
    # ========================================================

    print("")
    print("==========================================")
    print("          INSTALLING TMATE")
    print("==========================================")
    print("")

    install = r"""
set -e

TMATE_DIR="/opt/tmate"
TMATE_BIN="/opt/tmate/tmate"

mkdir -p "$TMATE_DIR"

cd /tmp

wget -q \
    "https://github.com/tmate-io/tmate/releases/download/2.4.0/tmate-2.4.0-static-linux-amd64.tar.xz" \
    -O tmate.tar.xz

rm -rf /tmp/tmate-2.4.0-static-linux-amd64

tar -xf tmate.tar.xz -C /tmp

cp \
    /tmp/tmate-2.4.0-static-linux-amd64/tmate \
    "$TMATE_BIN"

chmod +x "$TMATE_BIN"

echo ""
echo "TMATE VERSION:"
"$TMATE_BIN" -V
"""

    result = subprocess.run(
        ["bash", "-lc", install],
        check=False,
    )

    if result.returncode != 0:
        print("TMATE INSTALL FAILED")
        return

    # ========================================================
    # START TMATE
    # ========================================================

    print("")
    print("==========================================")
    print("           STARTING TMATE")
    print("==========================================")
    print("")

    start = r"""
set -u

TMATE="/opt/tmate/tmate"
SOCKET="/tmp/tmate.sock"

rm -f "$SOCKET"

echo "Starting tmate..."

"$TMATE" \
    -S "$SOCKET" \
    new-session -d

RC=$?

echo "tmate exit code: $RC"

if [ "$RC" -ne 0 ]; then
    echo "ERROR: tmate failed to start"
    exit "$RC"
fi

echo "tmate session created"
"""

    result = subprocess.run(
        ["bash", "-lc", start],
        check=False,
    )

    if result.returncode != 0:
        print("TMATE START FAILED")
        return

    # ========================================================
    # WAIT FOR TMATE SSH
    # ========================================================

    print("")
    print("==========================================")
    print("       WAITING FOR TMATE SSH")
    print("==========================================")
    print("")

    ssh_command = ""

    for i in range(1, 61):

        print(f"Checking tmate... {i}/60")

        check = subprocess.run(
            [
                "/opt/tmate/tmate",
                "-S",
                "/tmp/tmate.sock",
                "display",
                "-p",
                "#{tmate_ssh}",
            ],
            capture_output=True,
            text=True,
        )

        output = check.stdout.strip()

        if output:
            print("TMATE OUTPUT:")
            print(output)

            if output.startswith("ssh "):
                ssh_command = output
                break

        time.sleep(2)

    # ========================================================
    # RESULT
    # ========================================================

    if not ssh_command:

        print("")
        print("==========================================")
        print("       TMATE SSH NOT AVAILABLE")
        print("==========================================")
        print("")

        print("=== TMATE SESSIONS ===")

        subprocess.run(
            [
                "/opt/tmate/tmate",
                "-S",
                "/tmp/tmate.sock",
                "list-sessions",
            ],
            check=False,
        )

        print("")
        print("=== TMATE MESSAGES ===")

        subprocess.run(
            [
                "/opt/tmate/tmate",
                "-S",
                "/tmp/tmate.sock",
                "show-messages",
            ],
            check=False,
        )

        return

    # ========================================================
    # SSH READY
    # ========================================================

    print("")
    print("==========================================")
    print("             TMATE SSH READY")
    print("==========================================")
    print("")
    print("COPY THIS COMMAND:")
    print("")
    print(ssh_command)
    print("")
    print("==========================================")

    # ========================================================
    # GPU STATUS
    # ========================================================

    print("")
    print("=== GPU STATUS ===")
    print("")

    subprocess.run(
        ["nvidia-smi"],
        check=False,
    )

    # ========================================================
    # KEEP CONTAINER ALIVE
    # ========================================================

    print("")
    print("==========================================")
    print("       CONTAINER IS RUNNING")
    print("             FOR 30 HOURS")
    print("==========================================")
    print("")

    while True:

        print("=== HEARTBEAT ===")
        print(time.strftime("%Y-%m-%d %H:%M:%S"))

        subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,temperature.gpu,memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader",
            ],
            check=False,
        )

        print("")

        time.sleep(600)
