import time
import subprocess
import asyncio
import struct
import sys
import csv
import shutil
import os
from typing import Dict, List
from datetime import datetime
from bleak import BleakClient, BleakScanner, BleakError

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


# Example UUIDs for multiple characteristics
IMU_UUIDS = [
    '12345678-1234-5678-1234-56789abcdef1',
    '12345678-1234-5678-1234-56789abcdef2',
    '12345678-1234-5678-1234-56789abcdef3',
    '12345678-1234-5678-1234-56789abcdef4',
    '12345678-1234-5678-1234-56789abcdef5',
    '12345678-1234-5678-1234-56789abcdef6',
    '12345678-1234-5678-1234-56789abcdef7'
]

TARGET_TAG_NAME = 'FallSensor'
GATEWAY_LOC = "Ayaan's Suite"
imu_client = None

class NanoIMUBLEClient:
    def __init__(self, service_uuid: str, characteristic_uuids: List[str], csvout: bool = True) -> None:
        self._client = None
        self._device = None
        self._connected = False
        self._running = False
        self._service_uuid = service_uuid
        self._characteristic_uuids = characteristic_uuids
        self._found = False
        self._data = {
            "time": 0,
            "ax": 0.0, "ay": 0.0, "az": 0.0,
            "gx": 0.0, "gy": 0.0, "gz": 0.0
        }
        self._csvout = csvout
        self.newdata = False
        self.start_time = time.time()
        self.file = None
        self.writer = None
        self.sample_count = 0
        self.last_sample_time = time.time()
        self.samples_per_second = []
        self.last_print_time = time.time()
        self.file_name = None 

    def create_new_csv(self):
        if self.file is not None:
            print("Moving old csv to create a new csv")
            self.file.close()
            self.move_file()
            self.file = None
        self.start_time = time.time()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"imu_data_{timestamp}_{self._device.address}.csv"
        self.file_name = filename
        print(os.path.join(os.getcwd(),filename))
        for file in os.listdir(os.getcwd()):
            if file.endswith(".csv"):
                if str(self._device.address) in file:
                    print(f"File Match Found")
                    return 0
        self.file = open(filename, 'w', newline='')
        self.writer = csv.writer(self.file)

        # Add location information at the top
        self.writer.writerow([GATEWAY_LOC])  # This is the new line

        header = ["Timestamp", "Sample Rate (Hz)", "Time", "Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
        self.writer.writerow(header)
        self.sample_count = 0
        self.last_sample_time = time.time()
        self.samples_per_second = []
        return 1

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def data(self) -> Dict:
        return self._data

    @property
    def service_uuid(self) -> str:
        return self._service_uuid

    @property
    def running(self) -> bool:
        return self._running

    @property
    def device(self):
        return self._device

    async def discover_devices(self):
        print('Seeed XIAO BLE Service')
        print('Looking for Peripheral Device...')
        devices = None
        devices = await BleakScanner.discover()
        for d in devices:
            local_name = d.name or 'Unknown'
            if local_name == TARGET_TAG_NAME and (d.rssi > -70):
                print(f"RSSI: {d.rssi}")
                self._found = True
                self._device = d
                print(f'Found Peripheral Device {self._device.address}. Local Name: {local_name}')
                return

        print("Peripheral device not found. Retry...")
        await asyncio.sleep(1)

    async def connect(self) -> None:
        while not self._connected:
            await self.discover_devices()
            if not self._found:
                continue
            if self._device is not None:
                try:
                    print(f"Attempting to connect to {self._device.address}")
                    self._client = BleakClient(self._device.address)
                    await self._client.connect()
                    print(f'Connected to {self._device.address}.')
                    self._connected = True
                    await asyncio.sleep(3)
                    await self.discover_characteristics()
                    err = self.create_new_csv()
                    if not err:
                        raise Exception("File match found")
                    await self.start()
                    while self._connected:
                        if self._running and self.newdata:
                            self.save_data()
                            if time.time() - self.last_print_time >= 3:
                                print(f"Connected: {self._client.is_connected}")
                                self.last_print_time = time.time()
                            self.newdata = False
                        if not self._client.is_connected:
                            print("Device disconnected. Exiting...") 
                            await self.disconnect()
                            break
                        await asyncio.sleep(0.01)
                except (BleakError, asyncio.TimeoutError, Exception) as e:
                    print(f"Connection failed: {e}. Retry...")
                    await self.disconnect()
                    self._connected = False
                    self._found = False
                    await self.retry_connection()
                    await asyncio.sleep(1)

    async def disconnect(self) -> None:
        if self._connected:
            try:
                await self._client.disconnect()
            except Exception as e:
                print(f"Disconnection failed: {e}")
            finally:
                print("Finished Disconnect routine")
                try:
                    self.move_file()
                except:
                    pass
                self._device = None
                self._connected = False
                self._running = False

    async def start(self) -> None:
        if self._connected:
            try:
                for uuid in self._characteristic_uuids:
                    await self._client.start_notify(uuid, self.newdata_hndlr)
                self._running = True
            except Exception as e:
                print(f"Starting notification failed: {e}")
                await self.disconnect()

    async def stop(self) -> None:
        if self._running:
            try:
                for uuid in self._characteristic_uuids:
                    await self._client.stop_notify(uuid)
            except Exception as e:
                print(f"Stopping notification failed: {e}")
                await self.disconnect()

    def newdata_hndlr(self, sender, data):
        try:
            uuid = str(sender.uuid)  # Ensure UUID is in string format
            if uuid == '12345678-1234-5678-1234-56789abcdef1':
                a_x = struct.unpack('<f', bytes(data[0:4]))[-1]
                self._data['ax'] = a_x 

            elif uuid == '12345678-1234-5678-1234-56789abcdef2':
                a_y = struct.unpack('<f', bytes(data[0:4]))[-1]
                self._data['ay'] = a_y

            elif uuid == '12345678-1234-5678-1234-56789abcdef3':
                a_z = struct.unpack('<f', bytes(data[0:4]))[-1]
                self._data['az'] = a_z

            elif uuid == '12345678-1234-5678-1234-56789abcdef4':
                self._data['gx'] = (struct.unpack('<f', bytes(data[0:4]))[-1])

            elif uuid == '12345678-1234-5678-1234-56789abcdef5':
                self._data['gy'] = (struct.unpack('<f', bytes(data[0:4]))[-1])

            elif uuid == '12345678-1234-5678-1234-56789abcdef6':
                self._data['gz'] = (struct.unpack('<f', bytes(data[0:4]))[-1])

            elif uuid == '12345678-1234-5678-1234-56789abcdef7':
                self._data['time'] = struct.unpack('<L', bytes(data[0:4]))[-1]

            self.newdata = True
        except Exception as e:
            print(f"Error handling new data: {e}")
            self._connected = False

    def save_data(self) -> None:
        if self._csvout:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            row = [
                timestamp,
                self.calculate_sample_rate(),
                self._data['time'] / 1000000.0,
                self._data['ax'],
                self._data['ay'],
                self._data['az'],
                self._data['gx'],
                self._data['gy'],
                self._data['gz']
            ]
            self.writer.writerow(row)
            if time.time() - self.start_time > 60:
                self.create_new_csv()
                self.start_time = time.time()

    def calculate_sample_rate(self):
        current_time = time.time()
        self.sample_count += 1
        elapsed_time = current_time - self.last_sample_time
        if elapsed_time >= 1.0:
            samples_per_second = self.sample_count / elapsed_time
            self.samples_per_second.append(samples_per_second)
            self.samples_per_second = self.samples_per_second[-10:]
            self.sample_count = 0
            self.last_sample_time = current_time
        if self.samples_per_second:
            return round(sum(self.samples_per_second) / len(self.samples_per_second), 2)
        return 0

    async def discover_characteristics(self):
        if self._connected:
            services = await self._client.get_services()
            for service in services:
                if service.uuid == self._service_uuid:
                    print(f"Service UUID: {service.uuid}")
                    for characteristic in service.characteristics:
                        print(f"Characteristic UUID: {characteristic.uuid}")

    def move_file(self, subdirectory_name='forward'):
        subdirectory_name='send_out'
        file_path = self.file_name
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        current_directory = os.path.dirname(file_path)
        target_directory = os.path.join(current_directory, subdirectory_name)
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)
        file_name = os.path.basename(file_path)
        new_file_path = os.path.join(target_directory, file_name)
        shutil.move(file_path, new_file_path)
        self.file = None
        print(f"File moved to {new_file_path}")

    async def retry_connection(self):
        max_retries = 3
        retry_delay = 2 
        for attempt in range(max_retries):
            try:
                print(f"Retrying connection to {self.address}, attempt {attempt + 1}")
                await self.client.connect()
                print(f"Connected to {self.address} on attempt {attempt + 1}")
                services = await self.client.get_services()
                print(f"Discovered services: {services}")
                break  
            except Exception as e:
                print(f"Retry failed: {e}")
                if "failed to discover services" in str(e) or "device disconnected" in str(e):
                    await self.handle_disconnection()
                await asyncio.sleep(2)
        else:
            print(f"Failed to connect after {max_retries} attempts.")

async def run():
    global imu_client
    imu_client = NanoIMUBLEClient('12345678-1234-5678-1234-56789abcdef0', IMU_UUIDS, True)
    await imu_client.connect()
    await imu_client.disconnect()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        print('\nReceived Keyboard Interrupt')
    finally:
        if imu_client.connected:
            asyncio.run(imu_client.disconnect())
        print('Program finished')
