#!/usr/bin/python3
import time
import os
from subprocess import Popen, PIPE
from datetime import datetime
import psycopg2 as pg
import atexit
import curses

# IMPORTANT!!!! MODIFY THE FOLLOWING CONNECTION INFORMATION FOR THE SPECIFIC POSTGRES DATABASE
conn = pg.connect("host=localhost dbname=<postgres_database_goes_here> user=<postgres_user_goes_here> password=<posgres_password_goes_here>")
cur = conn.cursor()
screen = curses.initscr()
screen.nodelay(True)
curses.start_color()
screen.keypad(True)
curses.noecho()
curses.cbreak()
curses.curs_set(0)


def pg_disconnect():
    curses.nocbreak()
    screen.keypad(False)
    curses.echo()
    curses.endwin()
    conn.commit()
    cur.close()
    conn.close()


atexit.register(pg_disconnect)

# MODIFY AS NEEDED:
NUM_PS = 2
cur.execute("select * from ps_info")
ps_info = cur.fetchall()
ps_channels = []

key_pos = [0, 0]
toggle_power = False
screen_20 = ""


def map_ps(lines):
    ctr = 0
    for line in lines.split("\n")[:-1]:
        for ps in ps_info:
            if str(ps[0]) in line.split(',')[2]:
                ps_channels.append({"psid": ps[0], "dev": f"/dev/usbtmc{ctr}", "name": ps[1], "c1": {"name": ps[2]}, "c2": {"name": ps[3]}, "c3": {"name": ps[4]}})

        ctr += 1

    print(ps_channels)
    #if len(ps_channels) != NUM_PS:
    #    print("we have a problem")


def read_status():
    process = Popen(['./read_status.sh'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    lines = stdout.decode("utf-8")

    print(lines)
    lines = lines.split("\n")[:-1]
    for i in range(len(lines)):
        line = lines[i]
        # print(line)
        parts = line.split(',')
        # psid = (parts[2])[4:]
        channels = parts[4:-1]
        ps_channels[i]["c1"]["status"] = channels[0]
        ps_channels[i]["c2"]["status"] = channels[1]
        ps_channels[i]["c3"]["status"] = channels[2]


def read_power():
    # print(tstamp)
    process = Popen(['./read_power.sh'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    # print(stdout)

    lines = stdout.decode("utf-8")
    if len(ps_channels) != NUM_PS:
        map_ps(lines)

    lines = lines.split("\n")[:-1]
    for i in range(len(lines)):
        line = lines[i]
        # print(line)
        parts = line.split(',')
        # psid = (parts[2])[4:]
        channels = parts[4:-1]

        for j in range(1, 4):
            ps_channels[i][f"c{j}"]["v"] = float(channels[(j-1) * 3 + 0])
            ps_channels[i][f"c{j}"]["i"] = float(channels[(j-1) * 3 + 1])
            ps_channels[i][f"c{j}"]["w"] = float(channels[(j-1) * 3 + 2])


def insert_db():
    sql = "insert into measurements values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
    tstamp = datetime.utcnow().strftime('%F %T.%f')[:-3] + "+00"
    for ps in ps_channels:
        c1 = ps["c1"]
        c2 = ps["c2"]
        c3 = ps["c3"]
        if c1["status"] == "OFF" and c2["status"] == "OFF" and c3["status"] == "OFF":
            continue
        try:
            cur.execute(sql, (tstamp, ps["psid"],
                              c1["v"], c1["i"], c1["w"],
                              c2["v"], c2["i"], c2["w"],
                              c3["v"], c3["i"], c3["w"],
                              ))
        except (Exception, pg.DatabaseError) as error:
            print(error)

    conn.commit()


col_on = curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_GREEN)
col_off = curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)


def display_values():
    def print_channel(row, i):
        ps = ps_channels[i]
        c1 = ps["c1"]
        c2 = ps["c2"]
        c3 = ps["c3"]
        screen.addstr(row, 3,      f"{c1['name']:>20.20s}", curses.A_BOLD | curses.color_pair([1, 2][c1['status'] == 'ON']) | [0, curses.A_STANDOUT][key_pos == [i, 0]])
        screen.addstr(row, 3 + 21, f"{c2['name']:>20.20s}", curses.A_BOLD | curses.color_pair([1, 2][c2['status'] == 'ON']) | [0, curses.A_STANDOUT][key_pos == [i, 1]])
        screen.addstr(row, 3 + 42, f"{c3['name']:>20.20s}", curses.A_BOLD | curses.color_pair([1, 2][c3['status'] == 'ON']) | [0, curses.A_STANDOUT][key_pos == [i, 2]])
        screen.addstr(row + 1, 0, f"V: {c1['v']:20.2f}|{c2['v']:20.2f}|{c3['v']:20.2f}")
        screen.addstr(row + 2, 0, f"I: {c1['i']:20.2f}|{c2['i']:20.2f}|{c3['i']:20.2f}")
        screen.addstr(row + 3, 0, f"W: {c1['w']:20.2f}|{c2['w']:20.2f}|{c3['w']:20.2f}")
        return row + 4

    row = 0
    for i in range(len(ps_channels)):
        ps = ps_channels[i]
        screen.addstr(row, 0, ps["name"])
        row = print_channel(row+1, i)


def read_keys():
    global toggle_power, screen_20
    c = screen.getch()
    if c == curses.KEY_RIGHT:
        key_pos[1] += 1
    elif c == curses.KEY_LEFT:
        key_pos[1] -= 1
    elif c == curses.KEY_UP:
        key_pos[0] -= 1
    elif c == curses.KEY_DOWN:
        key_pos[0] += 1
    elif c == curses.KEY_ENTER or c == 10 or c == 13 or c == ord('\n'):
        print("POWER TOGGLE")
        toggle_power = True
    elif c == ord('n'):
        toggle_power = False
        screen_20 = ""
    elif c == ord('y') and toggle_power is True:
        # TODO thing
        toggle_power = False
        status = ps_channels[key_pos[0]][f"c{key_pos[1]+1}"]["status"]
        out_dir = ["ON", "OFF"][status == "ON"]
        out_str = f":OUTP CH{key_pos[1]+1},{out_dir}"
        screen_20 = f"{ps_channels[key_pos[0]]['dev']} is {status} sending: {out_str}"

        process = Popen(['./set_status.sh', str(key_pos[0]), out_str], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()

    if key_pos[0] < 0:
        key_pos[0] = 0
    if key_pos[0] > 1:
        key_pos[0] = 1

    if key_pos[1] < 0:
        key_pos[1] = 0
    if key_pos[1] > 2:
        key_pos[1] = 2


ctr = 0
while True:
    if ctr % 100 == 0:
        read_power()
        read_status()
        insert_db()

    read_keys()

    if ctr % 10 == 0:
        screen.clear()
        display_values()
        screen.addstr(0, 40, f"{key_pos[0]}, {key_pos[1]} {toggle_power}")

        if toggle_power:
            ps_name = ps_channels[key_pos[0]]['name']
            c_name = ps_channels[key_pos[0]][f'c{key_pos[1] + 1}']['name']
            screen_20 = f"Toggle {ps_name}->{c_name} [y/n] ?"

        screen.addstr(5*NUM_PS + 1, 0, screen_20)
        screen.refresh()

    time.sleep(0.01)
    ctr += 1
