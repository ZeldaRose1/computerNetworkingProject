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
            
            print("\n--- Peer Menu ---")
            print("1. Print list of peers")
            print("2. Refresh peer list from server")
            print("3. Disconnect from server")
            print("4. Connect to a specific peer")
            print("5. Exit program")
            response = input("Please enter your command:\t")

            match response:
                case "1":
                    self.peer.print_peers()
                case "2":
                    self.peer.refresh_peer_list()
                case "3":
                    self.peer.disconnect_from_server()
                    break
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
                                continue
                            exec(inp)
                        except Exception as e:
                            print(f"Error executing code: {e}")

                    break
                case _:
                    print("Invalid command. Please try again.")


if __name__ == "__main__":
    pass