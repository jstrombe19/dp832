import time
import os
from subprocess import Popen, PIPE
from datetime import datetime
import psycopg2 as pg
import atexit


conn = pg.connect("host=192.168.1.2 dbname=power_supplies user=postgres password=postgres")
cur = conn.cursor()

def pg_disconnect():
    conn.commit()
    cur.close()
    conn.close()

atexit.register(pg_disconnect)

sql = "insert into measurements values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
def insert():
    tstamp = datetime.utcnow().strftime('%F %T.%f')[:-3] + "+00"
    print(tstamp)
    process = Popen(['./read_power_supplies.sh'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    #print(stdout)

    lines=stdout.decode("utf-8")

    for line in lines.split("\n")[:-1]:
        print(line)
        parts=line.split(',')
        psid = (parts[2])[4:]
        channels=parts[4:-1]
        try:
            cur.execute(sql, (tstamp, psid, *channels))
        except (Exception, pg.DatabaseError) as error:
            print(error)

    conn.commit() 


while True:
    insert()
    time.sleep(1)
