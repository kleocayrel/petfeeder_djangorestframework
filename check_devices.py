import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Petfeeder.settings')
sys.path.append('c:\\Users\\Administrator\\Desktop\\FEEDandCONNECT3.0_REST\\Petfeeder')
django.setup()

# Import models after Django setup
from Feeder.models import ESP8266Device

# Check active devices
active_devices = ESP8266Device.objects.filter(is_active=True)
all_devices = ESP8266Device.objects.all()

print(f'Active devices: {active_devices.count()}')
print(f'All devices: {all_devices.count()}')

# Print details of all devices
for device in all_devices:
    print(f'Device: {device.name}, IP: {device.ip_address}, Port: {device.port}, Active: {device.is_active}, ID: {device.device_id}, Last Connected: {device.last_connected}')