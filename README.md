This is the data collector for the LN2 freezers  
It reads data via a serial interface from a CryoPlus2 or a CBS3000  

It then parses that data and pushes it via mqtt to home assistant

## Setup

One instance (one clone + one systemd service) per freezer.

```
python -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env   # then edit: device type, serial port, mqtt broker/credentials
```

Install `cp2s.service` (adjust paths/names for your instance) into
`/etc/systemd/system/` and `systemctl enable --now` it. The service restarts
automatically on failure, and the client keeps retrying the MQTT connection
with backoff if the broker is unreachable, so it survives network dropouts
and boots where the network comes up late.
