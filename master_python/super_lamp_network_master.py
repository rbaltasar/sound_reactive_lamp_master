from mqtt_controller import MQTTController
from udp_controller import udp_handler
import time
import visualization
import config
from datetime import datetime

#  ------- Global variables -------- #
#Process MQTT messages at a lower rate than UDP
mqtt_evaluation_ratio = 10
mqtt_evaluation_counter = 0
#Bit mask containing slave connection status (0: offline / 1: online)
alive_rx_mask = 0
#Frequency window used for each lamp (only spectrum window effect)
frequency_windows_masks = []
# MQTT communication controller (only used here)
mqtt_controller = MQTTController()
#UDP communication handling object is declared in udp_controller.py to be used also from visualization.py

# Shared memory (dictionary). Todo: structure?
system_status = { \
    'mode': 0, \
    'effect_type': 0, \
    'min_freq': 0, \
    'max_freq': 0, \
    'effect_delay': 0, \
    'effect_direction': 0, \
    'num_windows': 0, \
    'num_lamps': 0, \
    'r': 0, \
    'g': 0, \
    'b': 0, \
    'color_increment': 1, \
    'num_windows': 1
    }

#Select a visualization effect based on the lamp mode requested
def select_visualization_type(effect_type):

    if(effect_type == 0):
        visualization.visualization_effect = visualization.visualize_scroll
    elif(effect_type == 1):
        visualization.visualization_effect = visualization.visualize_energy
    elif(effect_type == 2): #TODO: remove this effect
        visualization.visualization_effect = visualization.visualize_energy_spectrum
    elif(effect_type == 3):
        visualization.visualization_effect = visualization.visualize_spectrum

#Handle communication and visualization in base of the requested mode
def evaluate_mode_req(mode_req):

    print("Received mode req: ", mode_req)

    # System requires switch from MQTT to UDP
    if( (system_status['mode'] < 100) and (mode_req >= 100 ) ):

        # Start UDP handler
        udp_handler.begin()
        # Send mode change request to the slaves via UDP
        udp_handler.send_mode_request(mode_req)
        # Send UDP sync request
        udp_handler.send_sync_req()
        # Begin visualization and signal processing
        visualization.begin(mode_req)
        # Update local memory
        system_status['mode'] = mode_req

    # System requires switch from UDP to MQTT
    elif( (system_status['mode'] >= 100) and (mode_req < 100 ) ):

        #Sleep a while to reduce network congestion to ensure that the mode request is received
        time.sleep(3)
        # Send mode change request to the slaves via UDP
        udp_handler.send_mode_request(mode_req)
        # Stop UDP handler
        udp_handler.stop()
        # Stop visualization and signal processing
        visualization.stop()
        # Display al lamps as OFFLINE in the Dashboard
        global alive_rx_mask
        alive_rx_mask = 0
        mqtt_controller.publish_alive_rx_status(alive_rx_mask)
        # Update local memory
        system_status['mode'] = mode_req

    # New mode request within music mode
    elif( (mode_req >= 100) and (system_status['mode'] is not mode_req) ):

        # Send mode change request to the slaves via UDP
        udp_handler.send_mode_request(mode_req)
        # Update local memory
        system_status['mode'] = mode_req
        #Update lamp effect
        visualization.update_lamp_effect(mode_req)

#Update the frequency window associated to each slave (MQTT request)
def update_frequency_windows(num_windows):

    print("Updating frequency windows")

    #Set number of windows in visualization algorithms
    visualization.num_spectrum_windows = num_windows

    #Delete old windows
    while len(frequency_windows_masks) > 0:
        frequency_windows_masks.pop(0)

    #Get new frequency windows from MQTT request
    freq_windows = mqtt_controller.get_freq_windows()

    #Compute masks out of frequency windows
    for i in range(0,num_windows):

        mask = 0

        for j in range(0,system_status['num_lamps']):

            if (freq_windows[j] - 1) == i:
                mask |= 1 << j

        frequency_windows_masks.append(mask)

    #Set the masks in the UDP controller
    udp_handler.set_window_masks(frequency_windows_masks)

#Handle a configuration request
def update_configuration():

    #Send configuration parameters to the slaves
    udp_handler.send_configuration(system_status['effect_delay'], system_status['effect_direction'],system_status['r'],system_status['g'],system_status['b'], system_status['color_increment'])
    #Update the visualization algorithm and signal processing
    select_visualization_type(system_status['effect_type'])
    update_frequency_windows(system_status['num_windows'])
    #Generate new color for each frequency from a base color
    visualization.generate_frequency_colors(system_status['r'],system_status['g'],system_status['b'], system_status['color_increment'])

