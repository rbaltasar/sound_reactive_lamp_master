#if !defined OTAUPDATER_H
#define OTAUPDATER_H

#if (ARDUINO >= 100)
 #include <Arduino.h>
#else
 #include <WProgram.h>
#endif

#include <WiFiClient.h>
# include <WebServer.h>
# include <ESPmDNS.h>
# include <Update.h>



class OTAUpdater
{

private: 
 

public: 

  //virtual OTAUpdater() = 0;
  virtual void OTA_handle() = 0;
  virtual void begin(const char* host_name) = 0;
  
};

#endif
/*********************************************************************************************************
  END FILE
*********************************************************************************************************/
