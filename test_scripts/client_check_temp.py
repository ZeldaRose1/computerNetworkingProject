#!/usr/bin/env python3

"""
Helper file to verify behavior of Connection class.
Sends data to the default port and current local
IP address
"""

from time import sleep
from utils.connection import Connection

con = Connection()
con.open_outbound_connection("192.168.0.53", 4144)

while True:
    in_str = input("Type string to send:\n")
    if in_str == "c":
        break
    else:
        con.send(in_str)

