from serial import Serial, STOPBITS_ONE, PARITY_NONE, EIGHTBITS
from requests import post, Timeout

webserver_url = "https://"
data_dump = "cp2s_data.txt"
with open(data_dump, 'at') as data_file:
    with Serial('/dev/ttyUSB0', 9600, stopbits=STOPBITS_ONE, parity=PARITY_NONE, bytesize=EIGHTBITS) as ser:
        while True:
            try:
                line = ser.readline()
                data_file.write(line.decode().strip() + "\n")
                post(webserver_url, json={'data': line.decode().strip()})
            except:  # I don't give a fuck thats its "too broad". Its meant to catch ALL exceptions!
                pass
