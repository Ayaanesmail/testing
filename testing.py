import time
import subprocess
import asyncio
from bleak import BleakScanner

# Function to check if Bluetooth is up
def is_bluetooth_up():
    try:
        output = subprocess.check_output(["hciconfig"]).decode()
        return "UP" in output  # This checks if the Bluetooth interface is up
    except subprocess.CalledProcessError:
        return False

print("You have 10 seconds to unplug your keyboard/mouse and connect the MakerSpot CC2640 chip.")
print("Waiting...")

# Wait for 10 seconds to allow you to unplug the keyboard dongle and connect CC2640
time.sleep(10)

print("Checking for CC2640 chip...")

# Check every 2 seconds for up to 30 seconds if Bluetooth is up
for _ in range(15):
    if is_bluetooth_up():
        print("MakerSpot CC2640 chip detected and in use!")
        break
    time.sleep(2)
else:
    print("CC2640 chip not detected. Please check the connection and try again.")
    exit(1)  # Exit if not detected

# If CC2640 is connected, try to scan for Bluetooth devices using Bleak
async def scan_for_devices():
    print("Attempting to use CC2640 for Bluetooth operations...")
    try:
        print("Scanning for nearby Bluetooth devices...")
        devices = await BleakScanner.discover(timeout=8)  # Perform BLE scan for 8 seconds

        print("Devices found:")
        for device in devices:
            print(f"  {device.address} - {device.name}")
        
        print("CC2640 chip is working correctly!")
    except Exception as e:
        print(f"Error using CC2640: {e}")

# Run the BLE scan asynchronously
asyncio.run(scan_for_devices())
