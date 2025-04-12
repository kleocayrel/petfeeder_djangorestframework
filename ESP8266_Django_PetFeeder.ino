/*
 * ESP8266 NodeMCU Pet Feeder Controller - Django Backend Version
 * This firmware allows the ESP8266 to communicate with a Django backend server
 * and control a stepper motor with microstepping precision.
 */

#include <ESP8266WiFi.h>
#include <WiFiManager.h>         // https://github.com/tzapu/WiFiManager
#include <ESP8266WebServer.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>         // https://arduinojson.org/

// ------------------------
// Wi-Fi SoftAP credentials
// ------------------------
const char *softAP_SSID = "PetFeeder-Setup";
const char *softAP_Password = "12345678";
const unsigned long softAPTimeout = 30000;

// ------------------------
// Django Server Configuration
// ------------------------
// These will be configurable via the web interface
String djangoServerIP = "";
int djangoServerPort = 8000;
String djangoAPIEndpoint = "/api/esp8266/";
String deviceID = "";

// ------------------------
// Stepper Motor Configuration
// ------------------------
#define STEP_PIN 5     // D1
#define DIR_PIN 4      // D2
#define MS1_PIN 14     // D5
#define MS2_PIN 12     // D6
#define MS3_PIN 13     // D7  
#define BUTTON_PIN 0   // D3 on NodeMCU
#define ENABLE_PIN 2   // D4 on NodeMCU

// Adjusted for 1/16 microstepping
const int STEP_DELAY = 500;           // Microseconds between steps
const int STEPS_PER_REVOLUTION = 3200;  // 200 steps * 16 microsteps
const int STEPS_PER_PORTION = 1600;     // Half revolution per portion

// Current microstepping mode
int currentMicrostepMode = 16; // Default to 1/16 microstepping

// ------------------------
// Web Server & Status Variables
// ------------------------
ESP8266WebServer server(80);
unsigned long lastHeartbeat = 0;
const unsigned long HEARTBEAT_INTERVAL = 10000; // 10 seconds
const unsigned long STATUS_CHECK_INTERVAL = 5000; // 5 seconds
unsigned long lastStatusCheck = 0;
bool isFeeding = false;

// ------------------------
// Setup Functions
// ------------------------
void setupStepperMotor() {
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(MS1_PIN, OUTPUT);
  pinMode(MS2_PIN, OUTPUT);
  pinMode(MS3_PIN, OUTPUT);
  pinMode(ENABLE_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);  // Using internal pull-up resistor
  
  // Set default microstepping to 1/16
  setMicrostepping(16);
  
  // Disable motor initially to save power
  digitalWrite(ENABLE_PIN, HIGH);
}

void setupWiFi() {
  WiFiManager wm;
  wm.setTimeout(30); // 30 seconds timeout

  // Attempt to connect using saved credentials or start AP for configuration
  if (!wm.autoConnect(softAP_SSID, softAP_Password)) {
    Serial.println("Failed to connect and hit timeout. Restarting...");
    delay(3000);
    ESP.restart();
  }

  Serial.print("Connected to Wi-Fi. IP: ");
  Serial.println(WiFi.localIP());
  
  // Generate a unique device ID based on MAC address if not already set
  if (deviceID == "") {
    deviceID = "ESP_" + String(ESP.getChipId(), HEX);
  }
}

void setupWebServer() {
  // Define server endpoints
  server.on("/", HTTP_GET, handleRoot);
  server.on("/motor", HTTP_POST, handleMotorControl);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/config", HTTP_GET, handleGetConfig);
  server.on("/config", HTTP_POST, handleSetConfig);
  
  // Start server
  server.begin();
  Serial.println("HTTP server started");
}

// ------------------------
// Main Setup & Loop
// ------------------------
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nESP8266 Pet Feeder - Django Version");
  
  setupStepperMotor();
  setupWiFi();
  setupWebServer();
  
  // Register with Django server
  registerWithDjangoServer();
}

