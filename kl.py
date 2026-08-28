from beam import function, Image
import subprocess
import time

image = (
    Image(base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04")
    .add_commands([
        "apt-get update -y",
        "apt-get install -y python3 python3-pip procps screen",
    ])
)

@function(
    name="gpu-shell",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=30 * 60 * 60,
)
def run_script():
    print("==========================================")
    print("       BEAM RTX4090 CONTAINER")
    print("==========================================")
    print("=== GPU STATUS ===")
    subprocess.run(["nvidia-smi"], check=False)
    print("=== SYSTEM INFORMATION ===")
    print("CPU:")
    subprocess.run(["nproc"], check=False)
    print("Memory:")
    subprocess.run(["free", "-h"], check=False)
    print("Disk:")
    subprocess.run(["df", "-h", "/"], check=False)
    print("==========================================")
    print("        CONTAINER IS READY")
    print("==========================================")
    print("GPU       : RTX4090")
    print("CPU       : 2")
    print("RAM       : 4Gi")
    print("TIMEOUT   : 30 HOURS")
    print("")
    print("Masuk dengan: beam shell kl.py:run_script")
    print("Setelah masuk: nvidia-smi")
    print("Untuk session: screen -S program")
    print("Jalankan: python3 program.py")
    print("Detach: CTRL+A lalu D")
    print("Kembali: screen -r program")

    while True:
        print("=== HEARTBEAT ===")
        print(time.strftime("%Y-%m-%d %H:%M:%S"))
        subprocess.run([
            "nvidia-smi",
            "--query-gpu=name,temperature.gpu,memory.used,memory.total,utilization.gpu",
            "--format=csv,noheader",
        ], check=False)
        time.sleep(600)
