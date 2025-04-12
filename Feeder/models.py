from django.db import models
import uuid
from django.utils import timezone

class FeedingSchedule(models.Model):
    time = models.TimeField()
    portion = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.time} - {self.portion}g"

class ESP8266Device(models.Model):
    name = models.CharField(max_length=100, default="Pet Feeder")
    ip_address = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    port = models.PositiveIntegerField(default=80)
    last_connected = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    device_id = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.ip_address})"

class FeedingHistory(models.Model):
    FEED_TYPES = (
        ('manual', 'Manual'),
        ('scheduled', 'Scheduled'),
        ('remote', 'Remote API'),
    )
    
    device = models.ForeignKey(ESP8266Device, on_delete=models.CASCADE, related_name='feeding_history')
    timestamp = models.DateTimeField(default=timezone.now)
    portion = models.PositiveIntegerField()
    feed_type = models.CharField(max_length=20, choices=FEED_TYPES)
    
    def __str__(self):
        return f"{self.device.name} - {self.timestamp} - {self.portion}g"
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Feeding histories"

class DeviceCommand(models.Model):
    COMMAND_TYPES = (
        ('feed', 'Feed'),
        ('config', 'Configuration'),
        ('reboot', 'Reboot'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(ESP8266Device, on_delete=models.CASCADE, related_name='commands')
    command_type = models.CharField(max_length=20, choices=COMMAND_TYPES)
    parameters = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.device.name} - {self.command_type} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
