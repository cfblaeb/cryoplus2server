from serial import Serial, STOPBITS_ONE, PARITY_NONE, EIGHTBITS
from requests import post
from sqlite3 import connect
from datetime import datetime
from config import webserver_url, freezer, logfile, db_name, ser_port

con = connect(db_name)
cur = con.cursor()

with Serial(ser_port, 9600, stopbits=STOPBITS_ONE, parity=PARITY_NONE, bytesize=EIGHTBITS) as ser:
    while True:
        try:
            line = ser.readline()
            print(line, flush=True)
            cur.execute("INSERT INTO data VALUES (?, ?, ?)", (datetime.now(), line.decode().strip(), freezer))
            con.commit()
            res = post(webserver_url, json={'data': line.decode().strip(), 'freezer': freezer})
            with open(logfile, 'at') as f:
                f.write(f"{datetime.now()}\t{res.status_code}\t{res.reason}\t{res.text}\n")

        except Exception as e:
            print(e, flush=True)
            with open(logfile, 'at') as f:
                f.write(f"{datetime.now()}\tERROR\t{e}\n")
