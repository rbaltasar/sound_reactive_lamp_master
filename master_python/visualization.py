from __future__ import print_function
from __future__ import division
import time
import numpy as np
from scipy.ndimage.filters import gaussian_filter1d
import config
import microphone
import dsp
import led
from udp_controller import udp_handler

_time_prev = time.time() * 1000.0
"""The previous time that the frames_per_second() function was called"""

_fps = dsp.ExpFilter(val=config.FPS, alpha_decay=0.2, alpha_rise=0.2)
"""The low-pass filter used to estimate frames-per-second"""

# Shared memory. Simple payload
effect_payload_r = 0
effect_payload_g = 0
effect_payload_b = 0
effect_payload_ampl = 0

#Shared memory. Spectrum payload. Allocate for the maximum number of lamps
num_spectrum_windows = 0

effect_payload_spectrum = np.tile(0, (6, 4))

def frames_per_second():
    """Return the estimated frames per second

    Returns the current estimate for frames-per-second (FPS).
    FPS is estimated by measured the amount of time that has elapsed since
    this function was previously called. The FPS estimate is low-pass filtered
    to reduce noise.

    This function is intended to be called one time for every iteration of
    the program's main loop.

    Returns
    -------
    fps : float
        Estimated frames-per-second. This value is low-pass filtered
        to reduce noise.
    """
    global _time_prev, _fps
    time_now = time.time() * 1000.0
    dt = time_now - _time_prev
    _time_prev = time_now
    if dt == 0.0:
        return _fps.value
    return _fps.update(1000.0 / dt)


def memoize(function):
    """Provides a decorator for memoizing functions"""
    from functools import wraps
    memo = {}

    @wraps(function)
    def wrapper(*args):
        if args in memo:
            return memo[args]
        else:
            rv = function(*args)
            memo[args] = rv
            return rv
    return wrapper


@memoize
def _normalized_linspace(size):
    return np.linspace(0, 1, size)


def interpolate(y, new_length):
    """Intelligently resizes the array by linearly interpolating the values

    Parameters
    ----------
    y : np.array
        Array that should be resized

    new_length : int
        The length of the new interpolated array

    Returns
    -------
    z : np.array
        New array with length of new_length that contains the interpolated
        values of y.
    """
    if len(y) == new_length:
        return y
    x_old = _normalized_linspace(len(y))
    x_new = _normalized_linspace(new_length)
    z = np.interp(x_new, x_old, y)
    return z