void loop() {
  server.handleClient();
  
  // Check for manual feed button press
  if (digitalRead(BUTTON_PIN) == LOW && !isFeeding) {
    Serial.println("Manual feed button pressed");
    isFeeding = true;
    moveStepper(STEPS_PER_PORTION, true);
    notifyManualFeedToDjango();
    isFeeding = false;
  }
  
  // Send heartbeat to Django server
  if (millis() - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    sendHeartbeatToDjango();
    lastHeartbeat = millis();
  }
  
  // Check for pending commands from Django server
  if (millis() - lastStatusCheck >= STATUS_CHECK_INTERVAL) {
    checkForPendingCommands();
    lastStatusCheck = millis();
  }
}

// ------------------------
// Motor Control Functions
// ------------------------
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

// Set microstepping mode based on the provided value
void setMicrostepping(int mode) {
  // MS1, MS2, MS3 pin settings for different microstepping modes
  // Based on common A4988 or DRV8825 driver settings
  switch (mode) {
    case 1: // Full step (no microstepping)
      digitalWrite(MS1_PIN, LOW);
      digitalWrite(MS2_PIN, LOW);
      digitalWrite(MS3_PIN, LOW);
      break;
    case 2: // Half step
      digitalWrite(MS1_PIN, HIGH);
      digitalWrite(MS2_PIN, LOW);
      digitalWrite(MS3_PIN, LOW);
      break;
    case 4: // Quarter step
      digitalWrite(MS1_PIN, LOW);
      digitalWrite(MS2_PIN, HIGH);
      digitalWrite(MS3_PIN, LOW);
      break;
    case 8: // Eighth step
      digitalWrite(MS1_PIN, HIGH);
      digitalWrite(MS2_PIN, HIGH);
      digitalWrite(MS3_PIN, LOW);
      break;
    case 16: // Sixteenth step
      digitalWrite(MS1_PIN, HIGH);
      digitalWrite(MS2_PIN, HIGH);
      digitalWrite(MS3_PIN, HIGH);
      break;
    default: // Default to sixteenth step if invalid value
      digitalWrite(MS1_PIN, HIGH);
      digitalWrite(MS2_PIN, HIGH);
      digitalWrite(MS3_PIN, HIGH);
      mode = 16;
      break;
  }
  
  currentMicrostepMode = mode;
  Serial.println("Microstepping set to 1/" + String(mode));
}

// ------------------------
// Web Server Handlers
// ------------------------
void handleRoot() {
  String html = "<html><body>";
  html += "<h1>ESP8266 Pet Feeder Controller</h1>";
  html += "<p>IP Address: " + WiFi.localIP().toString() + "</p>";
  html += "<p>Device ID: " + deviceID + "</p>";
  html += "<p>Django Server: " + djangoServerIP + ":" + String(djangoServerPort) + "</p>";
  html += "<p>Current Microstepping: 1/" + String(currentMicrostepMode) + "</p>";
  html += "<p>Use REST API endpoints to control the motor</p>";
  html += "<p><a href='/config'>Configure Django Server</a></p>";
  html += "</body></html>";
  server.send(200, "text/html", html);
}

void handleMotorControl() {
  if (server.hasArg("plain")) {
    String body = server.arg("plain");
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, body);
    
    if (error) {
      server.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Invalid JSON\"}\n");
      return;
    }
    
    // Extract parameters from JSON
    int steps = doc["steps"];
    String direction = doc["direction"];
    int speed = doc["speed"] | 1000; // Default to 1000 if not provided
    String microsteppingStr = doc["microstepping"] | "16"; // Default to 16 if not provided
    int microstepping = microsteppingStr.toInt();
    
    // Set microstepping mode if different from current
    if (microstepping != currentMicrostepMode) {
      setMicrostepping(microstepping);
    }
    
    // Set motor direction
    bool dirValue = (direction == "clockwise") ? true : false;
    
    // Move the motor
    isFeeding = true;
    moveStepper(steps, dirValue);
    isFeeding = false;
    
    // Send response
    DynamicJsonDocument response(256);
    response["status"] = "success";
    response["message"] = "Motor command executed";
    response["steps"] = steps;
    response["direction"] = direction;
    response["speed"] = speed;
    response["microstepping"] = microstepping;
    
    String jsonResponse;
    serializeJson(response, jsonResponse);
    server.send(200, "application/json", jsonResponse);
  } else {
    server.send(400, "application/json", "{\"status\":\"error\",\"message\":\"No data provided\"}\n");
  }
}

