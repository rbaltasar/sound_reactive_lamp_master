
#if !defined FREQUENCY_UTILITIES_H
#define FREQUENCY_UTILITIES_H

#if defined(ARDUINO) && ARDUINO >= 100
#include "Arduino.h"
#else
#include "WProgram.h"
#endif
#include "config.h"
#include <driver/adc.h>
#include <arduinoFFT.h>

class FrequencyUtilities
{

private:

  float max_level_freq_historic;
  unsigned long newTime, oldTime;
  

  uint8_t dominant_frequency;
  uint16_t max_level_historic;
  uint16_t iterations_count;
  unsigned int sampling_period_us;

  arduinoFFT FFT = arduinoFFT();

public:

  double max_level_actual;
  double max_level_freq_instant;
  double im[NSAMPLES], data[NSAMPLES];

  FrequencyUtilities();

  void begin();

  void get_freq_info();
  void take_samples();
  void time_to_freq();
  bool clap_detected();
  bool detect_single_clap();
  void process_audio();
  double* get_processed_spectrum();

};

#endif
/*********************************************************************************************************
  END FILE
*********************************************************************************************************/
