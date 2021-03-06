from serial import Serial, STOPBITS_ONE, PARITY_NONE, EIGHTBITS
from requests import post
from sqlite3 import connect
from datetime import datetime

webserver_url = "https://"

con = connect("cp2s_data.sqlite")
cur = con.cursor()

with Serial('/dev/ttyUSB0', 9600, stopbits=STOPBITS_ONE, parity=PARITY_NONE, bytesize=EIGHTBITS) as ser:
    while True:
        try:
            line = ser.readline()
            print(line)
            cur.execute("INSERT INTO data VALUES (?, ?)", (datetime.now(), line.decode().strip()))
            con.commit()
            post(webserver_url, json={'data': line.decode().strip()})
        except Exception as e:
            print(e)
