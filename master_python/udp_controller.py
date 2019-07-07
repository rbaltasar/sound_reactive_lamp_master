import socket
import config
from time import sleep

class UDPController:

    def __init__(self):

        self._last_r = 0
        self._last_g = 0
        self._last_b = 0
        self._last_ampl = 0

        self._mode = 100

    def __del__(self):

        self.stop()

    #Start the client
    def begin(self):

        print("Starting UDP client")

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def stop(self):

        print("Stoping UDP client")

        self._sock.close()

    def set_mode(self,mode):

        self._mode = mode

    def compare_and_update(self, r,g,b,ampl):

        if( (self._last_r == r) and (self._last_g == g) and (self._last_b == b) and (self._last_ampl == ampl) ):

            return True

        else:
            self._last_r = r
            self._last_g = g
            self._last_b = b
            self._last_ampl = ampl

            return False

    def send_multicast(self, msg, repetitions, delay_rep, delay_end):

        for i in range(1,repetitions):

            self._sock.sendto(msg, (config.UDP_IP, config.UDP_PORT))
            sleep(delay_rep)

        sleep(delay_end)

    def send_sync_req(self):

        print("Sending UDP sync request")

        msgId = 0x01
        delay = 0x00

        m = ''
        m += chr(msgId) + chr(delay)

        self.send_multicast(m, 3, 0, 0.5)

    def send_mode_request(self, mode_req):

        print("Sending UDP mode request")

        msgId = 0x00
        mode = int(mode_req)
        mask = 0xFF

        m = ''
        m += chr(msgId) + chr(mode) + chr(mask)

        self.send_multicast(m, 5, 0.5, 0)

    def send_payload_single(self, r, g, b, ampl):

        if(not self.compare_and_update(r,g,b,ampl)):

            msgId = 0x04
            mask = 0xFF

            m = ''
            m += chr(msgId) + chr(mask) + chr(int(r)) + chr(int(g)) + chr(int(b)) + chr(int(ampl))

            self.send_multicast(m, 3, 0.005, 0.01)

    def send_configuration(self, effect_delay, effect_direction, r, g, b, increment):

        msgId = 0x07

        m = ''
        m += chr(msgId) + chr(int(effect_delay)) + chr(int(effect_direction)) + chr(int(r)) + chr(int(g)) + chr(int(b)) + chr(int(increment))

        self.send_multicast(m, 4, 0.1, 0)

udp_handler = UDPController()
