echo "python3 $(pwd)/debugger.py \$@" | sudo tee /usr/bin/vdebugger
sudo chmod 775 /usr/bin/vdebugger