#Compute a bitwise mask to indicate what lamps have an alive UDP communication
def compute_alive_masks(current_time, alive_rx_timestamps):

    mask = 0
    mask_pos = 0

    #Iterate all received timestamps. Todo: check size for corner cases
    for rx_timestamp in alive_rx_timestamps:

        #Slave is not alive
        if( (current_time - rx_timestamp) > config.ALIVE_CHECK_RX*3 ):
            is_alive = 0
        else:
            is_alive = 1

        #Add to the mask
        mask |= is_alive << mask_pos
        mask_pos += 1

    return mask

#Handle UDP alive check communication
#Publish lamp connection status on-change
def handle_alive_check():

    global alive_rx_mask

    timestamp = time.time()

    #Handle Alive Check TX
    last_message_sent = udp_handler.get_last_tx_timestamp()
    if( (timestamp - last_message_sent) > config.ALIVE_CHECK_TX ):
        #A sync request suffices to resart the alive timer on the slaves
        udp_handler.send_sync_req()

    #Handle Alive Check RX
    #Get last received rx timestamps
    alive_rx_timestamps = udp_handler.get_last_rx_timestamps() #List of RX timestamps
    #Compute a mask with the alive slaves
    alive_rx_mask_local = compute_alive_masks(timestamp, alive_rx_timestamps) #Mask indicating the slaves with alive communication
    #Publish the mask on change
    if(alive_rx_mask_local != alive_rx_mask):
        mqtt_controller.publish_alive_rx_status(alive_rx_mask_local)
        alive_rx_mask = alive_rx_mask_local

#Handle MQTT communication
def mqtt_network_loop():

    global mqtt_evaluation_counter

    #Check for new MQTT updates only every 10 loop iterations
    if(mqtt_evaluation_counter is mqtt_evaluation_ratio):

        #Reset evaluation counter
        mqtt_evaluation_counter = 0

        #Check for mode request
        if(mqtt_controller.is_new_msg_mode()):

            #Get message
            mqtt_msg = mqtt_controller.get_msg_info()

            # Evaluate the mode request
            evaluate_mode_req(mqtt_msg['mode'])

        #Check for configuration messages
        elif(mqtt_controller.is_new_msg_config()):

            #Get message
            mqtt_msg = mqtt_controller.get_msg_info()

            #Update local memory. Todo: same data structure and one single copy
            system_status['min_freq'] = mqtt_msg['min_freq']
            system_status['num_windows'] = mqtt_msg['num_freq_windows']
            system_status['max_freq'] = mqtt_msg['max_freq']
            system_status['effect_delay'] = mqtt_msg['effect_delay']
            system_status['effect_direction'] = mqtt_msg['effect_direction']
            system_status['effect_delay'] = mqtt_msg['effect_delay']
            system_status['r'] = mqtt_msg['r']
            system_status['g'] = mqtt_msg['g']
            system_status['b'] = mqtt_msg['b']
            system_status['color_increment'] = mqtt_msg['color_increment']
            system_status['effect_type'] = mqtt_msg['effect_type']
            system_status['num_windows'] = mqtt_msg['num_freq_windows']
            system_status['num_lamps'] = mqtt_msg['num_lamps']

            #Update configuration
            update_configuration()

    else:

        mqtt_evaluation_counter += 1


def iddle_loop():
    time.sleep(0.5)

def music_loop():
    #Feed the signal processing algorithms
    visualization.feed()
    #Handle alive communication in UDP
    handle_alive_check()


if __name__== "__main__":

    #Start MQTT communication
    mqtt_controller.begin()

    if config.USE_GUI is True:
        visualization.configure_gui()

    #Endless loop
    do_loop = True
    while do_loop:

        try:

            # Check for new MQTT requests
            mqtt_network_loop()
            #Music mode is distinguished by mode ID >= 100
            if(system_status['mode'] >= 100):
                music_loop()
            else:
                iddle_loop()

        except KeyboardInterrupt:
                print "Ctrl-c received! Sending kill to threads..."
                # Display al lamps as OFFLINE in the Dashboard
                mqtt_controller.publish_alive_rx_status(0)
                #Stop MQTT controller
                mqtt_controller.stop()
                #Stop UDP controller
                udp_handler.stop()
                do_loop = False
