/*

*/
#include "serialFreqDisplay.h"
#include "HardwareSerial.h"

SerialFreqDisplay::SerialFreqDisplay(double threshold,  uint8_t fft_width)
{

  m_threshold = threshold;
  m_fft_width = fft_width;

}

void SerialFreqDisplay::begin()
{
 
}

void SerialFreqDisplay::printFreq(double* frequencies)
{

  for(uint8_t i = 2; i < m_fft_width - 1; i++)
  {
    if (frequencies[i] < m_threshold)
    {
      Serial.print("-");
    }
    else
    {
      Serial.print("#");
    }
  }

  Serial.println();

}

void SerialFreqDisplay::printVals(double* frequencies)
{

  for(uint8_t i = 0; i < m_fft_width - 1; i++)
  {
    Serial.print(frequencies[i]);
    Serial.print(" ");
  }

  Serial.println();
}

void SerialFreqDisplay::printVals_char(char* frequencies)
{

  for(uint8_t i = 0; i < m_fft_width - 1; i++)
  {
    Serial.print((int)frequencies[i]);
    Serial.print(" ");
  }

  Serial.println();
}
