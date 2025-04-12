from django.contrib import admin
from .models import FeedingSchedule, ESP8266Device, FeedingHistory, DeviceCommand

# Register your models here.
admin.site.register(FeedingSchedule)
admin.site.register(ESP8266Device)
admin.site.register(FeedingHistory)
admin.site.register(DeviceCommand)
