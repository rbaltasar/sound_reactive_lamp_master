import time
import numpy as np
import pyaudio
import config

class Microphone:

    def __init__(self, callback):

        self._callback = callback

    def __del__(self):

        self.stop()

    #Start the client
    def begin(self):

        self._p = pyaudio.PyAudio()
        self._frames_per_buffer = int(config.MIC_RATE / config.FPS)
        self._stream = self._p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=config.MIC_RATE,
                        input=True,
                        frames_per_buffer=self._frames_per_buffer)
        self._overflows = 0
        self._prev_ovf_time = time.time()

    def stop(self):

        self._stream.stop_stream()
        self._stream.close()
        self._p.terminate()

    def take_samples(self):

        try:
            y = np.fromstring(self._stream.read(self._frames_per_buffer, exception_on_overflow=False), dtype=np.int16)
            y = y.astype(np.float32)
            self._stream.read(self._stream.get_read_available(), exception_on_overflow=False)
            self._callback(y)
        except IOError:
            self._overflows += 1
            if time.time() > self._prev_ovf_time + 1:
                self._prev_ovf_time = time.time()
                print('Audio buffer has overflowed {} times'.format(self._overflows))


def start_stream(callback):
    p = pyaudio.PyAudio()
    frames_per_buffer = int(config.MIC_RATE / config.FPS)
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=config.MIC_RATE,
                    input=True,
                    frames_per_buffer=frames_per_buffer)
    overflows = 0
    prev_ovf_time = time.time()
    while True:
        try:
            y = np.fromstring(stream.read(frames_per_buffer, exception_on_overflow=False), dtype=np.int16)
            y = y.astype(np.float32)
            stream.read(stream.get_read_available(), exception_on_overflow=False)
            callback(y)
        except IOError:
            overflows += 1
            if time.time() > prev_ovf_time + 1:
                prev_ovf_time = time.time()
                print('Audio buffer has overflowed {} times'.format(overflows))
    stream.stop_stream()
    stream.close()
    p.terminate()
