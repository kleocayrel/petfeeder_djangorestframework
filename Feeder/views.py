from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import FeedingSchedule, ESP8266Device, FeedingHistory, DeviceCommand
import datetime
import requests
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import (FeedingScheduleSerializer, MotorControlSerializer, ESP8266DeviceSerializer,
                          FeedingHistorySerializer, DeviceCommandSerializer, DeviceRegistrationSerializer,
                          HeartbeatSerializer, FeedNotificationSerializer, CommandAcknowledgmentSerializer)
from django.utils import timezone

def home(request):
    """View function for the home page."""
    return render(request, 'app/home.html')

def feed_control(request):
    """View function for the feed control page."""
    if request.method == 'POST':
        # Initialize response data
        response_data = {'status': 'error', 'message': 'Unknown request type'}
        
        # Get request type from POST data
        request_type = request.POST.get('request_type')
        
        # Handle form submission for manual feeding
        if request_type == 'manual_feed' or request.POST.get('manual_feed'):
            try:
                portion = int(request.POST.get('portion', 5))
                # Get the ESP8266 device
                device = ESP8266Device.objects.filter(is_active=True).first()
                
                if device and device.ip_address:
                    try:
                        # Calculate steps based on portion size (adjust as needed)
                        steps = portion * 200  # Example: 200 steps per portion
                        
                        # Create a command in the database
                        command = DeviceCommand.objects.create(
                            device=device,
                            command_type='feed',
                            parameters={'portion': portion, 'steps': steps},
                            status='pending'
                        )
                        
                        # Construct the URL for the ESP8266 device
                        url = f"http://{device.ip_address}:{device.port}/motor"
                        
                        # Get motor control parameters from the request
                        direction = request.POST.get('direction', 'clockwise')
                        speed = int(request.POST.get('speed', 1000))
                        microstepping = request.POST.get('microstepping', '16')
                        
                        # Prepare the data to send to the ESP8266
                        data = {
                            'steps': steps,
                            'direction': direction,
                            'speed': speed,
                            'microstepping': microstepping
                        }
                        
                        # Send the request to the ESP8266
                        response = requests.post(url, json=data, timeout=5)
                        
                        if response.status_code == 200:
                            # Update the last connected timestamp
                            device.last_connected = timezone.now()
                            device.save()
                            
                            # Update command status
                            command.status = 'completed'
                            command.save()
                            
                            # Record the feeding in history
                            FeedingHistory.objects.create(
                                device=device,
                                portion=portion,
                                feed_type='remote'
                            )
                            
                            response_data = {'status': 'success', 'message': 'Feed command sent successfully!'}
                        else:
                            # Update command status
                            command.status = 'failed'
                            command.save()
                            response_data = {'status': 'error', 'message': f'Error: ESP8266 returned status code {response.status_code}'}
                            
                    except requests.exceptions.RequestException as e:
                        response_data = {'status': 'error', 'message': f'Failed to connect to ESP8266: {str(e)}'}
                else:
                    response_data = {'status': 'error', 'message': 'No active ESP8266 device configured. Please configure a device in the motor control page.'}
            except ValueError as e:
                response_data = {'status': 'error', 'message': f'Invalid input: {str(e)}'}
        
        # Handle form submission for scheduled feeding
        elif request_type == 'schedule_feed' or request.POST.get('schedule_feed'):
            try:
                time = request.POST.get('time')
                portion = int(request.POST.get('portion'))
                if not time or not portion:
                    response_data = {'status': 'error', 'message': 'Time and portion are required for scheduling'}
                else:
                    # Save the schedule to the database
                    FeedingSchedule.objects.create(time=time, portion=portion)
                    response_data = {'status': 'success', 'message': 'Feeding schedule added successfully!'}
            except ValueError:
                response_data = {'status': 'error', 'message': 'Invalid portion value provided'}
            except Exception as e:
                response_data = {'status': 'error', 'message': f'Failed to add schedule: {str(e)}'}
        
        # Check if this is an AJAX/fetch request
        # The fetch requests from feed_control.js include X-CSRFToken header
        is_fetch = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
                  request.headers.get('Accept') == 'application/json' or \
                  'application/json' in request.headers.get('Content-Type', '') or \
                  request.headers.get('X-CSRFToken') is not None
        
        # Always return JSON for fetch API requests
        if is_fetch:
            return JsonResponse(response_data)
        # For regular form submissions, redirect on success or show error
        if response_data['status'] == 'success':
            return redirect('feed_control')
        else:
            # For failed form submissions, show error message
            from django.contrib import messages
            messages.error(request, response_data['message'])
            return redirect('feed_control')
    
    # Get all scheduled feedings for GET request
    schedules = FeedingSchedule.objects.all().order_by('time')
    if request.headers.get('Accept') == 'application/json':
        schedule_data = [{'id': s.id, 'time': s.time.strftime('%H:%M'), 'portion': s.portion} for s in schedules]
        return JsonResponse({'status': 'success', 'schedules': schedule_data})
    return render(request, 'control/feed.html', {'schedules': schedules})

