# File: ham_nextion.py
"""
Based on the work of KM6LWY who wrote direwatch to work with the digipi project:
https://github.com/craigerl/direwatch

This version is Designed by KM6MZM as an extension to the direwatch intention, to work with a Nextion screen
Its also setup to display IP Address, GPS Data and a calculated Grid based on GPS.

The majority of the functions here are around the handling of button presses on the Nextion screen
and enebaling and disabling the services, as well as dispaying the status of the service, represented
by the color of the button on the screen. 


"""

import time
import socket
import io
import os
import datetime
import maidenhead
import gpsd
import serial.tools.list_ports
import logging
import asyncio
import subprocess
import aprslib
import re
from nextion import Nextion, EventType


# Define Global Variable Calls - for Recently Heard callsigns.
global calls
calls = []

# Define Systems, their name, command to check if its active, the status, Button Value and Button ID.
global systems
systems = [ {"name":"tnc", "command":"systemctl is-active tnc", "status":"", "button":"bt0.val", "button_id":14},
        {"name":"tnc300b", "command":"systemctl is-active tnc300b", "status":"", "button":"bt1.val", "button_id":15},
        {"name":"digipeater", "command":"systemctl is-active digipeater", "status":"", "button":"bt2.val", "button_id":16},
        {"name":"webchat", "command":"systemctl is-active webchat", "status":"", "button":"bt3.val", "button_id":17},
        {"name":"node", "command":"systemctl is-active node", "node":"", "button":"bt4.val", "button_id":18},
        {"name":"winlinkrms", "command":"systemctl is-active winlinkrms", "status":"", "button":"bt5.val", "button_id":19},
        {"name":"pat", "command":"systemctl is-active pat", "status":"", "button":"bt6.val", "button_id":20},
        {"name":"ardop", "command":"systemctl is-active ardop", "status":"", "button":"bt7.val", "button_id":21},
        {"name":"rigctld", "command":"systemctl is-active rigctld", "status":"", "button":"bt8.val", "button_id":22},
        {"name":"wsjtx", "command":"systemctl is-active wsjtx", "status":"", "button":"bt9.val", "button_id":23},
        {"name":"sstv", "command":"systemctl is-active sstv", "status":"", "button":"bt10.val", "button_id":24},                                
        {"name":"fldigi", "command":"systemctl is-active fldigi", "status":"", "button":"bt11.val", "button_id":25},
        {"name":"js8call", "command":"systemctl is-active js8call", "status":"", "button":"bt12.val", "button_id":26}
        ]


# Check if the GPS is connected & Active
def check_gps():
    try: 
        gpsd.connect()
        current = gpsd.get_current()
        return 1
    except Warning:
        print("no GPS")
        return 0

#return Longtitude from gpsd
def get_long():
    try: 
        gpsd.connect()
        current = gpsd.get_current()
        gps_lon = current.lon
        return float(gps_lon)
    except Warning:
        return 0

#return Latitude from gpsd
def get_lat():
    try: 
        gpsd.connect()
        current = gpsd.get_current()
        gps_lat = current.lat
        return float(gps_lat)
    except Warning:
        return 0

#return altitude from gpsd
def get_alt():
    try: 
        gpsd.connect()
        current = gpsd.get_current()
        gps_alt = current.alt
        return str(gps_alt)
    except Warning:
        return 0

# take the current GPS coordinates and calculate the maidenhead grid reference
def get_grid():
    current_gps_lat = get_lat()
    current_gps_lon = get_long()
    if current_gps_lat != 0 and current_gps_lon != 0:
        current_grid = maidenhead.to_maiden(current_gps_lat, current_gps_lon)
    else:
        current_grid = "No GPS"
    return current_grid

def get_drift():
    drift_cmd = "chronyc sources | grep NMEA"
    drift_result = str(subprocess.check_output(drift_cmd, shell=True))
    drift = drift_result.split(" ")[0].replace("b'", "")
    return drift
    
#return the current CPU operating temp
def get_cpu_temperature():
    try:
        tFile = open("/sys/class/thermal/thermal_zone0/temp", "r")
        temp = tFile.readline()
        tempC = int(temp)/1000
        return tempC
    except Exception:
        print("failed")

#try to connect to a random IP address in order to determine the working IP 
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# Date and Time functions
def get_current_date():
    now = datetime.datetime.now()
    return (now.strftime("%Y-%m-%d"))

