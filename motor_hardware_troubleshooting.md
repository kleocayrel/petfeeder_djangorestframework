# Stepper Motor Hardware Troubleshooting Guide

## Current Issue

The ESP8266 firmware is correctly receiving and processing motor control commands as evidenced by:

1. Successful API responses from both direct ESP8266 connection and Django API
2. Serial monitor output showing "Microstepping set to 1/1" and "Feed notification sent. Response code: 200"
3. No error messages in the firmware execution

However, the motor is not physically moving despite these successful software interactions.

## Hardware Verification Steps

### 1. Power Supply Check

- **Verify voltage**: Ensure the stepper motor driver is receiving adequate voltage (typically 12V for NEMA 17 motors)
- **Check current capacity**: The power supply must provide sufficient current (typically 1-2A minimum)
- **Measure voltage**: Use a multimeter to check voltage between VMOT and GND on the motor driver
- **Separate power**: Confirm the motor power supply is separate from the ESP8266 power supply

### 2. Motor Driver Connections

- **Pin connections**: Verify these connections match the firmware definitions:
  - STEP_PIN (D1/GPIO5) → STEP on driver
  - DIR_PIN (D2/GPIO4) → DIR on driver
  - MS1_PIN (D5/GPIO14) → MS1 on driver
  - MS2_PIN (D6/GPIO12) → MS2 on driver
  - MS3_PIN (D7/GPIO13) → MS3 on driver
  - ENABLE_PIN (D4/GPIO2) → ENABLE on driver

- **Logic level**: Ensure the driver accepts 3.3V logic from ESP8266 (some drivers require 5V logic)

### 3. Motor Driver Configuration

- **Current limiting**: Check if the current limiting potentiometer on the driver is set correctly
  - Too low: Motor won't have enough torque to move
  - Too high: Driver may overheat and enter thermal shutdown

- **Visual inspection**: Look for any signs of damage or overheating on the driver

### 4. Motor Wiring

- **Coil connections**: Verify the stepper motor wires are correctly connected to the driver
  - For bipolar stepper motors: A+, A-, B+, B- connections must be correct
  - Try swapping one coil's connections if the motor vibrates but doesn't rotate

- **Continuity test**: Use a multimeter to check continuity between motor wires and driver terminals

### 5. Physical Inspection

- **Shaft freedom**: Ensure the motor shaft can turn freely without binding
- **Mechanical load**: Disconnect the motor from any mechanical load to test it independently

## Testing Procedure

1. **Simplified test**: Disconnect the motor from any mechanical load
2. **Manual enable test**: 
   - Modify the firmware to keep ENABLE_PIN LOW (enabled) permanently
   - Add a delay after enabling the motor before attempting to move it

3. **Microstepping test**: 
   - Try different microstepping modes (1/1, 1/2, 1/4, 1/8, 1/16)
   - Full step mode (1/1) provides maximum torque but may be more jerky

4. **Speed test**: 
   - Try a much slower speed (100-200 steps/second) for initial testing
   - Some motors/drivers struggle with higher speeds without proper acceleration

## Firmware Modification for Testing

If needed, modify the `moveStepper()` function in the ESP8266 firmware:

```cpp
void moveStepper(int steps, bool direction) {
    // Enable motor and add longer delay for driver to stabilize
    digitalWrite(ENABLE_PIN, LOW);
    delay(500);  // Increased from 100ms to 500ms
    
    digitalWrite(DIR_PIN, direction);
    
    // Use slower step rate for testing
    int testStepDelay = 2000;  // 2000 microseconds = 0.5kHz step rate
    
    for (int i = 0; i < steps; i++) {
        digitalWrite(STEP_PIN, HIGH);
        delayMicroseconds(testStepDelay);
        digitalWrite(STEP_PIN, LOW);
        delayMicroseconds(testStepDelay);
        
        // Prevent watchdog timer issues
        if (i % 100 == 0) {
            yield();
        }
    }
    
    delay(500);
    
    // Keep motor enabled for testing
    // digitalWrite(ENABLE_PIN, HIGH);  // Comment this out for testing
}
```

## Hardware Alternatives

If all troubleshooting fails:

1. Try a different motor driver board
2. Try a different stepper motor
3. Consider using a simpler test circuit to verify motor functionality

## Common Issues and Solutions

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Motor doesn't move at all | Insufficient power | Check power supply voltage and current |
| Motor vibrates but doesn't rotate | Incorrect wiring | Try swapping one coil's connections |
| Motor moves erratically | Current limiting too low | Adjust current limiting potentiometer |
| Motor moves briefly then stops | Driver overheating | Check for proper cooling, reduce current |
| Motor only moves in one direction | DIR pin connection issue | Check DIR_PIN wiring and logic level |