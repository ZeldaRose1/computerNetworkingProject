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
from socket import SO_REUSEPORT
from socket import SOL_SOCKET
from socket import SO_ERROR  # This is meant to verify outbound connection
import threading
import time

# from models.friend import Friend
from utils.config import Config
from utils.menu import PeerMenu


conf = Config()

class Connection:
    """
    Abstract class for both server and client connections.
    """
    def __init__(self):
        """Constructor for the connection manager"""
        self.friends = {}  # Dictionary to store peer connections

    def _send_with_ack(self, con, data: bytes|str, retries:int=10, delay:int=1) -> bool:
        """Attempt to send a message and wait for ack, retrying if necessary."""
        pip, ppt = con.getpeername()
        con.settimeout(3)  # Optional: avoid hanging indefinitely
        
        # Convert payload to bytes if it is a string
        if isinstance(data, str):
            data = data.encode()
        
        # Loop for retries
        for attempt in range(retries):
            try:
                print(f"[SENDER] Attempt {attempt + 1} to send to {pip}:{ppt}")
                con.sendall(data)

                # Receive ACK
                ack = con.recv(1024).decode()

                if ack == "ACK":
                    print("[SENDER] Received ACK. Done.")
                    return True
                else:
                    print(f"[SENDER] Unexpected response: {ack}")

            except Exception as e:
                print(f"[SENDER] Error: {e}")
            
            time.sleep(delay)

        # Retries exhausted, return False
        print("[SENDER] Failed to receive ACK after all attempts.")
        return False
    
    def _listen_with_ack(self, con, retries:int=10, delay:int=1) -> bytes:
        """Accepts a single incoming message and responds with ACK."""
        # pip, ppt = con.getpeername()
        con.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # con.listen()

        data = con.recv(1024)
        print(f"[RECEIVER] Received: {data.decode()}")
        
        con.sendall("ACK".encode())
        print("[RECEIVER] Sent ACK.")
        return data


