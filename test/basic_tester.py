import paho.mqtt.client as mqtt #import the client1
import time
from threading import Thread
import subprocess

isRunning = True

def threaded_function(arg):
    while(isRunning):
        raw_input("Press Enter to start streaming...")
        if(isRunning == False):
            break
        print("Starting streaming!")
        client.publish("lamp_network/mode_request","{\"id_mask\":1,\"mode\":3}")
        time.sleep(4)   

def on_message(client, userdata, message):
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)


broker_address="192.168.0.41" 

client = mqtt.Client("TestScript_1") #create new instance   
client.on_message = on_message 

client.connect(broker_address) #connect to broker

client.loop_start() #start the loop

thread = Thread(target = threaded_function, args = (1, ))
thread.start()

try:
    while isRunning:
        client.publish("lamp_network/initcommrx","{\"mac_origin\":\"CC:50:E3:99:BA:40\",\"deviceID\":\"lamp\",\"OTA_URL\":\"lamp\",\"mode\":0}")
        time.sleep(4)
        client.publish("lamp_network/alive_rx","")
        time.sleep(4)
 
except KeyboardInterrupt:
    isRunning = False
    client.disconnect()
    client.loop_stop()

    print("done!")