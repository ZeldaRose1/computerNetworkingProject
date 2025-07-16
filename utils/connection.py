#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 19 08:14:37 2025

@author: zelda
"""

import select
from socket import socket
from socket import AF_INET
from socket import SOCK_STREAM
from socket import SO_REUSEADDR
from socket import SOL_SOCKET


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

    # Start functions
    def open_outbound_connection(self, ip: str, port: int) -> None:
        """Open and retain a connection for outbound connections"""
        self.con_out = socket(family=AF_INET, type=SOCK_STREAM)
        self.con_out.connect((ip, port))
        print("Connection Opened")

    def send(self, dat_out: bytes) -> None:
        """Send connection request to address and socket from friend"""
        if not hasattr(self, "con_out"):
            print("Error: Must open connection before sending data.")
        else:
            self.con_out.send(dat_out.encode())
            dat_in = self.con_out.recv(1024)

        if dat_in:
            print(dat_in.decode())

    def _attempt_connect(
            self,
            dstip: str,
            dstpt: int,
            srcpt: int = conf.default_port
    ) -> bool:
        """
            Helper function of initiate_hole_punch. Attempt connection to
            outbound port and ip.

            Note, self.con_in is set to listen so we can't use it
            for the connect function. We need to create a new
            socket for the outbound connection.

            Params:
                dstip: IP address to initiate connection with
                dstpt: Port to send data to
                srcpt: Port to send data from

            Returns:
                True if connection was successful, else False
        """
        # Create outbound socket
        self.sock_out = socket(AF_INET, SOCK_STREAM)
        self.sock_out.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # TODO: revert this back to 0.0.0.0 after testing
        self.sock_out.bind(("0.0.0.0", srcpt + 1000))
        # self.sock_out.bind(("127.0.0.2", srcpt + 1000))
        self.sock_out.setblocking(False)

        # Start outbound connection
        try:
            print("Attempting outbound connection to port:\t", dstpt)
            self.sock_out.connect((dstip, dstpt))
            print("sock_out connected!!")
            return True
        except BlockingIOError:
            # We expected to see an error here so no troubles
            return False
        except Exception as e:
            print(f"Outbound connection failed:\t{e}")
            self.sock_out.close()
            del self.sock_out
            return False

    def _handle_connection(self, conn_socket):
        """ Exchange messages over established connection. """
        conn_socket.setblocking(True)
        conn_socket.sendall(b"Hello peer, TCP hole punching worked!\n")
        self.active_socket = conn_socket

        while True:
            data = self.active_socket.recv(1024)
            if not data:
                print("[Connection] Friend closed connection")
                break
            print("[Connection] Received:", data.decode().strip())

            # For demonstration, echo back
            self.active_socket.sendall(b"Echo: " + data)

    def initiate_hole_punch(
            self,
            dstip: str,
            dstpt: int,
            srcpt: int = conf.default_port
    ) -> None:
        """
        Function to initiate TCP hole punching

        Params:
            dstip: IP address to initiate connection with
            dstpt: Port to send data to
            srcpt: Port to send data from

        Returns:
            None
        """
        # Start loop to try multiple times # TODO: increase attempt count
        for attempt in range(1):
            # Clean existing connections if they exist
            if hasattr(self, "con_in"):
                self.con_in.close()
                del self.con_in
            if hasattr(self, "con_out"):
                self.con_out.close()
                del self.con_out

            # Create socket
            self.con_in = socket(family=AF_INET, type=SOCK_STREAM)
            # Set socket to re-use connection to prevent in-use errors
            self.con_in.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            # Bind socket to address
            self.con_in.bind(("0.0.0.0", srcpt))
            print("Binding listening port to:\t", srcpt)
            # Set socket behavior to non-blocking for TCP hole punching
            # This will prevent our program from jamming
            self.con_in.setblocking(False)

            # Listen for incoming connections
            self.con_in.listen(1)  # Not sure why we let this fail after 1 try

            # Simultaneously send outbound request
            self._attempt_connect(dstip, dstpt, srcpt)

            while True:
                rlist, wlist, _ = select.select(
                    [self.con_in, self.sock_out], [self.sock_out], [], 10
                )

                if self.con_in in rlist:
                    # Incomming connections
                    conn, addr = self.con_in.accept()
                    print(f"Listener accepted, addr:\t{dstip}")
                    self._handle_connection(conn)
                    print("initiate_hole_punch finished")
                    return

                if self.sock_out in wlist:
                    # Outbound connect succeeded
                    print("Outbound connection established")
                    self._handle_connection(self.sock_out)
                    print("initiate_hole_punch finished")
                    return

                # print("Still waiting...")

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
