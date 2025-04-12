import requests
import json

# Device registration data
device_data = {
    'device_id': 'PetFeeder1',  # This should match the device_id in your ESP8266 firmware
    'name': 'Pet Feeder',
    'ip_address': '0.0.0.0',  # This will be updated by the device's heartbeat
    'port': 80,
    'is_active': True
}

# Send registration request to Django server
try:
    response = requests.post(
        'http://localhost:8000/api/esp8266/',
        json=device_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        print('Device registered successfully!')
        print('Response:', json.dumps(response.json(), indent=2))
    else:
        print('Error registering device!')
        print('Status code:', response.status_code)
        print('Response:', response.text)

except requests.exceptions.RequestException as e:
    print('Error connecting to server:', str(e))