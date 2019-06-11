#if !defined COMON_DATATYPES_H
#define COMON_DATATYPES_H

struct lamp_status
{
  uint8_t lamp_mode;
  // RGBcolor color;
  uint8_t brightness;
  bool resync;
  bool streaming;
  uint32_t effect_delay;
  uint32_t effect_speed;
};

#endif
