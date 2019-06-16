
#include "UDPHandler.h"
 

UDPHandler::UDPHandler(lamp_status* lamp_status_request):
m_lamp_status_request(lamp_status_request)
{
  m_message = new uint8_t[20];
}

UDPHandler::~UDPHandler()
{
  delete [] m_message;
}

void UDPHandler::begin() 
{
  //m_UDP.begin(7001);
  if(m_UDP.listenMulticast(IPAddress(239,1,2,3), 7001)) {
        //Serial.print("UDP Listening on IP: ");
        //Serial.println(WiFi.localIP());
        m_UDP.onPacket([this](AsyncUDPPacket packet) {

            m_message = packet.data();
            Serial.println(msg_count++);
#if 0
            Serial.print("UDP Packet Type: ");
            Serial.print(packet.isBroadcast()?"Broadcast":packet.isMulticast()?"Multicast":"Unicast");
            Serial.print(", From: ");
            Serial.print(packet.remoteIP());
            Serial.print(":");
            Serial.print(packet.remotePort());
            Serial.print(", To: ");
            Serial.print(packet.localIP());
            Serial.print(":");
            Serial.print(packet.localPort());
            Serial.print(", Length: ");
            Serial.print(packet.length());
            Serial.print(", Data: ");
            Serial.print(m_message[0]);
            Serial.print(m_message[1]);
            Serial.println();
            //reply to the client
            //packet.printf("Got %u bytes of data", packet.length());
#endif
            

            if(m_message[0] == 0x02)
            {
              /* Do synchronization */
              synchronize(0);
            }

            else if(m_message[0] == 0x03)
            {
              /* Do synchronization */
              m_lamp_status_request->streaming = false;
            }

            else if(m_message[0] == 0x01)
            {
              color_request req = *((color_request*)m_message);      
        
              /* Select color for next prints */
              m_lamp_status_request->color.R = req.red;
              m_lamp_status_request->color.G = req.green;
              m_lamp_status_request->color.B = req.blue;
            }
            
        });       
    }
}

void UDPHandler::stop()
{
  //m_UDP.stop();
  m_UDP.close();
}

void UDPHandler::synchronize(unsigned long delay_ms)
{ 
  Serial.print("Synchronized with delay: ");
  Serial.println(delay_ms);

  /* Delay synchronization */
  delay(delay_ms);

  /* Acknowledge synchronization */
  uint8_t resp = 3;
  //m_UDP.beginPacket(masterIP,7001);
  //m_UDP.write(resp);
  //m_UDP.endPacket();  

  /* Indicate that resynchronization has been done */
  m_lamp_status_request->resync = true;
  
}

bool UDPHandler::network_loop()
{

  bool retval = true;
#if 0
  int packetSize = m_UDP.parsePacket();
  if (packetSize)
  {
    /* Read the packet */
    m_UDP.read((char *)&m_message, packetSize);

    /* Sync request */
    if(m_message[0] == 0x02)
    {
      sync_request req = *((sync_request*)m_message);      

      /* Do synchronization */
      synchronize((unsigned long)req.msgContent);

      Serial.print("Message type: ");
      Serial.println(req.msgID);
      Serial.print("Message content: ");
      Serial.println(req.msgContent);

    }   
    /* Streaming message (color & amplitude) */
    else if(m_message[0] == 0x01)
    {
      color_request req = *((color_request*)m_message);      

      /* Select color for next prints */
      m_lamp_status_request->color.R = req.red;
      m_lamp_status_request->color.G = req.green;
      m_lamp_status_request->color.B = req.blue;
    }

     /* Stop streaming message */
    else if(m_message[0] == 0x03)
    {
      /* Answer with an acknowledge */

      /* Set return value to stop streaming mode */
      retval = false;
    }
  }
#endif

  return retval;
}

/*********************************************************************************************************
  END FILE
*********************************************************************************************************/