void handleStatus() {
  DynamicJsonDocument doc(256);
  doc["status"] = "running";
  doc["device_id"] = deviceID;
  doc["ip"] = WiFi.localIP().toString();
  doc["microstepping"] = currentMicrostepMode;
  doc["motor_enabled"] = (digitalRead(ENABLE_PIN) == LOW);
  doc["is_feeding"] = isFeeding;
  doc["django_server"] = djangoServerIP + ":" + String(djangoServerPort);
  
  String jsonResponse;
  serializeJson(doc, jsonResponse);
  server.send(200, "application/json", jsonResponse);
}

void handleGetConfig() {
  String html = "<html><body>";
  html += "<h1>Django Server Configuration</h1>";
  html += "<form method='post'>";
  html += "Server IP: <input type='text' name='server_ip' value='" + djangoServerIP + "'><br>";
  html += "Server Port: <input type='number' name='server_port' value='" + String(djangoServerPort) + "'><br>";
  html += "API Endpoint: <input type='text' name='api_endpoint' value='" + djangoAPIEndpoint + "'><br>";
  html += "Device ID: <input type='text' name='device_id' value='" + deviceID + "'><br>";
  html += "<input type='submit' value='Save'>";
  html += "</form>";
  html += "</body></html>";
  server.send(200, "text/html", html);
}

void handleSetConfig() {
  if (server.hasArg("server_ip")) {
    djangoServerIP = server.arg("server_ip");
  }
  if (server.hasArg("server_port")) {
    djangoServerPort = server.arg("server_port").toInt();
  }
  if (server.hasArg("api_endpoint")) {
    djangoAPIEndpoint = server.arg("api_endpoint");
  }
  if (server.hasArg("device_id")) {
    deviceID = server.arg("device_id");
  }
  
  // Redirect back to the config page
  server.sendHeader("Location", "/config");
  server.send(302, "text/plain", "");
  
  // Register with the new server settings
  registerWithDjangoServer();
}

// ------------------------
// Django Communication Functions
// ------------------------
void registerWithDjangoServer() {
  // Only attempt to register if we have a server IP
  if (djangoServerIP == "") {
    Serial.println("Django server IP not configured");
    return;
  }
  
  Serial.println("Registering with Django server...");
  
  WiFiClient client;
  HTTPClient http;
  
  // Construct the URL for the Django API endpoint
  String url = "http://" + djangoServerIP;
  if (djangoServerPort != 80) {
    url += ":" + String(djangoServerPort);
  }
  url += djangoAPIEndpoint;
  
  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  
  // Prepare the registration data
  DynamicJsonDocument doc(256);
  doc["name"] = "Pet Feeder - " + deviceID;
  doc["ip_address"] = WiFi.localIP().toString();
  doc["port"] = 80;
  doc["is_active"] = true;
  
  String jsonBody;
  serializeJson(doc, jsonBody);
  
  // Send the POST request
  int httpResponseCode = http.POST(jsonBody);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("HTTP Response code: " + String(httpResponseCode));
    Serial.println("Response: " + response);
  } else {
    Serial.println("Error on sending POST: " + String(httpResponseCode));
  }
  
  http.end();
}

