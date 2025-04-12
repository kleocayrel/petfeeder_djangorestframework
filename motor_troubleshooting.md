# Motor Troubleshooting Guide

## Summary of Findings

After thorough testing, we've determined that the software communication between the Django application and the ESP8266 device is working correctly. Both direct API calls to the ESP8266 and calls through the Django REST framework are successful. However, the motor is still not physically moving.

## Likely Issues

Since the software side is working correctly, the issue is most likely with the physical hardware setup:

1. **Power Supply Issues**:
   - Ensure the stepper motor is receiving adequate power
   - Check if the power supply is properly connected and turned on
   - Verify the voltage of the power supply matches the motor requirements

2. **Motor Driver Connections**:
   - Check all wiring connections between the ESP8266 and the motor driver (A4988/DRV8825)
   - Verify the following pins are correctly connected:
     - STEP_PIN (D1 on NodeMCU) to STEP on driver
     - DIR_PIN (D2 on NodeMCU) to DIR on driver
     - MS1_PIN, MS2_PIN, MS3_PIN (D5, D6, D7) to MS1, MS2, MS3 on driver
     - ENABLE_PIN (D4 on NodeMCU) to ENABLE on driver

3. **Motor Connections**:
   - Ensure the stepper motor wires are correctly connected to the driver
   - For a typical bipolar stepper motor, check connections to A+, A-, B+, B-
   - Try reversing one coil's connections if the motor vibrates but doesn't rotate

4. **Driver Configuration**:
   - Check if the current limiting potentiometer on the driver is set correctly
   - Too low current will prevent the motor from moving
   - Too high current can cause the driver to overheat and shut down

5. **Physical Obstructions**:
   - Check if there are any physical obstructions preventing the motor from turning
   - Ensure the motor shaft is not binding or jammed

## Testing Steps

1. **Manual Test**:
   - Press the manual feed button on the ESP8266 (D3 pin)
   - If this works but the API doesn't, there might be a software issue

2. **Driver Test**:
   - Check if the driver is getting hot - this indicates it's receiving power
   - Look for any LED indicators on the driver board

3. **Voltage Test** (if you have a multimeter):
   - Measure the voltage between VMOT and GND on the driver board when powered
   - Measure the logic voltage (3.3V or 5V) between VDD and GND

## Next Steps

If after checking all the above, the motor still doesn't move:

1. Try connecting the ESP8266 to a different motor driver if available
2. Try a different stepper motor if available
3. Check the ESP8266 firmware for any hardware-specific configurations that might need adjustment

## ESP8266 Firmware Notes

The ESP8266 firmware is correctly receiving and processing motor control commands. The relevant code in the firmware that controls the motor is:

```cpp
void moveStepper(int steps, bool direction) {
    // Enable motor
    digitalWrite(ENABLE_PIN, LOW);
    
    digitalWrite(DIR_PIN, direction);
    
    // Add initial delay for motor to settle
    delay(100);
    
    for (int i = 0; i < steps; i++) {
        digitalWrite(STEP_PIN, HIGH);
        delayMicroseconds(STEP_DELAY);
        digitalWrite(STEP_PIN, LOW);
        delayMicroseconds(STEP_DELAY);
        
        // Prevent watchdog timer issues
        if (i % 100 == 0) {
            yield();
        }
    }
    
    // Add final delay
    delay(100);
    
    // Disable motor to save power
    digitalWrite(ENABLE_PIN, HIGH);
}
```

This code looks correct for controlling a stepper motor with a standard driver. The issue is most likely with the physical connections or power supply.