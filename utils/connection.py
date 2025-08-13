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

    def __init__(self):
        """Constructor for the connection manager"""
        self.peer_connected = False
        self.server_connected = False

    # Start functions
    def send(self, con, dat_out: bytes) -> None:
        """Send connection request to address and socket from friend"""
        try:
            con.send(dat_out.encode())
        except BlockingIOError:
            print("[ERROR] Send would block, try again later.")
        con.settimeout(5)
        try:
            dat_in = con.recv(1024)
            if dat_in:
                print(dat_in.decode())
        except TimeoutError:
            pass  # Response optional
        except BlockingIOError:
            pass  # We expected this error
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
            self.server_connected = True
        except BlockingIOError:
            # Failure expected because of how blocking ports work
            pass

        # Send name
        time.sleep(2)
        self._send_with_ack(self.con_out, self.name)

        # Start background thread to listen to messages from server
        threading.Thread(target=self._listen_to_server, daemon=True).start()

        # self.refresh_peer_list()
        return
    
    def _listen_to_server(self):
        """Constantly listen for incoming messages from the server."""
        waiting_for_ack = False

        while True:
            self.con_out.settimeout(None)
            try:
                data = self.con_out.recv(4096)
                if not data:
                    print("[INFO] Server closed connection")
                    break
                message = data.decode('utf-8', errors='ignore').strip()
                print(f"[SERVER] {message}")

                if message.startswith("[PLU]:") or message.startswith("[FIN]"):
                    self.handle_peer_list_update(message)
  
                # Prepare for hole punch by creating listening socket
                elif message.startswith("PREPARE_HOLE_PUNCH:"):
                    # Extract peer info
                    local_ip, local_port = self.con_out.getsockname()
                    peer_info = message.split("PREPARE_HOLE_PUNCH:")[1].strip()
                    ip, port = peer_info.split(",")

                    # Notify the user or handle the hole punch logic
                    self.con_out.send("READY_HOLE_PUNCH".encode())
                    waiting_for_ack = True
                    print("Sent READY_HOLE_PUNCH to server")
                    print(f"listen_sock IP: {local_ip}\nlisten_sock Port: {local_port}")
                    
                elif message.startswith("ACK") and waiting_for_ack:
                    print("Received ACK for READY_HOLE_PUNCH")
                    waiting_for_ack = False

                elif message.startswith("START_HOLE_PUNCH:"):
                    # Pull information from commands
                    local_port += 20
                    peer_info = message.split("START_HOLE_PUNCH:")[1].strip()
                    ip, port = peer_info.split(",")

                    try:
                        self.peer_socket = self.hole_punch(local_ip, local_port, ip, int(port) + 20)
                        t = threading
                        return
                    except Exception as e:
                        print(f"[ERROR] Hole punch failed: {e}")

            except ConnectionResetError:
                print("[ERROR] Connection reset by server")
                break
            except Exception as e:
                print(f"[ERROR] Listening thread exception: {e}")
                break

        if hasattr(self, "peer_socket"):
            try:
                data = self.peer_socket.recv(4096)
                self.peer_socket.sendall(f"Hello from {self.name}!".encode())
                if not data:
                    print("[INFO] Peer closed connection")
                    self.peer_socket.close()
                    del self.peer_socket
                else:
                    print(f"[PEER] {data.decode(errors='ignore')}")
            except BlockingIOError:
                pass
            except Exception as e:
                print(f"[ERROR] Error receiving from peer: {e}")

    def hole_punch(self, local_ip, local_port, peer_ip, peer_port, timeout=120):
        """
        Initiate a hole punch connection to a peer.
        
        Params:
            local_ip: Local IP address to bind to
            local_port: Local port to bind to
            peer_ip: Peer IP address to connect to
            peer_port: Peer port to connect to
            timeout: Timeout for the hole punch attempt (default 120 seconds)
        """
        print(f"con_out IP: {local_ip}\ncon_out Port: {local_port}")

        print(f"[INFO] Preparing hole punch with peer: {peer_ip}:{peer_port}")
        listen_sock = socket(AF_INET, SOCK_STREAM)
        listen_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        listen_sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        listen_sock.bind((local_ip, local_port))
        listen_sock.listen(200)
        listen_sock.setblocking(False)
        # This will print the local IP
        print(f"[INFO] Listening for incoming connections on ({local_ip}, {local_port}")
        print(f"[INFO] Starting hole punch with peer: {peer_ip}:{peer_port}")

        # Save time for timeout
        start_time = time.time()

        # Loop for connect and accept
        while time.time() - start_time < timeout:
            # Setup outbound socket
            out_sock = socket(AF_INET, SOCK_STREAM)
            out_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            out_sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
            out_sock.setblocking(False)
            out_sock.bind((local_ip, local_port))
            out_sock.setblocking(False)
            try:
                out_sock.connect((peer_ip, peer_port))
            except BlockingIOError:
                pass

            readable, writable, _ = select.select(
                [listen_sock],
                [out_sock],
                [],
                2
            )
            
            if listen_sock in readable:
                conn, _ = listen_sock.accept()
                print(f"[INFO] Accepted incoming connection from {peer_ip}:{peer_port}")
                self.peer_connected = True
                return conn

            if out_sock in writable:
                err = out_sock.getsockopt(SOL_SOCKET, SO_ERROR)
                if err == 0:
                    print(f"[INFO] Outbound connection established to {peer_ip}:{peer_port}")
                    self.peer_connected = True
                    
                    return out_sock  # Store the peer socket for later use
                else:
                    print(f"[ERROR] Outbound connection failed with error: {err}")
                    out_sock.close()
                    del out_sock

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
        if not hasattr(self, "friends") or len(self.friends) == 0:
            print("[INFO] No peers available.")
        else:
            print("[INFO] Available peers:")
            for name, (ip, port) in self.friends.items():
                print(f" - {name} @ {ip}:{port}")
    
    def refresh_peer_list(self):
        """Refresh the peer list from the server."""
        print("[INFO] Refreshing peer list...")
        
        # Start or clear friends list
        if not hasattr(self, "friends"):
            self.friends = {}
        else:
            self.friends.clear()
        
        self.send(self.con_out, "REFRESH")
        print("[INFO] Peer list updated.")

    def handle_peer_list_update(self, msg: bytes|str) -> None:
        """Listening function to handle incoming peer list updates."""
        if not hasattr(self, "friends"):
            self.friends = {}
        
        if msg.startswith("[PLU]:"):
            self.con_out.sendall("ACK".encode())
            print("Sent ACK for peer list update")
            data = msg.replace("[PLU]:", "").strip()
            fn, fip, fpt = data.strip().split(",")
            fpt = int(fpt)
            self.friends[fn] = (fip, fpt)
                    
        elif msg.startswith("[FIN]"):
            self.con_out.sendall("ACK".encode())
            print("Sent ACK for end of peer list")
            print("[INFO] Peer list update complete.")

    def disconnect_from_server(self):
        """Disconnect from the server."""
        print("[INFO] Disconnecting from server...")
        try:
            self.send(self.con_out, "DISCONNECT")
            self.con_out.close()
            del self.con_out
            self.server_connected = False
            print("[INFO] Disconnected.")
        except Exception as e:
            print(f"[ERROR] Error while disconnecting: {e}")

    def connect_to_peer(self, peer_name: str):
        """Coordinate with the server and attempt a TCP hole punch."""
        print(f"[INFO] Requesting connection to {peer_name}")
        self.send(self.con_out, f"REQ_PEER:{peer_name}")
        return
    
    def handle_thread_to_peer(self):
        """Handle incoming messages from the peer."""
        if not hasattr(self, "peer_socket"):
            print("[ERROR] No peer socket available.")
            return
        
        while True:
            try:
                data = self.peer_socket.recv(4096)
                if not data:
                    print("[INFO] Peer closed connection")
                    self.peer_socket.close()
                    del self.peer_socket
                    break
                print(f"[PEER] {data.decode(errors='ignore')}")
            except BlockingIOError:
                pass
            except Exception as e:
                print(f"[ERROR] Error receiving from peer: {e}")
                break

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
                self.conn, f"[PLU]:{name},{ip},{port}".encode()
            )
        
        # Send end of list marker
        self.server._send_with_ack(
            self.conn, "[FIN]".encode()
        )

    def _dispatch_command(self, data: str):
        """Route incoming client requests"""
        print(f"[INFO] Received from {self.client_name}: {data}")
        if data.startswith("REQ_PEER:"):
            time.sleep(1)
            self._handle_peer_request(data)
        elif data == "REFRESH":
            self._send_peer_list()
        elif data == "DISCONNECT":
            self._handle_disconnect()
        elif data.startswith("READY_HOLE_PUNCH"):
            self.conn.send("ACK".encode())
            self.server.mark_peer_ready(self.client_name)
            print(f"[INFO] {self.client_name} is ready for hole punch.")
        else:
            print(f"[INFO] Unknown command from {self.client_name}: {data}")

    def _handle_peer_request(self, data: str):
        """Client requests connection to peer"""
        requested_name = data.split("REQ_PEER:")[1].strip()
        if requested_name not in self.server.client_list:
            self.server._send_with_ack(self.conn, "PEER_NOT_FOUND:".encode())
        else:
            self.server.handle_hole_punch(
                requester=self.client_name,
                target=requested_name
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
    pending_hole_punches = {}

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
            conn.send(data)
            print(f"[INFO] Sent data to {conn.getpeername()}")
        except Exception as e:
            print(f"[ERROR] Failed to send data: {e}")

    def handle_hole_punch(self, requester: str, target: str) -> None:
        """
            Coordinate hole punch between two peers:

            Params:
                requester: Name of the peer requesting the connection
                target: Name of the peer to connect to
        """
        if target not in self.client_list:
            print(f"[ERROR] Target peer {target} not found.")
            return
        
        # Step 1: Tell both peers to start listening
        requester_conn = self.client_list[requester][0]
        target_conn = self.client_list[target][0]
        requester_addr = self.client_list[requester][1]
        target_addr = self.client_list[target][1]

        # connections = {requester: requester_conn, target: target_conn}
        # addrs = {requester: requester_addr, target: target_addr}

        session_key = tuple(sorted([requester, target]))
        self.pending_hole_punches[session_key] = set()

        # Step 2: Wait for both peers to be ready
        target_conn.send(f"PREPARE_HOLE_PUNCH:{requester_addr}".encode())
        time.sleep(2)
        requester_conn.send(f"PREPARE_HOLE_PUNCH:{target_addr}".encode())
        
        # Step 3: Send both peers the IP and Port of other peer
        # requester_conn.send(f"START_HOLE_PUNCH:{target_addr[0]},{target_addr[1]}".encode())
        # target_conn.send(f"START_HOLE_PUNCH:{requester_addr[0]},{requester_addr[1]}".encode())

    def mark_peer_ready(self, peer_name):
        """Called when a peer sends READY_HOLE_PUNCH"""
        # Find session that includes this peer
        print("DEBUG: mark_peer_ready called for", peer_name)
        for session_key, ready_set in list(self.pending_hole_punches.items()):
            if peer_name in session_key:
                ready_set.add(peer_name)
                if len(ready_set) == 2:
                    # Both ready — send START to both
                    peer1, peer2 = session_key
                    conn1, addr1 = self.client_list[peer1]
                    conn2, addr2 = self.client_list[peer2]
                    conn1.send(f"START_HOLE_PUNCH:{addr2[0]},{addr2[1]}".encode())
                    conn2.send(f"START_HOLE_PUNCH:{addr1[0]},{addr1[1]}".encode())
                    del self.pending_hole_punches[session_key]
                break


if __name__ == "__main__":
    pass
