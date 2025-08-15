#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class for individual files to facilitate bundling and encryption

Need to import data from config file
"""
import base64
import os

from nacl.public import Box
from nacl.public import PrivateKey
from nacl.public import PublicKey
from nacl.bindings import crypto_box_beforenm

from models.friend import Friend
from utils.config import Config

# Initialize configuration file so File classes can read config
conf = Config()


class File:
    def __init__(self, path, new_file=False, chunk_size=1024):
        # Load file if it exists
        if not os.path.exists(path) and not new_file:
            raise FileNotFoundError("Cannot initialise File object")
        
        # Create new file if we are saving a new file
        elif new_file and not os.path.exists(path):
            # Create blank file if it does not exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, 'w').close()

        # Pull name from the last part of the path
        self.name = path.split("/")[-1]
        self.path = path
        if not new_file:
            self.size = os.path.getsize(path)
            self.greatest_chunk = self.size // chunk_size + 1
        else:
            self.size = 0

        self.chunk_size = chunk_size

    def __del__(self):
        del self.name
        del self.path
        del self.size

    def encrypt_bytes(self, private_key: bytes|PrivateKey, public_key: bytes|PublicKey, data: bytes) -> bytes:
        """
            Encrypt file with public - private encryption

            Params:
                private_key (bytes): private key of the user
                public_key (bytes): public key of the friend
                data (bytes): data to be encrypted
            
            Returns:
                bytes: encrypted data
        """
        # Verify keys are in bytes
        if isinstance(private_key, str):
            private_key = private_key.decode()
        if isinstance(public_key, str):
            public_key = public_key.decode()
        
        # Make nacl.key objects
        if isinstance(private_key, bytes):
            private_key = PrivateKey(private_key)
        if isinstance(public_key, bytes):
            public_key = PublicKey(public_key)

        # Make encryption box
        # print("Private key:", private_key)
        # print("Public key:", public_key)
        box = Box(private_key, public_key)
        
        # Ensure data is in bytestream format
        if not isinstance(data, bytes):
            data = data.encode()
        
        # Verify key
        print(f"[DEBUG]: Box verification\n{crypto_box_beforenm(public_key.encode(), private_key.encode()).hex()}")

        # Return encrypted data
        return base64.b64encode(box.encrypt(data)).decode()

    def decrypt(self, secret_key: str, public_key: str, data: bytes) -> bytes:
        """
            Decrypt encrypted file sent by friend
        
            Params:
                secret_key: secret key of user in format of a hex string
                public_key: public key of friend in format of a hex string
        """
        # print("[DEBUG]: File.decrypt() called")
        # Verify correct type for keys
        if isinstance(secret_key, bytes) or isinstance(public_key, bytes):
            raise TypeError(
                f" \
                    Error in File.decrypt: both keys must be \
                    in string format as hex objects.\n types are \
                    secret_key: {type(secret_key)}\npublic_key: \
                    {type(public_key)}\
                "
            )

        # Convert the string
        secret_key = PrivateKey(bytes.fromhex(secret_key))
        public_key = PublicKey(bytes.fromhex(public_key))
        
        # Check keys
        # print("Secret key", secret_key)
        # print("public key", public_key)

        data = base64.b64decode(data)
        box = Box(secret_key, public_key)
        print(f"[DEBUG]: Box verification\n{crypto_box_beforenm(public_key.encode(), secret_key.encode()).hex()}")
        if isinstance(data, str):
            unencrypted_data = box.decrypt(data.encode())
        elif isinstance(data, bytes):
            unencrypted_data = box.decrypt(data)
        
        print(f"[DEBUG]: ----- unencrypted_data: {unencrypted_data} -----")
        return unencrypted_data

    def get_chunk(self, chunk_number: int) -> bytes:
        """
        Get a specific chunk of the file.

        Params:
            chunk_number (int): The chunk number to retrieve.

        Returns:
            bytes: The requested chunk of the file.
        """

        if chunk_number < 0:
            chunk_number = 0

        if 0 <= chunk_number <= self.greatest_chunk:
            with open(self.path, "rb") as f:
                f.seek(int(chunk_number) * int(self.chunk_size))
                return f.read(self.chunk_size)
        else:
            raise ValueError(f"Chunk {chunk_number} does not exist.")


if __name__ == "__main__":
    pass
