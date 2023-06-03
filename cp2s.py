from serial import Serial, STOPBITS_ONE, PARITY_NONE, EIGHTBITS
from requests import post
from sqlite3 import connect
from datetime import datetime

webserver_url = "https://"
logfile = "log.log"

con = connect("cp2s_data.sqlite")
cur = con.cursor()

with Serial('/dev/ttyUSB0', 9600, stopbits=STOPBITS_ONE, parity=PARITY_NONE, bytesize=EIGHTBITS) as ser:
    while True:
        try:
            line = ser.readline()
            print(line)
            cur.execute("INSERT INTO data VALUES (?, ?)", (datetime.now(), line.decode().strip()))
            con.commit()
            res = post(webserver_url, json={'data': line.decode().strip()})
            with open(logfile, 'at') as f:
                f.write(f"{datetime.now()}\t{res.status_code}\t{res.reason}\t{res.text}\n")

        except Exception as e:
            print(e)
            with open(logfile, 'at') as f:
                f.write(f"{datetime.now()}\tERROR\t{e}\n")
