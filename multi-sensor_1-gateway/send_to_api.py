import requests
import os
import time
import csv
import json
import shutil

def upload_json_to_api(file_path: str, api_url: str, headers: dict = None) -> None:
    """
    Upload a JSON file to a REST API.

    :param file_path: Path to the JSON file to upload.
    :param api_url: URL of the REST API endpoint.
    :param headers: Optional headers to include in the request (e.g., for authentication).
    :return: None
    """
    try:
        # Open the JSON file
        with open(file_path, 'rb') as file:
            # Create a dictionary to represent the file payload
            files = {'file': (file_path, file, 'application/json')}
            
            # Send a POST request to the API
            response = requests.post(api_url, data=file, headers=headers)
            
            # Check if the request was successful
            if response.status_code == 200:
                print("File uploaded successfully.")
                print("Response:", response.json())
            else:
                f = open("error_log.txt", "a")
                f.write(f"Failed to upload file. Status code: {response.status_code}")
                f.write(f"Response: {response.text}")
                #now = time.datetime.now()
                #current= now.strftime("%H:%M:%S") 
                #f.write(f"Time: {current}")
                f.write("-------------------------------")
                print(f"Failed to upload file. Status code: {response.status_code}")
                print("Response:", response.text)
                

    except Exception as e:

        f = open("error_log.txt", "a")
        f.write(f"Error upload file: {e}")
        #now = time.datetime.now()
        #current= now.strftime("%H:%M:%S") 
        #f.write(f"Time: {current}")
        f.write("-------------------------------")

        print(f"Error uploading file: {e}")

def get_csv_files_from_directory(directory_path: str) -> list:
    """
    Get a list of all CSV files in a given directory.

    :param directory_path: Path to the directory to scan for CSV files.
    :return: List of paths to CSV files.
    """
    csv_files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.endswith('.csv')]
    return csv_files

def get_oldest_file(files: list) -> str:
    """
    Get the path to the oldest file in a list of files.

    :param files: List of file paths.
    :return: Path to the oldest file.
    """
    if not files:
        return None

    # Initialize with the first file
    oldest_file = files[0]
    oldest_time = os.path.getmtime(oldest_file)

    for file in files[1:]:
        file_time = os.path.getmtime(file)
        if file_time < oldest_time:
            oldest_file = file
            oldest_time = file_time

    return oldest_file

def send_to_rest_api(api_url, file):
    # Define optional headers if needed (e.g., for authentication)
    headers = {
           'Content-Type': 'application/json'  # Optional: specify content type if required
    }

    # Upload the file
    upload_json_to_api(file, api_url, headers)

def csv_to_json(csv_file_path):
    
    file_name = os.path.splitext(csv_file_path)[0]
    # Create a new file path with .json extension
    json_file_path = f"{file_name}.json"
    
    data = {}

    # Open the CSV file and read its content
    with open(csv_file_path, mode='r') as csv_file:
        csv_reader = csv.reader(csv_file)

        # Read the first row to get the location
        try:
            location_row = next(csv_reader)

        except StopIteration:
            print("File is empty...Removing File")
            return 0

        data['Location'] = location_row[0]  # Assuming 'Location' is the first entry of the first row

        # Read the second row as headers and ignore it
        try:
            headers = next(csv_reader)
        except StopIteration:
            print("File is empty...Removing File")
            return 0

        # Read the remaining rows (data starting from the third row) and transpose them
        columns = list(zip(*csv_reader))  # Transpose the CSV rows to columns

        # Assuming a specific order: ['Timestamp', 'Ax', 'Ay', 'Az', 'Gx', 'Gy', 'Gz']
        data['Timestamp'] = list(columns[0])  # First column is 'Timestamp'
        data['Ax'] = [float(i) for i in columns[3]]  # Second column is 'Ax'
        data['Ay'] = [float(i) for i in columns[4]]  # Third column is 'Ay'
        data['Az'] = [float(i) for i in columns[5]]  # Fourth column is 'Az'
        data['Gx'] = [float(i) for i in columns[6]]  # Fifth column is 'Gx'
        data['Gy'] = [float(i) for i in columns[7]]  # Sixth column is 'Gy'
        data['Gz'] = [float(i) for i in columns[8]]  # Seventh column is 'Gz'

    # Write the output to a JSON file
    with open(json_file_path, mode='w') as json_file:
        json.dump(data, json_file, indent=4)
    
    return json_file_path


def main():
    api_url = "http://3.98.214.27:5000/inference"
    sd = os.path.dirname(os.path.abspath(__file__))
    script_directory = os.path.join(sd, "send_out")
    print(script_directory)
    while(True):
        file_names = get_csv_files_from_directory(script_directory) 
        if len(file_names) > 0:
            old_file = get_oldest_file(file_names)
            json_file = csv_to_json(old_file)
            if json_file == 0:
                os.remove(old_file)
            else:
                print("Sending: ")
                print(json_file)
                send_to_rest_api(api_url, json_file)
                time.sleep(5)
                #shutil.move(json_file, os.path.join(processed_directory, os.path.basename(json_file)))
                #shutil.move(old_file, os.path.join(processed_directory, os.path.basename(old_file)))
                os.remove(json_file)
                os.remove(old_file)




if __name__ == "__main__":
    main()
