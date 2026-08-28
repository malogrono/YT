from beam import function, Image
import subprocess
import time
import os


image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y openssh-server curl ca-certificates procps",
    ])
)


@function(
    name="gpu-ngrok-ssh",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=30 * 60 * 60,
    secrets=["NGROK_AUTHTOKEN"],
)
def run_script():

    print("==========================================")
    print("       BEAM RTX4090 + NGROK SSH")
    print("==========================================")

    # --------------------------------------------------------
    # CEK TOKEN
    # --------------------------------------------------------

    token = os.environ.get("NGROK_AUTHTOKEN")

    if not token:
        print("ERROR: NGROK_AUTHTOKEN tidak tersedia.")
        return

    # --------------------------------------------------------
    # CEK GPU
    # --------------------------------------------------------

    print("")
    print("=== GPU ===")
    subprocess.run(["nvidia-smi"], check=False)

    # --------------------------------------------------------
    # SETUP SSH
    # --------------------------------------------------------

    print("")
    print("=== SETUP SSH ===")

    subprocess.run(
        ["mkdir", "-p", "/run/sshd"],
        check=False,
    )

    subprocess.run(
        ["useradd", "-m", "-s", "/bin/bash", "beam"],
        check=False,
    )

    subprocess.run(
        ["mkdir", "-p", "/home/beam/.ssh"],
        check=False,
    )

    public_key = (
        "ssh-ed25519 "
        "AAAAC3NzaC1lZDI1NTE5AAAAICIncgE5CCVHMLsEukl5ED4pgL4UTRhWrTgRmPOe0Tb9 "
        "beam2"
    )

    with open(
        "/home/beam/.ssh/authorized_keys",
        "w",
    ) as f:
        f.write(public_key + "\n")

    subprocess.run(
        ["chmod", "700", "/home/beam/.ssh"],
        check=False,
    )

    subprocess.run(
        ["chmod", "600", "/home/beam/.ssh/authorized_keys"],
        check=False,
    )

    subprocess.run(
        ["chown", "-R", "beam:beam", "/home/beam/.ssh"],
        check=False,
    )

    # --------------------------------------------------------
    # SSH CONFIG
    # --------------------------------------------------------

    with open(
        "/etc/ssh/sshd_config",
        "w",
    ) as f:

        f.write("""Port 22
ListenAddress 0.0.0.0
PubkeyAuthentication yes
PasswordAuthentication no
PermitRootLogin no
AuthorizedKeysFile .ssh/authorized_keys
UsePAM no
AllowTcpForwarding yes
""")

    # --------------------------------------------------------
    # START SSH
    # --------------------------------------------------------

    print("")
    print("=== START SSH SERVER ===")

    subprocess.run(
        ["/usr/sbin/sshd"],
        check=False,
    )

    # --------------------------------------------------------
    # INSTALL NGROK
    # --------------------------------------------------------

    print("")
    print("=== INSTALL NGROK ===")

    install = """
cd /opt

curl -fsSL \
https://bin.ngrok.com/c/bNyj1mQV4Yc/ngrok-v3-stable-linux-amd64.tgz \
-o ngrok.tgz

tar -xzf ngrok.tgz

chmod +x ngrok

./ngrok version
"""

    result = subprocess.run(
        ["bash", "-lc", install],
        check=False,
    )

    if result.returncode != 0:
        print("NGROK INSTALL FAILED")
        return

    # --------------------------------------------------------
    # CONFIGURE TOKEN
    # --------------------------------------------------------

    print("")
    print("=== CONFIGURE NGROK ===")

    subprocess.run(
        [
            "/opt/ngrok",
            "config",
            "add-authtoken",
            token,
        ],
        check=False,
    )

    # --------------------------------------------------------
    # START NGROK
    # --------------------------------------------------------

    print("")
    print("=== START NGROK TCP ===")

    log_file = open(
        "/tmp/ngrok.log",
        "w",
    )

    ngrok = subprocess.Popen(
        [
            "/opt/ngrok",
            "tcp",
            "22",
        ],
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )

    # --------------------------------------------------------
    # WAIT
    # --------------------------------------------------------

    tunnel = ""

    for i in range(30):

        time.sleep(2)

        if ngrok.poll() is not None:
            break

        try:
            with open(
                "/tmp/ngrok.log",
                "r",
            ) as f:
                log = f.read()

            for line in log.splitlines():

                if "url=tcp://" in line:
                    tunnel = line
                    break

        except Exception:
            pass

        if tunnel:
            break

        print(
            f"Waiting for ngrok... {i + 1}/30"
        )

    # --------------------------------------------------------
    # SHOW CONNECTION
    # --------------------------------------------------------

    print("")
    print("==========================================")

    if tunnel:

        print("       NGROK SSH READY")
        print("")
        print(tunnel)

    else:

        print("       NGROK SSH NOT READY")
        print("")
        print("=== NGROK LOG ===")

        try:
            with open(
                "/tmp/ngrok.log",
                "r",
            ) as f:
                print(f.read())
        except Exception:
            pass

    print("==========================================")

    # --------------------------------------------------------
    # KEEP CONTAINER ALIVE
    # --------------------------------------------------------

    while True:

        print("")
        print("=== HEARTBEAT ===")
        print(
            time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,temperature.gpu,"
                "memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader",
            ],
            check=False,
        )

        time.sleep(600)
