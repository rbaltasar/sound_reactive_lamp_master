from mqtt_controller import MQTTController
from udp_controller import udp_handler
from time import sleep
import visualization

mqtt_evaluation_ratio = 20
mqtt_evaluation_counter = 0

# Shared memory (dictionary)
system_status = {'mode': 0, 'min_freq': 0, 'max_freq': 0, 'effect_delay': 0, 'effect_direction': 0, 'num_lamps': 0, 'r': 0, 'g': 0, 'b': 0, 'color_increment': 1}

# Communication controllers
mqtt_controller = MQTTController()

def select_visualization_type(mode_req):

    if(mode_req == 100 or mode_req == 106):
        visualization.visualization_effect = visualization.visualize_scroll
        if(mode_req == 100):
            visualization.amplitude_type = 'BUBBLE'
            udp_handler.set_mode('BUBBLE')
        elif(mode_req == 106):
            visualization.amplitude_type = 'BARS'
            udp_handler.set_mode('BARS')

    elif(mode_req == 101 or mode_req == 102):
        visualization.visualization_effect = visualization.visualize_energy
        udp_handler.set_mode('BARS')
    elif(mode_req == 103 or mode_req == 104 or mode_req == 105):
        visualization.visualization_effect = visualization.visualize_spectrum
        udp_handler.set_mode('BARS')

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

    select_visualization_type(mode_req)


def update_configuration():

    #Send configuration parameters to the slaves
    udp_handler.send_configuration(system_status['effect_delay'], system_status['effect_direction'],system_status['r'],system_status['g'],system_status['b'], system_status['color_increment'])

    #Update the visualization algorithm

    #Update frequency (global)

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

            # Update minimum spectrum frequency
            if( system_status['min_freq'] is not mqtt_msg['min_freq'] ):

                # Increment change count
                changes_count += 1
                # Update local memory
                system_status['min_freq'] = mqtt_msg['min_freq']

            # Update maximum spectrum frequency
            if( system_status['max_freq'] is not mqtt_msg['max_freq'] ):

                # Increment change count
                changes_count += 1
                # Update local memory
                system_status['max_freq'] = mqtt_msg['max_freq']

            # Update the effect delay (in slaves)
            if( system_status['effect_delay'] is not mqtt_msg['effect_delay'] ):

                # Increment change count
                changes_count += 1
                # Update local memory
                system_status['effect_delay'] = mqtt_msg['effect_delay']

            # Update the effect direction (in slaves)
            if( system_status['effect_direction'] is not mqtt_msg['effect_direction'] ):

                # Increment change count
                changes_count += 1
                # Update local memory
                system_status['effect_direction'] = mqtt_msg['effect_direction']

            # Update the effect delay (in slaves)
            if( system_status['effect_delay'] is not mqtt_msg['effect_delay'] ):

                # Increment change count
                changes_count += 1
                # Update local memory
                system_status['effect_delay'] = mqtt_msg['effect_delay']

            # Update the base color
            if( system_status['r'] is not mqtt_msg['r'] ):

                # Increment change count
                changes_count += 1
                # Update local memory
                system_status['r'] = mqtt_msg['r']

            if( system_status['g'] is not mqtt_msg['g'] ):

                # Increment change count
                changes_count += 1
                # Update local memory
                system_status['g'] = mqtt_msg['g']

            if( system_status['b'] is not mqtt_msg['b'] ):

                # Increment change count
                changes_count += 1
                # Update local memory
                system_status['b'] = mqtt_msg['b']

            if( system_status['color_increment'] is not mqtt_msg['color_increment'] ):

                # Increment change count
                changes_count += 1
                # Update local memory
                system_status['color_increment'] = mqtt_msg['color_increment']

            if(changes_count > 0):

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
