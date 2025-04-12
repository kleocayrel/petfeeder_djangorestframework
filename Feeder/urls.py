from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

# Create a router for REST API viewsets
router = DefaultRouter()
router.register(r'api/schedules', views.FeedingScheduleViewSet)

urlpatterns = [
    path('', views.home, name='home'),
    path('feed_control/', views.feed_control, name='feed_control'),
    path('control_motor/', views.control_motor, name='control_motor'),
    path('motor_control/', views.motor_control_page, name='motor_control_page'),
    path('history/', views.history, name='history'),
    path('bmi/', views.bmi, name='bmi'),
    # REST API endpoints
    path('api/motor/', views.motor_control_api, name='motor_control_api'),
    
    # ESP8266 API endpoints for firmware communication
    path('api/esp8266/', views.esp8266_api, name='esp8266_api'),
    path('api/esp8266/heartbeat/', views.esp8266_heartbeat, name='esp8266_heartbeat'),
    path('api/esp8266/feed/', views.esp8266_feed_notification, name='esp8266_feed_notification'),
    path('api/esp8266/commands/', views.esp8266_commands, name='esp8266_commands'),
    path('api/esp8266/acknowledge/', views.esp8266_acknowledge_command, name='esp8266_acknowledge_command'),
    
    path('', include(router.urls)),
    # path('send_notification/', views.send_notification, name='send_notification'),
]
