import paho.mqtt.client as mqtt
import json
from serial import Serial, STOPBITS_ONE, PARITY_NONE, EIGHTBITS
from datetime import datetime
from config import *


# Define the callback functions
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected successfully")
        for config in sensor_configs:
            client.publish(f"homeassistant/sensor/{config['unique_id']}/config", json.dumps(config), retain=True)
    else:
        print(f"Failed to connect, reason code: {reason_code}")


def on_message(client, userdata, msg):
    print(f"{msg.topic} {msg.payload}")


# Create an MQTT client instance with the specified callback API version
client = mqtt.Client(protocol=mqtt.MQTTv5, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()


with Serial(ser_port, 9600, stopbits=STOPBITS_ONE, parity=PARITY_NONE, bytesize=EIGHTBITS) as ser:
    while True:
        try:
            line = ser.readline()
            print(line, flush=True)
            data = line.decode().strip()

            # different route depending on freezer
            if freezer == 0:  # cryoplus 2 handling:
                if data.startswith("CURRENT LEVEL"):  # normal data
                    data_split = data.split("=")
                    liquid_level = data_split[1].split(",")[0]  # this is a string
                    temperature = data_split[2].split(",")[0]   # this is a string
                    client.publish(MQTT_STATE_TOPIC_LL, liquid_level)
                    client.publish(MQTT_STATE_TOPIC_TEMP, temperature)
                else:  # less normal data
                    # This can be status updates like
                    # door open/close
                    #  - "TANK LID WAS CLOSED"
                    #  - "COVER CLOSED, (9) @ =00417. . . . . . . . . . . . . . .09:15PM SEP 14, 2023"
                    # auto refill
                    #  - "A LIQUID FILL CYCLE WAS JUST AUTOMATICALLY INITIATED"
                    #  - "AUTO FILL, (0) @ =00421. . . . . . . . . . . . . . . . 01:48AM SEP 15, 2023"
                    # manual refull
                    #  - "FILL CYCLE WAS STARTED MANUALLY"
                    #  - "MANUAL FILL STARTED, (6) @ =00042. . . . . . . . . . . 04:04PM OCT 05, 2023"
                    # or errors
                    # fill error
                    #  - "FILL ERROR - LIQUID TEMPERATURE IS ABOVE SET LIMIT."
                    #  - "ERROR # (11) @ =00417. . . . . . . . . . . . . . . . . 09:19PM SEP 14, 2023"
                    if data.startswith("ERROR #"):
                        pass  # ignore these lines. There should be an error description in next line
                    elif data.startswith("FILL ERROR"):
                        client.publish(MQTT_STATE_TOPIC_ALARM, "FILL_ERROR")
            elif freezer == 1:  # cbs3000 handling
                # look for these lines:
                # "TEMP-A: -185 *C"
                # "Liquid Level: 46.4 CM"  (avoid this line "Liquid Level 46.1 CM"
                if data.startswith("TEMP-A: "):
                    client.publish(MQTT_STATE_TOPIC_TEMP, data.split(" ")[1])
                elif data.startswith("Liquid Level: "):
                    client.publish(MQTT_STATE_TOPIC_LL, data.split(" ")[2])
                else:  # theres a daily report that contains all status/errors. I guess I could publish the days errors...
                    pass
            else:  # really shouldn't be here
                pass

            with open(logfile, 'at') as f:
                f.write(f"{datetime.now()}\t{data}\n")

        except Exception as e:
            print(e, flush=True)
            with open(logfile, 'at') as f:
                f.write(f"{datetime.now()}\tERROR\t{e}\n")
