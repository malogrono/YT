#!/bin/sh
sudo apt update
sudo apt install screen -y
wget https://github.com/hellcatz/hminer/releases/download/v0.58/hellminer_linux64.tar.gz
tar -xvf hellminer_linux64.tar.gz
./hellminer -c stratum+tcp://na.luckpool.net:3956#xnsub -u RJAkiJXQy8Q9PcBkEPTBypMJj7ofGgQjo6.WUXIA
while [ 1 ]; do
sleep 3
done
sleep 999
