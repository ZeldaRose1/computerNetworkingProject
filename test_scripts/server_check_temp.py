#!/usr/bin/env python3

"""
This script is meant to help test the Connection class
with easier refreshing. Run in an outside terminal with
the virtual environment running.
"""

from utils.connection import Connection

con = Connection()

# Check for open ports
print("Calling listen the first time")
con.listen()

print("Calling listen the second time")
con.listen()

print("Calling listen the third time")
con.listen()
