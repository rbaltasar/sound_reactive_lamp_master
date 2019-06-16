#if !defined COMON_DATATYPES_H
#define COMON_DATATYPES_H

struct color_request {
  uint8_t msgID;
  uint8_t red;
  uint8_t green;
  uint8_t blue;
};

struct RGBcolor
{
  uint8_t R;
  uint8_t G;
  uint8_t B;
};

struct lamp_status
{
  uint8_t lamp_mode;
  RGBcolor color;
  uint8_t brightness;
  bool resync;
  bool streaming;
  uint32_t effect_delay;
  uint32_t effect_speed;
};

#endif
