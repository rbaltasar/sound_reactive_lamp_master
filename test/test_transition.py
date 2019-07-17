import time
import paho.mqtt.client as paho


def transition_loop():

    print("publishing transition to OFF")
    client.publish("lamp_network/mode_request","{\"id_mask\":255,\"mode\":0}")#publish
    print("Sleeping 5 seconds")
    time.sleep(10)
    print("publishing transition to ON")
    client.publish("lamp_network/mode_request","{\"id_mask\":255,\"mode\":1}")#publish
    print("Sleeping 5 seconds")
    time.sleep(10)
    print("publishing transition to Music mode")
    client.publish("music_node/start","")#publish
    print("Sleeping 15 seconds")
    time.sleep(60)
    print("publishing transition to ON")
    client.publish("lamp_network/mode_request","{\"id_mask\":255,\"mode\":1}")#publish
    print("Sleeping 15 seconds")
    time.sleep(15)
    print("publishing color transition 1")
    client.publish("lamp_network/light_color","{\"id_mask\":255,\"R\":100,\"G\":1,\"B\":1}")#publish
    print("Sleeping 5 seconds")
    time.sleep(5)
    print("publishing color transition 2")
    client.publish("lamp_network/light_color","{\"id_mask\":255,\"R\":1,\"G\":100,\"B\":1}")#publish
    print("Sleeping 5 seconds")
    time.sleep(5)
    print("publishing color transition 3")
    client.publish("lamp_network/light_color","{\"id_mask\":255,\"R\":1,\"G\":1,\"B\":100}")#publish
    print("Sleeping 5 seconds")
    time.sleep(5)
    print("publishing color transition 4")
    client.publish("lamp_network/light_color","{\"id_mask\":255,\"R\":100,\"G\":100,\"B\":1}")#publish
    print("Sleeping 5 seconds")
    time.sleep(5)
    print("publishing color transition 5")
    client.publish("lamp_network/light_color","{\"id_mask\":255,\"R\":100,\"G\":1,\"B\":100}")#publish
    print("Sleeping 5 seconds")
    time.sleep(5)

#define callback
def on_message(client, userdata, message):
    time.sleep(1)
    print("received message =",str(message.payload.decode("utf-8")))

client= paho.Client("client-001")
client.on_message=on_message
print("connecting to broker ")
client.connect("192.168.2.118",1883)#connect
client.loop_start() #start loop to process received messages

while True:

    transition_loop()

client.disconnect() #disconnect
client.loop_stop() #stop loop