def get_current_time():
    now = datetime.datetime.now()
    return (now.strftime("%H:%M"))

# Functions to manage the system status and start/stop them
def checkStatus():
    for system in systems:
        ret = subprocess.run(system["command"], capture_output=True, shell=True)
        results = ret.stdout.decode().replace('\n', '').replace('\r', '') #.split("\n")
        #print(results)
        system["status"] = results
    return systems

def startStop(checkSystem, systems):
    for system in systems:
        if system["status"] != "active" and system["name"] == checkSystem:
            subprocess.run('sudo systemctl start ' + system["name"], shell=True)
        else:
            subprocess.run('sudo systemctl stop '+ system["name"], shell=True)


# Event handler from Nextion library example - this will listen for touch events
def event_handler(type_, data):
    if type_ == EventType.STARTUP:
        print('We have booted up!')
        systems = checkStatus()
        for system in systems:
            print(system["name"] + " is " + system["status"])

    elif type_ == EventType.TOUCH:
        systems = checkStatus()
        print(data)
        for system in systems:
            if system["button_id"] == data.component_id:
                print(system["button_id"])
                startStop(system["name"], systems)
                break
            else:
                print("unknown button")

# Function to handle all things nextion.
async def run(f,calls, systems):
        # Define the serial paramaters for the Nextion Device
        client = Nextion('/dev/ttyS0', 9600, event_handler)
        await client.connect()
        client.write_command('rest')
        time.sleep(2)
        callStr = ""
        # Define the systems to be used

        while True: 
            # Infinte Loop for setting the display parameters.
            line = f.stdout.readline().decode("utf-8", errors="ignore")
            search = re.search("^\[\d\.*\d*\] (.*)", line)
            if search is not None:
                packetstring = search.group(1)
                packetstring = packetstring.replace('<0x0d>','\x0d').replace('<0x1c>','\x1c').replace('<0x1e>','\x1e').replace('<0x1f>','\0x1f').replace('<0x0a>','\0x0a')
                try:
                    # Grab the APRS stuff from the packet
                    packet = aprslib.parse(packetstring) 
                    call = packet['from']
                    if call not in calls:
                        calls.append(call)
                except:
                    # If parsing the packet failed just grab the callsign
                    search = re.search("^\[\d\.*\d*\] ([a-zA-Z0-9-]*)", line)
                    if search is not None:
                        call = search.group(1) 
                        if call not in calls:
                            calls.append(call)

            # Limit the Callsign Array to 15 entries.
            if len(calls) >= 10: 
                calls.pop()
          
            # if the GPS is connected and working then get the values
            if check_gps() == 1: 
                long_status = str(get_long())
                lat_status = str(get_lat())
                alt_status = str(get_alt())
            else:
                long_status =  "--"
                lat_status = "--"
                alt_status = "--"
            
            # Define the Blank String for calls and then populate the array from direwolf.log
            callStr = "" 
            for call in calls:
                    callStr = callStr + call + "\r\n" 
                    
            try:
                # Set the values for the Text Fields
                await client.set('t1.txt', "IP: " + get_ip())
                await client.set('t2.txt', "CPU Temp: " + str(get_cpu_temperature()))
                await client.set('t3.txt', "GMT: " + get_current_time())
                await client.set('t4.txt', get_current_date())

                # Polulate the Recently Heard List to the text field
                await client.set('t5.txt', callStr)
                
                # Populate the GPS Data and Maidenhead Grid
                await client.set('t6.txt', lat_status)
                await client.set('t7.txt', long_status)
                await client.set('t8.txt', alt_status)
                await client.set('t9.txt', get_grid())
                
                # Set the color of the buttons based on if the system is active. 
                systems = checkStatus()
                for system in systems:
                    if system["status"] == "active":
                        await client.set(system["button"],1)
                        break
                    else:
                        await client.set(system["button"],0)
                        break
            except:
                pass

if __name__ == "__main__":
    # Tail direwolf.log
    f = subprocess.Popen(['tail','-F','-n','20','direwolf.log'], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    # Define Loop
    loop = asyncio.get_event_loop()
    # Call Async IO function
    asyncio.ensure_future(run(f,calls, systems))
    #Run forever
    loop.run_forever()
