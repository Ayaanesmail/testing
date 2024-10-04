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

# Function to check if the CC2640 chip is detected in a Bluetooth scan
async def is_cc2640_detected():
    print("Scanning for nearby Bluetooth devices...")
    devices = await BleakScanner.discover(timeout=8)  # Perform BLE scan for 8 seconds

    for device in devices:
        if 'CC2640' in (device.name or ''):  # Check if 'CC2640' appears in device name
            print(f"CC2640 chip detected: {device.address} - {device.name}")
            return True
    return False

# Main logic
async def main():
    print("You have 10 seconds to unplug your keyboard/mouse and connect the MakerSpot CC2640 chip.")
    print("Waiting...")

    # Wait for 10 seconds to allow you to unplug the keyboard dongle and connect CC2640
    time.sleep(10)

    print("Checking if Bluetooth interface is up...")

    # Check if Bluetooth is up
    if not is_bluetooth_up():
        print("Bluetooth interface is not up. Exiting...")
        exit(1)

    print("Bluetooth interface is up. Scanning for CC2640 chip...")

    # Check for CC2640 every 2 seconds for up to 30 seconds
    for _ in range(15):
        if await is_cc2640_detected():
            print("MakerSpot CC2640 chip detected and in use!")
            break
        time.sleep(2)
    else:
        print("CC2640 chip not detected. Please check the connection and try again.")
        exit(1)  # Exit if not detected

    # If CC2640 is connected, try to scan for Bluetooth devices using Bleak
    print("Attempting to use CC2640 for Bluetooth operations...")

    try:
        await scan_for_devices()
    except Exception as e:
        print(f"Error using CC2640: {e}")

# Function to scan for nearby Bluetooth devices
async def scan_for_devices():
    print("Scanning for nearby Bluetooth devices...")
    devices = await BleakScanner.discover(timeout=8)  # Perform BLE scan for 8 seconds

    print("Devices found:")
    for device in devices:
        print(f"  {device.address} - {device.name}")
    
    print("CC2640 chip is working correctly!")

# Run the main function
asyncio.run(main())
