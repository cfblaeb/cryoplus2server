from sqlite3 import connect

con = connect("cp2s_data.sqlite")
cur = con.cursor()
cur.execute("create table data (date timestamp, data text)")
con.commit()
con.close()
