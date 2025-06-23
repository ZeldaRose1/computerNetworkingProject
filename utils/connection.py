#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 19 08:14:37 2025

@author: zelda
"""

from socket import socket
from socket import AF_INET
from socket import SOCK_STREAM


from utils.config import Config
from models.friend import Friend

conf = Config()


class Connection:
    """This class will house the connections and methods for connecting."""

    # def __init__(self):
    #     """Constructor for the connection manager"""
    #     self.con_in = socket(family=AF_INET, type=SOCK_STREAM)
    #     self.con_in.bind(("0.0.0.0", conf.default_port))

    def listen(self):
        """Listen for incoming connections"""
        self.listen_stop()
        self.con_in = socket(family=AF_INET, type=SOCK_STREAM)
        self.con_in.bind(("0.0.0.0", conf.default_port))
        self.con_in.listen()
        self.sender_ip, self.in_port = self.con_in.accept()

        # "while True" will keep the connection to stay open until
        # manually closed.
        while True:
            data = self.sender_ip.recv(1024)
            print(data.decode())
            self.sender_ip.sendall("Hello From the same Side!".encode())
            self.sender_ip.close()
            break
        self.con_in.close()

    def listen_stop(self):
        """Free inbound port and friend connection if it exists"""
        if "con_in" in dir(self):
            self.con_in.close()
            del self.con_in
        if "sender_ip" in dir(self):
            self.sender_ip.close()
            del self.sender_ip
            del self.in_port

    # Start functions.
    def send(self, ip: str, port: int) -> None:
        # TODO: recode this so it also includes a data object argument
        """Send connection request to address and socket from friend"""
        with socket(family=AF_INET, type=SOCK_STREAM) as s:
            s.connect((ip, port))
            s.send("Hello from the other side!".encode())
            data = s.recv(1024)

        if data:
            print(data.decode())

    def __del__(self):
        """Destructor; Close connections and clear ports"""
        if "con_in" in dir(self):
            self.con_in.close()
            del self.con_in

        if "con_out" in dir(self):
            self.con_out.close()
            del self.con_out

        if "sender_ip" in dir(self):
            self.sender_ip.close()
            del self.sender_ip

        if "in_port" in dir(self):
            del self.in_port




if __name__ == "__main__":
    pass
