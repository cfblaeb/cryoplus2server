import os
from dotenv import load_dotenv

load_dotenv()  # local settings and secrets live in .env (see .env.example)

freezer = int(os.environ["FREEZER"])  # 0 = CryoPlus 2, 1 = CBS3000
freezer_name = "CryoPlus2" if freezer == 0 else "CBS3000"
freezer_short_name = "cp2" if freezer == 0 else "cbs3000"

logfile = os.environ.get("LOGFILE", "log.log")
ser_port = os.environ.get("SERIAL_PORT", "/dev/ttyUSB0")

# Define the MQTT settings
MQTT_BROKER = os.environ["MQTT_BROKER"]
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USERNAME = os.environ["MQTT_USERNAME"]
MQTT_PASSWORD = os.environ["MQTT_PASSWORD"]
MQTT_STATE_TOPIC_TEMP = f"home/{freezer_short_name}/temperature"
MQTT_STATE_TOPIC_LL = f"home/{freezer_short_name}/distance"
MQTT_STATE_TOPIC_ALARM = f"home/{freezer_short_name}/last_alarm"
MQTT_STATE_TOPIC_ALARM_TIME = f"home/{freezer_short_name}/last_alarm_time"
MQTT_STATE_TOPIC_ALARM_ACTIVE = f"home/{freezer_short_name}/alarm_active"

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
        "state_class": "measurement",
        "value_template": "{{ value }}",
        "unique_id": f"{freezer_short_name}_temperature_sensor_{freezer}",
        "device": device_config
    },
    {
        "name": f"{freezer_name} liquid level",
        "state_topic": MQTT_STATE_TOPIC_LL,
        "unit_of_measurement": "cm",
        "device_class": "distance",
        "state_class": "measurement",
        "value_template": "{{ value }}",
        "unique_id": f"{freezer_short_name}_liquid_sensor_{freezer}",
        "device": device_config
    },
    {
        # latest alarm announced by the freezer, as free text
        # (CryoPlus2: live "FILL ERROR - ..." lines; CBS3000: newest ALARM
        # event from the daily report)
        "name": f"{freezer_name} last alarm",
        "state_topic": MQTT_STATE_TOPIC_ALARM,
        "icon": "mdi:alert-circle-outline",
        "value_template": "{{ value }}",
        "unique_id": f"{freezer_short_name}_last_alarm_{freezer}",
        "device": device_config
    },
    {
        "name": f"{freezer_name} last alarm time",
        "state_topic": MQTT_STATE_TOPIC_ALARM_TIME,
        "device_class": "timestamp",
        "value_template": "{{ value }}",
        "unique_id": f"{freezer_short_name}_last_alarm_time_{freezer}",
        "device": device_config
    },
]

if freezer == 1:
    # only the CBS3000 reports alarm corrections, so only there can we tell
    # whether an alarm is still active (recomputed from each daily report)
    sensor_configs.append({
        "component": "binary_sensor",
        "name": f"{freezer_name} alarm active",
        "state_topic": MQTT_STATE_TOPIC_ALARM_ACTIVE,
        "device_class": "problem",
        "unique_id": f"{freezer_short_name}_alarm_active_{freezer}",
        "device": device_config
    })
