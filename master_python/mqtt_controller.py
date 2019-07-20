import time
import paho.mqtt.client as paho
import json

class MQTTController:

    def __init__(self):

        #Create client
        self._client = paho.Client("LampNetworkMaster")
        #Define callback for received topics
        self._client.on_message =  self.callback

        self._min_freq = 0
        self._max_freq = 0
        self._effect_delay = 0
        self._effect_direction = 0
        self._num_lamps = 0
        self._num_freq_windows = 0
        self._mode = 0
        self._base_color_r = 0
        self._base_color_g = 0
        self._base_color_b = 0
        self._color_increment = 1
        self._effect_type = 0

        self._freq_windows = [0,0,0,0,0,0]

    def __del__(self):

        self.stop()

    def callback(self, client, userdata, message):

        received_msg = json.loads(message.payload)
        print("received message =",received_msg)

        if(message.topic == "lamp_network_music/configuration"):

            print("Received a configuration message")
            self._new_msg_config = True
            self._min_freq = int(received_msg['min_freq'])
            self._max_freq = int(received_msg['max_freq'])
            self._effect_delay = int(received_msg['effect_delay'])
            self._effect_direction = int(received_msg['effect_direction'])
            self._num_lamps = int(received_msg['num_lamps'])
            self._num_freq_windows = int(received_msg['num_freq_windows'])
            self._base_color_r = int(received_msg['base_color_r'])
            self._base_color_g = int(received_msg['base_color_g'])
            self._base_color_b = int(received_msg['base_color_b'])
            self._color_increment = int(received_msg['color_increment'])
            self._effect_type = int(received_msg['effect_type'])

            self._freq_windows[0] = int(received_msg['freq_window_1'])
            self._freq_windows[1] = int(received_msg['freq_window_2'])
            self._freq_windows[2] = int(received_msg['freq_window_3'])
            self._freq_windows[3] = int(received_msg['freq_window_4'])
            self._freq_windows[4] = int(received_msg['freq_window_5'])
            self._freq_windows[5] = int(received_msg['freq_window_6'])

        elif(message.topic == "lamp_network/mode_request"):

            print("Received a mode request message")
            self._new_msg_mode = True
            self._mode = int(received_msg['mode'])

    #Start the client
    def begin(self):

        print("Starting MQTT client")

        self._client.connect("192.168.2.118",1883)#TODO: add as configuration parameter
        self._client.loop_start()

        self._new_msg_mode = False
        self._new_msg_config = False

        #Subscribe to topics
        self._client.subscribe("lamp_network/initcommrx")
        self._client.subscribe("lamp_network/mode_request")
        self._client.subscribe("lamp_network_music/configuration")

        self._min_freq = 0
        self._max_freq = 0
        self._effect_delay = 0

    def stop(self):

        print("Stopping MQTT client")

        self._client.disconnect() #disconnect
        self._client.loop_stop() #stop loop

    def publish_alive_rx_status(self, status):

        print("Publishing Alive status of slaves (mask): ", status)

        self._client.publish("lamp_network_music/alive_rx_mask", str(status))

    def is_new_msg_mode(self):

        retVal = self._new_msg_mode
        self._new_msg_mode = False

        return retVal

    def is_new_msg_config(self):

        retVal = self._new_msg_config
        self._new_msg_config = False

        return retVal

    def get_msg_info(self):

        return {'mode': self._mode, 'min_freq': self._min_freq, 'max_freq': self._max_freq, 'effect_delay': self._effect_delay, 'effect_direction': self._effect_direction, 'num_lamps': self._num_lamps, 'num_freq_windows': self._num_freq_windows, 'r':self._base_color_r, 'g': self._base_color_g, 'b': self._base_color_b, 'color_increment': self._color_increment, 'effect_type': self._effect_type}

    def get_freq_windows(self):

        return self._freq_windows
