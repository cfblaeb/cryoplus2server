freezer = 0
freezer_name = "CryoPlus2" if freezer == 0 else "CBS3000"
freezer_short_name = "cp2" if freezer == 0 else "cbs3000"

logfile = "log.log"
ser_port = '/dev/ttyUSB1'

# Define the MQTT settings
MQTT_BROKER = "192.38.14.162"
MQTT_PORT = 1883
MQTT_USERNAME = "mqttuser"
MQTT_PASSWORD = "mqttpass"
MQTT_DISCOVERY_TOPIC = f"homeassistant/sensor/{freezer_short_name}/config"
MQTT_STATE_TOPIC_TEMP = "home/R917/temperature"
MQTT_STATE_TOPIC_LL = "home/R917/distance"
MQTT_STATE_TOPIC_ALARM = "home/R917/enum"
#MQTT_STATE_TOPIC_LOG = "home/R917/..."  # could maybe be done with timestamp...

device_config = {
    "name": f"LN2 freezer {freezer_name}",
    "identifiers": [freezer_name],
    "manufacturer": "Thermo",
    "model": freezer_name,
    "sw_version": "1.0"
}

# sensor device class can be:
# distance: Generic distance in km, m, cm, mm, mi, yd, or in  ..will be used for liquid level
# duration: Duration in d, h, min, or s ...could e.g. be used for duration of door open
# enum: Has a limited set of (non-numeric) states ...maybe for alarm?
# temperature: Temperature in °C, °F or K ...obvious
# timestamp: Datetime object or timestamp string (ISO 8601)  # can be used to timestamp alarms maybe

sensor_configs = [
    {
        "name": f"{freezer_name} Temperature",
        "state_topic": MQTT_STATE_TOPIC_TEMP,
        "unit_of_measurement": "°C",
        "device_class": "temperature",
        "value_template": "{{ value }}",
        "unique_id": f"{freezer_short_name}_temperature_sensor_{freezer}",
        "device": device_config
    },
    {
        "name": f"{freezer_name} liquid level",
        "state_topic": MQTT_STATE_TOPIC_LL,
        "unit_of_measurement": "cm",
        "device_class": "distance",
        "value_template": "{{ value }}",
        "unique_id": f"{freezer_short_name}_liquid_sensor_{freezer}",
        "device": device_config
    },
    {
        "name": f"{freezer_name} alarm state",
        "state_topic": MQTT_STATE_TOPIC_ALARM,
        "device_class": "enum",
        "attributes": {
            "options": ["FILL_ERROR_ALARM", "HIGH_TEMP_ALARM", "NO_ALARM"]
        },
        "value_template": "{{ value }}",
        "unique_id": f"{freezer_short_name}_alarm_state_{freezer}",
        "device": device_config
    },
]
