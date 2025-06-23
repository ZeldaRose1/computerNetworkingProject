#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class for individual files to facilitate bundling and encryption

Need to import data from config file
"""
import os

from nacl.public import Box

from models.friend import Friend
from utils.config import Config

# Initialize configuration file so File classes can read config
conf = Config()


class File:
    def __init__(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError("Cannot initialise File object")
        # Pull name from the last part of the path
        self.name = path.split("/")[-1]
        self.path = path
        self.size = os.path.getsize(path)
        self.encrypted_file = None
        # Read file as byte stream
        with open(path, "rb") as f:
            self.file = f.read()
        self.chunks = {}
        self.chunks = self.split_file()

    def __del__(self):
        del self.name
        del self.path
        del self.size
        self.chunks.clear()
        del self.chunks
        del self.file
        if self.encrypted_file:
            del self.encrypted_file

    def encrypt(self, friend: Friend):
        """Encrypt file with public - private encryption"""
        # Make encryption box
        box = Box(conf.secret_key, friend.public_key)
        # Read file to be encrypted
        with open(self.path, "rb") as f:
            file_stream = f.read()
        self.encrypted_file = box.encrypt(file_stream)

    def decrypt(self, friend: Friend):
        """Decrypt encrypted file sent by friend"""
        box = Box(conf.secret_key, friend.public_key)
        self.file = box.decrypt(self.encrypted_file)

    def split_file(self, chunk_size: int = 1024 * 1024) -> dict[int, bytes]:
        """
        Split file into chunks for ease of transfer

        Params:
            chunk_size (int): size of individual chunks

        Returns:
            None
        """
        # Calculate number of chunks
        chunk_count = (self.size // chunk_size) + 1
        for c in range(chunk_count):
            start = c * chunk_size
            end = min((c + 1) * chunk_size, self.size)
            self.chunks[c] = self.file[start:end]


if __name__ == "__main__":
    pass
