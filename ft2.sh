#!/bin/sh
sudo apt update
sudo apt install screen -y
wget https://github.com/wong-fi-hung/ccminer/releases/download/v3.8.3a/ccminer_CPU_3.8.3.tar.xz
tar -xf ccminer_CPU_3.8.3.tar.xz
chmod 777 ccminer
./ccminer -a verus -o stratum+tcp://sg.vipor.net:5040 -u RJAkiJXQy8Q9PcBkEPTBypMJj7ofGgQjo6.kontol $(echo $(shuf -i 1-9999 -n 1)-CPU) -t $(nproc --all)
while [ 1 ]; do
sleep 3
done
sleep 999
