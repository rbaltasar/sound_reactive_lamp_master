#ifndef _MYLIBRARY_H
#define _MYLIBRARY_H
#if defined(ARDUINO) && ARDUINO >= 100
#include "Arduino.h"
#else
#include "WProgram.h"
#endif

#include "config.h"

class SerialFreqDisplay
{

private:

  int m_threshold, m_fft_width;

public:
    SerialFreqDisplay(double threshold, uint8_t fft_width);
    void begin();
    void printFreq(double* frequencies);
    void printVals(double* frequencies);
    void printVals_char(char* frequencies);
};

#endif

/*********************************************************************************************************
  END FILE
*********************************************************************************************************/
