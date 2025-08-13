#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""utils.menu.py
This module provides a menu interface for the Peer and Rendezvous classes.
It allows users to interact with the peer-to-peer network, and handles
all functions related to the peer menu.

It will be spit into an abstract class, and two concrete classes:
- PeerMenu: for the Peer class
- RendezvousMenu: for the Rendezvous class
This will allow for better separation of concerns and easier maintenance.
"""

from abc import ABC
from abc import abstractmethod


class BaseMenu(ABC):
    @abstractmethod
    def run(self):
        """Main loop for the menu."""
        pass


class PeerMenu(BaseMenu):
    def __init__(self, peer):
        self.peer = peer

    def run(self):
        """Main loop for the Peer menu."""
        while True:
            if hasattr(self.peer, 'peer_socket'):
                self.peer.peer_connected = True

            if self.peer.peer_connected:
                print("\n--- Peer-Peer Menu ---")
                print("1. Send Message to Peer")
                print("2. Transfer File to Peer")
                print("3. Disconnect from Peer")
                print("4. Disconnect from Server")
                print("5. Connect to Server")
                print("6. Exit Program")
                response = input("Please enter your command:\t")

                match response:
                    case "1":
                        message = input("Enter the message to send: ")
                        self.peer.peer_socket.sendall(message.encode())
                    case "2":
                        file_path = input("Enter the path to the file to send: ")
                        self.peer.transfer_file(file_path)
                    case "3":
                        self.peer.peer_socket.close()
                        del self.peer.peer_socket
                        print("Disconnected from peer.")
                    case "4":
                        if self.peer.server_connected:
                            self.peer.disconnect_from_server()
                            print("Disconnected from server.")
                        else:
                            print("You are not connected to a server.")
                    case "5":
                        ip = input("Enter the server IP address: ")
                        port = input("Enter the server port: ")
                        self.peer.connect_to_server(ip, int(port))
                    case "6":
                        print("Exiting program.")
                        break
                    case _:
                        print("Invalid command. Please try again.")

            elif self.peer.server_connected:
                print("\n--- Peer-Server Menu ---")
                print("1. Print list of peers")
                print("2. Refresh peer list from server")
                print("3. Disconnect from server")
                print("4. Connect to a specific peer")
                print("5. Exit program")
                print("6. Manually start a peer")
                response = input("Please enter your command:\t")

                match response:
                    case "1":
                        self.peer.print_peers()
                    case "2":
                        self.peer.refresh_peer_list()
                    case "3":
                        self.peer.disconnect_from_server()
                    case "4":
                        peer_name = input("Enter the name of the peer to connect to: ")
                        self.peer.connect_to_peer(peer_name)
                    case "5":
                        print("Exiting program.")
                        break
                    case "6":
                        # Debug mode
                        while True:
                            try:
                                inp = input("Enter Python code to execute:\n")
                                if inp.strip() == "exit":
                                    print("Exiting debug mode.")
                                    break
                                exec(inp)
                            except Exception as e:
                                print(f"Error executing code: {e}")
                    case _:
                        print("Invalid command. Please try again.")
            # No Connection
            else:
                print("\n--- No Connection ---")
                print("1. Connect to Rendezvous Server")
                print("2. Manual Connect to Peer")
                print("3. Exit Program")
                response = input("Please enter your command:\t")

                match response:
                    case "1":
                        ip = input("Enter the server IP address: ")
                        port = input("Enter the server port: ")
                        self.peer.connect_to_server(ip, int(port))
                    case "2":
                        local_ip = input("Enter IP you wish to bind to: ")
                        local_port = input("Enter port you wish to bind to: ")
                        peer_ip = input("Enter the peer's IP address: ")
                        peer_port = input("Enter the peer's port: ")
                        self.peer.peer_socket = self.peer.hole_punch(local_ip, int(local_port), peer_ip, int(peer_port))
                    case "3":
                        print("Exiting program.")
                        break
                    case _:
                        print("Invalid command. Please try again.")



if __name__ == "__main__":
    pass