ss = FeedingScheduleSerializer
def control_motor(request):
    """API endpoint for controlling the motor directly."""
    if request.method == 'POST':
        # Here you would add code to control the motor
        # For now, we'll just simulate it
        return JsonResponse({'status': 'success', 'message': 'Motor activated'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@api_view(['POST'])
def motor_control_api(request):
    """REST API endpoint for controlling the stepper motor with microstepping."""
    serializer = MotorControlSerializer(data=request.data)
    if serializer.is_valid():
        # Get the validated data
        steps = serializer.validated_data['steps']
        direction = serializer.validated_data['direction']
        speed = serializer.validated_data.get('speed', 1000)
        microstepping = serializer.validated_data.get('microstepping', '16')
        
        # Get the ESP8266 device (assuming there's at least one configured)
        device = ESP8266Device.objects.filter(is_active=True).first()
        
        if device and device.ip_address:
            try:
                # Construct the URL for the ESP8266 device
                url = f"http://{device.ip_address}:{device.port}/motor"
                
                # Prepare the data to send to the ESP8266
                data = {
                    'steps': steps,
                    'direction': direction,
                    'speed': speed,
                    'microstepping': microstepping
                }
                
                # Send the request to the ESP8266
                response = requests.post(url, json=data, timeout=5)
                
                if response.status_code == 200:
                    # Update the last connected timestamp
                    device.last_connected = timezone.now()
                    device.save()
                    
                    return Response({
                        'status': 'success',
                        'message': 'Command sent to ESP8266 successfully',
                        'esp_response': response.json()
                    })
                else:
                    return Response({
                        'status': 'error',
                        'message': f'ESP8266 returned status code {response.status_code}',
                        'esp_response': response.text
                    }, status=status.HTTP_502_BAD_GATEWAY)
                    
            except requests.exceptions.RequestException as e:
                return Response({
                    'status': 'error',
                    'message': f'Failed to connect to ESP8266: {str(e)}'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        else:
            return Response({
                'status': 'error',
                'message': 'No active ESP8266 device configured'
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
def esp8266_config(request):
    """API endpoint for managing ESP8266 device configuration."""
    if request.method == 'GET':
        # Get the current ESP8266 device configuration
        device = ESP8266Device.objects.first()
        if not device:
            device = ESP8266Device.objects.create(name="Pet Feeder")
        
        return Response({
            'name': device.name,
            'ip_address': device.ip_address,
            'port': device.port,
            'is_active': device.is_active,
            'device_id': device.device_id,
            'last_connected': device.last_connected
        })
    
    elif request.method == 'POST':
        # Update the ESP8266 device configuration
        device = ESP8266Device.objects.first()
        if not device:
            device = ESP8266Device.objects.create()
        
        # Update the device configuration
        if 'name' in request.data:
            device.name = request.data['name']
        if 'ip_address' in request.data:
            device.ip_address = request.data['ip_address']
        if 'port' in request.data:
            device.port = request.data['port']
        if 'is_active' in request.data:
            device.is_active = request.data['is_active']
        if 'device_id' in request.data:
            device.device_id = request.data['device_id']
        
        device.save()
        
        return Response({
            'status': 'success',
            'message': 'ESP8266 configuration updated successfully'
        })

class FeedingScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing FeedingSchedule instances."""
    queryset = FeedingSchedule.objects.all()
    serializer_class = FeedingScheduleSerializer
def history(request):
    """View function for the feeding history page."""
    # Fetch the feeding history from the database
    history_entries = FeedingHistory.objects.all().order_by('-timestamp')[:20]  # Get the 20 most recent entries
    
    # Format the history for display
    formatted_history = []
    for entry in history_entries:
        try:
            formatted_history.append({
                'date': entry.timestamp.strftime('%Y-%m-%d'),
                'time': entry.timestamp.strftime('%H:%M'),
                'portion': entry.portion,
                'type': dict(FeedingHistory.FEED_TYPES).get(entry.feed_type, entry.feed_type)
            })
        except Exception as e:
            # Log the error but continue processing other entries
            print(f"Error formatting history entry {entry.id}: {str(e)}")
    
    # If the request is for JSON, return JSON response
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'status': 'success',
            'history': formatted_history
        })
    
    return render(request, 'control/history.html', {'history': formatted_history})

def bmi(request):
    """View function for the BMI calculator page."""
    return render(request, 'control/bmi.html')

def motor_control_page(request):
    """View function for the motor control page."""
    return render(request, 'control/motor_control.html')

@api_view(['GET', 'POST'])
def esp8266_api(request):
    """Main API endpoint for ESP8266 device registration."""
    if request.method == 'POST':
        serializer = DeviceRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            # Check if device with this device_id already exists
            device_id = serializer.validated_data.get('device_id')
            device = ESP8266Device.objects.filter(device_id=device_id).first()
            
            if device:
                # Update existing device
                device.name = serializer.validated_data.get('name', device.name)
                device.ip_address = serializer.validated_data.get('ip_address')
                device.port = serializer.validated_data.get('port', 80)
                device.is_active = serializer.validated_data.get('is_active', True)
            else:
                # Create new device
                device = ESP8266Device.objects.create(
                    name=serializer.validated_data.get('name'),
                    ip_address=serializer.validated_data.get('ip_address'),
                    port=serializer.validated_data.get('port', 80),
                    device_id=device_id,
                    is_active=serializer.validated_data.get('is_active', True)
                )
            
            # Update last connected timestamp
            device.last_connected = timezone.now()
            device.save()
            
            return Response({
                'status': 'success',
                'message': 'Device registered successfully',
                'device_id': device.device_id
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'GET':
        # List all registered devices
        devices = ESP8266Device.objects.all()
        serializer = ESP8266DeviceSerializer(devices, many=True)
        return Response(serializer.data)

@api_view(['POST'])
def esp8266_heartbeat(request):
    """API endpoint for ESP8266 device heartbeat."""
    serializer = HeartbeatSerializer(data=request.data)
    if serializer.is_valid():
        device_id = serializer.validated_data.get('device_id')
        device = ESP8266Device.objects.filter(device_id=device_id).first()
        
        if device:
            # Update device IP address and last connected timestamp
            device.ip_address = serializer.validated_data.get('ip_address')
            device.last_connected = timezone.now()
            device.is_active = True
            device.save()
            
            return Response({
                'status': 'success',
                'message': 'Heartbeat received'
            })
        else:
            return Response({
                'status': 'error',
                'message': 'Device not found'
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def esp8266_feed_notification(request):
    """API endpoint for ESP8266 device feed notification."""
    serializer = FeedNotificationSerializer(data=request.data)
    if serializer.is_valid():
        device_id = serializer.validated_data.get('device_id')
        device = ESP8266Device.objects.filter(device_id=device_id).first()
        
        if device:
            # Record the feeding in history
            FeedingHistory.objects.create(
                device=device,
                portion=serializer.validated_data.get('portion', 1),
                feed_type=serializer.validated_data.get('type', 'manual')
            )
            
            return Response({
                'status': 'success',
                'message': 'Feed notification recorded'
            })
        else:
            return Response({
                'status': 'error',
                'message': 'Device not found'
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def esp8266_commands(request):
    """API endpoint for ESP8266 device to check for pending commands."""
    device_id = request.query_params.get('device_id')
    if not device_id:
        return Response({
            'status': 'error',
            'message': 'Device ID is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    device = ESP8266Device.objects.filter(device_id=device_id).first()
    if not device:
        return Response({
            'status': 'error',
            'message': 'Device not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get pending commands for this device
    commands = DeviceCommand.objects.filter(device=device, status='pending')
    
    # Format commands for the ESP8266
    command_list = []
    for command in commands:
        command_list.append({
            'id': str(command.id),
            'type': command.command_type,
            **command.parameters
        })
        
        # Mark command as sent
        command.status = 'sent'
        command.save()
    
    return Response({
        'status': 'success',
        'commands': command_list
    })

@api_view(['POST'])
def esp8266_acknowledge_command(request):
    """API endpoint for ESP8266 device to acknowledge command completion."""
    serializer = CommandAcknowledgmentSerializer(data=request.data)
    if serializer.is_valid():
        device_id = serializer.validated_data.get('device_id')
        command_id = serializer.validated_data.get('command_id')
        command_status = serializer.validated_data.get('status')
        
        device = ESP8266Device.objects.filter(device_id=device_id).first()
        if not device:
            return Response({
                'status': 'error',
                'message': 'Device not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            command = DeviceCommand.objects.get(id=command_id, device=device)
            command.status = 'completed' if command_status == 'completed' else 'failed'
            command.save()
            
            # If this was a feed command that completed successfully, record it in history
            if command.command_type == 'feed' and command_status == 'completed':
                portion = command.parameters.get('portion', 1)
                FeedingHistory.objects.create(
                    device=device,
                    portion=portion,
                    feed_type='scheduled'
                )
            
            return Response({
                'status': 'success',
                'message': 'Command acknowledged'
            })
        except DeviceCommand.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Command not found'
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)