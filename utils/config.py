#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File to read and store configuration attributes for ease of access.
"""

import os
import configparser

from nacl.public import PrivateKey


class Config:
    def __init__(self, path=os.path.expanduser("~/.config/sft")):
        """
        Constructor function for Config class. Uses the configparser package
        to manage an ini file. Configuration will be split into individual
        files to maintain modularity and allow for multiple entries per
        section.
        Public and private keys are saved to the folder in hexadecimal format
        and converted back into byte strings upon reading.

        Params:
            path (str): path to conf folder. Defaults is home/.config/sft
            folder

        Returns:
            None
        """
        self.path = path

        self.personal = configparser.ConfigParser()
        self.friends = configparser.ConfigParser()
        self.files = configparser.ConfigParser()

        # Setup personal setting file
        if os.path.exists(os.path.join(self.path, "personal.ini")):
            # Load attributes
            self.personal.read(os.path.join(self.path, "personal.ini"))
            self.secret_key = bytes.fromhex(self.personal["p"]["SECRET_KEY"])
            self.public_key = bytes.fromhex(self.personal["p"]["PUBLIC_KEY"])
            self.default_port = int(self.personal["p"]["DEFAULT_PORT"])
        else:
            if not os.path.exists(path):
                # Make subdirectories for the folder
                os.makedirs(path)

            # Create section before adding anything to it.
            self.personal["p"] = {}

            # Generate NaCl private key object
            sk = PrivateKey.generate()

            # Save public and private keys to the config file
            self.personal["p"]["SECRET_KEY"] = sk._private_key.hex()
            self.personal["p"]["PUBLIC_KEY"] = sk.public_key._public_key.hex()
            self.secret_key = sk._private_key
            self.public_key = sk.public_key._public_key
            self.personal["p"]["DEFAULT_PORT"] = "5000"
            with open(os.path.join(path, "personal.ini"), "w") as f1:
                self.personal.write(f1)

        # Setup friend list config
        if os.path.exists(os.path.join(path, "friends.ini")):
            # TODO: write code to translate all public keys in friend list
            # back into byte strings
            self.friends.read(os.path.join(path, "friends.ini"))
        else:
            with open(os.path.join(path, "friends.ini"), "w") as f2:
                self.friends.write(f2)

        # Setup file list config
        if os.path.exists(os.path.join(path, "files.ini")):
            self.files.read(os.path.join(path, "files.ini"))
        else:
            with open(os.path.join(path, "files.ini"), "w") as f3:
                self.files.write(f3)
        
    def get_username(self):
        """Get the username from the personal config."""
        try:
            return self.personal["p"]["USERNAME"]
        except KeyError:
            un = input("Enter your username: ")
            self.personal["p"]["USERNAME"] = un
            self.save_conf("personal")
            return un
    
    def save_friend(
            self,
            friend_name: str,
            friend_ip: str,
            friend_port: int,
            friend_public_key: str
        ) -> None:
        """
        Save a friend's information to the friends config file.
        
        Params:
            friend_name (str): The name of the friend.
            friend_ip (str): The IP address of the friend.
            friend_port (int): The port number of the friend.
            friend_public_key (str): The public key of the friend in hex format.
        
        Returns:
            None
        """
        if self.friends.has_section(friend_name):
            print("Friend already exists: Updating data")
        else:
            self.friends[friend_name] = {}

        self.friends[friend_name]["IP"] = friend_ip
        self.friends[friend_name]["PORT"] = str(friend_port)
        self.friends[friend_name]["PUBLIC_KEY"] = friend_public_key
        
        self.save_conf("friends")
        return
    
    def print_friends(self) -> None:
        """Print the list of friends from the config file."""
        if not self.friends.sections():
            print("No friends found.")
            return
        
        print("\n--- Friends List ---")
        for friend in self.friends.sections():
            ip = self.friends[friend].get("IP", "Unknown IP")
            port = self.friends[friend].get("PORT", "Unknown Port")
            print(f"Name: {friend}, IP: {ip}, Port: {port}")
        print("---------------------\n")
        return

    def __del__(self):
        """ Destructor for Config class, saves all files before exiting"""
        self.save_conf(self)

    def save_conf(self, files="all"):
        """Save conf without deleting the class"""
        # Verify folder exists
        if not os.path.isdir(self.path):
            os.makedirs(self.path)

        # Save files based on input
        if files == "all" or files == "personal":
            with open(os.path.join(self.path, "personal.ini"), "w") as f1:
                self.personal.write(f1)

        if files == "all" or files == "friends":
            with open(os.path.join(self.path, "friends.ini"), "w") as f2:
                self.friends.write(f2)

        if files == "all" or files == "files":
            with open(os.path.join(self.path, "files.ini"), "w") as f3:
                self.files.write(f3)


if __name__ == "__main__":
    pass