class Peer(Connection):
    """This class will house the connections and methods for connecting."""

    # def __init__(self):
        # """Constructor for the connection manager"""
        # self.bind_port = conf.personal["p"]["DEFAULT_PORT"]

    def listen(self) -> None:
        """Listen for incoming connections"""

        # Build initial socket connection for TCP communication
        self.con_in = socket(family=AF_INET, type=SOCK_STREAM)
        # Enable a safe way to reuse sockets in case they still have latent
        # traffic
        self.con_in.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.con_in.bind(("0.0.0.0", conf.default_port))
        self.con_in.listen()

        # "while True" will keep the connection to stay open until
        # manually closed.
        while True:
            self.sender_ip, self.in_port = self.con_in.accept()
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
    def send(self, con, dat_out: bytes) -> None:
        """Send connection request to address and socket from friend"""
        con.send(dat_out.encode())
        con.settimeout(5)
        try:
            dat_in = con.recv(1024)
            if dat_in:
                print(dat_in.decode())
        except TimeoutError:
            pass  # Response optional
        con.settimeout(None)
        
        

    def connect_to_server(self, dst_ip: str, dst_port: int) -> None:
        """Attempt outbound connection to given IP and port"""
        if not hasattr(self, "name"):
            self.name = input("Please input name you wish to be known by:")
        
        if not hasattr(self, "bind_port"):
            self.bind_port = int(conf.personal["p"]["DEFAULT_PORT"])

        # Create Socket
        self.con_out = socket(AF_INET, SOCK_STREAM)
        self.con_out.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.con_out.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        # self.con_out.bind(("", self.bind_port))
        # Change socket to non-blocking
        # self.con_out.setblocking(False)

        print("Attempting connection:")
        try:
            self.con_out.connect((dst_ip, dst_port))
            print(f"[INFO] Connected to rendezvous server at {dst_ip}:{dst_port}")
        except BlockingIOError:
            # Failure expected because of how blocking ports work
            pass

        # Send name
        time.sleep(2)
        self._send_with_ack(self.con_out, self.name)

        # Start background thread to listen to messages from server
        threading.Thread(target=self._listen_to_server, daemon=True).start()

        # Loop to collect peer list
        self.refresh_peer_list()
        return
    
    def _listen_to_server(self):
        """Constantly listen for incoming messages from the server."""
        while True:
            try:
                data = self.con_out.recv(4096)
                if not data:
                    print("[INFO] Server closed connection")
                    break
                message = data.decode('utf-8', errors='ignore').strip()
                print(f"[SERVER] {message}")
                # Optionally parse and handle message here
            except ConnectionResetError:
                print("[ERROR] Connection reset by server")
                break
            except Exception as e:
                print(f"[ERROR] Listening thread exception: {e}")
                break

    def request_peer_connection(self, peer_name: str):
        """
            Request the server connect to a specific peer.

            Params:
                peer_name: Name of the peer to connect to

            Returns:
                None
        """
        if not hasattr(self, "con_out"):
            print("[ERROR] No outbound connection established. Please connect to server first.")
            return
        
        print(f"[INFO] Requesting connection to {peer_name}")
        self._send_with_ack(self.con_out, f"REQ_PEER:{peer_name}")

        # Get server response
        response = self._listen_with_ack(self.con_out).decode()
        if response.startswith("PEER_INFO:"):
            _, name, ip, port = response.replace("PEER_INFO:", "").split(",")
            print(f"[INFO] Got peer info: {name} @ {ip}:{port}")
            return name, ip, int(port)
        else:
            print(f"[ERROR] Failed to get peer info: {response}")
            return None

    def _attempt_connect(
            self,
            dstip: str,
            dstpt: int,
            srcpt: int = conf.personal["p"]["DEFAULT_PORT"]
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

    def print_peers(self):
        """Prints the list of available peers."""
        if not self.friends or len(self.friends) == 0:
                    print("[INFO] No peers available.")
        else:
            print("[INFO] Available peers:")
            for name, (ip, port) in self.friends.items():
                print(f" - {name} @ {ip}:{port}")
    
    def refresh_peer_list(self):
        """Refresh the peer list from the server."""
        print("[INFO] Refreshing peer list...")
        self.friends.clear()
        self.send(self.con_out, "REFRESH")
        # Loop to collect updated peer list
        while True:
            data = self._listen_with_ack(self.con_out).decode()
            if not data or data.startswith("[FIN]"):
                break
            fn, fip, fpt = data.strip().split(",")
            fpt = int(fpt)
            self.friends[fn] = (fip, fpt)
        print("[INFO] Peer list updated.")

    def disconnect_from_server(self):
        """Disconnect from the server."""
        print("[INFO] Disconnecting from server...")
        try:
            self.send(self.con_out, "DISCONNECT")
            self.con_out.close()
            print("[INFO] Disconnected.")
        except Exception as e:
            print(f"[ERROR] Error while disconnecting: {e}")

    def connect_to_peer(self, peer_name: str):
        """Coordinate with the server and attempt a TCP hole punch."""
        print(f"[INFO] Requesting connection to {peer_name}")
        self.send(self.con_out, f"REQ_PEER:{peer_name}")
        data = self._listen_with_ack(self.con_out).decode()

        if data.startswith("PEER_NOT_FOUND"):
            print("[ERROR] Peer not found.")
            return

        if data.startswith("PEER_INFO:"):
            _, ip, port = data.strip().split(":")[1].split(",")
            port = int(port)
            print(f"[INFO] Got peer info: {ip}:{port}")
            return

            # Start hole punching attempt
            # TODO: fix this function
            # threading.Thread(target=self._p2p_connection, args=(ip, port), daemon=True).start()
    
    def tcp_hole_punch(self, ip, port):
        """Attempt a TCP simultaneous open with the peer."""
        print(f"[INFO] Starting TCP hole punch to {ip}:{port}")
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        # Optional: bind to the same local port used for server connection if needed
        try:
            sock.bind(('', self.local_peer_port))  # Must be set when client is created
        except Exception as e:
            print(f"[WARNING] Could not bind to port {self.local_peer_port}: {e}")

        # Simultaneously try to connect
        try:
            sock.settimeout(5)
            sock.connect((ip, port))
            print(f"[SUCCESS] Connected to peer at {ip}:{port}")
            self.handle_peer_connection(sock)
        except Exception as e:
            print(f"[ERROR] TCP hole punching failed: {e}")
            sock.close()

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


class RendezvousHandler:
    def __init__(self, server, conn, addr):
        self.server = server  # Reference to Rendezvous (holds client list and send/recv methods)
        self.conn = conn
        self.addr = addr
        self.client_name = None

    def handle(self):
        """Main handler entry point"""
        print(f"[INFO] New client from {self.addr}")

        if not self._register_client():
            return

        self._send_peer_list()

        while True:
            self.conn.settimeout(None)
            try:
                data = self.conn.recv(1024).decode()
                if not data:
                    self._handle_disconnect()
                    break
                self._dispatch_command(data.strip())
            except Exception as e:
                print(f"[ERROR] Error during communication: {e}")
                break

    def _register_client(self) -> bool:
        """Handle initial registration from the client"""
        try:
            self.client_name = self.server._listen_with_ack(self.conn).decode().strip()
            print(f"[INFO] Client registered as: {self.client_name}")

            if self.client_name in self.server.client_list:
                print("[WARNING] Duplicate name. Rejecting.")
                self.server._send_with_ack(self.conn, "duplicate_name,rejecting,client,0".encode())
                self.conn.close()
                return False
            else:
                with self.server.lock:
                    self.server.client_list[self.client_name] = (self.conn, self.addr)
                return True
        except Exception as e:
            print(f"[ERROR] Registration failed: {e}")
            return False

    def _send_peer_list(self):
        """Send known peer info to the new client"""
        names = [name for name in self.server.client_list if name != self.client_name]  # list(self.server.client_list.keys())
        peer_count = len(names)

        if peer_count <= 0:
            self.server._send_with_ack(self.conn, "[FIN]".encode())
            return

        for _, name in enumerate(names):
            ip, port = self.server.client_list[name][1]
            self.server._send_with_ack(
                self.conn, f"{name},{ip},{port}".encode()
            )
        
        # Send end of list marker
        self.server._send_with_ack(
            self.conn, "[FIN]".encode()
        )

    def _dispatch_command(self, data: str):
        """Route incoming client requests"""
        print(f"[INFO] Received from {self.client_name}: {data}")
        if data.startswith("REQ_PEER:"):
            self._handle_peer_request(data)
        elif data == "REFRESH":
            self._handle_refresh()
        elif data == "DISCONNECT":
            self._handle_disconnect()
        else:
            print(f"[INFO] Unknown command from {self.client_name}: {data}")

    def _handle_peer_request(self, data: str):
        """Client requests connection to peer"""
        requested_name = data.split("REQ_PEER:")[1].strip()
        if requested_name in self.server.client_list:
            ip, port = self.server.client_list[requested_name][1]
            self.server._send_with_ack(
                self.conn, f"PEER_INFO:{requested_name},{ip},{port}".encode()
            )
            self.server.send_to_connection(
                requested_name,
                f"{self.client_name} wants to connect. Y/N?"
            )
        else:
            self.server._send_with_ack(self.conn, "PEER_NOT_FOUND:".encode())

    def _handle_refresh(self):
        """Client wants the current list of peers"""
        names = list(self.server.client_list.keys())
        # Iterate over all names in the client list
        for name in names:
            # Skip current client
            if name == self.client_name:
                continue

            # Send if there are any peers left
            ip, port = self.server.client_list[name][1]
            self.server._send_with_ack(
                self.conn,
                f"{name},{ip},{port}".encode()
            )
        # If no peers left, send no peers message
        self.server._send_with_ack(
            self.conn, "[FIN]".encode()
        )

    def _handle_disconnect(self):
        """Remove client from list and close socket"""
        print(f"[INFO] {self.client_name} disconnected.")
        with self.server.lock:
            # Remove the client from the server's client list
            self.server.client_list.pop(self.client_name, None)
        self.conn.close()


class Rendezvous(Connection):
    """
    This class will help facilitate communication between two peers
    by creating the connection, and sending back the IP and port number
    of the connected individual.
    """
    lock = threading.Lock()

    def listen(self, host_ip="0.0.0.0", host_port=0):
        self.con_in = socket(family=AF_INET, type=SOCK_STREAM)
        self.con_in.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.con_in.bind((host_ip, host_port))
        self.con_in.listen()
        print("[STARTED] Server listening:")
        print(self.con_in.getsockname())

        # Client list is in form of {name: (conn, addr)}
        self.client_list = {}

        while True:
            conn, addr = self.con_in.accept()
            handler = RendezvousHandler(self, conn, addr)
            threading.Thread(target=handler.handle, daemon=True).start()
    
    def send_to_connection(self, conn_name: str, data: bytes|str):
        """Send data to a specific connection."""
        if isinstance(data, str):
            data = data.encode()
        conn = self.client_list.get(conn_name)[0]
        try:
            self._send_with_ack(conn, data)
            print(f"[INFO] Sent data to {conn.getpeername()}")
        except Exception as e:
            print(f"[ERROR] Failed to send data: {e}")


if __name__ == "__main__":
    pass
