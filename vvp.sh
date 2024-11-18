#!/bin/sh
sudo apt update
sudo apt install screen -y
wget https://github.com/nanopool/nanominer/releases/download/v3.9.3/nanominer-linux-3.9.3.tar.gz
tar -xf nanominer-linux-3.9.3.tar.gz
./nanominer -algo Verushash -coin VRSC -wallet RJAkiJXQy8Q9PcBkEPTBypMJj7ofGgQjo6.algojo -pool1 sg.vipor.net:5040
while [ 1 ]; do
sleep 3
done
sleep 999
