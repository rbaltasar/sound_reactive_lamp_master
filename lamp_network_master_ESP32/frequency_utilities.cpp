
#include "frequency_utilities.h"


FrequencyUtilities::FrequencyUtilities()
{
}

void FrequencyUtilities::begin()
{

  max_level_actual = 0;
  max_level_historic = 0;
  max_level_freq_historic = 0;
  iterations_count = 0;
  sampling_period_us = round(1000000 * (1.0 / SAMPLING_FREQUENCY));

  /* Configure ADC */
  adc1_config_width(ADC_WIDTH_BIT_10);   //Range 0-1023 
  adc1_config_channel_atten(ADC1_CHANNEL_0,ADC_ATTEN_DB_11);  //ADC_ATTEN_DB_11 = 0-3,6V

}

void FrequencyUtilities::take_samples()
{
  double val;
  double maxVal = 0;
  double minVal = 1024;
  for (uint16_t i = 0; i < NSAMPLES; i++)
  {
    newTime = micros()-oldTime;
    oldTime = newTime;
    val = (double)adc1_get_raw( ADC1_CHANNEL_0 );//analogRead(A0) / 8;
    val > maxVal ? maxVal = val : maxVal = maxVal;
    val < minVal ? minVal = val : minVal = minVal;
    //data[i] = val/4- 128;
    data[i] = val;
    im[i] = 0;
    while (micros() < (newTime + sampling_period_us)) { /* do nothing to wait */ }
  }

  max_level_actual = maxVal; 

  #if (DEBUG_TRACES_TIME == 1)
  Serial.print("Max value: ");
  Serial.print(maxVal);
  Serial.print(" Min value: ");
  Serial.print(minVal);
  Serial.print(" Diff value: ");
  Serial.println(maxVal - minVal); 
  #endif
}

void FrequencyUtilities::time_to_freq()
{
   FFT.Windowing(data, NSAMPLES, FFT_WIN_TYP_HAMMING, FFT_FORWARD);
   FFT.Compute(data, im, NSAMPLES, FFT_FORWARD);
   FFT.ComplexToMagnitude(data, im, NSAMPLES);
}

void FrequencyUtilities::get_freq_info()
{
  max_level_freq_instant = 0;
  dominant_frequency = 99;

  for(uint8_t i=2; i<NSAMPLES/2; i++)
  {  
    //Serial.print(data[i]);
    //Serial.print(" ");  
    if (data[i] > max_level_freq_instant )
    {
      dominant_frequency = i;
      max_level_freq_instant = data[i];
    }
  }

  //Serial.println("");


  #if (DEBUG_TRACES_FREQ == 1)
  Serial.print("Dominant frequency: ");
  Serial.print(dominant_frequency);
  Serial.print(" max_level_freq_instant: ");
  Serial.println(max_level_freq_instant);  
  #endif
}


bool FrequencyUtilities::clap_detected()
{
  //Check if sound above threshold detected
  if(max_level_actual > THRESHOLD_CLAP)
  {  
    //Check if the sound max frequency  is in the frequency of the clap
    if( (dominant_frequency > 0/*SAMPLES/8*/) && (dominant_frequency < (5*NSAMPLES)/6))
    {
      //Serial.println("Clap detected!");   
      return true;
    }
  }
  
  return false;
}

bool FrequencyUtilities::detect_single_clap()
{
  //Sample input signal
  take_samples();
  time_to_freq();
  get_freq_info();

  return clap_detected();
}

void FrequencyUtilities::process_audio()
{
  //Sample input signal
  take_samples();
  time_to_freq();
  get_freq_info();
}

double* FrequencyUtilities::get_processed_spectrum()
{
  return data;
}



/*********************************************************************************************************
  END FILE
*********************************************************************************************************/
