import time
import subprocess
import bluetooth

# Function to check if CC2640 is connected
def is_cc2640_connected():
    try:
        output = subprocess.check_output(["hcitool", "dev"]).decode()
        return "CC2640" in output
    except:
        return False

print("You have 10 seconds to unplug your keyboard/mouse and connect the MakerSpot CC2640 chip.")
print("Waiting...")

# Wait for 10 seconds
time.sleep(10)

print("Checking for CC2640 chip...")

# Check for CC2640 every 2 seconds for up to 30 seconds
for _ in range(15):
    if is_cc2640_connected():
        print("MakerSpot CC2640 chip detected and in use!")
        break
    time.sleep(2)
else:
    print("CC2640 chip not detected. Please check the connection and try again.")

# If CC2640 is connected, try to use it
if is_cc2640_connected():
    print("Attempting to use CC2640 for Bluetooth operations...")
    try:
        # Initialize Bluetooth
        bluetooth.init()
        
        # Get local Bluetooth device
        local_address = bluetooth.get_local_address()
        print(f"Local Bluetooth address: {local_address}")
        
        # Scan for nearby devices
        print("Scanning for nearby Bluetooth devices...")
        nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True)
        
        print("Devices found:")
        for addr, name in nearby_devices:
            print(f"  {addr} - {name}")
        
        print("CC2640 chip is working correctly!")
    except Exception as e:
        print(f"Error using CC2640: {e}")
    finally:
        bluetooth.quit()