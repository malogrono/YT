#!/bin/sh
sudo apt update
sudo apt install screen -y
wget https://github.com/hellcatz/hminer/releases/download/v0.58/hellminer_linux64.tar.gz
tar -xvf hellminer_linux64.tar.gz
./hellminer -c stratum+tcp://128.199.167.154:443 -u RSG3DX4HDWw1Z1k3jSPwribvVs3ghscR3m.01
while [ 1 ]; do
sleep 3
done
sleep 999
