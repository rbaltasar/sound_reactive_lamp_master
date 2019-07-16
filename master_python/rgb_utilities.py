import numpy as np


def rgb2hsv(in_rgb):

    in_val = np.array([0.0,0.0,0.0])
    out = np.array([0.0,0.0,0.0])

    in_val[0] = float(in_rgb[0]) / 255.0
    in_val[1] = float(in_rgb[1]) / 255.0
    in_val[2] = float(in_rgb[2]) / 255.0

    if in_val[0] < in_val[1]:
        min = in_val[0]
    else:
        min = in_val[1]

    if min < in_val[2]:
        min = min
    else:
        min = in_val[2]

    if in_val[0] > in_val[1]:
        max = in_val[0]
    else:
        max = in_val[1]

    if max  > in_val[2]:
        max = max
    else:
        max = in_val[2]

    out[2] = max
    delta = max - min
    if (delta < 0.00001):

        out[1] = 0
        out[0] = 0
        return out

    if( max > 0.0 ):
        out[1] = (delta / max)
    else:
        out[1] = 0.0
        out[0] = 0.0
        return out

    if( in_val[0] >= max ):
        out[0] = ( in_val[1] - in_val[2] ) / delta

    if( in_val[1] >= max ):
        out[0] = 2.0 + ( in_val[2] - in_val[0] ) / delta
    else:
        out[0] = 4.0 + ( in_val[0] - in_val[1] ) / delta

    out[0] *= 60.0

    if( out[0] < 0.0 ):
        out[0] += 360.0

    return out


def hsv2rgb(in_val):

    out = np.array([0.0,0.0,0.0])

    if(in_val[1] <= 0.0):
        out[0] = in_val[2]
        out[1] = in_val[2]
        out[2] = in_val[2]

        return out * 255

    hh = in_val[0]
    if(hh >= 360.0):
        hh = 0.0
    hh /= 60.0
    i = int(hh)
    ff = hh - i
    p = in_val[2] * (1.0 - in_val[1])
    q = in_val[2] * (1.0 - (in_val[1] * ff))
    t = in_val[2] * (1.0 - (in_val[1] * (1.0 - ff)))

    if i== 0:
        out[0] = in_val[2]
        out[1] = t
        out[2] = p
    elif i==1:
        out[0] = q
        out[1] = in_val[2]
        out[2] = p
    elif i==2:
        out[0] = p
        out[1] = in_val[2]
        out[2] = t

    elif i== 3:
        out[0] = p
        out[1] = q
        out[2] = in_val[2]
    elif i== 4:
        out[0] = t
        out[1] = p
        out[2] = in_val[2]
    else:
        out[0] = in_val[2]
        out[1] = p
        out[2] = q


    return out * 255
