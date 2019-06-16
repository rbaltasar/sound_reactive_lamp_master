#if !defined UDPHANDLER_H
#define UDPHANDLER_H

#if (ARDUINO >= 100)
 #include <Arduino.h>
#else
 #include <WProgram.h>
#endif

#include "config.h"
#include "common_datatypes.h"

//#include <WiFiUdp.h>
#include "AsyncUDP.h"

class UDPHandler
{

private:

  lamp_status* m_lamp_status_request;
  //WiFiUDP m_UDP;
  AsyncUDP m_UDP;
  //char m_message[20];
  uint8_t* m_message;

  uint32_t msg_count = 0;

  void synchronize(unsigned long delay_ms);

public: 

  UDPHandler(lamp_status* lamp_status_request);
  ~UDPHandler();

  void begin();
  void stop();

  bool network_loop();

 
};

#endif
/*********************************************************************************************************
  END FILE
*********************************************************************************************************/
