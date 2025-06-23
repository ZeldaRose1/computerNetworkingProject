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
        self.personal = configparser.ConfigParser()
        self.friends = configparser.ConfigParser()
        self.files = configparser.ConfigParser()

        # Setup personal setting file
        if os.path.exists(os.path.join(path, "personal.ini")):
            self.personal.read(os.path.join(path, "personal.ini"))
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
            self.personal["p"]["DEFAULT_PORT"] = "4144"
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

        def __del__(self):
            """ Destructor for Config class, saves all files before exiting"""
            save_conf(self)

        def save_conf(self, files="all"):
            """Save conf without deleting the class"""
            if files == "all" or files == "personal":
                with open(os.path.join(path, "personal.ini"), "w") as f1:
                    self.personal.write(f1)

            if files == "all" or files == "friends":
                with open(os.path.join(path, "friends.ini"), "w") as f2:
                    self.friends.write(f2)

            if files == "all" or files == "files":
                with open(os.path.join(path, "files.ini"), "w") as f3:
                    self.files.write(f3)


if __name__ == "__main__":
    pass
