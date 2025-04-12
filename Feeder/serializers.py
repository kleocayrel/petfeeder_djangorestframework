from rest_framework import serializers
from .models import FeedingSchedule, ESP8266Device, FeedingHistory, DeviceCommand

class FeedingScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedingSchedule
        fields = ['id', 'time', 'portion']

class MotorControlSerializer(serializers.Serializer):
    steps = serializers.IntegerField(required=True, help_text="Number of steps for the motor to move")
    direction = serializers.ChoiceField(choices=['clockwise', 'counterclockwise'], required=True, 
                                      help_text="Direction of motor rotation")
    speed = serializers.IntegerField(required=False, default=1000, 
                                   help_text="Speed of motor rotation in steps per second")
    microstepping = serializers.ChoiceField(choices=['1', '2', '4', '8', '16'], default='16', required=False,
                                          help_text="Microstepping mode (1, 2, 4, 8, or 16)")

class ESP8266DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ESP8266Device
        fields = ['id', 'name', 'ip_address', 'port', 'device_id', 'is_active', 'last_connected']

class FeedingHistorySerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.name', read_only=True)
    
    class Meta:
        model = FeedingHistory
        fields = ['id', 'device', 'device_name', 'timestamp', 'portion', 'feed_type']

class DeviceCommandSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.name', read_only=True)
    
    class Meta:
        model = DeviceCommand
        fields = ['id', 'device', 'device_name', 'command_type', 'parameters', 'status', 'created_at', 'updated_at']

class DeviceRegistrationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    ip_address = serializers.IPAddressField()
    port = serializers.IntegerField(default=80)
    device_id = serializers.CharField(max_length=50)
    is_active = serializers.BooleanField(default=True)

class HeartbeatSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=50)
    ip_address = serializers.IPAddressField()
    status = serializers.CharField(max_length=20)
    timestamp = serializers.IntegerField()

class FeedNotificationSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=50)
    portion = serializers.IntegerField()
    type = serializers.CharField(max_length=20)
    timestamp = serializers.IntegerField()

class CommandAcknowledgmentSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=50)
    command_id = serializers.UUIDField()
    status = serializers.CharField(max_length=20)
    timestamp = serializers.IntegerField()