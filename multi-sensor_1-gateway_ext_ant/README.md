# Instructions to incorperate external antenna into rpi zero w2

1. Plug in the adapter then boot the pi

2. Run the command to open the file:
```
sudo nano /boot/firmware/config.txt
```
3. When the file is open, add the line: 
```
dtoverlay=disable-bt
```
4. Save the file and reboot the pi

5. Open a terminal window and run the command:
```
sudo hciconfig
```
6. Make sure the adapter pops up, and the status should say 'UP'.

If the hci0 is down run the command:
```
sudo hciconfig hci0 up

```
7. Check that the bluetooth service is running with:
```
sudo systemctl status bluetooth
```
If inactive, run the command:
```
sudo systemctl start bluetooth
```
8. Next we need to power on the adapter with the command:
```
bluetoothctl
```
Then in the bluetooth control write:
```
power on
```
Exit the control with:
```
exit
```
9. You can then run the scripts with hopefully no errors
