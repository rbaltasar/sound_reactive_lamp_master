import socket
import config
import time
from threading import Thread
from datetime import datetime

#--------------------------------------------#
#Class to handle UDP communication between
#the master and the slavesself.
#Transmission is using a UDP multicast group
#Reception is on the same UDP socket (alive check)
#--------------------------------------------#
class UDPController:

    def __init__(self):

        #Initialize local variables
        self._last_r = 0
        self._last_g = 0
        self._last_b = 0
        self._last_ampl = 0
        self._mode = 100

        #Timestamps of last received alive checks. Maximum of 6 lamps supported
        self._last_timestamps = [0,0,0,0,0,0]
        self._get_last_tx_timestamp = 0

        #Mask for individual lamp addressing (spectrum mode)
        self._window_masks = []

    def __del__(self):

        #Stop communication
        self.stop()

    #Start the client. Todo: error handling
    def begin(self):

        print("Starting UDP payload socket")
        #Create a UDP socket for payload messages (muticast) - Tx only
        self._sock_payload = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #Create a UDP socket for Alive check - Rx only
        print("Starting UDP alive socket")
        self._sock_alive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._handle_alive = True
        server_address = ('192.168.2.123',7002) #Todo: get master IP
        self._sock_alive.bind(server_address)
        self._sock_alive.settimeout(1) #Allow safe exit of socket handle thread

        #Start alive check thread
        self._alive_thread = Thread(target = self.handle_alive_check)
        self._alive_thread.start()

    #Stop sockets and finish thread
    def stop(self):

        print("Stoping UDP payload socket")
        #Close payload socket
        self._sock_payload.close()
        print("Stoping UDP alive socket")
        #Stop alive thread
        self._handle_alive = False
        self._alive_thread.join()
        #Close alive socket
        self._sock_alive.close()

    #Handle alive check (Rx only).
    #Run on sepparate thread from main thread
    def handle_alive_check(self):

        print("Starting alive check thread")

        #Keep looping until finish signal
        while self._handle_alive is True:

          try:
            #Receive (with timeout) from the socket
            data, address = self._sock_alive.recvfrom(12) #Todo: max buffer size?

            #Get the node id of the received alive message
            data = bytearray(data)
            node_id = int(data[0]) #Todo: check this
            print('Received alive check from node {} with address {}'.format(node_id, address))
            #Get current time
            timestamp = time.time()
            #Update the timestamp for the received node. Todo: mutex?
            self._last_timestamps[node_id] = timestamp

          except socket.timeout:
            continue

        print("Exit alive check thread")

    def set_mode(self,mode):

        self._mode = mode

    def set_window_masks(self,masks):

        self._window_masks = masks

    def get_last_rx_timestamps(self):

        #Todo: mutex?
        return self._last_timestamps

    def get_last_tx_timestamp(self):

        return self._get_last_tx_timestamp

    #Check if requested color+amplitude is different than last one
    def compare_and_update(self, r,g,b,ampl):

        if( (self._last_r == r) and (self._last_g == g) and (self._last_b == b) and (self._last_ampl == ampl) ):

            return True

        else:
            self._last_r = r
            self._last_g = g
            self._last_b = b
            self._last_ampl = ampl

            return False

    #Send UDP multicast message
    def send_multicast(self, msg, repetitions, delay_rep, delay_end):

        for i in range(0,repetitions):

            self._sock_payload.sendto(msg, (config.UDP_IP, config.UDP_PORT))
            time.sleep(delay_rep)

        time.sleep(delay_end)

        self._get_last_tx_timestamp = time.time()

    #Send synchroniztion request
    def send_sync_req(self):

        print("Sending UDP sync request")

        msgId = 0x01 #Todo: define message IDs in a different file
        delay = 0x00 #Todo: remove, not used

        m = ''
        m += chr(msgId) + chr(delay)

        self.send_multicast(m, 3, 0, 0.5)

    #send mode change request
    def send_mode_request(self, mode_req):

        print("Sending UDP mode request")

        msgId = 0x00 #Todo: define message IDs in a different file
        mode = int(mode_req)
        mask = 0xFF #Address to all nodes

        m = ''
        m += chr(msgId) + chr(mode) + chr(mask)

        self.send_multicast(m, 8, 0.3, 0)

    #Send a single payload to all nodes
    def send_payload_single(self, r, g, b, ampl):

        if(not self.compare_and_update(r,g,b,ampl)):

            msgId = 0x04 #Todo: define message IDs in a different file
            mask = 0xFF #Address to all nodes

            m = ''
            m += chr(msgId) + chr(mask) + chr(int(r)) + chr(int(g)) + chr(int(b)) + chr(int(ampl))

            self.send_multicast(m, 4, 0.001, 0)

    #Send different payloads addressed to different nodes on the same UDP packet
    def send_payload_multiple(self, size, payload_list):

        msgId = 0x05 #Todo: define message IDs in a different file

        #Build message header (msg ID + msg size)
        m = ''
        m += chr(msgId) + chr(size)

        #Build message body (mask + payload)
        for i in range(0,size):
            #Add the mask
            m += chr(self._window_masks[i])
            #Add the payload
            m += chr(payload_list[i][0]) #red
            m += chr(payload_list[i][1]) #green
            m += chr(payload_list[i][2]) #blue
            m += chr(payload_list[i][3]) #amplitude

        self.send_multicast(m, 4, 0.001, 0)

    #Send configuration message
    def send_configuration(self, effect_delay, effect_direction, r, g, b, increment):

        msgId = 0x07

        m = ''
        m += chr(msgId) + chr(int(effect_delay)) + chr(int(effect_direction)) + chr(int(r)) + chr(int(g)) + chr(int(b)) + chr(int(increment))

        self.send_multicast(m, 8, 0.1, 0)

#Create the objet only once here to be directly accesible from visualization and super_lamp_network
udp_handler = UDPController()
