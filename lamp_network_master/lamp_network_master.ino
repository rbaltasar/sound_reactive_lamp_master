#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

#include "OTA_updater_ESP32.h"
#include "UDPHandler.h"
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
lamp_status current_status;
enum system_state_var
{
  STARTUP = 0,
  NORMAL = 1,
  STREAMING = 2
};
system_state_var sysState;
UDPHandler udp_handler(&status_request);
color_request streaming_msg;
int iterations;

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
  if( strcmp(topic,"lamp_network/mode_request") == 0 )
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

void status_update()
{ 
  
  /* Check difference in mode request */
  if(status_request.lamp_mode != current_status.lamp_mode)
  {
    
    /* Streaming request */
    if(status_request.lamp_mode == 3)
    {
      Serial.println("Streaming request received");
      /* Start UDP socket */
      status_request.streaming = true;
      sysState = STREAMING;
      /* Go to lamp mode 2 to show a demo effect */
      status_request.lamp_mode = 2;
    }

    /* Streaming request */
    if(status_request.lamp_mode == 1)
    {
      Serial.println("ON request received");
      status_request.color.R = RGB_DEFAULT;
      status_request.color.G = RGB_DEFAULT;
      status_request.color.B = RGB_DEFAULT;
      status_request.effect_delay = 50;
      status_request.effect_speed = 50;
      status_request.streaming = false;
    }
    
    Serial.print("Received change request to mode ");
    Serial.println(status_request.lamp_mode);
       
    current_status.lamp_mode = status_request.lamp_mode;   
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
  
  // Loop until we're reconnected
  while (!client.connected())
  {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect(IPAddress_string.c_str())) //Unique name for each instance of a slave
    {
      Serial.println("connected");
      /* Subscribe to topics */
      client.subscribe("lamp_network/mode_request");
      client.subscribe("lamp_network/alive_rx");
    }
    else
    {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(500);
    }
  }
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

  sysState = NORMAL;
  
  Serial.println("init OK");
}

void loop()
{

  switch(sysState)
  {
    case STARTUP:
      //network_loop();
      //initComm();
      break; 
    case NORMAL:
      client.loop();
      status_update();
      updater.OTA_handle();  
      iterations = 0;
      break;
    case STREAMING:
      uint8_t default_red, default_green, default_blue;
      default_red = 0x01;
      default_green = 0x01;
      default_blue = 0x01;
      
      iterations++;
      Serial.println(iterations);
      
      udp_handler.begin();
      if(iterations >100)
      {
        Serial.println("stop streaming");
        streaming_msg.msgID = 0x03;
        sysState = NORMAL;
      }
      else
      {
        double* frequencies;
        int sound_bit = 0;
        
        // FreqUtilities.process_audio();
        // freqDisplay.printFreq(FreqUtilities.get_processed_spectrum());
        // frequencies = FreqUtilities.get_processed_spectrum();
/*
        for(uint8_t i = 2; i < (NSAMPLES / 2) - 1; i++)
        {
          if (frequencies[i] >= THRESHOLD_DISPLAY)
          {
            sound_bit = sound_bit = 1;
          }
        }
 */       

        /* Send messages */
        streaming_msg.msgID = 0x01;
        streaming_msg.red = default_red;
        streaming_msg.green = default_green;
        streaming_msg.blue = default_blue;
        udp_handler.sendToAll((uint8_t *)&streaming_msg, sizeof(streaming_msg));
        delay(1000);
  
        streaming_msg.msgID = 0x02;
        streaming_msg.red = default_red;
        streaming_msg.green = default_green;
        streaming_msg.blue = default_blue;

        for(uint8_t red_count = 0; red_count < 7; red_count++)
        {
           delay(10);
           streaming_msg.red = streaming_msg.red << 1;
           udp_handler.sendToAll((uint8_t *)&streaming_msg, sizeof(streaming_msg));
           delay(27);
        }
        streaming_msg.red = default_red;
        streaming_msg.green = default_green;
        streaming_msg.blue = default_blue;
        for(uint8_t green_count = 0; green_count < 7; green_count++)
        {
           delay(10);
           streaming_msg.green = streaming_msg.green << 1;
           udp_handler.sendToAll((uint8_t *)&streaming_msg, sizeof(streaming_msg));
           delay(27);
        }
        streaming_msg.red = default_red;
        streaming_msg.green = default_green;
        streaming_msg.blue = default_blue;
        for(uint8_t rblue_count = 0; rblue_count < 7; rblue_count++)
        {
           delay(10);
           streaming_msg.blue = streaming_msg.blue << 1;
           udp_handler.sendToAll((uint8_t *)&streaming_msg, sizeof(streaming_msg));
           delay(27);
        }
      }

      break;
    default: 
      Serial.println("ERROR: unknown sysStatus");
  }
}
