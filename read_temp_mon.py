#!/usr/bin/python3
import time
import os
import sys
from subprocess import Popen, PIPE
from datetime import datetime
import psycopg2 as pg
import atexit
import serial

conn = pg.connect("host=10.10.10.120 dbname=power_supplies user=postgres password=starbucks")
cur = conn.cursor()

if len(sys.argv) < 2:
    print("must provide the serial port as the first argument")
    exit(1)

ser = serial.Serial(port=sys.argv[1], baudrate=19200)


def pg_disconnect():
    conn.commit()
    cur.close()
    conn.close()
    ser.close()


atexit.register(pg_disconnect)

def insert_db(tstamp, measurements):
    sql = "insert into thermal values (%s,%s,%s,%s,%s,%s,%s,%s,%s);"
    try:
        cur.execute(sql, (tstamp, *measurements))
    except (Exception, pg.DatabaseError) as error:
        print(error)
    conn.commit()

ctr = 0
while True:
    tstamp = datetime.utcnow().strftime('%F %T.%f')[:-3] + "+00"
    line = ser.readline().decode()

    if ctr == 10:
        parts = line.split()[1:]
        if len(parts) < 8:
            continue
        measurements = []
        for m in parts:
            measurements.append(m[:-1])
        insert_db(tstamp, measurements)
        ctr = 0

    ctr += 1
    print(line)
