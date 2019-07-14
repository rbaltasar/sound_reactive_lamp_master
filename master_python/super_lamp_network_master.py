from mqtt_controller import MQTTController
from udp_controller import udp_handler
from time import sleep
import visualization

mqtt_evaluation_ratio = 20
mqtt_evaluation_counter = 0

# Shared memory (dictionary)
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

#Frequency window used for each lamp (only spectrum window effect)
frequency_windows_masks = []

# Communication controllers
mqtt_controller = MQTTController()

def select_visualization_type(effect_type):

    if(effect_type == 0):
        visualization.visualization_effect = visualization.visualize_scroll
    elif(effect_type == 1):
        visualization.visualization_effect = visualization.visualize_energy
    elif(effect_type == 2):
        visualization.visualization_effect = visualization.visualize_energy_spectrum
    elif(effect_type == 3):
        visualization.visualization_effect = visualization.visualize_spectrum

def evaluate_mode_req(mode_req):

    print("Received mode req: ", mode_req)

    # System requires switch from MQTT to UDP
    if( (system_status['mode'] < 100) and (mode_req >= 100 ) ):

        # Start UDP client
        udp_handler.begin()
        # Send mode change request to the slaves via UDP
        udp_handler.send_mode_request(mode_req)
        # Send UDP sync request
        udp_handler.send_sync_req()

        visualization.begin()
        # Update local memory
        system_status['mode'] = mode_req

    # System requires switch from UDP to MQTT
    elif( (system_status['mode'] >= 100) and (mode_req < 100 ) ):

        #Sleep a while to reduce network congestion to ensure that the mode request is received
        sleep(3)
        # Send mode change request to the slaves via UDP
        udp_handler.send_mode_request(mode_req)
        # Stop UDP client
        udp_handler.stop()
        # Stop audio analyzer
        visualization.stop()
        # Update local memory
        system_status['mode'] = mode_req

    # New mode request within music mode
    elif( (mode_req >= 100) and (system_status['mode'] is not mode_req) ):

        # Send mode change request to the slaves via UDP
        udp_handler.send_mode_request(mode_req)
        # Update local memory
        system_status['mode'] = mode_req

    # Either request to the same mode or a request between non-music modes. Do nothing
    else:

        pass

def update_frequency_windows(num_windows):

    print("Updating frequency windows")

    #Set number of windows in visualization algorithms
    visualization.num_spectrum_windows = num_windows

    #Delete old windows
    while len(frequency_windows_masks) > 0:
        frequency_windows_masks.pop(0)

    #Get new frequency windows
    freq_windows = mqtt_controller.get_freq_windows()

    print("Freq windows: ", freq_windows)

    #Compute masks out of frequency windows
    for i in range(0,num_windows):

        mask = 0

        for j in range(0,system_status['num_lamps']):

            if (freq_windows[j] - 1) == i:
                mask |= 1 << j

        frequency_windows_masks.append(mask)

    print("New computed masks: ", frequency_windows_masks)

    #Set the masks in the UDP controller
    udp_handler.set_window_masks(frequency_windows_masks)


def update_configuration():

    #Send configuration parameters to the slaves
    udp_handler.send_configuration(system_status['effect_delay'], system_status['effect_direction'],system_status['r'],system_status['g'],system_status['b'], system_status['color_increment'])

    #Update the visualization algorithm
    select_visualization_type(system_status['effect_type'])

    update_frequency_windows(system_status['num_windows'])


def mqtt_network_loop():

    global mqtt_evaluation_counter

    if(mqtt_evaluation_counter is mqtt_evaluation_ratio):

        mqtt_evaluation_counter = 0

        if(mqtt_controller.is_new_msg_mode()):

            mqtt_msg = mqtt_controller.get_msg_info()

            # Evaluate the mode request. Act accordingly
            evaluate_mode_req(mqtt_msg['mode'])

        elif(mqtt_controller.is_new_msg_config()):

            changes_count = 0

            mqtt_msg = mqtt_controller.get_msg_info()

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

            update_configuration()

    else:

        mqtt_evaluation_counter += 1


def iddle_loop():

    sleep(0.1)


def music_loop():

    visualization.feed()


if __name__== "__main__":


    mqtt_controller.begin()
    visualization.configure_gui()

    while True:

        # Check for new MQTT requests
        mqtt_network_loop()

        if(system_status['mode'] >= 100):

            music_loop()

        else:

            iddle_loop()
