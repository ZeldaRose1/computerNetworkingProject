#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 19 08:14:37 2025

@author: zelda
"""

from socket import socket
from socket import AF_INET
from socket import SOCK_STREAM
from socket import SOL_SOCKET
from socket import SO_REUSEADDR


from utils.config import Config
from models.friend import Friend

conf = Config()


class Connection:
    """This class will house the connections and methods for connecting."""

    # def __init__(self):
    #     """Constructor for the connection manager"""
    #     self.con_in = socket(family=AF_INET, type=SOCK_STREAM)
    #     self.con_in.bind(("0.0.0.0", conf.default_port))

    def listen(self) -> None:
        """Listen for incoming connections"""
        # Ensure ports are clear in case of multiple calls
        # self.listen_stop()
        # Build initial socket connection for TCP communication
        self.con_in = socket(family=AF_INET, type=SOCK_STREAM)
        # Enable a safe way to reuse sockets in case they still have latent
        # traffic
        self.con_in.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.con_in.bind(("0.0.0.0", conf.default_port))
        self.con_in.listen()
        self.sender_ip, self.in_port = self.con_in.accept()

        # "while True" will keep the connection to stay open until
        # manually closed.
        while True:
            data = self.sender_ip.recv(1024)
            if not data:
                print("[Server] Client closed conn. Ending server conn")
                self.con_in.close()
                break
            print(data.decode())
            self.sender_ip.sendall("Hello From the server Side!".encode())
        self.con_in.close()

    def listen_stop(self) -> None:
        """Free inbound port and friend connection if it exists"""
        if hasattr(self, "con_in"):
            self.con_in.close()
            del self.con_in
        if hasattr(self, "sender_ip"):
            self.sender_ip.close()
            del self.sender_ip
            del self.in_port

    # Start functions.
    def open_outbound_connection(self, ip: str, port: int) -> None:
        """Open and retain a connection for outbound connections"""
        self.con_out = socket(family=AF_INET, type=SOCK_STREAM)
        self.con_out.connect((ip, port))
        print("Connection Opened")

    def send(self, dat_out: bytes) -> None:
        # TODO: recode this so it also includes a data object argument
        """Send connection request to address and socket from friend"""
        if not hasattr(self, "con_out"):
            print("Error: Must open connection before sending data.")
        else:
            self.con_out.send(dat_out.encode())
            dat_in = self.con_out.recv(1024)

        if dat_in:
            print(dat_in.decode())

    def initiate_hole_punch(
            self,
            dstip: str,
            dstpt: int,
            srcpt: int = conf.default_port
    ) -> None:
        """
        Function to initiate hole punching

        Params:
            dstip: IP address to initiate connection with
            dstpt: Port to send data to
            srcpt: Port to send data from

        Returns:
            None
        """
        # Create socket
        self.con_in = socket(family=AF_INET, type=SOCK_STREAM)
        # Set socket to re-use connection to prevent in-use errors
        self.con_in.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.con_in.bind(("0.0.0.0", conf.default_port))
        self.con_in.setblocking(False)

        # Send initial packet to punch hole.
        try:
            self.con_in.send((dstip, dstpt))
        except Exception as e:
            print(str(e))
            pass  # Error thrown since connection necessarily fails.

        # Listen for a given time until connected or timeout
        while True:
            dat = self.con_in.recv(1024)


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