r_filt = dsp.ExpFilter(np.tile(0.01, config.N_PIXELS // 2),
                       alpha_decay=0.2, alpha_rise=0.99)
g_filt = dsp.ExpFilter(np.tile(0.01, config.N_PIXELS // 2),
                       alpha_decay=0.05, alpha_rise=0.3)
b_filt = dsp.ExpFilter(np.tile(0.01, config.N_PIXELS // 2),
                       alpha_decay=0.1, alpha_rise=0.5)
common_mode = dsp.ExpFilter(np.tile(0.01, config.N_PIXELS // 2),
                       alpha_decay=0.99, alpha_rise=0.01)
p_filt = dsp.ExpFilter(np.tile(1, (3, config.N_PIXELS // 2)),
                       alpha_decay=0.1, alpha_rise=0.99)

p = np.tile(1.0, (3, config.N_PIXELS // 2))

gain = dsp.ExpFilter(np.tile(0.01, config.N_FFT_BINS),
                     alpha_decay=0.001, alpha_rise=0.99)


p_filt_window = []
p_filt_window.append(dsp.ExpFilter(np.tile(1, (3, config.N_PIXELS // 2)),
                       alpha_decay=0.1, alpha_rise=0.99))
p_filt_window.append(dsp.ExpFilter(np.tile(1, (3, config.N_PIXELS // 2)),
                       alpha_decay=0.1, alpha_rise=0.99))
p_filt_window.append(dsp.ExpFilter(np.tile(1, (3, config.N_PIXELS // 2)),
                       alpha_decay=0.1, alpha_rise=0.99))
p_filt_window.append(dsp.ExpFilter(np.tile(1, (3, config.N_PIXELS // 2)),
                       alpha_decay=0.1, alpha_rise=0.99))
p_filt_window.append(dsp.ExpFilter(np.tile(1, (3, config.N_PIXELS // 2)),
                       alpha_decay=0.1, alpha_rise=0.99))
p_filt_window.append(dsp.ExpFilter(np.tile(1, (3, config.N_PIXELS // 2)),
                       alpha_decay=0.1, alpha_rise=0.99))

def compute_amplitude_energy(r,g,b):

    amplitude = (r+g+b) / (3 * 255)
    amplitude *= 100* 0.8

    return np.clip(int(amplitude),0, 80).astype(int)


def visualize_scroll(y):
    """Effect that originates in the center and scrolls outwards"""
    global p
    y = y**2.0
    gain.update(y)
    y /= gain.value
    y *= 255.0

    r = np.clip(int(np.max(y[:len(y) // 3])), 0, 255).astype(int)
    g = np.clip(int(np.max(y[len(y) // 3: 2 * len(y) // 3])), 0, 255).astype(int)
    b = np.clip(int(np.max(y[2 * len(y) // 3:])), 0, 255).astype(int)

    global effect_payload_r, effect_payload_g, effect_payload_b, effect_payload_ampl
    effect_payload_r = r
    effect_payload_g = g
    effect_payload_b = b
    effect_payload_ampl = compute_amplitude_energy(r,g,b)

    # Scrolling effect window
    p[:, 1:] = p[:, :-1]
    p *= 0.98
    p = gaussian_filter1d(p, sigma=0.2)
    # Create new color originating at the center
    p[0, 0] = r
    p[1, 0] = g
    p[2, 0] = b
    # Update the LED strip
    return np.concatenate((p[:, ::-1], p), axis=1)

def visualize_energy(y):
    """Effect that expands from the center with increasing sound energy"""
    global p
    y = np.copy(y)
    gain.update(y)
    y /= gain.value
    # Scale by the width of the LED strip
    y *= float((config.N_PIXELS // 2) - 1)
    # Map color channels according to energy in the different freq bands
    scale = 0.9
    r = np.clip(int(np.mean(y[:len(y) // 3]**scale)), 0, 255).astype(int)
    g = np.clip(int(np.mean(y[len(y) // 3: 2 * len(y) // 3]**scale)), 0, 255).astype(int)
    b = np.clip(int(np.mean(y[2 * len(y) // 3:]**scale)), 0, 255).astype(int)

    # Assign color to different frequency regions
    p[0, :r] = 255.0
    p[0, r:] = 0.0
    p[1, :g] = 255.0
    p[1, g:] = 0.0
    p[2, :b] = 255.0
    p[2, b:] = 0.0
    p_filt.update(p)
    p = np.round(p_filt.value)
    # Apply substantial blur to smooth the edges
    p[0, :] = gaussian_filter1d(p[0, :], sigma=4.0)
    p[1, :] = gaussian_filter1d(p[1, :], sigma=4.0)
    p[2, :] = gaussian_filter1d(p[2, :], sigma=4.0)

    # Set the new pixel value
    retval = np.concatenate((p[:, ::-1], p), axis=1)

    global effect_payload_r, effect_payload_g, effect_payload_b, effect_payload_ampl
    effect_payload_r = retval[0][int(len(retval[0])/2)]
    effect_payload_g = retval[1][int(len(retval[1])/2)]
    effect_payload_b = retval[2][int(len(retval[2])/2)]
    effect_payload_ampl = compute_amplitude_energy(effect_payload_r,effect_payload_g,effect_payload_b)


    #print("R: ", effect_payload_r, "G: ",effect_payload_g, "B: ", effect_payload_b, "Amplitude: ", effect_payload_ampl)

    return retval

def visualize_energy_spectrum(y):

    global p

    y = np.copy(y)
    gain.update(y)
    y /= gain.value

    # Scale by the width of the LED strip
    y *= float((config.N_PIXELS // 2) - 1)

    #Process each of the spectrum windows independently
    for i in range(0,num_spectrum_windows):

        #Extract the spectrum information
        freq_start = i * (len(y) // num_spectrum_windows)
        freq_end = freq_start + (len(y) // num_spectrum_windows)

        y_window = np.copy(y[freq_start:freq_end])

        #print("Window: ", i)
        #print("Frequency window: ", freq_start, "-", freq_end)

        # Map color channels according to energy in the different freq bands
        scale = 0.9
        r = np.clip(int(np.mean(y_window[:len(y_window) // 3]**scale)), 0, 255).astype(int)
        g = np.clip(int(np.mean(y_window[len(y_window) // 3: 2 * len(y_window) // 3]**scale)), 0, 255).astype(int)
        b = np.clip(int(np.mean(y_window[2 * len(y_window) // 3:]**scale)), 0, 255).astype(int)

        # Assign color to different frequency regions
        p[0, :r] = 255.0
        p[0, r:] = 0.0
        p[1, :g] = 255.0
        p[1, g:] = 0.0
        p[2, :b] = 255.0
        p[2, b:] = 0.0

        p_filt_window[i].update(p)
        p = np.round(p_filt_window[i].value)

        global effect_payload_r, effect_payload_g, effect_payload_b, effect_payload_ampl
        effect_payload_spectrum[i][0] = p[0][r]
        effect_payload_spectrum[i][1] = p[1][g]
        effect_payload_spectrum[i][2] = p[2][b]
        effect_payload_spectrum[i][3] = compute_amplitude_energy(p[0][r],p[1][g],p[2][b])


        #print("R: ", effect_payload_spectrum[i][0], "G: ",effect_payload_spectrum[i][1], "B: ", effect_payload_spectrum[i][2], "Amplitude: ", effect_payload_spectrum[i][3])

        # Apply substantial blur to smooth the edges
        p[0, :] = gaussian_filter1d(p[0, :], sigma=4.0)
        p[1, :] = gaussian_filter1d(p[1, :], sigma=4.0)
        p[2, :] = gaussian_filter1d(p[2, :], sigma=4.0)

        # Set the new pixel value
        retval = np.concatenate((p[:, ::-1], p), axis=1)

    return retval


_prev_spectrum = np.tile(0.01, config.N_PIXELS // 2)


def visualize_spectrum(y):
    """Effect that maps the Mel filterbank frequencies onto the LED strip"""
    global _prev_spectrum
    y = np.copy(interpolate(y, config.N_PIXELS // 2))
    common_mode.update(y)
    diff = y - _prev_spectrum
    _prev_spectrum = np.copy(y)
    # Color channel mappings
    r = r_filt.update(y - common_mode.value)
    g = np.abs(diff)
    b = b_filt.update(np.copy(y))
    # Mirror the color channels for symmetric output
    r = np.concatenate((r[::-1], r))
    g = np.concatenate((g[::-1], g))
    b = np.concatenate((b[::-1], b))
    output = np.array([r, g,b]) * 255
    return output


fft_plot_filter = dsp.ExpFilter(np.tile(1e-1, config.N_FFT_BINS),
                         alpha_decay=0.5, alpha_rise=0.99)
mel_gain = dsp.ExpFilter(np.tile(1e-1, config.N_FFT_BINS),
                         alpha_decay=0.01, alpha_rise=0.99)
mel_smoothing = dsp.ExpFilter(np.tile(1e-1, config.N_FFT_BINS),
                         alpha_decay=0.5, alpha_rise=0.99)
volume = dsp.ExpFilter(config.MIN_VOLUME_THRESHOLD,
                       alpha_decay=0.02, alpha_rise=0.02)
fft_window = np.hamming(int(config.MIC_RATE / config.FPS) * config.N_ROLLING_HISTORY)
prev_fps_update = time.time()


def microphone_update(audio_samples):
    global y_roll, prev_rms, prev_exp, prev_fps_update
    # Normalize samples between 0 and 1
    y = audio_samples / 2.0**15
    # Construct a rolling window of audio samples
    y_roll[:-1] = y_roll[1:]
    y_roll[-1, :] = np.copy(y)
    y_data = np.concatenate(y_roll, axis=0).astype(np.float32)

    vol = np.max(np.abs(y_data))
    if vol < config.MIN_VOLUME_THRESHOLD:
        print('No audio input. Volume below threshold. Volume:', vol)
        led.pixels = np.tile(0, (3, config.N_PIXELS))
        led.update()
    else:
        # Transform audio input into the frequency domain
        N = len(y_data)
        N_zeros = 2**int(np.ceil(np.log2(N))) - N
        # Pad with zeros until the next power of two
        y_data *= fft_window
        y_padded = np.pad(y_data, (0, N_zeros), mode='constant')
        YS = np.abs(np.fft.rfft(y_padded)[:N // 2])
        # Construct a Mel filterbank from the FFT data
        mel = np.atleast_2d(YS).T * dsp.mel_y.T
        # Scale data to values more suitable for visualization
        # mel = np.sum(mel, axis=0)
        mel = np.sum(mel, axis=0)
        mel = mel**2.0
        # Gain normalization
        mel_gain.update(np.max(gaussian_filter1d(mel, sigma=1.0)))
        mel /= mel_gain.value
        mel = mel_smoothing.update(mel)

        # Map filterbank output onto LED strip
        output = visualization_effect(mel)

        led.pixels = output
        #led.update()

        # Send single payload
        if(visualization_effect is not visualize_energy_spectrum):
            udp_handler.send_payload_single(effect_payload_r,effect_payload_g,effect_payload_b,effect_payload_ampl)

        #Send multiple payload
        else:

            udp_handler.send_payload_multiple(num_spectrum_windows, effect_payload_spectrum)

            pass

        if config.USE_GUI:
            # Plot filterbank output
            x = np.linspace(config.MIN_FREQUENCY, config.MAX_FREQUENCY, len(mel))
            mel_curve.setData(x=x, y=fft_plot_filter.update(mel))
            # Plot the color channels
            r_curve.setData(y=led.pixels[0])
            g_curve.setData(y=led.pixels[1])
            b_curve.setData(y=led.pixels[2])

    if config.USE_GUI:
        app.processEvents()

    if config.DISPLAY_FPS:
        fps = frames_per_second()
        if time.time() - 0.5 > prev_fps_update:
            prev_fps_update = time.time()
            print('FPS {:.0f} / {:.0f}'.format(fps, config.FPS))


# Number of audio samples to read every time frame
samples_per_frame = int(config.MIC_RATE / config.FPS)

# Array containing the rolling audio sample window
y_roll = np.random.rand(config.N_ROLLING_HISTORY, samples_per_frame) / 1e16

visualization_effect = visualize_energy_spectrum
"""Visualization effect to display on the LED strip"""

# Global microphone
mic = microphone.Microphone(microphone_update)

def begin():

    mic.begin()

def stop():

    mic.stop()
    #app.exit()

def feed():

    mic.take_samples()

def configure_gui():
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtGui, QtCore

    #Define global variables
    global mel_curve
    global led_plot
    global r_pen
    global g_pen
    global b_pen
    global r_curve
    global g_curve
    global b_curve
    global x_data
    global app

    # Create GUI window
    app = QtGui.QApplication([])
    view = pg.GraphicsView()
    layout = pg.GraphicsLayout(border=(100,100,100))
    view.setCentralItem(layout)
    view.show()
    view.setWindowTitle('Visualization')
    view.resize(800,600)
    # Mel filterbank plot
    fft_plot = layout.addPlot(title='Filterbank Output', colspan=4)
    fft_plot.setRange(yRange=[-0.1, 1.2])
    fft_plot.disableAutoRange(axis=pg.ViewBox.YAxis)
    x_data = np.array(range(1, config.N_FFT_BINS + 1))

    mel_curve = pg.PlotCurveItem()
    mel_curve.setData(x=x_data, y=x_data*0)
    fft_plot.addItem(mel_curve)
    # Visualization plot
    layout.nextRow()
    led_plot = layout.addPlot(title='Visualization Output', colspan=4)
    led_plot.setRange(yRange=[-5, 260])
    led_plot.disableAutoRange(axis=pg.ViewBox.YAxis)
    # Pen for each of the color channel curves
    r_pen = pg.mkPen((255, 30, 30, 200), width=4)
    g_pen = pg.mkPen((30, 255, 30, 200), width=4)
    b_pen = pg.mkPen((30, 30, 255, 200), width=4)
    # Color channel curves
    r_curve = pg.PlotCurveItem(pen=r_pen)
    g_curve = pg.PlotCurveItem(pen=g_pen)
    b_curve = pg.PlotCurveItem(pen=b_pen)
    # Define x data
    x_data = np.array(range(1, config.N_PIXELS + 1))
    r_curve.setData(x=x_data, y=x_data*0)
    g_curve.setData(x=x_data, y=x_data*0)
    b_curve.setData(x=x_data, y=x_data*0)
    # Add curves to plot
    led_plot.addItem(r_curve)
    led_plot.addItem(g_curve)
    led_plot.addItem(b_curve)
    # Frequency range label
    freq_label = pg.LabelItem('')
    # Frequency slider
    def freq_slider_change(tick):
        minf = freq_slider.tickValue(0)**2.0 * (config.MIC_RATE / 2.0)
        maxf = freq_slider.tickValue(1)**2.0 * (config.MIC_RATE / 2.0)
        t = 'Frequency range: {:.0f} - {:.0f} Hz'.format(minf, maxf)
        freq_label.setText(t)
        config.MIN_FREQUENCY = minf
        config.MAX_FREQUENCY = maxf
        dsp.create_mel_bank()
    freq_slider = pg.TickSliderItem(orientation='bottom', allowAdd=False)
    freq_slider.addTick((config.MIN_FREQUENCY / (config.MIC_RATE / 2.0))**0.5)
    freq_slider.addTick((config.MAX_FREQUENCY / (config.MIC_RATE / 2.0))**0.5)
    freq_slider.tickMoveFinished = freq_slider_change
    freq_label.setText('Frequency range: {} - {} Hz'.format(
        config.MIN_FREQUENCY,
        config.MAX_FREQUENCY))
    # Effect selection
    active_color = '#16dbeb'
    inactive_color = '#FFFFFF'
    def energy_click(x):
        global visualization_effect
        visualization_effect = visualize_energy
        energy_label.setText('Energy', color=active_color)
        energy_spectr_label.setText('Energy spectr', color=inactive_color)
        scroll_label.setText('Scroll', color=inactive_color)
        spectrum_label.setText('Spectrum', color=inactive_color)
    def energy_spectrum_click(x):
        global visualization_effect
        visualization_effect = visualize_energy_spectrum
        energy_label.setText('Energy', color=inactive_color)
        energy_spectr_label.setText('Energy spectr', color=active_color)
        scroll_label.setText('Scroll', color=inactive_color)
        spectrum_label.setText('Spectrum', color=inactive_color)
    def scroll_click(x):
        global visualization_effect
        visualization_effect = visualize_scroll
        energy_label.setText('Energy', color=inactive_color)
        energy_spectr_label.setText('Energy spectr', color=inactive_color)
        scroll_label.setText('Scroll', color=active_color)
        spectrum_label.setText('Spectrum', color=inactive_color)
    def spectrum_click(x):
        global visualization_effect
        visualization_effect = visualize_spectrum
        energy_label.setText('Energy', color=inactive_color)
        energy_spectr_label.setText('Energy spectr', color=inactive_color)
        scroll_label.setText('Scroll', color=inactive_color)
        spectrum_label.setText('Spectrum', color=active_color)

    # Create effect "buttons" (labels with click event)
    energy_label = pg.LabelItem('Energy')
    energy_spectr_label = pg.LabelItem('Energy Spectr')
    scroll_label = pg.LabelItem('Scroll')
    spectrum_label = pg.LabelItem('Spectrum')
    energy_label.mousePressEvent = energy_click
    energy_spectr_label.mousePressEvent = energy_spectrum_click
    scroll_label.mousePressEvent = scroll_click
    spectrum_label.mousePressEvent = spectrum_click
    energy_click(0)
    # Layout
    layout.nextRow()
    layout.addItem(freq_label, colspan=4)
    layout.nextRow()
    layout.addItem(freq_slider, colspan=4)
    layout.nextRow()
    layout.addItem(energy_label)
    layout.addItem(scroll_label)
    layout.addItem(spectrum_label)
    layout.addItem(energy_spectr_label)

if __name__ == '__main__':


    if config.USE_GUI:
        configure_gui()
    # Initialize LEDs
    led.update()
    # Start listening to live audio stream
    microphone.start_stream(microphone_update)
