import os
import sys
import django
import requests
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Petfeeder.settings')
sys.path.append('c:\\Users\\Administrator\\Desktop\\FEEDandCONNECT3.0_REST\\Petfeeder')
django.setup()

# Import models after Django setup
from Feeder.models import ESP8266Device

def test_direct_esp_connection():
    # Get the active ESP8266 device
    device = ESP8266Device.objects.filter(is_active=True).first()
    
    if not device or not device.ip_address:
        print("No active ESP8266 device with IP address found.")
        return False
    
    print(f"Testing direct connection to ESP8266 at {device.ip_address}:{device.port}")
    
    try:
        # Test the device status endpoint first
        status_url = f"http://{device.ip_address}:{device.port}/status"
        status_response = requests.get(status_url, timeout=5)
        
        if status_response.status_code == 200:
            print("Status endpoint response:")
            print(json.dumps(status_response.json(), indent=2))
        else:
            print(f"Status endpoint returned status code {status_response.status_code}")
            print(status_response.text)
            return False
        
        # Now test the motor control endpoint
        motor_url = f"http://{device.ip_address}:{device.port}/motor"
        
        # Prepare minimal motor control data (small movement)
        motor_data = {
            'steps': 400,  # Increased number of steps for more noticeable movement
            'direction': 'clockwise',
            'speed': 500,  # Slower speed for more torque
            'microstepping': '1'  # Full step mode for maximum torque
        }
        
        print("\nSending motor control command:")
        print(json.dumps(motor_data, indent=2))
        
        motor_response = requests.post(motor_url, json=motor_data, timeout=10)
        
        if motor_response.status_code == 200:
            print("\nMotor control response:")
            print(json.dumps(motor_response.json(), indent=2))
            return True
        else:
            print(f"\nMotor control endpoint returned status code {motor_response.status_code}")
            print(motor_response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to ESP8266: {str(e)}")
        return False

def test_django_api():
    # Test the Django REST API endpoint for motor control
    print("\nTesting Django REST API endpoint for motor control")
    
    try:
        # Use Django's internal API endpoint
        api_url = "http://localhost:8000/api/motor/"
        
        # Prepare the same motor control data
        motor_data = {
            'steps': 400,  # Increased number of steps
            'direction': 'clockwise',
            'speed': 500,  # Slower speed
            'microstepping': '1'  # Full step mode
        }
        
        print("Sending motor control command through Django API:")
        print(json.dumps(motor_data, indent=2))
        
        api_response = requests.post(api_url, json=motor_data, timeout=10)
        
        print("\nDjango API response:")
        print(f"Status code: {api_response.status_code}")
        print(json.dumps(api_response.json(), indent=2) if api_response.status_code == 200 else api_response.text)
        
        return api_response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Django API: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== ESP8266 Motor Control Test ===\n")
    
    # First test direct connection to ESP8266
    direct_result = test_direct_esp_connection()
    
    # Then test through Django API
    api_result = test_django_api()
    
    print("\n=== Test Results ===")
    print(f"Direct ESP8266 connection test: {'SUCCESS' if direct_result else 'FAILED'}")
    print(f"Django API test: {'SUCCESS' if api_result else 'FAILED'}")
    
    if not direct_result and not api_result:
        print("\nBoth tests failed. Possible issues:")
        print("1. ESP8266 device is not powered on or not connected to the network")
        print("2. ESP8266 IP address in the database is incorrect")
        print("3. ESP8266 firmware has issues or is not responding")
        print("4. Network connectivity issues between Django and ESP8266")
    elif not direct_result and api_result:
        print("\nDjango API works but direct connection fails. Possible issues:")
        print("1. ESP8266 IP address in the database is incorrect")
        print("2. ESP8266 device is not accessible from this machine")
    elif direct_result and not api_result:
        print("\nDirect connection works but Django API fails. Possible issues:")
        print("1. Django REST framework configuration issue")
        print("2. Django view for motor control has errors")
        print("3. Django server is not running on port 8000")
    else:
        print("\nBoth tests passed! The system appears to be working correctly.")
        print("If the motor still doesn't move, check the physical connections and power supply.")