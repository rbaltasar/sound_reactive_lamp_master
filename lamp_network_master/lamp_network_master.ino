#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

#include "OTA_updater_ESP32.h"

#include "common_datatypes.h"
#include "network_settings.h"
#include "config.h"

#include "frequency_utilities.h"
#include "serialFreqDisplay.h"


/* Communication settings */
WiFiClient espClient;
PubSubClient client(espClient);
DynamicJsonBuffer jsonBuffer(250);
String IPAddress_string;
String MACAddress_string;

/* enable the remote firware updates */
OTAUpdater_ESP32 updater;

/* Audio signal analyzer */
FrequencyUtilities FreqUtilities;

/* Serial frequency display */
SerialFreqDisplay freqDisplay(THRESHOLD_DISPLAY, NSAMPLES/2);

/* control variables */
lamp_status status_request;

/* convert IP address to a string */
String IpAddress2String(const IPAddress& ipAddress)
{
  return String(ipAddress[0]) + String(".") +\
  String(ipAddress[1]) + String(".") +\
  String(ipAddress[2]) + String(".") +\
  String(ipAddress[3])  ;
}

/* Configure the callback function for a subscribed MQTT topic */
void callback(char* topic, byte* payload, unsigned int length) 
{
  /* Parse JSON object */
  JsonObject& root = jsonBuffer.parseObject(payload);

  /* Filter for topics */
  if( strcmp(topic,"lamp_network/master/mode_request") == 0 )
  {
    status_request.lamp_mode = root["mode"];   
    Serial.println("mode_request");
    Serial.println(status_request.lamp_mode);
  }
  else if( strcmp(topic,"lamp_network/alive_rx") == 0 )
  {;   
    Serial.println("alive_rx");
  }
}

void setup_OTA(const char *url)
{
  updater.begin(url);
}


void setup_wifi(const char *s, const char *p)
{
  WiFi.begin(s, p); // Connect to the network
  Serial.print("Connecting to ");
  Serial.print(ssid);
  Serial.println(" ...");

  WiFi.mode(WIFI_STA);
  
  int i = 0;
  while (WiFi.status() != WL_CONNECTED)
  { // Wait for the Wi-Fi to connect
    delay(1000);
    Serial.print(++i);
    Serial.print(' ');
  }
  Serial.println('\n');
  Serial.println("Connection established!");
  Serial.print("IP address:\t");
  Serial.println(WiFi.localIP()); // Send the IP address of the ESP8266 to the computer
  Serial.print("MAC address: ");
  Serial.println(WiFi.macAddress());

  MACAddress_string = WiFi.macAddress();

  /* Translate the IP address to String to have a unique name for MQTT client */
  IPAddress_string = IpAddress2String(WiFi.localIP());  
  
}

void setup_mqtt()
{
  /* Define MQTT broker */
  client.setServer(mqtt_server, 1883);

  /* Define callback function */
  client.setCallback(callback);

  /* Subscribe to topics */
  client.subscribe("lamp_network/master/mode_request");
  client.subscribe("lamp_network/alive_rx");
}

void setup() {

  Serial.begin(115200);
  delay(10);

  setup_wifi(ssid, password);
  delay(10);

  setup_OTA(IPAddress_string.c_str());
  delay(100);
  
  setup_mqtt();
  delay(100);

  FreqUtilities.begin();
  delay(100);
  
  Serial.println("init OK");
}

void loop() {
  updater.OTA_handle();
  client.loop();

  FreqUtilities.process_audio();
  // TODO freqDisplay.printFreq(FreqUtilities.get_processed_spectrum());

  //delay(200);

}
