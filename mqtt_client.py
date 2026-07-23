import paho.mqtt.client as mqtt
import json
import re
from serial import Serial, SerialException, STOPBITS_ONE, PARITY_NONE, EIGHTBITS
from datetime import datetime
from config import *


# Define the callback functions
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected successfully", flush=True)
        for config in sensor_configs:
            component = config.get("component", "sensor")
            payload = {k: v for k, v in config.items() if k != "component"}
            client.publish(f"homeassistant/{component}/{config['unique_id']}/config", json.dumps(payload), retain=True)
    else:
        print(f"Failed to connect, reason code: {reason_code}", flush=True)


def on_disconnect(client, userdata, flags, reason_code, properties):
    # paho's network loop reconnects on its own (see reconnect_delay_set below)
    print(f"Disconnected, reason code: {reason_code}", flush=True)


def on_message(client, userdata, msg):
    print(f"{msg.topic} {msg.payload}")


def make_client():
    client = mqtt.Client(protocol=mqtt.MQTTv5, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    # connect_async + loop_start keeps retrying (1s-2min backoff) if the broker is
    # unreachable, both at startup (e.g. network not up yet) and after a dropout.
    client.reconnect_delay_set(min_delay=1, max_delay=120)
    client.connect_async(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    return client


# --- CryoPlus 2 alarms ---
# Alarms are announced live as two consecutive lines, e.g.
#   "ERROR # (4) @ =00139. . . . . . . 01:13PM JUL 23, 2026"
#   "FILL ERROR - VALVE IS TURNED ON BUT LIQUID NOT RISING."
# There is no all-clear message, so we only track the latest alarm.
cp2_last_error_code = None

# --- CBS3000 alarms ---
# No live alarm messages. Besides hourly status lines ("TANK ID:") the unit
# sends a daily report ("TANK #:" header ... "REPORT DONE BY" footer) whose
# HISTORY section lists dated events, newest first, e.g.
#   "LOW ALARM 07 April 2026 05:31"
#   "LOW CORRECTION 07 April 2026 06:54"
# An alarm family (LOW, SOURCE, ...) is active if its newest ALARM has no
# newer CORRECTION.
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}
CBS_EVENT_RE = re.compile(r"^([A-Z][A-Z ]*?) (\d{1,2}) ([A-Z][a-z]+) (\d{4}) (\d{2}):(\d{2})$")
cbs_report = None  # dict while inside a report, else None


def handle_cbs_report_line(client, data):
    global cbs_report
    if "TANK #:" in data:  # report header (the hourly status uses "TANK ID:")
        cbs_report = {"alarms": {}, "corrections": {}}
        return
    if cbs_report is None:
        return
    if data.startswith("REPORT DONE BY"):
        finish_cbs_report(client)
        cbs_report = None
        return
    m = CBS_EVENT_RE.match(data)
    if not m or m.group(3) not in MONTHS:
        return
    event = m.group(1)
    when = datetime(int(m.group(4)), MONTHS[m.group(3)], int(m.group(2)), int(m.group(5)), int(m.group(6)))
    for suffix, bucket in ((" ALARM", cbs_report["alarms"]), (" CORRECTION", cbs_report["corrections"])):
        if event.endswith(suffix):
            family = event[:-len(suffix)]
            if family not in bucket or when > bucket[family]:
                bucket[family] = when


def finish_cbs_report(client):
    alarms, corrections = cbs_report["alarms"], cbs_report["corrections"]
    active = [fam for fam, when in alarms.items() if fam not in corrections or when > corrections[fam]]
    client.publish(MQTT_STATE_TOPIC_ALARM_ACTIVE, "ON" if active else "OFF", retain=True)
    if alarms:
        family = max(alarms, key=alarms.get)  # family with the newest alarm
        client.publish(MQTT_STATE_TOPIC_ALARM, f"{family} ALARM", retain=True)
        client.publish(MQTT_STATE_TOPIC_ALARM_TIME, alarms[family].astimezone().isoformat(), retain=True)


def handle_line(client, data, now=None):
    global cp2_last_error_code
    if now is None:
        now = datetime.now()

    if freezer == 0:  # cryoplus 2 handling:
        if data.startswith("CURRENT LEVEL"):  # normal data
            # "CURRENT LEVEL=003.00, TEMP=-00141., (1) @ =00141. . . .02:28PM JUL 23, 2026"
            data_split = data.split("=")
            try:
                liquid_level = float(data_split[1].split(",")[0])
                temperature = float(data_split[2].split(",")[0])
            except (ValueError, IndexError):
                return
            client.publish(MQTT_STATE_TOPIC_LL, liquid_level)
            client.publish(MQTT_STATE_TOPIC_TEMP, temperature)
        elif data.startswith("ERROR #"):
            # error code; the description follows on the next line
            m = re.search(r"\((\d+)\)", data)
            cp2_last_error_code = m.group(1) if m else None
        elif data.startswith("FILL ERROR"):
            alarm = f"{data} (#{cp2_last_error_code})" if cp2_last_error_code else data
            cp2_last_error_code = None
            client.publish(MQTT_STATE_TOPIC_ALARM, alarm, retain=True)
            client.publish(MQTT_STATE_TOPIC_ALARM_TIME, now.astimezone().isoformat(), retain=True)
        # other lines are status updates like "TANK LID WAS CLOSED" or
        # "A LIQUID FILL CYCLE WAS JUST AUTOMATICALLY INITIATED" - ignored

    elif freezer == 1:  # cbs3000 handling
        # hourly status:
        # "TEMP-A: -185 *C"
        # "Liquid Level: 46.4 CM"  (the daily report has a colon-less variant - skipped)
        if data.startswith("TEMP-A: "):
            try:
                client.publish(MQTT_STATE_TOPIC_TEMP, float(data.split(" ")[1]))
            except ValueError:
                pass
        elif data.startswith("Liquid Level: "):
            try:
                client.publish(MQTT_STATE_TOPIC_LL, float(data.split(" ")[2]))
            except ValueError:
                pass
        else:
            handle_cbs_report_line(client, data)


def main():
    client = make_client()
    with Serial(ser_port, 9600, stopbits=STOPBITS_ONE, parity=PARITY_NONE, bytesize=EIGHTBITS) as ser:
        while True:
            try:
                line = ser.readline()
                print(line, flush=True)
                data = line.decode().strip()
                handle_line(client, data)

                with open(logfile, 'at') as f:
                    f.write(f"{datetime.now()}\t{data}\n")

            except SerialException:
                raise  # dead serial port: exit and let systemd restart the service
            except Exception as e:
                print(e, flush=True)
                with open(logfile, 'at') as f:
                    f.write(f"{datetime.now()}\tERROR\t{e}\n")


if __name__ == "__main__":
    main()
