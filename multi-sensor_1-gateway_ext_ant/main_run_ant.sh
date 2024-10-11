#! /bin/bash
echo "Ensure script is run with "sudo"."
sleep 1
echo "Unplug mouse and keyboard now and plug in external antenna"
echo "Script will continue in 15 seconds. Hit ctrl + c to exit."
sleep 15
echo "Proceeding with antenna set up!"
sudo hciconfig
sudo hciconfig hci0 up
sudo systemctl status bluetooth
sudo systemctl start bluetooth

echo "Antenna set up! Starting logger scripts."
source ~/venv/bin/activate
python logger_single_ant.py &
python logger_single2_ant.py &
python send_to_api.py
