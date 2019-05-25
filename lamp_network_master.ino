
#include "frequency_utilities.h"
#include "serialFreqDisplay.h"
#include "config.h"

/* Audio signal analyzer */
FrequencyUtilities FreqUtilities;

/* Serial frequency display */
SerialFreqDisplay freqDisplay(THRESHOLD_DISPLAY, NSAMPLES/2);

void setup() {

  Serial.begin(115200);
  
  FreqUtilities.begin();

}

void loop() {
  // put your main code here, to run repeatedly:

  FreqUtilities.process_audio();
  freqDisplay.printFreq(FreqUtilities.get_processed_spectrum());

  //delay(200);

}