void sendHeartbeatToDjango() {
  // Only attempt to send heartbeat if we have a server IP
  if (djangoServerIP == "") {
    return;
  }
  
  WiFiClient client;
  HTTPClient http;
  
  // Construct the URL for the Django API endpoint
  String url = "http://" + djangoServerIP;
  if (djangoServerPort != 80) {
    url += ":" + String(djangoServerPort);
  }
  url += djangoAPIEndpoint + "heartbeat/";
  
  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  
  // Prepare the heartbeat data
  DynamicJsonDocument doc(256);
  doc["device_id"] = deviceID;
  doc["ip_address"] = WiFi.localIP().toString();
  doc["status"] = "online";
  doc["timestamp"] = millis();
  
  String jsonBody;
  serializeJson(doc, jsonBody);
  
  // Send the POST request
  int httpResponseCode = http.POST(jsonBody);
  
  // We don't need to process the response for heartbeats
  http.end();
}

void notifyManualFeedToDjango() {
  // Only attempt to notify if we have a server IP
  if (djangoServerIP == "") {
    return;
  }
  
  WiFiClient client;
  HTTPClient http;
  
  // Construct the URL for the Django API endpoint
  String url = "http://" + djangoServerIP;
  if (djangoServerPort != 80) {
    url += ":" + String(djangoServerPort);
  }
  url += djangoAPIEndpoint + "feed/";
  
  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  
  // Prepare the feed notification data
  DynamicJsonDocument doc(256);
  doc["device_id"] = deviceID;
  doc["portion"] = 1; // Default to 1 portion for manual feeds
  doc["type"] = "manual";
  doc["timestamp"] = millis();
  
  String jsonBody;
  serializeJson(doc, jsonBody);
  
  // Send the POST request
  int httpResponseCode = http.POST(jsonBody);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Feed notification sent. Response code: " + String(httpResponseCode));
  }
  
  http.end();
}

void checkForPendingCommands() {
  // Only attempt to check if we have a server IP
  if (djangoServerIP == "") {
    return;
  }
  
  WiFiClient client;
  HTTPClient http;
  
  // Construct the URL for the Django API endpoint
  String url = "http://" + djangoServerIP;
  if (djangoServerPort != 80) {
    url += ":" + String(djangoServerPort);
  }
  url += djangoAPIEndpoint + "commands/?device_id=" + deviceID;
  
  http.begin(client, url);
  
  // Send the GET request
  int httpResponseCode = http.GET();
  
  if (httpResponseCode == 200) {
    String response = http.getString();
    
    // Parse the JSON response
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, response);
    
    if (!error) {
      // Check if there are any pending commands
      if (doc.containsKey("commands") && doc["commands"].is<JsonArray>()) {
        JsonArray commands = doc["commands"];
        
        for (JsonObject command : commands) {
          if (command.containsKey("type") && command["type"] == "feed") {
            // Execute feed command
            int portion = command["portion"] | 1; // Default to 1 if not specified
            
            Serial.println("Executing feed command from Django. Portion: " + String(portion));
            
            isFeeding = true;
            moveStepper(STEPS_PER_PORTION * portion, true);
            isFeeding = false;
            
            // Acknowledge the command
            acknowledgeCommand(command["id"]);
          }
        }
      }
    }
  }
  
  http.end();
}

void acknowledgeCommand(const String& commandId) {
  WiFiClient client;
  HTTPClient http;
  
  // Construct the URL for the Django API endpoint
  String url = "http://" + djangoServerIP;
  if (djangoServerPort != 80) {
    url += ":" + String(djangoServerPort);
  }
  url += djangoAPIEndpoint + "acknowledge/";
  
  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  
  // Prepare the acknowledgment data
  DynamicJsonDocument doc(256);
  doc["device_id"] = deviceID;
  doc["command_id"] = commandId;
  doc["status"] = "completed";
  doc["timestamp"] = millis();
  
  String jsonBody;
  serializeJson(doc, jsonBody);
  
  // Send the POST request
  http.POST(jsonBody);
  http.end();
}