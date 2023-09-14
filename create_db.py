from sqlite3 import connect
from config import db_name

con = connect(db_name)
cur = con.cursor()
cur.execute("create table data (date timestamp, data text, freezer integer)")
con.commit()
con.close()
