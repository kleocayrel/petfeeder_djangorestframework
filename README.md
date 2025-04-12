# ESP8266 NodeMCU Pet Feeder Controller

This firmware allows the ESP8266 NodeMCU to receive REST API commands from the Django web interface and control a stepper motor with 1/16 microstepping precision.

## Hardware Requirements

- ESP8266 NodeMCU board
- Stepper motor driver (A4988, DRV8825, or similar)
- Stepper motor
- Power supply for the stepper motor
- Jumper wires

## Wiring Instructions

Connect the ESP8266 NodeMCU to the stepper motor driver as follows:

| ESP8266 Pin | Stepper Driver Pin |
|-------------|--------------------|
| D1          | STEP               |
| D2          | DIR                |
| D3          | ENABLE             |
| D5          | MS1 (Microstepping)|
| D6          | MS2 (Microstepping)|
| D7          | MS3 (Microstepping)|
| GND         | GND                |

**Note:** Make sure to connect the stepper motor and power supply to the driver according to the driver's specifications.

## Software Setup

1. Install the Arduino IDE
2. Add ESP8266 board support to Arduino IDE
3. Install the following libraries:
   - ESP8266WiFi
   - ESP8266WebServer
   - ArduinoJson
   - AccelStepper
4. Open the ESP8266_PetFeeder.ino file
5. Update the WiFi credentials with your network details:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
6. Upload the sketch to your ESP8266 NodeMCU
7. Open the Serial Monitor to see the assigned IP address
8. Configure this IP address in the Django web interface

## REST API Endpoints

### GET /

Returns basic information about the device.

### POST /motor

Controls the stepper motor. Send a JSON payload with the following parameters:

```json
{
  "steps": 200,
  "direction": "clockwise",
  "speed": 1000,
  "microstepping": "16"
}
```

- **steps**: Number of steps to move
- **direction**: "clockwise" or "counterclockwise"
- **speed**: Steps per second (optional, default: 1000)
- **microstepping**: "1", "2", "4", "8", or "16" (optional, default: "16")

### GET /status

Returns the current status of the device and motor.

## Microstepping

The firmware supports the following microstepping modes:

- Full step (1)
- Half step (1/2)
- Quarter step (1/4)
- Eighth step (1/8)
- Sixteenth step (1/16) - Default

The microstepping mode can be changed via the REST API by sending the appropriate value in the "microstepping" parameter.

## Troubleshooting

- If the motor doesn't move, check the wiring and ensure the power supply is connected.
- If the ESP8266 doesn't connect to WiFi, verify the credentials and ensure the network is available.
- If the web interface can't connect to the ESP8266, check that the IP address is correctly configured in the Django settings.